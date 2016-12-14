from datetime import datetime, timedelta

import cv2 as cv
import logging
import requests

from buffer import RingBuffer
from PIL import Image
from urllib.parse import urljoin
from socket import gethostname
from threading import Thread


class EventLoop:
    def __init__(self, url, name=None, noup=False, size=5, fps=10.0):
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
        self.noup = noup
        if name is None:
            self.name = gethostname()
        else:
            self.name = name

    def update(self, frame):
        # Append to pre event or post event if recording
        if not self.recording:
            self.pre_buffer.append(frame)
        else:
            self.post_buffer.append(frame)

    def update_event(self):
        self.last_event = datetime.now()
        self.cutoff = self.last_event + timedelta(0, 5)

    def start_event(self, event_name=None):
        # Label the video and start recording
        self.recording = True
        self.event_name = event_name
        if event_name is None:
            self.event_name = self.name
        self.event_time = datetime.now()
        self.update_event()

    def check_cutoff(self):
        if self.recording:
            if datetime.now() > self.cutoff:
                self.finish()

    def save(self):
        # Save video with event name & start time
        name = '{event_name} {event_time}'.format(
            event_name=self.event_name,
            event_time=self.event_time.strftime('%Y-%m-%d %H-%M-%S')
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
        if not self.noup:
            Upload(video_name, image_name, name, self.url).start()

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


class Upload(Thread):
    def __init__(self, video, image, name, url):
        super().__init__()
        self.video = video
        self.image = image
        self.name = name
        self.url = url

    def run(self):
        dest = urljoin(self.url, '/event/new')
        files = {
            'video': open(self.video, 'rb'),
            'image': open(self.image, 'rb')
        }
        data = {
            'name': self.name
        }
        resp = requests.post(dest, params=data, files=files)
        logging.info('Uploaded, status: {}'.format(resp.ok))
        return
