import cv2
import numpy as np
import sys

draw_color = (27, 255, 255)
debug = False

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

def crop_to_greenscreen(image, green_pixels):
    """ create a crop of image to the largest green area found by using the provided green pixels """
    # collect contour data for all blobs of green
    tmp_green = np.copy(green_pixels)
    contours, hierarchy = cv2.findContours(tmp_green, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if debug:
        cv2.drawContours(image, contours, -1, (0, 0, 255, 255), 1)

    # assume the biggest one is the greenscreen
    lpoly = largest_poly(contours)

    # return image and mask cropped to the boundaries of the greenscreen polygon
    # NOTE: bitflip the mask here to remove the green when applied and leave the nongreen
    return get_cropped_img(source_im, lpoly), 255 - get_cropped_img(green_pixels, lpoly)

def greenscreen_by_method1(image):
    # for HSV colorspace
    #im = cv2.cvtColor(source_im, cv2.COLOR_BGR2HSV)
    #l_green = np.array([45,0,0], np.uint8)
    #u_green = np.array([75,255,255], np.uint8)

    # for BGR colorspace
    l_green = np.array([0, 50, 0, 255], np.uint8)
    u_green = np.array([80, 255, 80, 255], np.uint8)

    # get all the greens that fall into the lower/upper range and use them to isolate greenscreen
    green_pixels = cv2.inRange(image, l_green, u_green)
    out_im, green_mask = crop_to_greenscreen(image, green_pixels)

    # mask away the greenscreen pixels from the cropped image leaving only the letters
    return cv2.bitwise_and(out_im, out_im, mask=green_mask)

def greenscreen_by_method2(image):

    # compute green channel minus blue channel (works well, not sure why!)
    green_channel = cv2.split(image)[1] - cv2.split(image)[0]

    # compute green channel minus red channel too (works badly, no idea!)
    #green_channel = green_channel - cv2.split(im)[2]

    # take a totally arbitrary range of single channel intensities which seems to capture 
    # the greenscreen area
    green_pixels = cv2.inRange(green_channel, np.array([50], np.uint8), np.array([200], np.uint8))

    out_im, green_mask = crop_to_greenscreen(image, green_pixels)
    
    # create and execute mask from temp img to discard all greenscreen pixels on original img
    return cv2.bitwise_and(out_im, out_im, mask=green_mask)


if __name__ == '__main__':
    outfile = 'test/img/out_%s.png'

    # load image file and convert it to HSV colorspace
    source_im = cv2.imread(sys.argv[1], -1)
    im = np.copy(source_im)

    cv2.imwrite(outfile % (1), greenscreen_by_method1(im))
    cv2.imwrite(outfile % (2), greenscreen_by_method2(im))


