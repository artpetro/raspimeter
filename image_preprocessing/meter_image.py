'''
Created on 13.10.2015

@author: Artem
'''

# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
        
from .digit import Digit

# DEBUG
show_digits = 0
show_aligned_bounding_rects = 0
show_digits_candidates = 0
show_all_bounding_rects = 0
show_rotated_image = 0
show_canny_andlines = 0
show_horizontal_lines = 0
show_aligned_boxes = 0

store_aligned_boxes = 1

class MeterImage(object):
        
    '''
    Class doc
    '''

    def __init__(self, meter, source_image, root_dir):
        '''
        Constructor
        '''
        self.__meter = meter
        self.__root_dir = root_dir
        self.__meter_image_settings = meter.meter_image_settings
        self.__image_width = meter.meter_image_settings.image_width
        self.__rgb_source_image = source_image
        self.__grayscaled_source_image = self.__getPreparedImage(source_image.copy())
        self.__digits_number = meter.meter_settings.digits_number
    
    
    def getMeter(self):
        '''
        '''
        return self.__meter
    
    
    def storeImage(self, path, message='', store_preview=False, store_rgb=True):
        '''
        '''
        if store_rgb:
            image = self.__rgb_source_image
        
        else:
            image = self.__grayscaled_source_image
        
        if message != '':
            image = self.__putLabel(image, message)
            
        cv2.imwrite(path, image)
        
        if store_preview:
            height, width = image.shape[:2]
            #TODO resize correctly
            copy = image.copy()
            resized = cv2.resize(copy, (int(width / 4), int(height / 4)))
            cv2.imwrite(path.replace('.png', '_preview.png'), resized)
            
    
    def __putLabel(self, image, message):
        height, width = image.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1
        thickness = 2
        pos = (10, 40)
        size, baseline = cv2.getTextSize(message, font, scale, thickness)
        cv2.rectangle(image, (pos[0], pos[1]+baseline),
          (pos[0]+size[0], pos[1]-size[1]),
          (0,0,255), -1);
        cv2.putText(image, message, pos, font, scale, (255,255,255), thickness)
            
        return image
        

    def getGrayScaledSourceImage(self):
        '''
        '''
        return self.__grayscaled_source_image    
              
                
    def getRBGSourceImage(self):
        '''
        '''
        return self.__rgb_source_image
    
    
    def getDigits(self):
        '''
        '''
        self.__getLines()
        lines, theta = self.__getRotationAngle()
        self.__rotate(theta)
        
        return self.__findDigits()
        
    def __getPreparedImage(self, image):
        '''
        '''
        prepared_image = image
        if len(image.shape) == 3: 
            prepared_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        height, width = prepared_image.shape[:2]
        prepared_image = cv2.resize(prepared_image, (self.__image_width, int(self.__image_width * height / width)))
        # remove noise
        prepared_image = cv2.GaussianBlur(prepared_image, (3, 3), 0)
        
        return prepared_image

    def __getLines(self):
        '''
        '''
        lines_threshold = self.__meter_image_settings.hough_lines
        edges = self.__getCannyEdges()
        lines = cv2.HoughLines(edges, 1, np.pi/180, lines_threshold)
        
        if show_canny_andlines:
            lines_img = self.__drawHoughLines(lines)
            #cv2.imwrite(self.__root_dir + 'canny.png', edges)
            cv2.imshow('getLinesEdges', np.concatenate((edges, lines_img), axis=1))
            cv2.waitKey(0)  

        return lines
    
    
    def __getRotationAngle(self):
        '''
        Detect the skew of the image by finding almost (+- 30 deg) horizontal lines.
        src: https://www.kompf.de/cplus/emeocv.html, https://github.com/skaringa/emeocv/blob/master/ImageProcessor.cpp
        TODO (+- )angle in config 
        '''
        lines = self.__getLines()
        horizontal_lines = list()
        theta_min = 60 * np.pi/180;
        theta_max = 120 * np.pi/180;
        theta_avr = 0.0;
        theta_deg = 0.0;
        
        for line in lines[0]:
            theta = line[1]
            
            if theta > theta_min and theta < theta_max:
                horizontal_lines.append(line)
                theta_avr += theta;
       
        if len(horizontal_lines) > 0:
            theta_avr /= len(horizontal_lines)
            theta_deg = (theta_avr / np.pi * 180) - 90
             
        
        if show_horizontal_lines:
            lines_img = self.__drawLines(horizontal_lines)
            cv2.imshow('show_horizontal_lines', lines_img)
            #cv2.imwrite(self.__root_dir + 'horizontal_lines.png', lines_img)
            cv2.waitKey(0)
        
        return horizontal_lines, theta_deg
    
    
    def __findDigits(self):
        '''
        based on https://www.kompf.de/cplus/emeocv.html, https://github.com/skaringa/emeocv/blob/master/ImageProcessor.cpp
        '''
        edges = self.__getCannyEdges()
        # only two ret vals in opencv 2.* :
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        # v 3.*:
        #_, contours, hierarchy = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        # filter contours by bounding rect size
        filtered_contours, boundingBoxes = self.__filterContours(contours)
        alignedBoundingBoxes = list()
        
        for box in boundingBoxes:
            tmp_alignedBoundingBoxes = self.__getAlignedBoundingBoxes(box, boundingBoxes)
            
            if len(tmp_alignedBoundingBoxes) > len(alignedBoundingBoxes):
                alignedBoundingBoxes = tmp_alignedBoundingBoxes
        
        
        alignedBoundingBoxes = sorted(set(alignedBoundingBoxes))
        
#         print "alignedBoundingBoxes SET len: %s" % len(alignedBoundingBoxes)
#         for box in alignedBoundingBoxes:
#             print box
        if store_aligned_boxes:
            copy = self.__grayscaled_source_image.copy()
            
            for br in alignedBoundingBoxes:
                x,y,w,h = br
                cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 255, 255), 1)
                
            cv2.imwrite(self.__root_dir + 'last_knn_capture.png', copy)
            
        if show_aligned_boxes:
            copy = self.__grayscaled_source_image.copy()
            
            for br in alignedBoundingBoxes:
                x,y,w,h = br
                cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 255, 255), 1)
                #cv2.line(copy, (x_mid, 5), (x_mid, 20), (255, 255, 255), 1)
            #cv2.imwrite(self.__root_dir + 'alignedBoundingBoxes.png', copy)
            cv2.imshow("alignedBoundingBoxes", copy)
            cv2.waitKey(0)

        # check for x gap and remove duplicates, calculate position
        digits_by_position = self.__getPositions(alignedBoundingBoxes)
        digits, x_gaps = self.__cropDigits(digits_by_position)
        
        if show_digits:
            self.__showDigits(digits)
        
        return digits, x_gaps
                
        
    def __getPositions(self, alignedBoundingBoxes):
        '''
        '''
        digit_data_list = list()
        return_list = list()
        boxesList = list(alignedBoundingBoxes)
        
        digit_area_width = (boxesList[-1][0] - boxesList[0][0] + boxesList[-1][2]) / self.__digits_number
        
        # calculate positions
        for box in boxesList:
            
            x = box[0]
            w = box[2]
            h = box[3]
        
            position = (x + w/2) / digit_area_width
            digit_data_list.append((position, box, w*h))
        
#             print position
#             print box
            
        box_dict = dict()

        for digit_data in digit_data_list:
            position = digit_data[0]
            
            if position in box_dict:
                # append the new number to the existing array at this slot
                box_dict[position].append((digit_data[1], digit_data[2]))
            
            else:
                # create a new array in this slot
                box_dict[position] = [(digit_data[1], digit_data[2])]
        
        # sort by area size
        for position, value in box_dict.iteritems():
            value.sort(key=lambda tup: tup[1], reverse=True)
            # create a digit from biggest candidate
            return_list.append((position, value[0][0]))
            
        if show_aligned_bounding_rects:
            copy = self.__grayscaled_source_image.copy()
            
            for br in return_list:
                x,y,w,h = br[1]
                cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 255, 255), 1)   
                
            cv2.imshow("show_aligned_bounding_rects", copy)
            cv2.waitKey(0) 
        
        return return_list
        
            
    def __cropDigits(self, digits_by_position):
        '''
        '''
        digits = list()
        x_axis_gaps = list()
        tmp_gap = digits_by_position[0][1][0] # x of first digit
        
        # cut and return rects with digits
        for roi_and_pos in digits_by_position:
            x,y,w,h = roi_and_pos[1]
            roi = self.__grayscaled_source_image[y : y + h, x : x + w]
            digits.append(Digit(roi))
            x_axis_gaps.append(x-tmp_gap)
            tmp_gap = x
            
#         print x_axis_gaps
                 
        return digits, x_axis_gaps    
    
    
    def __getAlignedBoundingBoxes(self, box, boundingBoxes):
        '''
        '''
        boundingBoxesCopy = list(boundingBoxes)
        alignedBoundingBoxes = list()
        #x = box[0]
        y = box[1]
        max_y_gap = self.__meter_image_settings.digits_y_axis_max_gap
        #min_x_gap = 30
        
        for box_iter in boundingBoxesCopy:
            y_iter = box_iter[1]
            #x_iter = box_iter[0]
            
            if abs(y - y_iter) < max_y_gap:# and abs(x - x_iter) > min_x_gap:
                alignedBoundingBoxes.append(box_iter)
        
        return alignedBoundingBoxes   
        
        
    def __filterContours(self, contours):  
        '''
        '''
#         print self.__meter_image_settings.to_json()
        
        max_digit_height = self.__meter_image_settings.max_digit_height
        min_digit_height = self.__meter_image_settings.min_digit_height
        max_digit_width = self.__meter_image_settings.max_digit_width
        min_digit_width = self.__meter_image_settings.min_digit_width
        
        filtered_contours = list()
        bounding_rects = list()
        
        copy = self.__grayscaled_source_image.copy()
        
        for contour in contours:
            bounding_rect = cv2.boundingRect(contour)
            w = bounding_rect[2]
            h = bounding_rect[3]
            
            if show_all_bounding_rects:
                x,y,w,h = bounding_rect
                cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 255, 255), 1)
            
            
            if w < h and h > min_digit_height and h < max_digit_height and w > min_digit_width and w < max_digit_width:
                filtered_contours.append(contour)
                bounding_rects.append(bounding_rect)
        
        if show_all_bounding_rects:
            #cv2.imwrite(self.__root_dir + 'all_bounding_rects.png', copy)
            cv2.imshow("show_all_bounding_rects", copy)
            cv2.waitKey(0)
        
        if show_digits_candidates:
            copy = self.__grayscaled_source_image.copy()
            
            for br in bounding_rects:
                x,y,w,h = br
                cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 255, 255), 1)
                #cv2.line(copy, (x_mid, 5), (x_mid, 20), (255, 255, 255), 1)
                
            cv2.imshow("digitsCandidate", copy)
            cv2.waitKey(0)
            
        #print "Filtered contours len: %s" % len(filtered_contours)    
            
        return filtered_contours, bounding_rects
        
        
    def __getCannyEdges(self):
        '''
        TODO adopt canny params
        '''
        canny_1 = self.__meter_image_settings.canny_1
        canny_2 = self.__meter_image_settings.canny_2
        edges = cv2.Canny(self.__grayscaled_source_image, canny_1, canny_2)
        
        return edges    
    
    
    def __rotate(self, angle):
        '''
        '''
        rows, cols = self.__grayscaled_source_image.shape 
        M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
        self.__grayscaled_source_image = cv2.warpAffine(self.__grayscaled_source_image, M, (cols, rows))
        
        if show_rotated_image:
            cv2.imshow('RotatedImage', self.__grayscaled_source_image)
            cv2.waitKey(0)
        
    
    def __drawHoughLines(self, lines):
        '''
        '''
        copy = self.__grayscaled_source_image.copy()
            
        for rho,theta in lines[0]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            cv2.line(copy,(x1,y1),(x2,y2),(0,0,255),2)
            
        return copy
    
    def __drawLines(self, lines):
        '''
        '''
        copy = self.__grayscaled_source_image.copy()
            
        for rho,theta in lines:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            cv2.line(copy,(x1,y1),(x2,y2),(0,0,255),2)
            
        return copy

        
    def __showDigits(self, digits):
        '''
        '''
        vis = None
        
        for digit in digits:
            
            if vis is None:
                vis = digit.getPreparedImage()
            
            else:
                vis = np.concatenate((vis, digit.getPreparedImage()), axis=1)
                label =  1
                
                #cv2.putText(vis, label, (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, 255)
        #cv2.imwrite(self.__root_dir + 'digits.png', vis)
        cv2.imshow("", vis)
        cv2.waitKey(0)      
        