'''
Created on 13.10.2015

@author: Artem
'''

import pyowm

class Weather(object):
    
    def __init__(self, api_key):
        '''
        Constructor
        '''
        self.__api_key = api_key
        self.__owm = pyowm.OWM(api_key)
        
    
    def isApiOnline(self):
        '''
        '''
        try:
            return self.__owm.is_API_online()
        
        except Exception as e:
            print e
            return False
    
    
    def getCurrentWeather(self, position):
        '''
        '''
        try:
            observation = self.__owm.weather_at_place(position)
            w = observation.get_weather()
            #print(w)   
            #print w.get_temperature('celsius')     
            #print w.get_humidity() 
            return w
            
        except Exception as e:
            print e
            return None   
            
            
            
if __name__ == '__main__':
    
    API_KEY = '9d78daf127ad45a1d3f57f86e69accb4'
    
    position = 'Berlin, Germany'
    
    weather = Weather(API_KEY)
    
    print weather.isApiOnline()
    
    if weather.getCurrentWeather(position):
        print weather.getCurrentWeather(position).get_temperature('celsius')['temp']
    
    
        



                
