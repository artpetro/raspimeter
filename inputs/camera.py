'''
Created on 13.10.2015

@author: Artem
'''

from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import RPi.GPIO as GPIO

class Camera(object):
    '''
    classdocs
    '''

    def __init__(self, number, led_pin):
        '''
        Constructor
        '''
        self.__cameraNumber = number
        self.__led_pin = led_pin
        self.__camera = PiCamera()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(led_pin, GPIO.OUT)

        
    def capture(self):
        '''
        '''
        GPIO.output(self.__led_pin, GPIO.HIGH)
        time.sleep(0.1)
        rawCapture = PiRGBArray(self.__camera)
        # allow the camera to warmup
        time.sleep(0.1)
        self.__camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        time.sleep(0.1)
        GPIO.output(self.__led_pin, GPIO.LOW)
            
        return image
