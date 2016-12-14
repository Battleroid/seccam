import time

import cv2 as cv
import imutils as im

from camera import Camera
from event import EventLoop
from server import Server


class Sentry:
    def __init__(self, fps=5.0, src=0, min_area=250, verbose=False):
        self.camera = Camera(src)
        self.loop = EventLoop(size=fps * 5, fps=fps)
        self.min_area = min_area
        self.verbose = verbose
        self.fps = fps

    def start(self):
        self.camera.start()
        average_frame = None
        time.sleep(1)

        while True:
            frame = self.camera.read()

            # Process frame
            frame = im.resize(frame, width=300)
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray = cv.GaussianBlur(gray, (21, 21), 0)

            # Init average frame
            if average_frame is None:
                average_frame = gray.copy().astype('float')
                continue

            # Add frame to average to help differentiate from existing background
            cv.accumulateWeighted(gray, average_frame, 0.5)
            delta = cv.absdiff(gray, cv.convertScaleAbs(average_frame))
            threshold = cv.threshold(delta, 25, 255, cv.THRESH_BINARY)[1]
            threshold = cv.dilate(threshold, None, iterations=2)
            _, contours, _ = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL,
                                             cv.CHAIN_APPROX_SIMPLE)

            # Check if movement exceeds min threshold
            if len(contours) > 0:
                max_area = cv.contourArea(max(contours, key=cv.contourArea))
                if max_area >= self.min_area:
                    if not self.loop.recording:
                        self.loop.start_event()
                        self.loop.max_area = max_area
                        self.loop.poster_image = frame
                    else:
                        self.loop.update_event()

                    # Replace poster image for video if movement is larger
                    if max_area is not None and max_area > self.loop.max_area:
                        self.loop.max_area = max_area
                        self.loop.poster_image = frame

            # Add frame to appropriate buffer
            self.loop.update(frame)

            # Let loop decide if it's time to finish the event
            self.loop.check_cutoff()

            # Show preview window if verbose mode is on
            if self.verbose:
                cv.imshow('Sentry', frame)
                cv.waitKey(1)

            # Sleep for an interval to achieve our desired framerate target
            time.sleep(1 / self.fps)


if __name__ == '__main__':
    # TODO: docopt or something similar for cli params
    s = Sentry(src=1, verbose=True)
    server = Server(s.camera, fps=s.fps)

    # Start main loop last
    server.start()
    s.start()
