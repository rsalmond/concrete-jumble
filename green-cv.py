import cv2
import numpy as np
import sys

outfile = 'test/img/out.png'

l_green = np.array([45,0,0], np.uint8)
u_green = np.array([75,255,255], np.uint8)

im = cv2.imread(sys.argv[1])
im = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

#carve out everything not in the green range
green_pixels = cv2.inRange(im, l_green, u_green)

contours, hierarchy = cv2.findContours(green_pixels, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

#TODO: iterate contours and find the one with the largest area then clip image to that box

cv2.drawContours(im, contours, -1, (0,0,255), 5)

cv2.imwrite(outfile, im)
