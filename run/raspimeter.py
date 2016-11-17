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
   
    def __init__(self, db, camera_input, simulated=True, configure=True, usb=False):
        '''
        Constructor
        TODO handle meter_id to load meter depended settings
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
        self.__configure = configure
        
        if simulated:
            from inputs.simulated_camera import SimulatedCamera
            self.__camera = SimulatedCamera(self.__camera_input.camera_number, self.__camera_input.led_pin)
                
        elif not usb:
            from inputs.camera import Camera
            self.__camera = Camera(self.__camera_input.camera_number, self.__camera_input.led_pin)
        
        else:
            from inputs.usb_camera import USBCamera
            self.__camera = USBCamera(0)
    
    
    def run(self):
        '''
        '''
        if self.__configure:
            sleeptime = 10
        else:
            sleeptime = self.__camera_input.sleep_time
        
        while True:
            
            try:
                if self.__configure:
                    print 'configure'
                    self.takeAndStoreImage()
                else:
                    print 'recognize'
                    self.takeAndRecognizeImage()
            
            except Exception as e:
                traceback.print_exc()
                
            time.sleep(sleeptime)
            
    
    def takeAndStoreImage(self):
        '''
        used for configuration run
        '''
        meter = self.__camera_input.meter
        image = self.__camera.capture()
        meter_image = MeterImage(meter, image, ROOT_DIR)
        image_name = '%s_last_meter_capture.png' % (meter.id)
        meter_image.storeImage(ROOT_DIR + image_name, message='Configure', store_rgb=True)
        meter.last_capture = image_name
        self.__db.updateLastMeterCaptures(meter)
        meter_image.getDigits()
            

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
        image_name = '%s_last_meter_capture.png' % (meter.id)
        meter_image.storeImage(ROOT_DIR + image_name, message='Running', store_rgb=True)
        meter.last_capture = image_name
        self.__db.updateLastMeterCaptures(meter)
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
            flag = Raspimeter.validateMeterValue(db, meter.id, numeric_value, timestamp)
            
        meter_value_id = db.storeMeterValue(meter.id, timestamp, flag, numeric_value)
            
        if (store_recognized_images and flag == VALIDE_VALUE) or flag != VALIDE_VALUE:
            image_name = '%s_%s_%s.png' % (timestamp.strftime(DATE_FORMAT),
                                            meter.id,
                                            meter_value_id)
            meter_image.storeImage(ROOT_DIR + image_name, store_preview=True, store_rgb=store_rgb_images)
            
        return flag, numeric_value
            
    
    @staticmethod
    def validateMeterValue(db, meter_id, numeric_value, timestamp):
        '''
        TODO add check of meter max_consumption
        '''
        # get last recognized value
        last_value = db.getLastValideMeterValue(meter_id, timestamp)
        next_value = db.getNextValideMeterValue(meter_id, timestamp)
        
        if last_value <= numeric_value:
            if next_value is None:
                return VALIDE_VALUE
            elif numeric_value <= next_value.numeric_value:
                return VALIDE_VALUE
        
        return NOT_VALIDE_VALUE
        
        
        
    @staticmethod
    def recognizeAllImagesOnPage(db, meter_id, page, store_recognized_images):
        '''
        '''
        flags = (NOT_TRAINED, DIGITS_NOT_RECOGNIZED, NOT_ENOUGH_DIGITS, PREPROCESSING_ERROR, NOT_VALIDE_VALUE)
        pagination = db.getImagesWithPagination(meter_id, flag=ALL_VALUES, page=page, per_page=20)
        
        success_recogn_count = 0
        
        for meter_value in pagination.items:
            
            timestamp = meter_value.timestamp
            image_name = "%s_%s_%s.png" % (timestamp.strftime('%Y-%m-%d_%H-%M-%S'), meter_value.meter.id, meter_value.id)
            
            if meter_value.flag in flags:
                #print "recognize %d" % meter_value.flag
                flag = Raspimeter.readAndRecognizeImage(db, image_name, store_recognized_images)[1]
                #print "new flag %d" % flag
            
                if flag == VALIDE_VALUE:
                    success_recogn_count += 1
        
        #print success_recogn_count
                
        return success_recogn_count
    
    
    @staticmethod
    def recognizeBulk(db, meter_id, flag):
        '''
        '''
        store_recognized_images = True
        success_recogn_count = 0
        
        values = db.getValuesWithImages(meter_id, flag=flag)
        print "flag %s, values %s" % (flag, len(values))
        counter = 0
        
        for meter_value in values:
            print "recognize %s" % counter
            counter += 1
                
            try:
                timestamp = meter_value.timestamp
                image_name = "%s_%s_%s.png" % (timestamp.strftime('%Y-%m-%d_%H-%M-%S'), meter_value.meter.id, meter_value.id)
                flag = Raspimeter.readAndRecognizeImage(db, image_name, store_recognized_images)[1]
                
                if flag == VALIDE_VALUE:
                    print "success"
                    success_recogn_count += 1
                    
                else:
                    print "flag %s" % flag
                
            except Exception as e:
                traceback.print_exc()
        
        print "recognized %s" % success_recogn_count
        
        return success_recogn_count
    
    
    @staticmethod
    def validateBulk(db, meter_id):
        '''
        '''
        valid_values = db.getValuesWithImages(meter_id, flag=VALIDE_VALUE)
        not_valid_values = db.getValuesWithImages(meter_id, flag=NOT_VALIDE_VALUE)
        print "val_values %s" % len(valid_values)
        print "n_val_values %s" % len(not_valid_values)
        
        counter = 0
        
        for meter_value in valid_values:
            flag = Raspimeter.validateMeterValue(db, meter_id, meter_value.numeric_value, meter_value.timestamp)
            if flag != VALIDE_VALUE:
                db.updateMeterValue(meter_value)
                counter +=1
            
        print "invalide %s of %s" % (counter, len(valid_values))
        counter = 0
        
        for meter_value in not_valid_values:
            flag = Raspimeter.validateMeterValue(db, meter_id, meter_value.numeric_value, meter_value.timestamp)
            if flag == VALIDE_VALUE:
                db.updateMeterValue(meter_value)
                counter +=1
                
        print "valid %s of %s" % (counter, len(not_valid_values))
            
            
            
    
    
    @staticmethod
    def deleteBulk(db, meter_id, flag):
        if flag != 1:
            pass
        
        
    @staticmethod
    def readAndRecognizeImage(db, image_name, store_recognized_images):
        '''
        read an image from file system timestamp_meterId_valueId.png
        recognize it, validate meter value and upsert the meter value into db 
        '''
        meter = db.getMeter(image_name.split('_')[2])
        path = ROOT_DIR + image_name
        image = cv2.imread(path, 0)#cv2.IMREAD_COLOR)
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
    
    @staticmethod
    def deleteImage(image_name):
        '''
        '''
        path = ROOT_DIR + image_name
        try:
            os.remove(path)
            os.remove(os.path.splitext(path)[0]+'_preview.png')
            
        except:
            print "file not found %s" % image_name
            
            
if __name__ == '__main__':
    from db.mongo_db_manager import MongoDataBaseManager as db
    meters = db.getMeters()
    
    for meter in meters:
        Raspimeter.validateBulk(db, meter.id)
        
            
            
