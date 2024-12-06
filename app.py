from flask import Flask, render_template, request
import requests, datetime
  
app = Flask(__name__)
 
@app.route('/')
def index():
   return render_template('index.html')
 
@app.route('/air_pollution', methods=['GET', 'POST'])
def air_pollution():
   air_pollution_data = None
   if request.method == 'POST':
        Latitude = request.form['Latitude']
        Longitude = request.form['Longitude']
        info = request.form['info']
        API_KEY = 'c04faa84bc5f1882f53f19f8cbe9eb72'
        
   # Current air_pollution API call
   current_url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
   current_response = requests.get(current_url)
   current_data = current_response.json()
 
   air_pollution_data = {
           'info' : info,
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
   
   # Fetch AIR Polution Forecast Data 

   # Weekly forecast API call
   forecast_url = f'http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={Latitude}&lon={Longitude}&appid={API_KEY}&units=metric'
   forecast_response = requests.get(forecast_url)
   forecast_data = forecast_response.json()
 
 
   weekly_forecast = []
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
   else:
       error_message = forecast_data['message']
       return render_template('error.html', error_message=error_message)
 


 
   return render_template('air_pollution.html', air_pollution=air_pollution_data, weekly_forecast=weekly_forecast )
 
 
if __name__ == '__main__':
   app.run(debug=True)
