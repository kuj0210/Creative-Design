from observer import *
import cv2
import numpy as np
import time
import os

class Vi(Observer):
    BREAK_AWAY = ""
    RETURN_BACK = ""
    UNTILL_BREAK = ""
    frame = []
    origin_frame = []
    my_contours = []
    st_frame = 0
    out_frame = 0
    sz_frame = 0
    os_frame = 0
    ob_frame = 0
    cap = 0
    vi_width = 0
    vi_height = 0
    contours = []
    edges = []
    old_frame = []
    old_gray = []
    diff = []
    babyCNT = []
    babyCNT_ST = 0
    out_time = 0

    def __init__(self,Push):
        self.reSet(Push)
        self.BREAK_AWAY = "아이가 자리에서 벗어났어요!"
        self.RETURN_BACK = "아이가 자리에 돌아왔어요!"
        self.UNTILL_BREAK = "아이가 오랫동안 자리에서 벗어났어요!"
        self.mPush = Push
        self.sz_frame = 15
        self.os_frame = 10
        self.ob_frame = 1
        self.babyCNT_ST = 50
      
    def openCamera(self):
        os.system('sudo modprobe bcm2835-v4l2')
        self.cap = cv2.VideoCapture(0)
        self.vi_width = int(self.cap.get(3))
        self.vi_height = int(self.cap.get(4))     
        self.getSaftyZone()
        ret, self.old_frame = self.cap.read()
        if self.old_frame is None:
            print("camera error1")
            return
        self.old_gray = cv2.cvtColor(self.old_frame, cv2.COLOR_BGR2GRAY)
        
    def getCapture(self):
        ret, self.frame = self.cap.read()
        if self.frame is None:
            print("camera error2")
            return
        self.origin_frame = self.frame.copy()
        self.frame_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        self.diff = cv2.absdiff(self.old_gray, self.frame_gray)
        kernel = np.ones((3, 3), np.float32) / 25
        dst = cv2.filter2D(self.diff, -1, kernel)
        self.edges = cv2.Canny(dst, 0, 30)
        _, self.contours, _ = cv2.findContours(self.edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    def checkBabyCNT(self):
        time = time.time()
        el_time = time - self.out_time
        if self.babyCNT < self.babyCNT_ST:
            if self.out_time == 0:
                self.out_time = time.time()
                return (self.BREAK_AWAY)
        else:
            if self.out_time > 0:
                self.out_time = 0
                return (self.RETURN_BACK)
        if self.out_time > 0 and int(el_time) % 600 == 0:
            return (self.UNTILL_BREAK)
        return 0

    def getMoment(self):
        max_area = 0
        ci = 0
        for i in range(0, len(self.contours)):
            cnt = self.contours[i]
            area = cv2.contourArea(cnt)
            if (area > max_area):
                max_area = area
                ci = i
        cnt = self.contours[ci]
        self.babyCNT = cnt

    def checkObserveFrame(self):
        self.st_frame = self.st_frame + 1
        if self.st_frame < self.os_frame: return 1
        if self.st_frame != self.sz_frame:
            if self.st_frame % self.ob_frame != 0 and self.out_frame == 0:
                return 1
            if self.st_frame % 5 != 0:
                return 1
        return 0

    def show(self):
        cv2.imshow('fgmask', self.frame)
        cv2.imshow('EDGES', self.edges)

    def copyFrame(self):
        self.old_gray = self.frame_gray.copy()

    def run(self):
        print("Running Vi")
        while(True):
            try :
                if self.cap == 0 :
                    self.openCamera()
            except :
                print("Open camera error")
                continue
            try :
                item = self.popRQ()
            except :
                print("Vo에서 popRQ 리퀘스트 받기 에러")
                continue
            if (item != False):
                try :
                    print("Running picture request")
                    cv2.imwrite(self.mPush.T.SERIAL + ".png" , self.origin_frame)
                    self.mPush.T.pushImage(item.user,self.mPush.T.SERIAL + ".png" )
                except :
                    print('Picture push error')
                    continue

            if(True):
                if self.checkObserveFrame() == 1:
                    continue
                try :
                    self.getCapture()
                    if self.contours :
                        self.getMoment()
                except :
                    print("Image processing error")
                try :
                    MSG = self.checkBabyCNT()
                    if MSG != 0:
                        self.mPush.insertMSG('ALL', MSG)
                        #time.sleep(10)
                except :
                    print("MSG error")
                self.show()
                k = cv2.waitKey(1) & 0xff
                if k == 27:
                    break
                self.copyFrame()
        self.cap.release()
        cv2.destroyAllWindows()

        time.sleep(15)
