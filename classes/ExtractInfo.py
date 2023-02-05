from classes.GeoInfoGrabber import GeoInfoGrabber
from classes.dicts.weatherDict import weatherDict
from classes.enums.Params import params

class ExtractInfo(GeoInfoGrabber):
    
    weatherData = 0
    
    def __init__(self, location):
        latitude, longitude = GeoInfoGrabber.get_location(location)
        self.weatherData = GeoInfoGrabber.get_data(latitude, longitude, self.create_list_from_enum(params))
    
    def create_list_from_enum(self, enum):
        return [elem.value for elem in enum]    
    
    def extract_specific_info(self, delay):
        hourCode = GeoInfoGrabber.calculate_time(delay)
        hourDataDict = self.weatherData['hourly']
        currentHourIndex = hourDataDict['time'].index(hourCode)
        return [hourCode, hourDataDict, currentHourIndex]
    
    def get_weather(self, delay):
        hourCode, hourDataDict, currentHourIndex = self.extract_specific_info(delay)
        currentHourIndex = hourDataDict['time'].index(hourCode)
        return weatherDict[hourDataDict[params.WEATHERCODE.value][currentHourIndex]]
    
    def get_wind_speed(self, delay):
        hourcode, hourDataDict, currentHourIndex = self.extract_specific_info(delay)
        return str(hourDataDict[params.WINDSPEED.value][currentHourIndex])+" km/h"
