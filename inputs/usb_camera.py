'''
Created on 13.10.2015

@author: Artem
'''

import time
import cv2
import numpy as np

class USBCamera(object):
    '''
    classdocs
    '''

    def __init__(self, number):
        '''
        Constructor
        '''
        self.__cameraNumber = number
        self.__camera = cv2.VideoCapture(number)
        
        
    def capture(self):
        '''
        '''
        if self.__camera.isOpened(): # try to get the first frame
            rval, image = self.__camera.read()
        
#         self.__camera.capture(rawCapture, format="bgr")
#         image = rawCapture.array
            
        return image
