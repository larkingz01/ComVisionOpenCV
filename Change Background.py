import os
import cvzone
import cv2
import requests
from cv2 import WINDOW_NORMAL, line
from cvzone.SelfiSegmentationModule import SelfiSegmentation
from cvzone.HandTrackingModule import HandDetector
from datetime import date
from tkinter import *
from tkinter import filedialog


def nothing(x):
    pass


def get_background():
    listImg = os.listdir("BackgroundImages")
    imgList = []

    for imgPath in listImg:
        img = cv2.imread(f'BackgroundImages/{imgPath}')
        imgList.append(img)
    return imgList


def insert_img():
    root = Tk()
    root.withdraw()
    pic_path = filedialog.askopenfilename(filetypes=[
        ("all file", ".png"),
        ("all file", ".jpg")])
    if len(pic_path) > 0:
        img = cv2.imread(pic_path)
        cv2.imwrite('BackgroundImages/' +
                    str(len([i for i in os.listdir("BackgroundImages")]) + 1) + ".jpg", img)
        root.destroy()


def rescale_frame(frame, percent=50):
    width = int(frame.shape[1] * percent / 100)
    height = int(frame.shape[0] * percent / 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)


def create_trackbar():
    # create a seperate window named 'controls' for trackbar
    cv2.namedWindow('controls', WINDOW_NORMAL)
    cv2.resizeWindow("controls", 550, 10)

    # create trackbar in 'controls' window with name 'r''
    cv2.createTrackbar('r', 'controls', 0, 255, nothing)
    cv2.createTrackbar('g', 'controls', 0, 255, nothing)
    cv2.createTrackbar('b', 'controls', 0, 255, nothing)


def linenotify(message, path):
    url = 'https://notify-api.line.me/api/notify'
    token = 'Dn7jX79Ak82Tl10zaS3V1OrMcZl5MJIPHZx9ymzfofo'
    img = {'imageFile': open(path, 'rb')}
    data = {'message': message}
    headers = {'Authorization': 'Bearer ' + token}
    session = requests.Session()
    session_post = session.post(url, headers=headers, files=img, data=data)
    print(session_post.text)


def captured(img_counter, img_out):
    today = date.today()
    img_name = "{}_P{}.png".format(today, img_counter)
    if not os.path.exists('CapturedImages'):
        os.mkdir('CapturedImages')
    cv2.imwrite('CapturedImages/'+img_name, img_out)
    print("{} is written!".format(img_name))
    linenotify(img_name+" is captured.", "CapturedImages/"+img_name)


def main():

    def convert_code():
        code = text.get()
        color_input.destroy()
        converter = []
        if code.startswith("#"):
            code = code.lstrip("#")
            if len(code) == 3:
                code = [i*2 for i in code]
                code = "".join(code)
            for i in (0, 2, 4):
                decimal = int(code[i:i+2], 16)
                converter.append(decimal)
        cv2.setTrackbarPos('r', 'controls', int(converter[0]))
        cv2.setTrackbarPos('g', 'controls', int(converter[1]))
        cv2.setTrackbarPos('b', 'controls', int(converter[2]))
        print('RGB =', converter)


    finger_check = False
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

    imgList = get_background()
    indexImg = 0

    detector = HandDetector(detectionCon=0.8, maxHands=2)
    while True:
        _, img = cap.read()
        img = rescale_frame(img, percent=50)
        imgHand = img.copy()
        hands, _ = detector.findHands(imgHand)

        background = cv2.resize(imgList[indexImg], (int(img.shape[1]), int(
            img.shape[0])), interpolation=cv2.INTER_AREA)

        if mode:
            if trackbar_check:
                saved_r = int(cv2.getTrackbarPos('r', 'controls'))
                saved_g = int(cv2.getTrackbarPos('g', 'controls'))
                saved_b = int(cv2.getTrackbarPos('b', 'controls'))
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
            # returns current position/value of trackbar
            r = int(cv2.getTrackbarPos('r', 'controls'))
            g = int(cv2.getTrackbarPos('g', 'controls'))
            b = int(cv2.getTrackbarPos('b', 'controls'))
            img_out = segmentor.removeBG(img, (b, g, r))

        cv2.imshow("Image", cvzone.stackImages([img, img_out], 2, 1))

        key_press = cv2.waitKey(1)
        if key_press == ord('a') and mode:
            if indexImg > 0:
                indexImg -= 1
            elif not indexImg:
                indexImg = len(imgList)-1
        if key_press == ord('d') and mode:
            if indexImg < len(imgList)-1:
                indexImg += 1
            elif indexImg == len(imgList)-1:
                indexImg = 0
        if key_press == ord('q'):
            break
        if key_press == ord('s'):
            captured(img_counter, img_out)
            img_counter += 1
        if hands:
            if detector.fingersUp(hands[0]) == [1, 1, 1, 1, 1]:
                finger_check = True
            if finger_check and detector.fingersUp(hands[0]) == [0, 0, 0, 0, 0]:
                captured(img_counter, img_out)
                img_counter += 1
                finger_check = False
        if key_press == ord('m'):
            mode = not mode
        if key_press == ord('i'):
            insert_img()
            imgList.clear()
            imgList = get_background()
            if trackbar_check:
                mode = not mode
            indexImg = len(imgList) - 1
        if key_press == ord('c'):
            color_input = Tk()
            color_input.title("Input Custom Color")
            color_input.geometry("300x100")
            Label(color_input, text="Input custom color",
                  font=("Modern", 10)).pack()
            text = StringVar()
            Entry(color_input, textvariable=text).pack()
            Button(color_input, text="Enter", bg="red",
                   fg="black", command=convert_code).pack()
            color_input.mainloop()
    cap.release()
    cv2.destroyAllWindows()


main()
