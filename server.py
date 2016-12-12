import cv2 as cv
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from PIL import Image
from io import BytesIO
import time


class SampleHandler(BaseHTTPRequestHandler):
    cam = None
    fps = 5.0

    def do_GET(self):
        if self.path.endswith('video.mjpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()

            while True:
                # Convert frame from 3D array to jpeg
                rgb = cv.cvtColor(self.cam.read(), cv.COLOR_BGR2RGB)
                jpeg = Image.fromarray(rgb)
                buf = BytesIO()
                jpeg.save(buf, 'JPEG')

                # Write mjpg headers
                self.wfile.write('--jpgboundary'.encode('utf-8'))
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(buf))
                self.end_headers()
                jpeg.save(self.wfile, 'JPEG')

                # Wait to match up with Sentry framerate target
                time.sleep(1 / self.fps)

            return


class Server(Thread):
    def __init__(self, cam, fps=5.0, addr='127.0.0.1', port=8080):
        super().__init__()
        Handler = SampleHandler
        Handler.cam = cam
        Handler.fps = fps
        Server = HTTPServer
        self.httpd = Server((addr, port), Handler)

    def run(self):
        self.httpd.serve_forever()

    def shutdown(self):
        self.httpd.shutdown()
        self.httpd.socket.close()
