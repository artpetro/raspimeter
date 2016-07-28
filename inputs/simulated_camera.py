'''
Created on 13.10.2015

@author: Artem
'''

import cv2
import os

class SimulatedCamera(object):
    '''
    classdocs
    '''


    def __init__(self, number, led_pin):
        '''
        Constructor
        '''
        self.__cameraNumber = number
        self.__led_pin = led_pin
#         self.__camera = PiCamera()

        # simulated camera
        images_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/simulation/images/nonstop/"
        self.__images = []
        
        for image in os.listdir(images_dir):
            image = cv2.imread(images_dir + image, cv2.IMREAD_COLOR)
            self.__images.append(image)
            
        self.__index = 0
         
        
        
    
    def capture(self):
        '''
        '''
        image = self.__images[self.__index]
        
        if len(self.__images) > 0:
            self.__index += 1
            self.__index %= len(self.__images) 
            
        return image

        