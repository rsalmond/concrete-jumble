import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import sys

draw_color = (27, 255, 255)
debug = True

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
        outfile = '%s_out.png' % (sys.argv[1].split('.')[0])
        cv2.imwrite('%s_debug.png' % (sys.argv[1].split('.')[0]), image)

    # assume the biggest one is the greenscreen
    lpoly = largest_poly(contours)

    # return image and mask cropped to the boundaries of the greenscreen polygon
    # NOTE: bitflip the mask here to remove the green when applied and leave the nongreen
    return get_cropped_img(source_im, lpoly), 255 - get_cropped_img(green_pixels, lpoly)

def greenscreen_by_method1(image):
    """ first method for words, doesn't work well at all, just here for posterity """
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

def save_bgr_hist(image):
    plt.figure()
    plt.title('histogram for %s' % (sys.argv[1]))
    plt.xlabel('pixel value')
    plt.ylabel('pixel count')

    for chan, color in zip(cv2.split(image), ('b','g','r')):
        hist = cv2.calcHist([chan], [0], None, [256], [0, 256])
        plt.plot(hist, color=color)
        plt.xlim([0, 256])

    outfile = '%s_hist.png' % (sys.argv[1].split('.')[0])
    print 'writing %s' % (outfile)
    plt.savefig(outfile)

def gen_3d_hist(image):
    hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    print "3D histogram shape: %s, with %d values" % (hist.shape, hist.flatten().shape[0])
    np.set_printoptions(suppress=True)
    print hist
    import pdb
    pdb.set_trace()

def dynamic_green_range(pixels):
    """ compute a good range of intensities to use as upper/lower bounds for color matching """
    
    bins = 256

    #pretty much just experimenting with histograms here ...

    hist = cv2.calcHist([pixels], [0], None, [bins], [0, 256])
    plt.figure()
    plt.title(sys.argv[1])
    plt.xlabel('bins')
    plt.ylabel('numpixls')
    plt.plot(hist)
    plt.xlim([0, 256])
    plt.savefig('test/img/hist.png')

    popular_green = 0 
    pixel_count = 0
    for i in range(bins):
        if hist[i] > pixel_count:
            large_green = hist[i]
            large_bin = i

    return 0,0

def greenscreen_by_method2(image):
    """ improved greenscreen method works well for words """

    # compute green channel minus blue channel (works well, not sure why!)
    green_channel = cv2.split(image)[1] - cv2.split(image)[0]
    #green_lower, green_upper = dynamic_green_range(green_channel)

    # compute green channel minus red channel too (works badly, no idea!)
    #green_channel = green_channel - cv2.split(im)[2]

    # take a totally arbitrary range of single channel intensities which seems to capture 
    # the greenscreen area
    green_pixels = cv2.inRange(green_channel, np.array([40], np.uint8), np.array([175], np.uint8))
    #green_pixels = cv2.inRange(green_channel, green_lower, green_upper)

    out_im, green_mask = crop_to_greenscreen(image, green_pixels)
   
    # create and execute mask from temp img to discard all greenscreen pixels on original img
    return cv2.bitwise_and(out_im, out_im, mask=green_mask)


def greenscreen_by_method3(image):
    """ experimenting with techniques for full body greenscreen """

    # rip out every pixel that isn't primarily green
    for i in range(len(image)):
        for j in range(len(image[i])):
            pixel = image[i][j]
            if pixel[1] > pixel[0] and pixel[1] > pixel[2]:
                continue
            else:
                image[i][j] = np.array([0,0,0,255], np.uint8)

    
    tmp_green = cv2.split(image)[1]
    #contours, hierarchy = cv2.findContours(tmp_green, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    big_green_rows = []
    start = False

    average_green = tmp_green.mean()

    # trying to find a way to help findcontours out by cropping the green in another way
    # think I need more test pictures ...

    for row in range(len(tmp_green)):
        if tmp_green[row].mean() > average_green:
            if not start:
                start = row
            image[row] = np.array([0], np.uint8) * len(tmp_green[row])
        else:
            if start:
                big_green_rows.append([start, row])
                start = False
                continue

    print big_green_rows

    return image

if __name__ == '__main__':
    outfile = '%s_out.png' % (sys.argv[1].split('.')[0])

    source_im = cv2.imread(sys.argv[1], -1)

    work_im = np.copy(source_im)

    work_im = greenscreen_by_method3(work_im)
    save_bgr_hist(work_im)
    #gen_3d_hist(source_im)

    cv2.imwrite(outfile, work_im)
