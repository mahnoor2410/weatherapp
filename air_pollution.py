import requests
import datetime
import re
from gemini_config import model

def get_air_pollution_data(request):
    air_pollution_data = None
    recommendations = None
    suggestions = None
    weekly_forecast = []

    if request.method == 'POST':
        Latitude = request.form['Latitude']
        Longitude = request.form['Longitude']
        info = request.form['info']
        API_KEY = 'c04faa84bc5f1882f53f19f8cbe9eb72'

        try:
            # =====================================  Current Air Quality API call  ======================================
            current_url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
            current_response = requests.get(current_url)
            current_response.raise_for_status()  # Raise an exception for HTTP errors

            current_data = current_response.json()
            aqi = current_data['list'][0]['main']['aqi']  # Extract AQI value

            # Store air pollution data
            air_pollution_data = {
                'info': info,
                'aqi': aqi,  # Store only the AQI value
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

            # ===================================== Get Recommendations and Suggestions from Gemini ======================================
            chat_session = model.start_chat(history=[])
            recommendations_response = chat_session.send_message(
                f"Provide broader recommendations for dealing with current air quality issues at AQI level  {aqi} in 3-4 lines without any Markdown or formatting."
            )
            suggestions_response = chat_session.send_message(
                f"Provide broader long term suggestions for dealing with air quality issues at AQI level {aqi} in 3-4 lines without any Markdown or formatting."
            )

            # Function for cleaning and truncating response
            def truncate_text(text, max_lines=4):  # function for cleaning response
                lines = text.splitlines()
                return '\n'.join(lines[:max_lines])

            # Clean and truncate the responses
            recommendations = re.sub(r'[\*\_]', '', recommendations_response.text)
            suggestions = re.sub(r'[\*\_]', '', suggestions_response.text)

            recommendations = truncate_text(recommendations)
            suggestions = truncate_text(suggestions)

            # =====================================  Weekly Air Quality Forecast API call ======================================
            forecast_url = f'http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
            forecast_response = requests.get(forecast_url)
            forecast_response.raise_for_status()  # Raise an exception for HTTP errors

            forecast_data = forecast_response.json()
            current_date = None
            forecast_group = None

            # Process and group the forecast data by date
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

        except requests.exceptions.RequestException as e:
            # Handle errors 
            air_pollution_data = None
            recommendations = "Error fetching air pollution data."
            suggestions = "Please try again later."
            print(f"Request failed: {e}")  

    return air_pollution_data, recommendations, suggestions, weekly_forecast
