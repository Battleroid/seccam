from threading import Thread
import cv2 as cv


class Camera:
    def __init__(self, src=0):
        self.cam = cv.VideoCapture(src)
        self.ok, self.frame = self.cam.read()
        self.stopped = False

    def update(self):
        while True:
            if self.stopped:
                return
            self.ok, self.frame = self.cam.read()

    def start(self):
        self.stopped = False
        Thread(target=self.update, args=()).start()
        # return self

    def stop(self):
        self.stopped = True

    def read(self):
        return self.frame

    def to_jpeg(self):
        _, jpeg = cv.imencode('.jpg', self.frame)
        return jpeg.tobytes()
