import time
from Queue import Queue
from collections import deque
from threading import Thread
import cv2 as cv


class EventRecorder(object):
    def __init__(self, bufsize=150):
        self.frames = deque(maxlen=bufsize)
        self.Q = None
        self.writer = None
        self.thread = None
        self.recording = False

    def update(self, frame):
        self.frames.appendleft(frame)
        if self.recording:
            self.Q.put(frame)

    def start(self, output, fourcc=cv.VideoWriter_fourcc(*'MJPG'), fps=30):
        self.recording = True
        h, w, _ = self.frames[0].shape
        self.writer = cv.VideoWriter(output, fourcc, fps, (w, h))
        self.Q = Queue()

        for i in range(len(self.frames), 0, -1):
            self.Q.put(self.frames[i - 1])

        self.thread = Thread(target=self.write, args=())
        self.thread.daemon = True
        self.thread.start()

    def write(self):
        while True:
            if not self.recording:
                return

            if not self.Q.empty():
                frame = self.Q.get()
                self.writer.write(frame)
            else:
                time.sleep(1.0)

    def flush(self):
        while not self.Q.empty():
            frame = self.Q.get()
            self.writer.write(frame)

    def finish(self):
        self.recording = False
        self.thread.join()
        self.flush()
        self.writer.release()
