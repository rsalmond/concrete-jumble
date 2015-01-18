import cv2
import numpy as np
import sys

def largest_poly(contours):

    biggest_blob = np.array([],np.int32)
    largest_area = 0

    for con in contours:
        arclen = cv2.arcLength(con, True)
        # use 10% of contour arc length for polygon calculation, not sure why but it seems to work well
        # http://opencvpython.blogspot.ca/2012/06/contours-2-brotherhood.html
        poly = cv2.approxPolyDP(con, arclen * .1, 1)

        # calculate moments cuz for some reason moments['m00'] == area of the contour *shrug*
        moments = cv2.moments(con)

        if len(poly) >= 4:
            if moments['m00'] > largest_area:
                largest_area = moments['m00']
                biggest_blob = np.copy(poly)

    return biggest_blob


if __name__ == '__main__':
    outfile = 'test/img/out.png'
    draw_color = (255,0,0)

    l_green = np.array([45,0,0], np.uint8)
    u_green = np.array([75,255,255], np.uint8)

    # load image file and convert it to HSV colorspace
    im = cv2.imread(sys.argv[1])
    im = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

    #carve out everything not in the green range
    green_pixels = cv2.inRange(im, l_green, u_green)

    contours, hierarchy = cv2.findContours(green_pixels, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cv2.drawContours(im, largest_poly(contours), -1, draw_color, 25)
    cv2.imwrite(outfile, im)
