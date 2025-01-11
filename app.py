from flask import Flask, render_template, request, jsonify
import requests, datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

app = Flask(__name__)

# ==================== GEMINI CONFIGURATION ============================
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# system_instruction
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction=(
        "Act as a knowledgeable and approachable environmental science guide, tailoring insights and actionable advice based on the Air Quality Index (AQI) levels. "
        " AQI is 1 good ,AQI is 2 Moderate , AQI is 3 Unhealthy for Sensitive Groups, AQI is 4 Very Unhealthy for all, AQI is 5 Hazardous . "
        "Provide clear and concise recommendations and suggestions as separate outputs. "
        "Recommendations should be specific actions to take for the current AQI level. "
        "Suggestions should include long-term or broader strategies to improve air quality or minimize risks in the future. "
    ),
)

# =============================== HOME PAGE ROUTE ====================================

@app.route('/')
def index():
    return render_template('index.html')
    
# =============================== CHATBOT ROUTE ====================================

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
        user_input = request.json.get('message')
        if not user_input:
            return jsonify({"error": "No message provided."}), 400

        # Generate Gemini response
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_input)
        
        bot_response = response.text.strip()

        # Format the response for proper display
        formatted_response = format_response(bot_response)

        return jsonify({"response": formatted_response})

    return render_template('chatbot.html')

# =============================== AIR POLLUTION PAGE ROUTE ====================================

@app.route('/air_pollution', methods=['GET', 'POST'])
def air_pollution():
    air_pollution_data = None
    recommendations = None
    suggestions = None
    weekly_forecast = []

    if request.method == 'POST':
        Latitude = request.form['Latitude']
        Longitude = request.form['Longitude']
        info = request.form['info']
        API_KEY = 'c04faa84bc5f1882f53f19f8cbe9eb72'

        # Current air pollution API call
        current_url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
        current_response = requests.get(current_url)
        current_data = current_response.json()

        air_pollution_data = {
            'info': info,
            'aqi': current_data['list'][0]['main']['aqi'],
            'co': current_data['list'][0]['components']['co'],
            'no': current_data['list'][0]['components']['no'],
            'no2': current_data['list'][0]['components']['no2'],
            'o3': current_data['list'][0]['components']['o3'],
            'so2': current_data['list'][0]['components']['so2'],
            'pm2_5': current_data['list'][0]['components']['pm2_5'],
            'pm10': current_data['list'][0]['components']['pm10'],
            'nh3': current_data['list'][0]['components']['nh3'],
            'dt': datetime.datetime.fromtimestamp(current_data['list'][0]['dt']).strftime('%H:%M:%S'),
            'day': datetime.datetime.now().strftime('%A'),
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }

        # Generate Gemini responses for recommendations and suggestions
        chat_session = model.start_chat(history=[])
        recommendations_response = chat_session.send_message(
            f"Provide specific recommendations for AQI level {air_pollution_data} in 3-4 lines without any Markdown or formatting."
        )
        suggestions_response = chat_session.send_message(
            f"Provide broader suggestions for dealing with air quality issues at AQI level {air_pollution_data} in 3-4 lines without any Markdown or formatting."
        )

        def truncate_text(text, max_lines=4): # function for cleaning response
            lines = text.splitlines()
            return '\n'.join(lines[:max_lines])

        recommendations = re.sub(r'[\*\_]', '', recommendations_response.text)
        suggestions = re.sub(r'[\*\_]', '', suggestions_response.text)

        recommendations = truncate_text(recommendations)
        suggestions = truncate_text(suggestions)

        # Weekly forecast API call
        forecast_url = f'http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()

        current_date = None
        forecast_group = None

        for forecast in forecast_data['list']:
            forecast_date = datetime.datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
            forecast_day = datetime.datetime.fromtimestamp(forecast['dt']).strftime('%A')
            if forecast_date != current_date:
                if forecast_group:
                    weekly_forecast.append(forecast_group)
                forecast_group = {
                    'day': forecast_day,
                    'date': forecast_date,
                    'aqi': forecast['main']['aqi'],
                    'co': forecast['components']['co'],
                    'pm2_5': forecast['components']['pm2_5'],
                    'forecasts': []
                }
                current_date = forecast_date

            forecast_item = {
                'aqi': forecast['main']['aqi'],
                'co': forecast['components']['co'],
                'pm2_5': forecast['components']['pm2_5'],
            }
            forecast_group['forecasts'].append(forecast_item)

        if forecast_group:
            weekly_forecast.append(forecast_group)

    return render_template(
        'air_pollution.html',
        air_pollution=air_pollution_data,
        recommendations=recommendations,
        suggestions=suggestions,
        weekly_forecast=weekly_forecast
    )

if __name__ == '__main__':
    app.run(debug=True)
