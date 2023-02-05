# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.

# Below is the list of outside modules you'll be using in your skill.
# They might be built-in to Python, from mycroft-core or from external
# libraries.  If you use an external library, be sure to include it
# in the requirements.txt file so the library is installed properly
# when the skill gets installed later by a user.

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from classes.ExtractInfo import ExtractInfo
import enum
import datetime
import http
import json

class WeatherSkillInfo(MycroftSkill):
    # A specific trafic light cannot move from location and is fixed. This one is stationed in Amsterdam
    # If no location is given use the TRAFIC_LIGHT_LOCATION constant.
    TRAFIC_LIGHT_LOCATION = "Amsterdam"
    
    def __init__(self):
        super(WeatherSkillInfo, self).__init__(name="WeatherSkillInfo")
    
    # Determines if ExtractInfo should use given location or predefined TRAFIC_LIGHT_LOCATION
    def location_handler(self, location):
        info
        if location:
            info = ExtractInfo(location)
        else:
            location = self.TRAFIC_LIGHT_LOCATION 
            info = ExtractInfo(location)
            
        if info == 400:
            location = self.get_response('This location did not work can you provide another?')
            return self.location_handler(location)
        else:    
            return info
    
    # Determines which day the forecast should be given
    def delay(utterance):
        for key in delayDict:
            if delayDict[key] in utterance:
                return key
            
        return 0
    
    @intent_handler('weather_in_location.intent')
    def handle_weather(self, message):
        location = message.data.get('location')
        utterance = message.data.get('utterance')
        
        info = self.location_handler(location)
        
        currentWeather = info.get_weather(self.delay(utterance))
        self.speak_dialog("ofcouse, "+ currentWeather +" in "+location)
        
    @intent_handler('windspeed.intent')
    def handle_windspeed(self, message):
        location = message.data.get('location')
        utterance = message.data.get('utterance')
          
        info = self.location_handler(location)
            
        windspeed = info.get_wind_speed(self.delay(utterance))
        self.speak_dialog("The wind is blowing with a speed of: "+ windspeed)
        
    @intent_handler('temperature.intent')
    def handle_temperature(self, message):
        location = message.data.get('location')
        utterance = message.data.get('utterance')
        
        info = self.location_handler(location)
        
        temperature = info.get_temperature_forecast(self.delay(utterance))
        
        if "cool" in utterance or "cold" in utterance:
            if temperature > 15:
                self.speak_dialog("it is not cold, it is "+ temperature+"°C in "+ location)
            else:
                self.speak_dialog("it is cold, it is "+ temperature+"°C in "+ location)
        
        elif "hot" in utterance or "warm" in utterance:
            if temperature < 30:
               self.speak_dialog("it is not hot, it is "+ temperature+"°C in "+ location)
            else:
                self.speak_dialog("it is hot, it is "+ temperature+"°C in "+ location)
        else:
            self.speak_dialog("it is  "+ temperature+"°C in "+ location)
        
    @intent_handler('raining.intent')
    def handle_rain(self, message):
        location = message.data.get('location')
        utterance = message.data.get('utterance')

        info = self.location_handler(location)
        
        rain = info.get_rain_forecast(self.delay(utterance))
        
        if rain > 0:
            if "will" in utterance:
                self.speak_dialog("yes it will rain in"+location)
            else:
                self.speak_dialog("it is raining "+ rain+"mm in "+ location)
        else:
            if "will" in utterance:
                self.speak_dialog("no it will not rain in"+location)
            else:
                self.speak_dialog("it is not raining in "+ location)


def create_skill():
    return WeatherSkillInfo()

# This class handles the open-meteo api calls.
class GeoInfoGrabber:
    
    # Gets the longitude and latitude of a provided city.
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
    
    # Gets weather data from given longitude and latitude + added params these are the items that have to exrtracted from the API.
    @staticmethod
    def get_data(latitude, longitude, params):
        conn = http.client.HTTPSConnection('api.open-meteo.com')
        conn.request("GET", "/v1/forecast?latitude="+str(latitude)+"&longitude="+str(longitude)+"&hourly="+','.join(params))
        response = conn.getresponse()
        if response.status >= 400:
            return 400
        else:
            return json.loads(response.read().decode('utf-8'))
    
    # To get specific data from the open-meteo object there has to a be a certain timecode string. This function builds that string.
    @staticmethod
    def calculate_time(delay):
        date = datetime.datetime.now().date()
        date = str(date + datetime.timedelta(days=delay)).strip()
        time = str(datetime.datetime.now().hour).strip()+':00'
        hourCode = date+'T'+time
        return hourCode

# This class extrats data from the GeoInfoObject
class ExtractInfo(GeoInfoGrabber):
    
    weatherData = 0
    
    # Gets longitude and latitude from specific location and get weather data from that specific location.
    def __init__(self, location):
        latitude, longitude = GeoInfoGrabber.get_location(location)
        self.weatherData = GeoInfoGrabber.get_data(latitude, longitude, self.create_list_from_enum(params))
    
    # I store all the paramaters in a python Enum. This enum class has to be converted to a array so 
    # it can be passed to GeoInfoGrabber.get_data().
    def create_list_from_enum(self, enum):
        return [elem.value for elem in enum]    
    
    # Get current weather data, if a delay is greater than 0 it moves that amount of days ahead. delay = 7 = forecast in a week.
    # returns [specific timecode (hourCode), actual weather data without unnesecary objects attached (hourDataDict), 
    # get the index of which represents the hourcode. this index is used to grab specific data from the array at the right index(currentHourIndex)]
    def extract_specific_info(self, delay):
        hourCode = GeoInfoGrabber.calculate_time(delay)
        hourDataDict = self.weatherData['hourly']
        currentHourIndex = hourDataDict['time'].index(hourCode)
        return [hourCode, hourDataDict, currentHourIndex]
    
    # This functions extracts the weather object from the weatherData object.
    def get_weather(self, delay):
        hourCode, hourDataDict, currentHourIndex = self.extract_specific_info(delay)
        currentHourIndex = hourDataDict['time'].index(hourCode)
        return weatherDict[hourDataDict[params.WEATHERCODE.value][currentHourIndex]]
    
    # This functions extracts the wind object from the weatherData object.
    def get_wind_speed(self, delay):
        hourcode, hourDataDict, currentHourIndex = self.extract_specific_info(delay)
        return str(hourDataDict[params.WINDSPEED.value][currentHourIndex])+" km/h"
    
    # This functions extracts the rain object from the weatherData object.
    def get_rain_forecast(self, delay):
        hourcode, hourDataDict, currentHourIndex = self.extract_specific_info(delay)
        return str(hourDataDict[params.RAIN.value][currentHourIndex])+" mm"    
    
    # This functions extracts the temeprature object from the weatherData object.
    def get_temperature_forecast(self, delay):
        hourcode, hourDataDict, currentHourIndex = self.extract_specific_info(delay)
        return str(hourDataDict[params.TEMPERATURE.value][currentHourIndex])+" °C"  

# Enum clas which holds the paramaters that are given to the api call.
class params(enum.Enum):
    WEATHERCODE = 'weathercode'
    WINDSPEED   = 'windspeed_10m'
    RAIN        = 'rain'
    TEMPERATURE = 'temperature_2m'

# A dict which links sentence to number which can be used for a delay
delayDict = {
    1: 'tomorrow',
    2: 'day after tomorrow',
    7: 'in a week'
}

# The weathercode api call returns a weathercode which represents something. I have created this dict which translates
# the code to a readable meaning. This was not fun to make.
weatherDict = {
    0: 'Clear sky',
    1: 'The weather is mainly clear at the moment',
    2: 'It is partly clouded at the moment',
    3: 'There is a overcast at the moment',
    45: 'There is fog at the moment',
    48: 'There is depositing rime fog at the moment',
    51: 'There is light drizzle at the moment',
    53: 'There is moderate drizzle at the moment',
    55: 'There is heavy drizzle at the moment',
    56: 'There is slight freezing drizzle at the moment, take care!',
    57: 'There is dense freezing drizzle at the moment, take care!',
    61: 'It is slightly raining at the moment',
    63: 'It is raining at the moment',
    65: 'There is heavy rain at the moment',
    66: 'There is light freezing rain at the moment',
    67: 'There is heavy freezing rain at the moment, take care!',
    71: 'It is slightly snowing at the moment',
    73: 'It is snowing at the moment',
    75: 'There is heavy snow at the moment',
    77: 'There is snowgrain at the moment',
    80: 'There is more rain than normal',
    81: 'It is raining very hard',
    82: 'You should probably go inside',
    85: 'It is snowing more than normal',
    86: 'There is heavy snow at the moment',
    95: 'There is a thunderstorm at the moment',
    96: 'There is a thunderstorm with rain at the moment',
    99: 'There is a heavy thunderstorm with hail at the moment'
}