'''
Created on 08.01.2016

@author: Artem
'''
import cv2
import numpy as np
import pickle


class SingleDigitKNNRecogniserException(Exception):
    '''
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class SingleDigitKNNRecogniser(object):
    '''
    classdocs
    '''
    
    NOT_RECOGNISED = 63

    def __init__(self, db=None, meter_id=None):
        '''
        Constructor
        read settings from DB
        '''
        self.__knn_settings = db.getMeter(meter_id).knn_settings
        self.__knn_sample_size = self.__knn_settings.knn_sample_size
        self.__knn_neghtbors = self.__knn_settings.knn_neghtbors
        self.__max_distance = self.__knn_settings.max_distance
        self.__db = db
        self.__meter_id = meter_id
        
    
    def isTrained(self):
        return self.__knn_settings.trained
        
    def __loadTrainedData(self):
        '''
        '''
        if self.__db:
            train_data = self.__db.loadKNNTrainData(self.__meter_id) 
            return train_data['samples'], train_data['responses']
            
        #load from file    
        else:
            f = open(self.__samples_file, 'r')
            samples = pickle.load(f)
            f = open(self.__responses_file, 'r')
            responses = pickle.load(f)
           
        return samples, responses
    
    
    def __storeTrainedData(self, samples, responses, digits):
        '''
        '''
        print 'store trained data'
        
        for i in range(len(samples)):
            self.__db.storeKNNTrainData(self.__meter_id, samples[i], responses[i], digits[i])
        
        
    def __reshapeImage(self, digit):
        '''
        '''
        image = digit.getPreparedImage()
        resized = cv2.resize(image, (self.__knn_sample_size, self.__knn_sample_size))
        reshaped = resized.reshape(self.__knn_sample_size * self.__knn_sample_size).astype(np.float32)
        
        return reshaped
    
    
    def loadData(self):
        '''
        '''
        samples, responses = self.__loadTrainedData()
        
        if self.__knn_settings.trained:
            self.__knn = cv2.KNearest(np.array(samples), np.array(responses))
            
        return samples, responses
    
    
    def trainAndStoreData(self, digits, responses=None, manually=False):
        '''
        '''
        samples = []
        trained_responses = []
        digits_images = []
        new_records_count = 0
        
        for i in range(len(digits)):
            
            if responses:
                response = responses[i]
            
            # manually    
            elif manually:    
                response = self.__trainSingleDigitFromShell(digits[i])
                
            else:
                response = -1
            
            if response != -1:
                samples.append(self.__reshapeImage(digits[i]))
                trained_responses.append(response)
                digits_images.append(digits[i])
                new_records_count += 1
#             print 'response: %d' % response
#             print '%d digits left' % (len(digits) - i)
            
        self.__knn = cv2.KNearest(np.array(samples), np.array(trained_responses))
        self.__storeTrainedData(samples, trained_responses, digits_images)
        
        if not self.__knn_settings.trained and new_records_count > 0:
            self.__knn_settings.trained = True
            self.__db.updateKNNSettings(self.__meter_id, self.__knn_settings)
            
        
        return new_records_count
        
    
    def __trainSingleDigitFromShell(self, digit):
        '''
        '''
        cv2.imshow("Train", digit.getPreparedImage())
        key = 0
        
        # check users input for number
        while key not in range(48, 58) and key != 63:
            key = int(cv2.waitKey())
            if key not in range(48, 58) and key != 63:
                print "press '?' or a number key!"
        
        return key-48 if key != 63 else -1
        
        
    def recognize(self, digit):
        '''
        '''
        if not self.__knn_settings.trained:
            return -1
        
        sample = self.__reshapeImage(digit)
        test_data = np.array([sample])
        ret, results, neighbours, dist = self.__knn.find_nearest(test_data, k = self.__knn_neghtbors)
        
        if neighbours[0,0] == neighbours[0,1]:
            if dist[0,0] < self.__max_distance:
                return int(ret)
        
        #print "result: ", results
        #print "neighbours: ", neighbours
        #print "distance: ", dist
        
#         cv2.imshow('asdf',digit.getPreparedImage())
#         cv2.waitKey(0)
        
        # TODO store digit into DB (not_recognized_digits)
        raise SingleDigitKNNRecogniserException("Error: can't recognize digit")
