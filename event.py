from datetime import datetime, timedelta

import cv2 as cv

from buffer import RingBuffer


class EventLoop:
    def __init__(self, size=5, fps=10.0):
        # Buffer(s)
        self.size = int(size * fps)
        self.pre_buffer = RingBuffer(self.size)
        self.post_buffer = []  # TODO: Replace with buffer that caches every so often

        # Recording
        self.fps = fps
        self.recording = False
        self.event_name = None
        self.event_time = None
        self.last_event = None
        self.cutoff = None

        # For recording the poster image of an event
        self.poster_image = None
        self.max_area = None

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
