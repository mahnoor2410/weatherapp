from datetime import datetime
import requests
import re
from gemini_config import model

def get_air_pollution_data(request):
    air_pollution_data = None
    recommendations = None
    suggestions = None
    weekly_forecast = []
    hourly_data = []
    hourly_pm25 = []
    hourly_pm10 = []
    selected_time = None
    selected_aqi = None
    daily_data = []

    if request.method == 'POST':
        Latitude = request.form['Latitude']
        Longitude = request.form['Longitude']
        info = request.form['info']
        API_KEY = 'c04faa84bc5f1882f53f19f8cbe9eb72'

        try:
            # Current Air Quality API call
            current_url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
            current_response = requests.get(current_url)
            current_response.raise_for_status()
            current_data = current_response.json()
            aqi = current_data['list'][0]['main']['aqi']

            # Correct time, date, and day based on AQI data timestamp
            current_timestamp = current_data['list'][0]['dt']
            selected_time = datetime.now().strftime('%H:%M:%S')  # Current time for 'selected_time'
            selected_date = datetime.now().strftime('%Y-%m-%d')  # Current date for 'selected_date'

            air_pollution_data = {
                'info': info,
                'aqi': aqi,
                'co': current_data['list'][0]['components']['co'],
                'no': current_data['list'][0]['components']['no'],
                'no2': current_data['list'][0]['components']['no2'],
                'o3': current_data['list'][0]['components']['o3'],
                'so2': current_data['list'][0]['components']['so2'],
                'pm2_5': current_data['list'][0]['components']['pm2_5'],
                'pm10': current_data['list'][0]['components']['pm10'],
                'nh3': current_data['list'][0]['components']['nh3'],
                'dt': datetime.fromtimestamp(current_timestamp).strftime('%H:%M:%S'),
                'day': datetime.fromtimestamp(current_timestamp).strftime('%A'),
                'date': datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d')
            }

            # Recommendations & Suggestions
            chat_session = model.start_chat(history=[])
            recommendations_response = chat_session.send_message(
                f"Provide broader recommendations for dealing with current air quality issues at AQI level {aqi} in 3-4 lines without any Markdown or formatting."
            )
            suggestions_response = chat_session.send_message(
                f"Provide broader long term suggestions for dealing with air quality issues at AQI level {aqi} in 3-4 lines without any Markdown or formatting."
            )

            recommendations = truncate_text(re.sub(r'[\*\_]', '', recommendations_response.text))
            suggestions = truncate_text(re.sub(r'[\*\_]', '', suggestions_response.text))

            # Weekly Forecast
            forecast_url = f'http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
            forecast_response = requests.get(forecast_url)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            current_date = None
            forecast_group = None

            for forecast in forecast_data['list']:
                forecast_timestamp = forecast['dt']
                print(f"Forecast Raw Timestamp: {forecast_timestamp}")
                forecast_date = datetime.fromtimestamp(forecast_timestamp).strftime('%Y-%m-%d')
                forecast_day = datetime.fromtimestamp(forecast_timestamp).strftime('%A')

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

            # Hourly Data
            for data in forecast_data['list']:
                time_str = datetime.fromtimestamp(data['dt']).strftime('%H:%M:%S')
                hourly_data.append({'time': time_str, 'value': data['main']['aqi']})
                hourly_pm25.append({'time': time_str, 'value': data['components']['pm2_5']})
                hourly_pm10.append({'time': time_str, 'value': data['components']['pm10']})

            # Daily Data - Only one bar per day
            seen_dates = set()
            for forecast in forecast_data['list']:
                print(f"Raw Timestamp: {forecast['dt']}")  # Print raw timestamp
                forecast_date = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
                
                # Add daily data for each unique day
                if forecast_date not in seen_dates:
                    seen_dates.add(forecast_date)
                    daily_data.append({
                        'date': forecast_date,
                        'aqi': forecast['main']['aqi'],
                        'pm2_5': forecast['components'].get('pm2_5', 0),
                        'pm10': forecast['components'].get('pm10', 0),
                        'co': forecast['components'].get('co', 0),
                        'o3': forecast['components'].get('o3', 0),
                        'so2': forecast['components'].get('so2', 0),
                    })

        except requests.exceptions.RequestException as e:
            air_pollution_data = None
            recommendations = "Error fetching air pollution data."
            suggestions = "Please try again later."
            print(f"Request failed: {e}")

    return {
        'air_pollution_data': air_pollution_data,
        'recommendations': recommendations,
        'suggestions': suggestions,
        'weekly_forecast': weekly_forecast,
        'hourly_data': hourly_data,
        'hourly_pm25': hourly_pm25,
        'hourly_pm10': hourly_pm10,
        'selected_time': selected_time,  # Displaying current time
        'selected_aqi': selected_aqi,
        'daily_data': daily_data,
        'selected_date': selected_date  # Display current date
    }


def truncate_text(text, max_lines=4):
    lines = text.splitlines()
    return '\n'.join(lines[:max_lines])
