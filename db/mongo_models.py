# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#from flask_server.server import mongo_db_engine

from mongoengine.queryset import *
from flask_server import mongo_db_engine


class MeterType(mongo_db_engine.Document):
    '''
    '''
    name = mongo_db_engine.StringField(max_length=255, required=True)
    
    
class MeterSettings(mongo_db_engine.EmbeddedDocument):
    '''
    used for image preprocessing and to find digits
    '''
    digits_number = mongo_db_engine.IntField(default=8, required=True)
    decimal_places = mongo_db_engine.IntField(default=3, required=True)
    value_units = mongo_db_engine.StringField(default='m^3', max_length=255, required=True)
    converted_value_units = mongo_db_engine.StringField(default='kWh', max_length=255, required=True) # kwh for gas meter
    unit_price = mongo_db_engine.FloatField(default=1.0, requiered=True) # TODO periodic per value_unit
    calorific_value = mongo_db_engine.FloatField(default = 1.0, required=True) # used to convert units to converted units m^3 -> kwh
    condition_number = mongo_db_engine.FloatField(default = 1.0, required=True)
    max_consumption_per_minute = mongo_db_engine.FloatField(default = 10.0, required=True)
    weather_api_key = mongo_db_engine.StringField(max_length=255, required=True)
    position = mongo_db_engine.StringField(max_length=255, required=True, unique=True)
    
class MeterImageSettings(mongo_db_engine.EmbeddedDocument):
    '''
    used for image preprocessing and to find digits
    '''
    image_width = mongo_db_engine.IntField(default=600, required=True)
    canny_1 = mongo_db_engine.IntField(default=50, required=True)
    canny_2 = mongo_db_engine.IntField(default=100, required=True)
    hough_lines = mongo_db_engine.IntField(default=150, required=True)
    max_digit_height = mongo_db_engine.IntField(default=50, required=True)
    min_digit_height = mongo_db_engine.IntField(default=35, required=True)
    max_digit_width = mongo_db_engine.IntField(default=30, required=True)
    min_digit_width = mongo_db_engine.IntField(default=10, required=True)
    digits_x_axis_max_gap = mongo_db_engine.IntField(default=90, required=True)
    digits_y_axis_max_gap = mongo_db_engine.IntField(default=8, required=True)
    ignore_last_digit = mongo_db_engine.BooleanField(default=True, required=True)
    
    
class KNNSettings(mongo_db_engine.EmbeddedDocument):
    '''
    used for image recognition
    '''
    trained = mongo_db_engine.BooleanField(default=False, required=True)
    images_to_train = mongo_db_engine.IntField(default=10, required=True)
    knn_sample_size = mongo_db_engine.IntField(default=10, required=True)
    knn_neghtbors = mongo_db_engine.IntField(default=3, required=True)
    max_distance = mongo_db_engine.IntField(default=80000, required=True)
    
        
class Meter(mongo_db_engine.Document):
    '''
    '''
    meter_type = mongo_db_engine.ReferenceField(MeterType)
    name = mongo_db_engine.StringField(max_length=255, required=True)
    meter_settings = mongo_db_engine.EmbeddedDocumentField('MeterSettings')
    meter_image_settings = mongo_db_engine.EmbeddedDocumentField('MeterImageSettings')
    knn_settings = mongo_db_engine.EmbeddedDocumentField('KNNSettings')
    last_capture = mongo_db_engine.StringField(max_length=255)


class CameraInput(mongo_db_engine.Document):
    '''
    '''
    meter = mongo_db_engine.ReferenceField(Meter)
    camera_number = mongo_db_engine.IntField(default=1, max_length=1, required=True, unique=True)
    led_pin = mongo_db_engine.IntField(default=12, max_length=2, required=True)
    store_recognized_images = mongo_db_engine.BooleanField(default=True, required=True)
    store_rgb_images = mongo_db_engine.BooleanField(default=True, required=True)
    sleep_time = mongo_db_engine.IntField(default=60, required=True)
    
    
class KNNTrainData(mongo_db_engine.Document):
    '''
    '''
    meter = mongo_db_engine.ReferenceField(Meter, required=True)
    sample = mongo_db_engine.BinaryField(required=True)
    response = mongo_db_engine.IntField(max_length=255, required=True)
    src_image = mongo_db_engine.BinaryField()


class MeterValue(mongo_db_engine.Document):
    '''
    '''
    meter = mongo_db_engine.ReferenceField(Meter, required=True)
    timestamp = mongo_db_engine.DateTimeField(unique=True, required=True, unique_with='meter')
    numeric_value = mongo_db_engine.IntField()
    flag = mongo_db_engine.IntField()
    has_image = mongo_db_engine.BooleanField(default=False)
    meta = {
        'indexes': ['timestamp']
        }
    
    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.order_by('timestamp')


class Consumption(mongo_db_engine.Document):
    '''
    '''
    meter = mongo_db_engine.ReferenceField(Meter)
    timestamp = mongo_db_engine.DateTimeField(required=True)
    numeric_value = mongo_db_engine.IntField(default=-1)
    period = mongo_db_engine.StringField(max_length=1, unique_with=['timestamp', 'meter', 'period'])    
    
    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.order_by('timestamp')
    

class WeatherValue(mongo_db_engine.Document):
    '''
    '''
    meter = mongo_db_engine.ReferenceField(Meter)
    timestamp = mongo_db_engine.DateTimeField(unique_with=['timestamp', 'meter'], required=True)
    temperature = mongo_db_engine.FloatField()
    
    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.order_by('timestamp')

