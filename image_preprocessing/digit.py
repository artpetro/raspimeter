'''
Created on 06.01.2016

@author: Artem
'''
import cv2

class Digit(object):
    '''
    classdocs
    '''
    
    def __init__(self, soure_image):
        '''
        Constructor
        '''
        self.__grayscaled_source_image = cv2.resize(soure_image, (20, 45))
        self.__number = '?'
        
    def getPreparedImage(self):
        return self.__grayscaled_source_image.copy()
    
    def setNumber(self, number):
        self.__number = number
        
    def getNumber(self):
        return self.__number
        
    