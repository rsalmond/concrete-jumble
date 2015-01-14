"""
find green pixel value in an image by most common shade or most green intensity for hacky chromakey stuff
"""

import sys
from PIL import Image

def img(filename):
    return Image.open(filename)

def hexencode(rgb):
    r=rgb[0]
    g=rgb[1]
    b=rgb[2]
    return '#%02x%02x%02x' % (r,g,b)

def is_green(rgb):
    # true if green the dominant component of the pixel
    return rgb[1] - (rgb[0] + rgb[2]) > 0

def greenness(rgb):
    if is_green(rgb):
        return rgb[1] - (rgb[0] + rgb[2])

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
                #print "replacing %s occurances of %s (greeness: %s) with %s occurances of %s (greenness: %s)" % (occurances, colcode, green_score, count, hexencode(rgb), greenness(rgb))
                occurances = count
                colcode = hexencode(rgb)
                green_score = greenness(rgb)
    #print 'colcount: %s' % (colcount)

    return colcode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        im = img(sys.argv[1])
        h, w = im.size
        colors = im.getcolors(h*w)
        #print "lencols: %s" % (len(colors))
        print commoncolor(colors, green_thresh=30)
