'''Sentry camera.

URL points to the accompanying seccam-web instance which will process
events, store videos and images in duplicate, and notify the owner of
newly captured events.

Usage:
    sentry.py [options] <URL>

Options:
    -h --help         Show this screen.
    -s --src=<src>    Camera source [default: 0].
    -f --fps=<fps>    Camera/stream framerate [default: 5].
    --stream          Stream the video feed.
    --addr=<address>  Address/port to attach to for streaming [default: 127.0.0.1:8080].
    -d --debug        Show current video feed in window.
    --name=<name>     Label for camera when uploading video.
    --noup            Do not upload to remote.
'''
__version__ = '0.1'

import time
import docopt
import logging

import cv2 as cv
import imutils as im

from camera import Camera
from event import EventLoop
from server import Server

logging.basicConfig(level=logging.INFO)


class Sentry:
    def __init__(self, url, fps=5.0, src=0, min_area=250, noup=True, verbose=False):
        self.camera = Camera(src)
        self.loop = EventLoop(url, noup=noup, size=fps * 5, fps=fps)
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
                        logging.info('Area exceeded ({} > {}), starting capture'.format(
                            max_area, self.min_area
                        ))
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
    # Collect args
    args = docopt.docopt(__doc__, version='Sentry {}'.format(__version__))

    # Sentry related
    src = int(args['--src'])
    fps = int(args['--fps'])
    debug = args['--debug']
    url = args['<URL>']
    name = args['--name']
    noup = args['--noup']

    # Server related
    streaming = args['--stream']
    addr, port = args['--addr'].split(':')
    port = int(port)

    # If streaming the stream first
    sentry = Sentry(url, noup=noup, src=src, fps=fps, verbose=debug)

    # Start streaming MJPG portion if required
    if streaming:
        server = Server(sentry.camera, fps=sentry.fps, addr=addr, port=port)
        logging.info('Streaming MJPG server at {}:{}'.format(
            addr, str(port)
        ))
        server.start()

    # Finally start the sentry
    logging.info('Starting Sentry')
    sentry.start()