from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, ChatHistory
from forms import SignupForm, LoginForm
from gemini_config import model
from air_pollution import get_air_pollution_data
from config import Config
from flask_migrate import Migrate
from markupsafe import Markup
import re

app = Flask(__name__)
migrate = Migrate(app, db)

# ===================== DATABASE CONFIGURATION =======================
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

# Initialize Login Manager (session manage + handle user auth)
login_manager = LoginManager() 
login_manager.init_app(app)
login_manager.login_view = 'login'  # Set the login view (redirect if user not logged in)

# ================== User Load Function used by Flask-Login ===================
@login_manager.user_loader  # decorator func - load user from database using their user_id
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================== HOME ROUTES =====================
@app.route('/')
def home():
    return render_template('base.html')

# ===================== SIGNUP ROUTES =====================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        # Check if the username already exists in the database
        existing_user_by_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_by_username:
            flash('Username is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))

        # Check if the email already exists in the database
        existing_user_by_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_by_email:
            flash('Email is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))

        # If both username and email are unique, check if passwords match
        if form.password.data != form.confirm_password.data:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('signup'))

        # If passwords match, create the user
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

# ===================== LOGIN ROUTES =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

# ===================== LOGOUT ROUTES =====================
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ===================== DASHBOARD ROUTES =====================
@app.route('/dashboard')
@login_required
def index():
    return render_template('index.html', username=current_user.username)

# ===================== AIR POLLUTION PAGE ROUTES =====================
@app.route('/air_pollution', methods=['GET', 'POST'])
@login_required
def air_pollution():
    air_pollution_data, recommendations, suggestions, weekly_forecast = get_air_pollution_data(request)
    
    if air_pollution_data is None:
        flash('Error fetching air pollution data.', 'danger')
        return redirect(url_for('index'))

    return render_template(
        'air_pollution.html',
        air_pollution=air_pollution_data,  
        recommendations=recommendations,
        suggestions=suggestions,
        weekly_forecast=weekly_forecast
    )

# ===================== CHATBOT RESPONSE =====================
def format_response(text):
    cleaned_text = re.sub(r'[\*\_]', '', text)
    formatted_text = re.sub(r'(^[A-Za-z\s]+:)', r'<b>\1</b><br><br>', cleaned_text, flags=re.M)
    formatted_text = re.sub(r'(\.)(\s+)', r'.<br><br>', formatted_text)
    return Markup(formatted_text)

def sanitize_title(title):
    # Remove any special characters like * or _
    return re.sub(r'[\*\_]', '', title).strip()

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        user_input = request.json.get('message')
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        # Start a chat session and send user input to the bot -- (methods of gemini)
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_input)
        
        bot_response = response.text.strip()
        formatted_response = format_response(bot_response)

        # Create prompt to generate a meaningful title from both user input and bot response
        title_prompt = f"Generate a concise and meaningful title for a conversation that reflects the full context of the interaction. Include user input.\n\nUser: {user_input}"
        title_response = model.start_chat(history=[]).send_message(title_prompt).text.strip()

        # Ensure the title is meaningful and doesn’t exceed 100 characters
        if len(title_response) > 100:
            title_response = title_response[:100] + "..."

        # Save chat history with the generated title
        chat_history = ChatHistory(
            user_id=current_user.id,  
            user_input=user_input,
            bot_response=formatted_response,
            title=title_response  # Set the title generated by Gemini
        )
        db.session.add(chat_history)
        db.session.commit()

        return jsonify({'response': formatted_response})

    return render_template('chatbot.html')

# ===================== CHAT HISTORY ROUTES =====================
@app.route('/history')
@login_required
def history():
     # Calculate the date 7 days ago from the current date
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Fetch chat history for the current user (only chats from the last 7 days)
    history = ChatHistory.query.filter(
        ChatHistory.user_id == current_user.id,  # Filter by the current user
        ChatHistory.timestamp >= seven_days_ago  # Only include chats from the last 7 days
    ).order_by(ChatHistory.timestamp.desc()).all()  # latest chats first
    
    return render_template('history.html', history=history)


# ===================== CHAT DETAIL ROUTE =====================
@app.route('/history/<int:chat_id>')
@login_required
def chat_detail(chat_id):
    chat = ChatHistory.query.get_or_404(chat_id) # get chat history from db provided by chat_id

    if chat.user_id != current_user.id:
        flash('You do not have permission to view this chat.', 'danger')
        return redirect(url_for('history'))

    return render_template('chat_detail.html', chat=chat)

# ===================== EDIT CHAT ROUTE =====================
@app.route('/history/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def edit_title(chat_id):
    chat = ChatHistory.query.get_or_404(chat_id)

    if request.method == 'POST':
        new_title = request.form.get('title')

        if not new_title:
            # Agar user ne title nahi diya toh, existing title ko hi use karo
            new_title = chat.title  # jo chatbot route me pehle generate hua tha

        new_title = sanitize_title(new_title)

        if len(new_title) > 100:
            new_title = new_title[:100] + "..." 

        # Update the chat title
        chat.title = new_title
        db.session.commit()
        return redirect(url_for('chat_detail', chat_id=chat.id))

    return render_template('edit_title.html', chat=chat)

# ==================== DELETE CHAT ROUTE =====================
@app.route('/history/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    chat = ChatHistory.query.get_or_404(chat_id)

    if chat.user_id != current_user.id:
        flash('You do not have permission to delete this chat.', 'danger')
        return redirect(url_for('history'))

    db.session.delete(chat)
    db.session.commit()
    return redirect(url_for('history'))

# ===================== APP RUN =====================
if __name__ == '__main__':
    app.run(debug=True)
