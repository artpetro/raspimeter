'''
Created on 28.05.2016

@author: Artem
'''
# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import threading
import time

from image_preprocessing.meter_image import MeterImage
from recognisers.single_digit_knn_recogniser import SingleDigitKNNRecogniser
from recognisers.meter_value_recogniser import MeterValueRecogniser
from db.mongo_db_manager import *

dir = os.path.dirname(__file__)
ROOT_DIR = os.path.join(dir, '../flask_server/static/images/')


class Raspimeter(threading.Thread):
    '''
    classdocs
    '''
   
    def __init__(self, db, camera_input, simulated=True):
        '''
        Constructor
        TODO handle meter_id for load meter depended settings
        '''
        threading.Thread.__init__(self)
        meter = db.getMeter(camera_input.meter.id)
        self.__meter = meter
        self.__meter_settings = meter.meter_settings
        self.__meter_image_settings = meter.meter_image_settings 
        self.__digits_number = meter.meter_settings.digits_number       
        self.__db = db
        self.__meter_id = meter.id
        self.__knn = SingleDigitKNNRecogniser(self.__db, self.__meter_id)
        self.__camera_input = camera_input
        
        if simulated:
            from inputs.simulated_camera import SimulatedCamera
            self.__camera = SimulatedCamera(self.__camera_input.camera_number, self.__camera_input.led_pin)
                
        else:
            from inputs.camera import Camera
            self.__camera = Camera(self.__camera_input.camera_number, self.__camera_input.led_pin)
    
    
    def run(self):
        '''
        '''
        while True:
            print"recognize"
            
            try:
                self.takeAndRecognizeImage()
            
            except Exception as e:
                traceback.print_exc()
                
            time.sleep(self.__camera_input.sleep_time)
            

    def takeAndRecognizeImage(self):
        '''
        '''
        meter = self.__camera_input.meter
        image = self.__camera.capture()
        timestamp = datetime.utcnow()
        meter_image, flag, digits_values = Raspimeter.recognizeMeterValue(self.__db, self.__meter, image)
        Raspimeter.validateAndStoreMeterValue(self.__db, 
                                              meter_image, 
                                              flag, 
                                              digits_values, 
                                              timestamp, 
                                              self.__camera_input.store_recognized_images,
                                              self.__camera_input.store_rgb_images)
        self.__db.updateLastMeterCaptures(meter)
        
        image_name = '%s_last_meter_capture.png' % (meter.id)
        meter_image.storeImage(ROOT_DIR + image_name, store_rgb=True)
        meter.last_capture = image_name
        
        self.__db.updateWeather(meter, timestamp)
        
        
        
    
    
    @staticmethod
    def recognizeMeterValue(db, meter, image):
        '''
        '''
        meter_image = MeterImage(meter, image, ROOT_DIR)
        digits, x_gaps = meter_image.getDigits()   
        knn = SingleDigitKNNRecogniser(db, meter.id) 
        mvr = MeterValueRecogniser(knn, meter, digits, x_gaps)

        flag, digits_values = mvr.recognize(ignore_gaps=False, ignore_digits_number=False)

        return meter_image, flag, digits_values        
        
    
    @staticmethod
    def validateAndStoreMeterValue(db, meter_image, flag, digits_values, timestamp, store_recognized_images, store_rgb_images=True):
        '''
        '''
        meter = meter_image.getMeter()
        numeric_value = -1
        
        if flag == RECOGNIZED:
            numeric_value = int(''.join(map(str, digits_values)))
            flag = Raspimeter.validateMeterValue(db, meter.id, numeric_value)
            
        meter_value_id = db.storeMeterValue(meter.id, timestamp, flag, numeric_value)
            
        if (store_recognized_images and flag == VALIDE_VALUE) or flag != VALIDE_VALUE:
            # TODO rgb / grayScale
            image_name = '%s_%s_%s.png' % (timestamp.strftime(DATE_FORMAT),
                                            meter.id,
                                            meter_value_id)
            meter_image.storeImage(ROOT_DIR + image_name, store_preview=True, store_rgb=store_rgb_images)
            
        return flag, numeric_value
            
    
    @staticmethod
    def validateMeterValue(db, meter_id, numeric_value):
        '''
        TODO implement depends on meter settings
        '''
        # get last recognized value
        last_value = db.getLastValideMeterValue(meter_id)
        
        if last_value <= numeric_value:
            return VALIDE_VALUE
        
        else:
            return NOT_VALIDE_VALUE
        
        
        
    @staticmethod
    def readAndRecognizeAllImages(db, meter_id, store_recognized_images):
        '''
        '''
        flags = (NOT_TRAINED, DIGITS_NOT_RECOGNIZED, NOT_ENOUGH_DIGITS, PREPROCESSING_ERROR)
        meter_images = []
        
        for flag in flags:
            meter_images.extend(db.getImages(meter_id, flag))
        
        success_recogn_count = 0
        
        for meter_image in meter_images:
            flag = Raspimeter.readAndRecognizeImage(db, meter_image['name'], store_recognized_images)[1]
            
            if flag == VALIDE_VALUE:
                success_recogn_count += 1
                
        return success_recogn_count
        
        
    @staticmethod
    def readAndRecognizeImage(db, image_name, store_recognized_images):
        '''
        read an image from file system timestamp_meterId_valueId.png
        recognize it, validate meter value and upsert the meter value into db 
        '''
        meter = db.getMeter(image_name.split('_')[2])
        path = ROOT_DIR + image_name
        image = cv2.imread(path, cv2.IMREAD_COLOR)
#         cv2.imshow("", image)
#         cv2.waitKey(0)

        timestamp_str = image_name.split('_')[0] + '_' + image_name.split('_')[1]
        timestamp = datetime.strptime(timestamp_str, DATE_FORMAT)
        meter_image, flag, digits_values = Raspimeter.recognizeMeterValue(db, meter, image)
        flag, numeric_value = Raspimeter.validateAndStoreMeterValue(db, meter_image, flag, digits_values, timestamp, store_recognized_images)
            
        return meter_image, flag, numeric_value, digits_values
    
    
    
    @staticmethod    
    def trainKNNAndStoreIntoDB(db, image_name, responses, manually=False):
        '''
        image_name=2016-06-05_21-34-30_5753bea9ca18a204c435d117_57549ae6108d4caa345b1fdb.png
                                            meter_id                    meter_value_id
        timestamp_meterId_valueId.png
        '''
        # create digits_images_array
        meter = db.getMeter(image_name.split('_')[2])
        path = ROOT_DIR + image_name
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
#         cv2.imshow("", image)
#         cv2.waitKey(0)
        meter_image = MeterImage(meter, image, ROOT_DIR)
        digits, x_gaps = meter_image.getDigits()
        
        print digits
        print responses
        
        knn = SingleDigitKNNRecogniser(db, meter.id) 
        knn_new_records_counter = knn.trainAndStoreData(digits, responses, manually)
        
        return knn_new_records_counter
