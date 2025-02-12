from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
from forms import SignupForm, LoginForm
from gemini_config import model  # Custom module for your Gemini AI model configuration
from air_pollution import get_air_pollution_data  # External function for air pollution API calls
from config import Config  # Import the Config class
from flask_migrate import Migrate
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
login_manager.login_view = 'login' # Set the login view (redirect if user not logged in)

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
        user = User(username=form.username.data, email=form.email.data) # query username + email from db on form submission
        user.set_password(form.password.data) # hash pass
        db.session.add(user) # user add in db session
        db.session.commit()  # changes
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

# ===================== LOGIN ROUTES =====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() # query user's username from db on form submission
        if user: # if user found
            print(f"User found: {user.username}, is_active: {user.is_active()}")
        if user and user.check_password(form.password.data):  
            login_user(user)  # finally login
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
# @login_required
def air_pollution():
    air_pollution_data, recommendations, suggestions, weekly_forecast = get_air_pollution_data(request) # call func
    
    if air_pollution_data is None:  # If no air pollution data, return an error message
        flash('Error fetching air pollution data.', 'danger')
        return redirect(url_for('index'))

    return render_template(
        'air_pollution.html',
        air_pollution=air_pollution_data,  
        recommendations=recommendations,
        suggestions=suggestions,
        weekly_forecast=weekly_forecast
    )

# ===================== CHATBOT ROUTES =====================

def format_response(text):
    """
    Format the chatbot's response:
    - Remove unwanted characters like * or _.
    - Bold headings (lines ending with ':' or similar heading indicators).
    - Add line breaks for better readability.
    """
    cleaned_text = re.sub(r'[\*\_]', '', text)  # Remove unwanted characters
    formatted_text = re.sub(r'(^[A-Za-z\s]+:)', r'<b>\1</b><br><br>', cleaned_text, flags=re.M)  # Bold headings
    formatted_text = re.sub(r'(\.)(\s+)', r'.<br><br>', formatted_text)  # Add line breaks after sentences
    return formatted_text

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        # Get the user's input from the request
        user_input = request.json.get('message')

        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        # Start a chat session with the Gemini AI model - built in methods to interact with the Gemini model
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_input)
        
        bot_response = response.text.strip() # Get the chatbot's response
        formatted_response = format_response(bot_response) # and format it

        return jsonify({'response': formatted_response})

    return render_template('chatbot.html')

if __name__ == '__main__':
    app.run(debug=True)
