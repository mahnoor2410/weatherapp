# from datetime import datetime, timedelta
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# from flask_login import LoginManager, login_user, login_required, logout_user, current_user
# from models import db, User, ChatHistory
# from forms import SignupForm, LoginForm
# from gemini_config import model
# from air_pollution import get_air_pollution_data
# from config import Config
# from flask_migrate import Migrate
# import google.generativeai as genai
# from markupsafe import Markup
# import re

# app = Flask(__name__)
# migrate = Migrate(app, db)

# # ===================== DATABASE CONFIGURATION =======================
# app.config.from_object(Config)

# # Initialize the database
# db.init_app(app)

# # Initialize Login Manager (session manage + handle user auth)
# login_manager = LoginManager() 
# login_manager.init_app(app)
# login_manager.login_view = 'login'  # Set the login view (redirect if user not logged in)

# # ================== User Load Function used by Flask-Login ===================
# @login_manager.user_loader  # decorator func - load user from database using their user_id
# def load_user(user_id):
#     return User.query.get(int(user_id))

# # ===================== HOME ROUTES =====================
# @app.route('/')
# def home():
#     return render_template('base.html')

# # ===================== SIGNUP ROUTES =====================
# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     form = SignupForm()

#     if form.validate_on_submit():
#         # Check if the username already exists in the database
#         existing_user_by_username = User.query.filter_by(username=form.username.data).first()
#         if existing_user_by_username:
#             flash('Username is already taken. Please choose a different one.', 'danger')
#             return redirect(url_for('signup'))

#         # Check if the email already exists in the database
#         existing_user_by_email = User.query.filter_by(email=form.email.data).first()
#         if existing_user_by_email:
#             flash('Email is already taken. Please choose a different one.', 'danger')
#             return redirect(url_for('signup'))

#         # If both username and email are unique, check if passwords match
#         if form.password.data != form.confirm_password.data:
#             flash('Passwords do not match. Please try again.', 'danger')
#             return redirect(url_for('signup'))

#         # If passwords match, create the user
#         user = User(username=form.username.data, email=form.email.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Account created! Please log in.', 'success')
#         return redirect(url_for('login'))

#     return render_template('signup.html', form=form)

# # ===================== LOGIN ROUTES =====================
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.username.data).first()
#         if user and user.check_password(form.password.data):
#             login_user(user)
#             return redirect(url_for('index'))
#         else:
#             flash('Login Unsuccessful. Please check username and password', 'danger')
#     return render_template('login.html', form=form)

# # ===================== LOGOUT ROUTES =====================
# @app.route('/logout')
# def logout():
#     logout_user()
#     return redirect(url_for('index'))

# # ===================== DASHBOARD ROUTES =====================
# @app.route('/dashboard')
# @login_required
# def index():
#     return render_template('index.html', username=current_user.username)

# # ===================== AIR POLLUTION PAGE ROUTES =====================
# @app.route('/air_pollution', methods=['GET', 'POST'])
# @login_required
# def air_pollution():
#     air_pollution_data, recommendations, suggestions, weekly_forecast = get_air_pollution_data(request)
    
#     if air_pollution_data is None:
#         flash('Error fetching air pollution data.', 'danger')
#         return redirect(url_for('index'))

#     return render_template(
#         'air_pollution.html',
#         air_pollution=air_pollution_data,  
#         recommendations=recommendations,
#         suggestions=suggestions,
#         weekly_forecast=weekly_forecast
#     )

# # ===================== CHATBOT RESPONSE =====================
# def format_response(text):
#     cleaned_text = re.sub(r'[\*\_]', '', text)
#     formatted_text = re.sub(r'(^[A-Za-z\s]+:)', r'<b>\1</b><br><br>', cleaned_text, flags=re.M)
#     formatted_text = re.sub(r'(\.)(\s+)', r'.<br><br>', formatted_text)
#     return Markup(formatted_text)

# def sanitize_title(title):
#     # Remove any special characters like * or _
#     return re.sub(r'[\*\_]', '', title).strip()

# @app.route('/chatbot', methods=['GET', 'POST'])
# @login_required
# def chatbot():
#     if request.method == 'POST':
#         user_input = request.json.get('message')
#         if not user_input:
#             return jsonify({'error': 'No message provided'}), 400

#         # Start a chat session with Gemini
#         chat_session = model.start_chat(history=[])
#         response = chat_session.send_message(user_input)
        
#         bot_response = response.text.strip()
#         formatted_response = format_response(bot_response)

#         # Create prompt to generate a meaningful title from both user input and bot response
#         title_prompt = f"Generate a concise and meaningful title for a conversation that reflects the full context of the interaction. Include both user input and the bot's response.\n\nUser: {user_input}\nBot: {bot_response}"
#         title_response = model.start_chat(history=[]).send_message(title_prompt).text.strip()

#         # Ensure the title is meaningful and doesn’t exceed 100 characters
#         if len(title_response) > 100:
#             title_response = title_response[:100] + "..."

#         # Save chat history with the generated title
#         chat_history = ChatHistory(
#             user_id=current_user.id,  
#             user_input=user_input,
#             bot_response=formatted_response,
#             title=title_response  # Set the title generated by Gemini
#         )
#         db.session.add(chat_history)
#         db.session.commit()

#         return jsonify({'response': formatted_response})

#     return render_template('chatbot.html')

# # ===================== CHAT HISTORY ROUTES =====================
# @app.route('/history')
# @login_required
# def history():
#     seven_days_ago = datetime.utcnow() - timedelta(days=7)
#     history = ChatHistory.query.filter(
#         ChatHistory.user_id == current_user.id,
#         ChatHistory.timestamp >= seven_days_ago
#     ).order_by(ChatHistory.timestamp.desc()).all()

#     return render_template('history.html', history=history)

# # ===================== CHAT DETAIL ROUTE =====================
# @app.route('/history/<int:chat_id>')
# @login_required
# def chat_detail(chat_id):
#     chat = ChatHistory.query.get_or_404(chat_id)

#     if chat.user_id != current_user.id:
#         flash('You do not have permission to view this chat.', 'danger')
#         return redirect(url_for('history'))

#     return render_template('chat_detail.html', chat=chat)

# # ===================== EDIT CHAT ROUTE =====================

# @app.route('/history/<int:chat_id>', methods=['GET', 'POST'])
# @login_required
# def edit_title(chat_id):
#     chat = ChatHistory.query.get(chat_id)
#     if chat is None:
#         return jsonify({'error': 'Chat not found'}), 404

#     if request.method == 'POST':
#         # Get the new title from the form
#         new_title = request.form.get('title')

#         if not new_title:
#             # If no title provided, use Gemini to suggest a title based on the entire context of the conversation
#             bot_response = genai.GenerativeModel(
#                 model_name="gemini-1.5-pro",
#                 generation_config={
#                     "temperature": 1,
#                     "top_p": 0.95,
#                     "top_k": 40,
#                     "max_output_tokens": 8192,
#                     "response_mime_type": "text/plain",
#                 }
#             ).start_chat(history=[]).send_message(
#                 f"Generate a concise, context-aware title for this conversation. Use both user input and bot response to form a title that sums up the main topic.\n\nUser: {chat.user_input}\nBot: {chat.bot_response}"
#             ).text.strip()

#             # Clean the bot response and ensure it's a valid title
#             bot_response = format_response(bot_response)

#             # Use the Gemini suggestion directly as the new title
#             new_title = bot_response

#         # Clean and sanitize the title
#         new_title = sanitize_title(new_title)

#         # Ensure the title is meaningful and doesn’t exceed 100 characters
#         if len(new_title) > 100:
#             new_title = new_title[:100] + "..."

#         # Update the chat title
#         chat.title = new_title
#         db.session.commit()

#         return redirect(url_for('chat_detail', chat_id=chat.id))

#     return render_template('edit_title.html', chat=chat)

# # ===================== DELETE CHAT ROUTE =====================
# @app.route('/history/<int:chat_id>/delete', methods=['POST'])
# @login_required
# def delete_chat(chat_id):
#     chat = ChatHistory.query.get_or_404(chat_id)

#     if chat.user_id != current_user.id:
#         flash('You do not have permission to delete this chat.', 'danger')
#         return redirect(url_for('history'))

#     db.session.delete(chat)
#     db.session.commit()
#     return redirect(url_for('history'))

# # ===================== APP RUN =====================
# if __name__ == '__main__':
#     app.run(debug=True)










##################################################################################################33





# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Air Quality App</title>
#     <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
#     <style type="text/css">
#         #map {
#             height: 400px;
#             width: 600px;
#         }
#     </style>
# </head>
# <body>

# <div class="container">
#     <h4>Welcome, {{ username }}!
#         <a href="{{ url_for('logout') }}">Logout</a>
#         <a href="{{ url_for('chatbot') }}">ChatBot</a>
#     </h4>

#     <h2>Global Air Quality App</h2>
#     <p>Current and 5 Day Forecast Air Quality Data (Any Place on Google Map)</p>

#     <input id="searchInput" type="text" placeholder="Type Location (Auto Name)">
#     <form action="/air_pollution" method="post">
#         <input type="text" id="Lat" name="Latitude" placeholder="Latitude" required style="display:none;">
#         <input type="text" id="Lng" name="Longitude" placeholder="Longitude" required style="display:none;">
#         <input type="text" id="info" name="info" placeholder="info" style="display:none;">
#         <button type="submit">Get AQI Data</button>
#     </form>
#     <br>
#     <div id="successAlert" class="alert alert-success" role="alert" style="display:none;"></div>
#     <div id="errorAlert" class="alert alert-danger" role="alert" style="display:none;"></div>

#     <div id="map"></div>

#     {% if air_pollution_data %}
#         {% if air_pollution_data['air_pollution'] %}
#             <div id="air_pollution-result" class="air_pollution-result">
#                 <h1>Air Quality Index: {{ air_pollution_data['air_pollution']['aqi'] }}</h1>
#                 <p>CO: {{ air_pollution_data['air_pollution']['co'] }}</p>
#                 <p>PM2.5: {{ air_pollution_data['air_pollution']['pm2_5'] }}</p>
#                 <p>PM10: {{ air_pollution_data['air_pollution']['pm10'] }}</p>
#                 <p>NO2: {{ air_pollution_data['air_pollution']['no2'] }}</p>
#                 <p>O3: {{ air_pollution_data['air_pollution']['o3'] }}</p>
#                 <p>SO2: {{ air_pollution_data['air_pollution']['so2'] }}</p>
#                 <p>NH3: {{ air_pollution_data['air_pollution']['nh3'] }}</p>
#             </div>
#         {% else %}
#             <p class="error">Air quality data not available for this location.</p>
#         {% endif %}
#     {% else %}
#         <p class="error">No data found for this location or the location might be incorrect.</p>
#     {% endif %}
# </div>

# <!-- Recommendations Section -->
# <div class="container">
#     <div>
#         <h3>Current Air Quality Recommendations</h3>
#         <p>{{ recommendations }}</p>
#     </div>

#     <div>
#         <h3>Long-Term Suggestions</h3>
#         <p>{{ suggestions }}</p>
#     </div>
# </div>

# <!-- 4-Day Forecast Data -->
# <div class="container">
#     <h3>4 Day Forecast Data</h3>
#     <div class="forecast">
#         {% for forecast_group in weekly_forecast %}
#             <div class="forecast-group">
#                 <h4 style="background-color: rgb(219, 219, 219); padding: 5px; border-radius: 5px;">
#                     {{ forecast_group['day'] }}, {{ forecast_group['date'] }}
#                 </h4>
#                 <div class="forecast-item">
#                     <p>Air Quality Index: {{ forecast_group['aqi'] }}</p>
#                     <p>Carbon monoxide (CO): {{ forecast_group['co'] }}</p>
#                     <p>Particulates (PM2.5): {{ forecast_group['pm2_5'] }}</p>
#                 </div>
#             </div>
#         {% endfor %}
#     </div>
# </div>

# <!-- Graphs for Hourly & Daily Data (using Chart.js for plotting) -->
# <div class="container">
#     <!-- Buttons for Hourly / Daily View -->
#     <div class="button-container">
#         <button id="hourlyButton" onclick="changeView('Hourly')" class="selected">Hourly</button>
#         <button id="dailyButton" onclick="changeView('Daily')">Daily</button>
#     </div>

#     <!-- AQI and Chart Section -->
#     <div id="aqiSection">
#         <div id="hourlyView" style="display: block;">
#             <h3>Hourly Air Quality</h3>

#             <!-- Hourly AQI and Time -->
#             <div id="aqiTime">
#                 <p>Selected Time: {{ selected_time }}</p>
#                 <p>Selected AQI: {{ selected_aqi }}</p>
#             </div>

#             <!-- Hourly Bar Chart (using Chart.js) -->
#             <canvas id="hourlyChart"></canvas>

#             <div id="pollutants">
#                 <h4>PM2.5</h4>
#                 <canvas id="hourlyPm25Chart"></canvas>

#                 <h4>PM10</h4>
#                 <canvas id="hourlyPm10Chart"></canvas>
#             </div>
#         </div>

#         <div id="dailyView" style="display: none;">
#             <h3>Daily Air Quality</h3>

#             <!-- Daily AQI -->
#             <div id="dailyAqi">
#                 <p>Selected Date: {{ selected_time }}</p>
#                 <p>Selected AQI: {{ selected_aqi }}</p>
#             </div>

#             <!-- Daily Bar Chart (using Chart.js) -->
#             <canvas id="dailyChart"></canvas>

#             <div id="dailyPollutants">
#                 <h4>PM2.5</h4>
#                 <canvas id="dailyPm25Chart"></canvas>

#                 <h4>PM10</h4>
#                 <canvas id="dailyPm10Chart"></canvas>
#             </div>
#         </div>
#     </div>
# </div>

# <script
#     src="https://maps.gomaps.pro/maps/api/js?key=AlzaSyhqNEIUpRypzrhtdvV4-VgfidVRB0lFaNs&libraries=geometry,places">
# </script>

# <script type="text/javascript">
#     let hourlyData = {{ hourly_data | tojson }};
#     let dailyData = {{ daily_data | tojson }};
#     let hourlyPm25 = {{ hourly_pm25 | tojson }};
#     let hourlyPm10 = {{ hourly_pm10 | tojson }};

#     function initMap() {
#         var map = new google.maps.Map(document.getElementById('map'), {
#             center: {lat: 31.5436644, lng: 74.32700779},
#             zoom: 15
#         });

#         var input = document.getElementById('searchInput');
#         map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
#         var autocomplete = new google.maps.places.Autocomplete(input);
#         autocomplete.bindTo('bounds', map);

#         var infowindow = new google.maps.InfoWindow();
#         var marker = new google.maps.Marker({
#             map: map,
#             anchorPoint: new google.maps.Point(0, -29)
#         });

#         autocomplete.addListener('place_changed', function() {
#             infowindow.close();
#             marker.setVisible(false);
#             var place = autocomplete.getPlace();
#             if (!place.geometry) {
#                 window.alert("Autocomplete's returned place contains no geometry");
#                 return;
#             }

#             if (place.geometry.viewport) {
#                 map.fitBounds(place.geometry.viewport);
#             } else {
#                 map.setCenter(place.geometry.location);
#                 map.setZoom(13);
#             }

#             marker.setIcon({
#                 url: place.icon,
#                 size: new google.maps.Size(71, 71),
#                 origin: new google.maps.Point(0, 0),
#                 anchor: new google.maps.Point(17, 34),
#                 scaledSize: new google.maps.Size(35, 35)
#             });
#             marker.setPosition(place.geometry.location);
#             marker.setVisible(true);

#             infowindow.setContent('<div><strong>' + place.name + '</strong><br>' + place.formatted_address);
#             infowindow.open(map, marker);

#             document.getElementById('Lat').value = place.geometry.location.lat();
#             document.getElementById('Lng').value = place.geometry.location.lng();
#             document.getElementById('info').value = place.name;
#         });
#     }

#     google.maps.event.addDomListener(window, 'load', initMap);

#     function changeView(view) {
#         if (view === 'Hourly') {
#             document.getElementById('hourlyView').style.display = 'block';
#             document.getElementById('dailyView').style.display = 'none';
#             renderHourlyCharts();
#         } else {
#             document.getElementById('hourlyView').style.display = 'none';
#             document.getElementById('dailyView').style.display = 'block';
#             renderDailyCharts();
#         }
#     }

#     function renderHourlyCharts() {
#         const hourlyChart = new Chart(document.getElementById('hourlyChart'), {
#             type: 'bar',
#             data: {
#                 labels: hourlyData.map(item => item.time),
#                 datasets: [{
#                     label: 'Hourly AQI',
#                     data: hourlyData.map(item => item.value),
#                     backgroundColor: 'rgba(88, 191, 230, 0.3)',
#                     borderColor: 'rgba(88, 191, 230, 1)',
#                     borderWidth: 1
#                 }]
#             },
#             options: {
#                 responsive: true,
#                 scales: {
#                     y: {
#                         beginAtZero: true
#                     }
#                 }
#             }
#         });

#         const hourlyPm25Chart = new Chart(document.getElementById('hourlyPm25Chart'), {
#             type: 'line',
#             data: {
#                 labels: hourlyPm25.map(item => item.time),
#                 datasets: [{
#                     label: 'PM2.5',
#                     data: hourlyPm25.map(item => item.value),
#                     fill: false,
#                     borderColor: 'rgba(88, 191, 230, 1)',
#                     tension: 0.1
#                 }]
#             },
#             options: {
#                 responsive: true,
#                 scales: {
#                     y: {
#                         beginAtZero: true
#                     }
#                 }
#             }
#         });

#         const hourlyPm10Chart = new Chart(document.getElementById('hourlyPm10Chart'), {
#             type: 'line',
#             data: {
#                 labels: hourlyPm10.map(item => item.time),
#                 datasets: [{
#                     label: 'PM10',
#                     data: hourlyPm10.map(item => item.value),
#                     fill: false,
#                     borderColor: 'rgba(153, 102, 255, 1)',
#                     tension: 0.1
#                 }]
#             },
#             options: {
#                 responsive: true,
#                 scales: {
#                     y: {
#                         beginAtZero: true
#                     }
#                 }
#             }
#         });
#     }

#     function renderDailyCharts() {
#         const dailyChart = new Chart(document.getElementById('dailyChart'), {
#             type: 'bar',
#             data: {
#                 labels: dailyData.map(item => item.date),
#                 datasets: [{
#                     label: 'Daily AQI',
#                     data: dailyData.map(item => item.value),
#                     backgroundColor: 'rgba(88, 191, 230, 0.3)',
#                     borderColor: 'rgba(88, 191, 230, 1)',
#                     borderWidth: 1
#                 }]
#             },
#             options: {
#                 responsive: true,
#                 scales: {
#                     y: {
#                         beginAtZero: true
#                     }
#                 }
#             }
#         });
#     }
# </script>
# </body>
# </html>
