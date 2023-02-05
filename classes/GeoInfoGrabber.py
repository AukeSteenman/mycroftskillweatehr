import datetime
import http
import json
import urllib.request
from classes.dicts.weatherDict import weatherDict

class GeoInfoGrabber:
    
    @staticmethod
    def get_location(location):
        conn = http.client.HTTPSConnection('geocoding-api.open-meteo.com')
        conn.request("GET", "/v1/search?name="+location)
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        json_result = json.loads(result)
        latitude = json_result['results'][0]['latitude']
        longitude = json_result['results'][0]['longitude']
        return [latitude, longitude]
    
    @staticmethod
    def get_data(latitude, longitude, params):
        conn = http.client.HTTPSConnection('api.open-meteo.com')
        conn.request("GET", "/v1/forecast?latitude="+str(latitude)+"&longitude="+str(longitude)+"&hourly="+','.join(params))
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        return json.loads(result)
    
    @staticmethod
    def calculate_time(delay):
        date = datetime.datetime.now().date()
        date = str(date + datetime.timedelta(days=delay)).strip()
        time = str(datetime.datetime.now().hour).strip()+':00'
        hourCode = date+'T'+time
        return hourCode
