# -*- coding: utf-8 -*-
"""
"""

from preprocessing import get_grayscale, get_binary, invert_area, draw_text, detect
from ROI_selection import detect_lines, get_ROI, show_image
import cv2 as cv
import pytesseract
import numpy as np
import sys
import json
import os.path

pytesseract.pytesseract.tesseract_cmd = r"/usr/local/bin/tesseract"
#filename = "../images/1.png"
image = 0
copy_back = 0
lines = []
height = 0
width = 0

def remove_lines (image, th):
    #Load image grayscalem Otsu's thre
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV, + cv.THRESH_OTSU)[1]
    #repair horizontal lines
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (1,1))
    thresh = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel, iterations=1)

    #Remove horizontal lines
    horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (50,1))
    detect_horizontal = cv.morphologyEx(thresh, cv.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv.findContours (detect_horizontal, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv.drawContours(image, [c], -1, (255,255,255), th)    #Remove horizontal lines

    #Remove vertical lines
    vertical_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1,50))
    detect_vertical = cv.morphologyEx(thresh, cv.MORPH_OPEN, vertical_kernel, iterations=2)
    cnts = cv.findContours (detect_vertical, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv.drawContours(image, [c], -1, (255,255,255), th)
    return image


def draw (event,x, y, flags, params):
    global image, lines, copy_back
    height, width = image.shape[:2]
    loff = (255,255,255)
    lon = (0,0,0)
    th = params[0]
    ptr_t = 3

    #Left mounse button pressed
    if (event == cv.EVENT_LBUTTONDOWN):
        if (flags & cv.EVENT_FLAG_SHIFTKEY):
            #remove lines
            if (flags & cv.EVENT_FLAG_CTRLKEY):
                #remove vertical
                pt1 = (x ,0)
                pt2 = (x, height)
            else:
                pt1 = (0, y)
                pt2 = (width, y)
            #cv.line(image, pt1, pt2, color=loff, thickness = th)
            lines = list (filter (lambda pt: abs (pt[0]-x) > ptr_t and abs(pt[1] - y) > ptr_t, lines))
            #print(r"Updates lines")
            #print(lines)
            image = copy_back.copy()
            # after deletion, draw remaining lines
            for pt in lines:
                if (pt[2] == 0):
                    cv.line(image, (pt[0],0), (pt[0], height), color=lon, thickness = th)
                else:
                    cv.line(image, (0, pt[1]), (width, pt[1]), color=lon, thickness = th)
        else:
            #draw a line
            if (flags & cv.EVENT_FLAG_CTRLKEY):
                #Vertical
                pt1 = (x, 0)
                pt2 = (x, height)
                vh = 0
            else:
                #Horizontal
                pt1 = (0, y)
                pt2 = (width, y)
                vh = 1

            cv.line(image, pt1, pt2, color=lon, thickness = th)
            lines.append([x, y, vh])
            #print (lines)

def add_lines():
    global copy_back, image, height, width
    copy_back = image.copy()
    th = 1

    if (lines):
        #draw lines
        for i in lines:
            if (i[2] == 1):
                cv.line(image, (0, i[1]), (width, i[1]), color = (0,0,0), thickness = 1)
            else:
                cv.line(image, (i[0], 0), (i[0], height), color = (0,0,0), thickness = 1)

    #Making window for a image
    cv.namedWindow("DRAW LINES")
    #Add mouse callback
    cv.setMouseCallback("DRAW LINES", draw, [th])
    #Start the loop
    while (True):
        cv.imshow("DRAW LINES", image)
        k = cv.waitKey(20) & 0xFF

        if k == ord('w'):
            th = 4
            cv.setMouseCallback("DRAW LINWS", draw, [th])
        elif k == ord('q'):
            #draw an imgae to file
            #cv.imwrite('dima.png', image)
            break
    cv.destroyAllWindows()
    return image




def main(display = False, print_text = False, write = False):
    global image, lines, height, width

    ddict = {}
    counter = 0

    args = sys.argv[1:]
    in_file = args[0]
    lang = args[1]
    det = args[2]

    # read file
    src = cv.imread(cv.samples.findFile(args[0]))
    # get dims
    height, width = src.shape[:2]
    # print (height, width)

    #remove black lines
    image =  remove_lines(src, 6)

    if os.path.isfile (in_file + '.lines'):
        print ("Reading lines from file")
        with open(in_file + '.lines', "r") as fp:
            lines = json.load(fp)
            print(lines)

    #Manually add the grid together with saved lines. No args, only globas
    #TODO might be an error if identical lines
    image = add_lines()
    # If there are lines, store them
    if lines:
        print ("Saving lines to file")
        with open(in_file + '.lines', "w") as fp:
            b = json.dump(lines, fp)

    #If lines detection is needed
    if (det == '1'):
        #horizontal, vertical = detect_lines(image, rho=1, threshold=50, minLinLength=1000, maxLineGap=8, display=True, write = False)
        horizontal, vertical = detect_lines(image, minLinLength=50, display=True, write = False)
        print('H2: ', horizontal)
        print('V2: ', verticalxs)

    # lines are stored (x, y, type), they are converted to (0, y1, width-1, y1) for H, and (x0, height-1, x0, y1
    # filter
    h = list (filter (lambda x: x[2] == 1, lines))
    v = list (filter (lambda x: x[2] == 0, lines))
    #sort
    h.sort(key = lambda x: x[1])
    v.sort(key = lambda x: x[0])
    horizontal = list ( map (lambda x: [0,    x[1],     width-1, x[1]], h ))
    vertical =   list ( map (lambda x: [x[0], height-1, x[0],    0],    v ))
    print('H1: ', horizontal)
    print('V1: ', vertical)


    #Wait
#    cv.waitKey(0)
    gray = get_grayscale(image)
    # bw = get_binary(gray)
    # cv.imshow("bw", bw)
    # cv.imwrite("bw.png", bw)
    # bw = invert_area(bw, x, y, w, h, display=True)
    # cv.imwrite("bw_inver.png", bw)
    # #bw = erode(bw, kernel_size=2)
    bw = gray
    # cv.waitKey(0)

    for j in range (0, len (vertical)-1):
        ddict[str(j)] = []

    ## read text
    print("Start detecting text...")
    for i in range(0, len(horizontal) - 1):
        for j in range(0, len(vertical) - 1):

            counter += 1
            progress = counter/((len(horizontal)-1)*(len(vertical)-1)) * 100
            percentage = "%.2f" % progress
            print("Progress: " + percentage + "%")

            # crop the cell
            cropped_image, (x,y,w,h) = get_ROI(bw, horizontal, vertical, j, j+1, i, i+1, offset=1)
#            show_image (cropped_image)
            text = detect(cropped_image, is_number=True, lang = lang)
 #           print (text)

            #store it
            ddict [ str(j) ].append(text.replace('\n','').replace('\x0c','').replace('{','(').replace('}', ')'))

            #print("Is number" + ", Row: ", str(i), ", Keyword: " + keyword + ", Text: ", text)

#            if (display or write):
#                    image_with_text = draw_text(src, x, y, w, h, text)

            if (write):
                cv.imwrite("../images/"+ str(counter) + ".png", image_with_text);


    print(ddict)
    with open (in_file + '.csv', 'w+', encoding='utf-8') as f:
        for col in zip (*ddict.values()):
            #print(col)
            f.write(';'.join(col) + '\n')
    return 0

if __name__ == "__main__":
    main()
