import cv2
import numpy as np
import sys

draw_color = (27, 255, 255)


def commoncolor(colors, green_thresh=0):
    # loop the color histogram for the most commonly occuring shade of green
    occurances = 0
    colcode = ''
    green_score = 0
    colcount = 0
    for count, rgb in colors:
        colcount += 1
        if is_green(rgb):
            if count > occurances and greenness(rgb) > green_thresh:
                occurances = count
                colcode = hexencode(rgb)
                green_score = greenness(rgb)

    return colcode

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

def get_tlbr_from_poly(polygon, inner=False):
    """ return the topmost, leftmost, bottommost, and rightmost pixel offset found 
        in a set of points"""

    xs, ys = [], []
    for point in polygon:
        xs.append(point[0][0])
        ys.append(point[0][1])

    xs.sort()
    ys.sort()

    # not certain yet that I won't need both inner and outer bounding box
    if inner:
        lowest_key = 1
        highest_key = 2
    else:
        lowest_key = 0
        highest_key = 1

    top = ys[lowest_key]
    bottom = ys[len(ys) - highest_key]
    left = xs[lowest_key]
    right = xs[len(xs) - highest_key]

    return top, left, bottom, right

def get_cropped_img(image, polygon):
    """ return new image cropped at points in polygon """
    top, left, bottom, right = get_tlbr_from_poly(polygon, inner=True)
    return image[top:bottom, left:right]

if __name__ == '__main__':
    outfile = 'test/img/out.png'

    # load image file and convert it to HSV colorspace
    source_im = cv2.imread(sys.argv[1], -1)
    im = np.copy(source_im)

    #im = cv2.cvtColor(source_im, cv2.COLOR_BGR2HSV)
    #l_green = np.array([45,0,0], np.uint8)
    #u_green = np.array([75,255,255], np.uint8)

    green_channel = cv2.split(im)[1] - cv2.split(im)[0]
    #green_channel = green_channel - cv2.split(im)[2]
    #green_channel = 255 - green_channel
    green_pixels = cv2.inRange(green_channel, np.array([50], np.uint8), np.array([200], np.uint8))
    #cv2.imwrite(outfile, green_wut)
    #exit(0)

    l_green = np.array([0, 50, 0, 255], np.uint8)
    u_green = np.array([80, 255, 80, 255], np.uint8)

    # carve out everything not in the green range
    #green_pixels = cv2.inRange(im, l_green, u_green)

    # collect contour data for all blobs of green
    contours, hierarchy = cv2.findContours(green_pixels, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    #cv2.drawContours(source_im, contours, -1, (0, 0, 255, 255), 1)

    # assume the biggest one is the greenscreen
    lpoly = largest_poly(contours)

    # create a new image cropped to the boundaries of the greenscreen polygon
    out_im = get_cropped_img(source_im, lpoly)
    
    # create and execute mask from temp img to discard all greenscreen pixels on original img
    mask_im = get_cropped_img(im, lpoly)
    #green_mask = cv2.inRange(mask_im, l_green, u_green)
    green_out_im = cv2.split(mask_im)[1] - cv2.split(mask_im)[0]
    green_mask = cv2.inRange(green_out_im, np.array([50], np.uint8), np.array([200], np.uint8))
    green_mask = 255 - green_mask
    out_im = cv2.bitwise_and(out_im, out_im, mask=green_mask)

    cv2.imwrite(outfile, out_im)
