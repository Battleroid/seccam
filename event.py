from datetime import datetime, timedelta

import cv2 as cv
import logging
import requests

from buffer import RingBuffer
from PIL import Image
from urllib.parse import urljoin


class EventLoop:
    def __init__(self, url, size=5, fps=10.0):
        # Buffer(s)
        self.size = int(size * fps)
        self.pre_buffer = RingBuffer(self.size)
        self.post_buffer = []

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

        # Uploading
        self.url = url

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
        name = '{event_name}-{event_time}'.format(
            event_name=self.event_name,
            event_time=self.event_time.strftime('%Y_%m_%d_%H_%M_%S')
        )
        video_name = name + '.avi'
        image_name = name + '.jpg'
        h, w, _ = self.post_buffer[0].shape
        tape = self.pre_buffer.get() + self.post_buffer
        fourcc = cv.VideoWriter_fourcc(*'MJPG')
        writer = cv.VideoWriter(video_name, fourcc, self.fps, (w, h))
        for f in tape:
            writer.write(f)
        writer.release()
        rgb = cv.cvtColor(self.poster_image, cv.COLOR_BGR2RGB)
        jpeg = Image.fromarray(rgb)
        jpeg.save(image_name)
        logging.info('Saving video and image as {}'.format(
            name
        ))
        self._upload(name, video_name, image_name)

    def _upload(self, name, video_name, image_name):
        dest = urljoin(self.url, '/event/new')
        files = {
            'video': open(video_name, 'rb'),
            'image': open(image_name, 'rb')
        }
        data = {
            'name': name
        }
        resp = requests.post(dest, params=data, files=files)
        logging.info('Uploaded, status: {}'.format(resp.ok))

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
