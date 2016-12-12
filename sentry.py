import time
from datetime import datetime, timedelta

import cv2 as cv
import imutils as im

from buffer import RingBuffer
from camera import Camera


class EventLoop:
    def __init__(self, size=30 * 5, fps=10.0):
        # Buffer(s)
        self.size = int(size)
        self.pre_buffer = RingBuffer(self.size)
        self.post_buffer = []  # TODO: Replace with buffer that caches every so often

        # Recording
        self.fps = fps
        self.recording = False
        self.event_name = None
        self.event_time = None
        self.last_event = None
        self.cutoff = None

    def update(self, frame):
        # Append to pre event or post event if recording
        if not self.recording:
            self.pre_buffer.append(frame)
        else:
            self.post_buffer.append(frame)

    def update_event(self):
        self.last_event = datetime.now()
        self.cutoff = self.last_event + timedelta(0, 5)

    def start_event(self, event_name='event'):
        # Label the video and start recording
        self.recording = True
        self.event_name = event_name
        self.event_time = datetime.now()
        self.update_event()

    def check_cutoff(self):
        if self.recording:
            if datetime.now() > self.cutoff:
                self.finish()

    def save(self):
        # Save video with event name & start time
        name = '{event_name}-{event_time}.avi'.format(
            event_name=self.event_name,
            event_time=self.event_time.strftime('%Y_%m_%d_%H_%M_%S')
        )
        h, w, _ = self.post_buffer[0].shape
        tape = self.pre_buffer.get() + self.post_buffer
        fourcc = cv.VideoWriter_fourcc(*'MJPG')
        writer = cv.VideoWriter(name, fourcc, self.fps, (w, h))
        for f in tape:
            writer.write(f)
        writer.release()

    def finish(self):
        # Flush buffers and save video
        self.save()
        self._flush()

        # Reset recording info
        self.recording = False
        self.event_name = None
        self.event_time = None
        self.last_event = None
        self.cutoff = None

    def _flush(self):
        # Seed pre buffer with tail end of event frames
        tail_frames = self.post_buffer[-self.size:]
        for f in tail_frames:
            self.pre_buffer.append(f)
        self.post_buffer = []


class Sentry:
    def __init__(self, fps=10.0, src=0, min_area=250, verbose=False):
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
                    else:
                        self.loop.update_event()

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
    s = Sentry(verbose=True)
    s.start()
