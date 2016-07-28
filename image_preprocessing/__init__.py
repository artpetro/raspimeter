

'''
import cv2
import os
import math
import numpy as np

DIGIT_AREA_MIN_HEIGHT = 75
DIGIT_AREA_MAX_HEIGHT = 150

HOUGH_LINES_THRESHOLD = 150


image = cv2.imread(os.path.dirname(__file__) + "/gas_meter_3.jpg", cv2.IMREAD_GRAYSCALE)


# load key feature
sample = cv2.imread(os.path.dirname(__file__)+"/comma_feature.png", cv2.IMREAD_GRAYSCALE)


sample_h, sample_w = sample.shape
                
# find key feature on image
res = cv2.matchTemplate(image, sample, cv2.TM_CCORR_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

# center of feature located
x_center = max_loc[0] + sample_w/2
y_center = max_loc[1] + sample_h/2       

cv2.circle(image, (x_center, y_center), sample_w, (255, 255, 255), 1)

cv2.imshow("src", image)



image = cv2.imread(os.path.dirname(__file__) + "/gas_meter_3.jpg", cv2.IMREAD_GRAYSCALE)

resized = cv2.resize(image, (600, 450))

# load key feature
sample = cv2.imread(os.path.dirname(__file__)+"/comma_feature.png", cv2.IMREAD_GRAYSCALE)

sample = cv2.resize(image, (30, 40))

sample_h, sample_w = sample.shape
                
# find key feature on image
res = cv2.matchTemplate(resized, sample, cv2.TM_CCORR_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

# center of feature located
x_center = max_loc[0] + sample_w/2
y_center = max_loc[1] + sample_h/2       

cv2.circle(resized, (x_center, y_center), sample_w, (255, 255, 255), 1)

cv2.imshow("src", resized)



blur = cv2.GaussianBlur(resized, (5, 5), 0)

clahe_tmp = cv2.createCLAHE(clipLimit = 2.0, tileGridSize = (8,8))

clahe = clahe_tmp.apply(blur)

#cv2.imshow("blur", clahe)

cv2.imwrite("clahe.png", clahe)

ret, thresh = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

edges = cv2.Canny(thresh, 100, 200)

#cv2.imshow("edges", edges)

# TODO adopt thres
lines = cv2.HoughLines(edges, 1, np.pi/180, threshold = HOUGH_LINES_THRESHOLD)

for line in lines[0]:

    rho = line[0];
    theta = line[1];
    a = math.cos(theta) 
    b = math.sin(theta);
    x0 = a*rho
    y0 = b*rho;
    pt1 = ( int(x0 - 1000 * b), int(y0 + 1000 * a))
    pt2 = (int(x0 + 1000*b), int(y0 - 1000 * a))
        
    cv2.line(resized, pt1, pt2, (255, 255, 255), 1)

borders = []

for line in lines[0]:
    pass 


cv2.imshow("lines", resized)





cv2.waitKey()

'''