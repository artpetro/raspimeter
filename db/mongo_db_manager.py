'''
Created on 11.01.2016

@author: Artem
'''
from mongo_models import MeterType, Meter, MeterValue, Consumption, KNNTrainData,\
    MeterImageSettings, KNNSettings, MeterSettings, CameraInput, WeatherValue

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
from inputs.weather import Weather
    
from datetime import datetime, timedelta
import calendar
import traceback
import cPickle
from bson.binary import Binary

ALL_VALUES = -1
VALIDE_VALUE = 0
RECOGNIZED = 1
NOT_TRAINED = 2
NOT_VALIDE_VALUE = 3
DIGITS_NOT_RECOGNIZED = 4
NOT_ENOUGH_DIGITS = 5
DELETED = 6
PREPROCESSING_ERROR = 7

DATE_FORMAT = '%Y-%m-%d_%H-%M-%S'
        
class MongoDataBaseManager():
    
    def __init__(self, params=0):
        '''
        Constructor
        '''
    
    @staticmethod
    def createCameraInput(led_pin):
        '''
        '''
        camera_input = CameraInput(led_pin=led_pin)
        camera_input.save()
    
    
    @staticmethod
    def setMeterForCameraInput(meter_id, camera_number):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()
        camera_input = CameraInput.objects(camera_number=camera_number).first()
        camera_input.meter = meter
        camera_input.save()
    
        
    @staticmethod
    def getCameraInputs():
        '''
        '''
        camera_inputs = CameraInput.objects()
        
        return camera_inputs

             
    @staticmethod   
    def storeMeterType():
        meter_type = MeterType(name='Gas Meter')
        meter_type.save()
    
    
    @staticmethod   
    def createAndStoreMeterAndSettings(meter_type_id,
                   name):
        '''
        '''
        meter_type = MeterType.objects(id=meter_type_id).first()
        
        meter = Meter(meter_type=meter_type,
                      name = name,
                      meter_settings = MeterSettings(),
                      meter_image_settings = MeterImageSettings(),
                      knn_settings = KNNSettings()
                      )
        
        
        meter.save()
   
     
    @staticmethod
    def getMeters():
        return Meter.objects()
     
             
    @staticmethod
    def getMeter(meter_id=None):
        '''
        {'type': "{'type': '0', 'id': '1', 'name': 'Gas Meter'}", 'id': '1', 'name': 'Gas Meter 1', ...}
        '''
        return Meter.objects(id=meter_id).first()
    
    
    @staticmethod
    def updateLastMeterCaptures(meter):
        '''
        '''
        Meter.objects(id=meter.id).upsert_one(set__last_capture=meter.last_capture)
    
    
    @staticmethod
    def updateKNNSettings(meter_id, knn_settings):
        '''
        '''
        Meter.objects(id=meter_id).upsert_one(set__knn_settings=knn_settings)
        
    
    @staticmethod
    def storeKNNTrainData(meter_id, sample, response, src_image):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()
        
        data = KNNTrainData(meter, 
                            Binary(cPickle.dumps(sample, protocol=2)), 
                            response, 
                            Binary(cPickle.dumps(src_image, protocol=2)))
        data.save()
        
    
    @staticmethod
    def loadKNNTrainData(meter_id):
        '''
        '''
        samples = []
        responses = []
        src_images = []
        
        meter = Meter.objects(id=meter_id).first()
        
        for data in KNNTrainData.objects(meter=meter):
            samples.append(cPickle.loads(data.sample))
            responses.append(data.response)
            src_images.append(cPickle.loads(data.src_image))
            
        return {'samples': samples, 'responses': responses, 'src_images': src_images}
        
     
    @staticmethod
    def getImage(image_id):
        '''
        TODO rename to get meter_numeric_value_and_image and argument=image_name
        TODO remove id in ret dict
        
        '''
        meter_value = MeterValue.objects(id=image_id).first()
        meter_id = meter_value.meter.id
        timestamp = meter_value.timestamp
         
        image_name = "%s_%s_%s.png" % (timestamp.strftime(DATE_FORMAT), meter_id, meter_value.id) 
         
        return {'name': image_name, 
                'time': timestamp.strftime('%Y-%m-%d-%H:%M:%S'), 
                'value':  meter_value.numeric_value, 
                'flag': meter_value.flag, 
                'id': str(meter_value.id)}
         
             
    @staticmethod
    def getImages(meter_id=1, flag=ALL_VALUES):
        '''
        '''
        images_list = []
        
        meter = Meter.objects(id=meter_id).first()
        meter_values = MeterValue.objects(meter=meter) if flag == ALL_VALUES else MeterValue.objects(flag=flag, meter=meter)
             
        for meter_value in meter_values:
            timestamp = meter_value.timestamp
            image_name = "%s_%s_%s.png" % (timestamp.strftime('%Y-%m-%d_%H-%M-%S'), meter_value.meter.id, meter_value.id)
            
            images_list.append({'name': image_name,
                'time': timestamp.strftime('%Y-%m-%d-%H:%M:%S'), 
                'value':  meter_value.numeric_value, 
                'flag': meter_value.flag, 
                'id': meter_value.id})
             
        return images_list
    
    
    @staticmethod
    def getValuesWithImages(meter_id=1, flag=ALL_VALUES):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()
        
        if flag == ALL_VALUES:
            return MeterValue.objects(has_image=True, meter=meter)  
        else: 
            return MeterValue.objects(has_image=True, flag=flag, meter=meter)
             

    @staticmethod
    def getImagesWithPagination(meter_id=1, 
                                image_requiered=True, 
                                flag=ALL_VALUES, page=1, 
                                per_page=10, 
                                start_date=None,
                                end_date=None):
        '''
        '''
        date_format = '%Y-%m-%d %H:%M:%S'
        try: 
            start_date = datetime.strptime(start_date, date_format)
            end_date = datetime.strptime(end_date, date_format)
        except Exception:
            start_date = end_date = None
        
        meter = Meter.objects(id=meter_id).first()
        
        if start_date is None:
            if image_requiered:
                if flag == ALL_VALUES:
                    meter_values = MeterValue.objects(has_image=True, meter=meter)  
                else: 
                    MeterValue.objects(has_image=True, flag=flag, meter=meter)
    
            else:
                if flag == ALL_VALUES:
                    meter_values = MeterValue.objects(meter=meter)  
                else: 
                    MeterValue.objects(flag=flag, meter=meter)
                
        else:
            if image_requiered:
                if flag == ALL_VALUES:
                    meter_values = MeterValue.objects(has_image=True, meter=meter, timestamp__gte=start_date, timestamp__lte=end_date)  
                else: 
                    MeterValue.objects(has_image=True, flag=flag, meter=meter, timestamp__gte=start_date, timestamp__lte=end_date)
    
            else:
                if flag == ALL_VALUES:
                    meter_values = MeterValue.objects(meter=meter, timestamp__gte=start_date, timestamp__lte=end_date)  
                else: 
                    MeterValue.objects(flag=flag, meter=meter, timestamp__gte=start_date, timestamp__lte=end_date)

        return meter_values.paginate(page=page, per_page=per_page)
    
    
    @staticmethod
    def getKNNData(meter_id=1):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()

        return KNNTrainData.objects(meter=meter)
    
    
    @staticmethod
    def deleteKNNData(meter_id, id):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()
        knn_data = KNNTrainData.objects(meter=meter, id=id)
        knn_data.delete()
                          
    
    @staticmethod   
    def storeMeterValue(meter_id, 
                        timestamp, 
                        flag=VALIDE_VALUE, 
                        numeric_value=-1):
        '''
        '''
        #ignore microsecond
        timestamp = timestamp.replace(microsecond=0)
        
        meter = Meter.objects(id=meter_id).first()  
        
        meter_value = MeterValue.objects(meter=meter, timestamp=timestamp).upsert_one(set__numeric_value=numeric_value, set__flag=flag, set__has_image=True)
        
        if flag == VALIDE_VALUE:
            MongoDataBaseManager.updatePeriodicConsumptions(timestamp, meter)
        
        return meter_value.id
    
    @staticmethod   
    def updateMeterValue(meter_value):
        '''
        '''
        MongoDataBaseManager.updatePeriodicConsumptions(meter_value.timestamp, meter_value.meter)
        meter_value.update_one()
    
                  
    @staticmethod   
    def getLastValideMeterValue(meter_id, timestamp):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()
        meter_value = MeterValue.objects(meter=meter, flag=VALIDE_VALUE, timestamp__lt=timestamp).order_by('-timestamp').first()
        
        if not meter_value:
            return 0
        
        return meter_value.numeric_value
    
    @staticmethod   
    def getNextValideMeterValue(meter_id, timestamp):
        '''
        '''
        meter = Meter.objects(id=meter_id).first()
        meter_value = MeterValue.objects(meter=meter, flag=VALIDE_VALUE, timestamp__gt=timestamp).order_by('timestamp').first()
        
        return meter_value
        
             
    @staticmethod   
    def deleteMeterValue(value_id, perm):
        '''
        '''
        try:
            meter_value = MeterValue.objects(id=value_id).first()
            flag = meter_value.flag
            meter = meter_value.meter
            timestamp = meter_value.timestamp
            
            deleted = False
            
            MeterValue.objects(id=value_id).update_one(set__flag=DELETED, upsert=True)
            
            if flag == VALIDE_VALUE:
                  
                try:
                    MongoDataBaseManager.updatePeriodicConsumptions(timestamp, meter)
              
                except Exception as e:
                    traceback.print_exc()
                    return "timestamp: %s meter_id: %d, error update periodic (deleteMeterValue): %s" % (str(e))

            if perm:
                meter_value.delete()
                deleted = True
                     
            return deleted
             
        except Exception as e:
            traceback.print_exc()
            return str(e)
    
        
    @staticmethod   
    def deleteImage(value_id):
        '''
        '''
        MeterValue.objects(id=value_id).update_one(set__has_image=False, upsert=True)
        
        
    @staticmethod
    def deleteAllSuccRecImages(meter_id):
        '''
        method to remove all success full recognized images from file system 
        '''
        meter = Meter.objects(id=meter_id).first()
        meter_values = MeterValue.objects(meter=meter, flag=VALIDE_VALUE)
        
        for meter_value in meter_values:
            meter_value.update(set__has_image=False)
            timestamp = meter_value.timestamp
            image_name = "%s_%s_%s.png" % (timestamp.strftime('%Y-%m-%d_%H-%M-%S'), meter_value.meter.id, meter_value.id)
            from run.raspimeter import Raspimeter
            Raspimeter.deleteImage(image_name)


    @staticmethod
    def updatePeriodicConsumptions(date, meter):
        '''
            TODO called on create, update or delete of MeterValue if MeterValue.flag==VALIDE_VALUE or 
            flag changed from VALIDE_VALUE to other
        '''
        for period in ('h', 'd', 'w', 'm', 'y'):
            period_start_date = MongoDataBaseManager.getPeriodStart(date, period)
            MongoDataBaseManager.__updatePeriodicConsumption(period_start_date, period, meter)

            # update previous period's consumption if this first element in the period            
            if date == MeterValue.objects(timestamp=date).first().timestamp:
                # TODO pick last value and compute period of this value
                prev_period_start_date = MongoDataBaseManager.getPeriodStart(period_start_date - timedelta(seconds=1), period)
                MongoDataBaseManager.__updatePeriodicConsumption(prev_period_start_date, period, meter)
         
     
    @staticmethod
    def __updatePeriodicConsumption(period_start_date, period, meter):
        '''
               period_1        period_2
            |__.__.__._.__._|__.__.__._.__._|
               ^               ^
              v_1             v_2
               
            or if period_2 is empty:
               
               period_1        period_2
            |__.__.__._.__._|_
               ^          ^     
              v_1        v_2
               
            consumption_1 = v_2 - v_1           
        ''' 
        period_end_date = MongoDataBaseManager.getPeriodEnd(period_start_date, period)
        next_perion_start_date = period_end_date + timedelta(seconds=1)
         
        try:
            start_value = MeterValue.objects(timestamp__gte=period_start_date, 
                                             meter=meter, 
                                             flag=VALIDE_VALUE).first()
             
            
            end_value = MeterValue.objects(timestamp__gte=next_perion_start_date, 
                                            meter=meter, 
                                            flag=VALIDE_VALUE).first()
                                            
            if not end_value:
                end_value = MeterValue.objects(meter=meter, 
                                               flag=VALIDE_VALUE, 
                                               timestamp__lte=period_end_date).order_by('-timestamp').first()
             
            numeric_value = end_value.numeric_value - start_value.numeric_value
                 
            Consumption.objects(meter=meter, timestamp=period_start_date, period=period).upsert_one(set__numeric_value = numeric_value)
             
        except Exception as e:
            traceback.print_exc()   
     
    @staticmethod
    def updateWeather(meter, timestamp):
        # TODO weather hourly
        timestamp = timestamp.replace(microsecond=0)
        weather_api_key = meter.meter_settings.weather_api_key
        position = meter.meter_settings.position
        weather = Weather(weather_api_key)
        #weather_timestamp = MongoDataBaseManager.getPeriodStart(timestamp, period='h')
        
        #if weather.isApiOnline():
        current_weather = weather.getCurrentWeather(position)
            
        if current_weather:
            temperature = current_weather.get_temperature('celsius')['temp'] 
            WeatherValue.objects(meter=meter, timestamp=timestamp).upsert_one(set__temperature=temperature)
                
     
    @staticmethod
    def getPeriodStart(date, period='h'):
        '''
        '''    
        date = date.replace(minute=0, second=0, microsecond=0)
        switcher = {
            'h': date,
            'd': date.replace(hour=0),
            'w': (date - timedelta(days=date.weekday())).replace(hour=0),
            'm': date.replace(day=1, hour=0),
            'y': date.replace(month=1, day=1, hour=0),
        }
         
        return switcher.get(period, None)
     
     
    @staticmethod
    def getPeriodEnd(date, period='h'):
        '''
        ''' 
        date = date.replace(minute=59, second=59, microsecond=0)   
        switcher = {
            'h': date,
            'd': date.replace(hour=23),
            'w': (date + timedelta(days=6)).replace(hour=23),
            'm': date.replace(day=calendar.monthrange(date.year, date.month)[1], hour=23),
            'y': date.replace(month=12, day=31, hour=23),
        }
         
        return switcher.get(period, None)
         
     
    '''
    Functions to get data for Charts
    '''
    @staticmethod
    def getPeriodicConsumptions(period='h', meter_id=1, start_date=None, end_date=None, show_date_as_string=False):
        '''
        575281fdca18a21894d35cf5
        period=h
        start_date=2016-05-04 00:00:00
        end_date=2016-06-04 11:06:48
        '''
        data = []
         
        date_format = '%Y-%m-%d %H:%M:%S'
        
        meter = Meter.objects(id=meter_id).first()
         
        try: 
            if not start_date:
                start_date = Consumption.objects(meter=meter, period=period).first().timestamp
            else:
                start_date = datetime.strptime(start_date, date_format)
             
            if not end_date:
                end_date = datetime.utcnow()
             
            else:
                end_date = datetime.strptime(end_date, date_format)
                 
            start_date = MongoDataBaseManager.getPeriodStart(start_date, period)
            end_date = MongoDataBaseManager.getPeriodEnd(end_date, period)
            
            consumptions = Consumption.objects(meter=meter, period=period, timestamp__gte=start_date, timestamp__lte=end_date) 
             
            epoch = datetime.utcfromtimestamp(0) 
             
            for consumption in consumptions:
                # millis for highchart
                milliseconds = int((consumption.timestamp - epoch).total_seconds()) * 1000
                
                if show_date_as_string:
                    data.append([str(consumption.timestamp), consumption.numeric_value])
                else:
                    data.append([milliseconds, consumption.numeric_value])
                 
         
        except Exception as e:
            print e
            # TODO log
            traceback.print_exc()
             
        return data
    
    @staticmethod
    def getPeriodicConsumptionsMR(period='h', meter_id=1, start_date=None, end_date=None, show_date_as_string=False):
        '''
        575281fdca18a21894d35cf5
        period=h
        start_date=2016-05-04 00:00:00
        end_date=2016-06-04 11:06:48
        '''
        data = []
         
        date_format = '%Y-%m-%d %H:%M:%S'
        
        meter = Meter.objects(id=meter_id).first()
         
        try: 
            if not start_date:
                start_date = Consumption.objects(meter=meter, period=period).first().timestamp
            else:
                start_date = datetime.strptime(start_date, date_format)
             
            if not end_date:
                end_date = datetime.utcnow()
             
            else:
                end_date = datetime.strptime(end_date, date_format)
                 
            start_date = MongoDataBaseManager.getPeriodStart(start_date, period)
            end_date = MongoDataBaseManager.getPeriodEnd(end_date, period)
            
            map_f = MongoDataBaseManager.getMapFunction(period=period, data='meter_value')
            
            reduce_f = """
                function(key, values) {
                    return Math.min.apply(Math, values);
                };
            """
            values = MeterValue.objects(meter=meter, flag=VALIDE_VALUE, timestamp__gte=start_date, timestamp__lte=end_date)
            min_values = values.map_reduce(map_f, reduce_f, {"replace":"min_values"})
            
            reduce_f = """
                function(key, values) {
                    return Math.max.apply(Math, values);
                };
            """
            
            max_values = values.map_reduce(map_f, reduce_f, {"replace":"max_values"})
            
            epoch = datetime.utcfromtimestamp(0)
            
            # convert to dict
            min_values = dict((c.key, c.value) for c in min_values)
            max_values = dict((c.key, c.value) for c in max_values)
            
            
            
            min_max_values = dict(min_values.items() + max_values.items() + [(k, (min_values[k], max_values[k])) for k in set(min_values) & set(max_values)]) 
            
            for key in min_max_values:
                value = min_max_values[key]
                #print key
                #print  value
                
                # millis for highchart
                milliseconds = int((key - epoch).total_seconds()) * 1000
                
                if show_date_as_string:
                    data.append([str(key), value])
                else:
                    data.append([milliseconds, value])
            
        except Exception as e:
            print e
            # TODO log
            traceback.print_exc()
             
        return data
    
    @staticmethod
    def getWeather(period='h', meter_id=1, start_date=None, end_date=None, show_date_as_string=False, map_reduce=True):
        '''
        575281fdca18a21894d35cf5
        period=h
        start_date=2016-05-04 00:00:00
        end_date=2016-06-04 11:06:48
        '''
        data = []
         
        date_format = '%Y-%m-%d %H:%M:%S'
        
        meter = Meter.objects(id=meter_id).first()
        
        try: 
            if not start_date:
                start_date = WeatherValue.objects(meter=meter).first().timestamp
            else:
                start_date = datetime.strptime(start_date, date_format)
             
            if not end_date:
                end_date = datetime.utcnow()
             
            else:
                end_date = datetime.strptime(end_date, date_format)
                 
            start_date = MongoDataBaseManager.getPeriodStart(start_date, period)
            end_date = MongoDataBaseManager.getPeriodEnd(end_date, period)
            
            map_f = MongoDataBaseManager.getMapFunction(period=period)
            
            reduce_f = """
                function(key, values) {
                    return Array.sum(values) / values.length;
                };
            """
            weathers = WeatherValue.objects(meter=meter, timestamp__gte=start_date, timestamp__lte=end_date)
            
#             for w in weathers:
#                 print w.timestamp
#                 print w.temperature
            if map_reduce:
                weathers = weathers.map_reduce(map_f, reduce_f, {"replace":"COLLECTION_NAME"})
            
            epoch = datetime.utcfromtimestamp(0) 
             
            for weather in weathers:
                if map_reduce:
                    key = weather.key
                    value = weather.value
                    
                else:
                    key = weather.timestamp
                    value = weather.temperature
                
                # millis for highchart
                milliseconds = int((key - epoch).total_seconds()) * 1000
                
                if show_date_as_string:
                    data.append([str(key), value])
                else:
                    data.append([milliseconds, value])
                 
        except Exception as e:
            print e
            # TODO log
            traceback.print_exc()
             
        return data
    
    
    @staticmethod
    def getMapFunction(period = 'h', data='temperature'):
        map_f_pref = """
            function() {
                var key = new Date(this.timestamp);
                key.setMinutes(0);
                key.setSeconds(0);
        """
        
        if period == 'd':
            map_f_body = """
                key.setHours(0);
            """
        
        elif period == 'w':
            map_f_body = """    
                var first = key.getDate() - key.getDay() + 1;
                key.setHours(0);
                key.setDate(first);
            """      
        
        elif period == 'm':
            map_f_body = """    
                key.setHours(0);
                key.setDate(1);
            """
        
        elif period == 'y':
            map_f_body = """    
                key.setDate(1);
                key.setMonth(0);
                key.setHours(1);
            """
        
        else: 
            map_f_body = ""
        
        if data == 'temperature':
            map_f_suff = """        
                    emit(key, this.temperature);
                }
            """
        elif data == 'meter_value':
            map_f_suff = """        
                    emit(key, this.numeric_value);
                }
            """
            
        
        return map_f_pref + map_f_body + map_f_suff
         

    @staticmethod
    def createMeterType(name):
        mt = MeterType(name)
        mt.save()
        
    @staticmethod
    def createMeter(meter_type_name, meter_name):
        mt = MeterType.objects(name=meter_type_name).first()
        MongoDataBaseManager.createAndStoreMeterAndSettings(meter_type_id=mt.id, name=meter_name)
         
         
if __name__ == '__main__':

    #MongoDataBaseManager.deleteAllSuccRecImages()

    #MongoDataBaseManager.createMeterType('Gas Meter Type')
    #MongoDataBaseManager.createMeter('Gas Meter Type', 'Gas Meter')
    
    #MongoDataBaseManager.createCameraInput(12)
    #meter = Meter.objects(name='Gas Meter').first()
    #MongoDataBaseManager.setMeterForCameraInput(meter.id, 1)
    
    API_KEY = '9d78daf127ad45a1d3f57f86e69accb4'
    position = 'Osnabrueck, Germany'
    
    meter = Meter.objects().first()
    meter.meter_settings.weather_api_key = API_KEY
    meter.meter_settings.position = position
    meter.meter_settings.condition_number = 0.9627
    meter.meter_settings.value_units = 'm^3'
    meter.meter_settings.calorific_value = 9.833
    meter.meter_settings.unit_price = 0.09
    
    meter.save()
    
    
#     MeterValue.drop_collection() 
#     Consumption.drop_collection()
    
    

#     '''
#      DROP DataBase
#     '''
#     from mongoengine import connect
#   
#     db = connect('raspimeter')
#     db.drop_database('raspimeter')
#  
#     '''
#     CREATE MeterType
#     '''
#     mt = MeterType(name="Gas Meter Type")
#     mt.save()
#     
#     '''
#     create Simulated meter
#     '''
#     Meter.drop_collection()
#     MeterValue.drop_collection() 
#     Consumption.drop_collection()
#     KNNTrainData.drop_collection()
#     
#     mt = MeterType.objects().first()
#      
#     MongoDataBaseManager.createAndStoreMeterAndSettings(meter_type_id=mt.id, name='Simulated Gas Meter 1')
#       
#     '''
#     store camera input
#     '''
#     CameraInput.drop_collection()
#     
#     meter = Meter.objects().first()
#     MongoDataBaseManager.storeCameraInput(meter_id=meter.id)
