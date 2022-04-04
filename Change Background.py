import os
from cv2 import line
import cvzone
import cv2
import requests
from cvzone.SelfiSegmentationModule import SelfiSegmentation
from datetime import date

def nothing(x):
    pass

def rescale_frame(frame, percent=50):
    width = int(frame.shape[1] * percent/ 100)
    height = int(frame.shape[0] * percent/ 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)


def create_trackbar():
    #create a seperate window named 'controls' for trackbar
    cv2.namedWindow('controls',2)
    cv2.resizeWindow("controls", 550,10);

    #create trackbar in 'controls' window with name 'r''
    cv2.createTrackbar('r','controls',0,255,nothing)
    cv2.createTrackbar('g','controls',0,255,nothing)
    cv2.createTrackbar('b','controls',0,255,nothing)

def linenotify(message, path):
    url = 'https://notify-api.line.me/api/notify'
    token = 'xxxxxxxxxxxxxxxxxxxxxxxxx' # Line Notify Token
    img = {'imageFile': open(path,'rb')} #Local picture File
    data = {'message': message}
    headers = {'Authorization':'Bearer ' + token}
    session = requests.Session()
    session_post = session.post(url, headers=headers, files=img, data =data)
    print(session_post.text) 

def main():
    today = date.today()
    img_counter = 1
    mode = False
    trackbar_check = False
    saved_r = 0
    saved_g = 0
    saved_b = 0

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    segmentor = SelfiSegmentation()

    # create_trackbar()

    listImg = os.listdir("BackgroundImages")
    imgList = []
    for imgPath in listImg:
        img = cv2.imread(f'BackgroundImages/{imgPath}')
        imgList.append(img)
    indexImg = 0

    while True:
        _, img = cap.read()
        img = rescale_frame(img, percent=50) 

        background = cv2.resize(imgList[indexImg], (int(img.shape[1]), int(img.shape[0])), interpolation = cv2.INTER_AREA)
        
        if mode:
            if trackbar_check:
                saved_r = int(cv2.getTrackbarPos('r','controls'))
                saved_g = int(cv2.getTrackbarPos('g','controls'))
                saved_b = int(cv2.getTrackbarPos('b','controls'))
                cv2.destroyWindow('controls')
                trackbar_check = False
            img_out = segmentor.removeBG(img, background)
        else:
            if not trackbar_check:
                create_trackbar()
                cv2.setTrackbarPos('r', 'controls', saved_r)
                cv2.setTrackbarPos('g', 'controls', saved_g)
                cv2.setTrackbarPos('b', 'controls', saved_b)
                trackbar_check = True
            #returns current position/value of trackbar 
            r = int(cv2.getTrackbarPos('r','controls'))
            g = int(cv2.getTrackbarPos('g','controls'))
            b = int(cv2.getTrackbarPos('b','controls'))
            img_out = segmentor.removeBG(img, (b, g, r))

        cv2.imshow("Image", cvzone.stackImages([img, img_out], 2, 1))

        key_press = cv2.waitKey(1)
        if key_press == ord('a') and mode:
            if indexImg>0:
                indexImg -=1
            elif not indexImg:
                indexImg = len(imgList)-1
        if key_press == ord('d') and mode:
            if indexImg<len(imgList)-1:
                indexImg +=1
            elif indexImg == len(imgList)-1:
                indexImg = 0
        if key_press == ord('q'):
            break
        if key_press == ord('s'):
            img_name = "{}_P{}.png".format(today, img_counter)
            cv2.imwrite(img_name, img_out)
            print("{} is written!".format(img_name))
            linenotify(img_name, "./"+img_name)
            img_counter += 1
        
        if key_press == ord('m'):
            mode = not mode
    cap.release()
    cv2.destroyAllWindows()

main()
