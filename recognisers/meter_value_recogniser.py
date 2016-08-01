'''
Created on 10.01.2016

@author: Artem
'''
# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import traceback

from .single_digit_knn_recogniser import SingleDigitKNNRecogniser, SingleDigitKNNRecogniserException
from db.mongo_db_manager import RECOGNIZED, NOT_TRAINED, DIGITS_NOT_RECOGNIZED, NOT_ENOUGH_DIGITS, PREPROCESSING_ERROR


class MeterValueRecogniser(object):
    '''
    classdocs
    '''

    def __init__(self, knn, meter, digits, x_gaps):
        '''
        Constructor
        '''
        self.__knn = knn # used for knn
        self.__digits = digits
        self.__gaps = x_gaps
        self.__max_x_gap = meter.meter_image_settings.digits_x_axis_max_gap
        self.__digits_number = meter.meter_settings.digits_number
        self.__values = [-1] * self.__digits_number
        # set last digit to 0 if ignore
        if meter.meter_image_settings.ignore_last_digit:
            self.__digits_number -= 1
            self.__values[-1] = 0

        
    def recognize(self, ignore_gaps=False, ignore_digits_number=False):
        '''
        '''
        if not self.__knn.isTrained():
            return NOT_TRAINED, self.__values
        
        try:
            self.__knn.loadData()
        
        # raise if knn can't load data (trained=True, but there are not samples and responses in the db)
        except Exception as e:
            print e
            traceback.print_exc()
            return NOT_TRAINED, self.__values
        
        # check number of digits
        if len(self.__digits) < self.__digits_number and not ignore_digits_number:
            return NOT_ENOUGH_DIGITS, self.__values
        
        # check for gaps
        for gap in self.__gaps:
            if gap > self.__max_x_gap and not ignore_gaps:
                return PREPROCESSING_ERROR, self.__values
        
        flag = RECOGNIZED
        
        for i in range(self.__digits_number):
            
            try:
                self.__values[i] = self.__knn.recognize(self.__digits[i])
            
            except SingleDigitKNNRecogniserException as e:
                #print "MVR: digit %d not recognized" % index  
                '''
                TODO log
                '''
                flag = DIGITS_NOT_RECOGNIZED
                #traceback.print_exc()
                
        return flag, self.__values

        
        
        
        for digit in self.__digits:
            index = self.__digits.index(digit)
            
            try:
                self.__values[index] = self.__knn.recognize(digit)
            
            except SingleDigitKNNRecogniserException as e:
                #print "MVR: digit %d not recognized" % index  
                '''
                TODO log
                '''
                flag = DIGITS_NOT_RECOGNIZED
                traceback.print_exc()
           
        return flag, self.__values
