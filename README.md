# seccam

Seccam works in conjunction with [seccam-web][0]. The entrypoint `sentry.py` will do basic motion detection using OpenCV 3.1.0 and upload the motion captured event(s) to the seccam-web instance.

### Details

Seccam works like this:

1. Start `sentry.py http://urltoseccamweb.com` with any other options you require.
2. The circular buffer continually records all frames up until a motion event is triggered.
3. The event buffer is then used to record video up until motion has ceased for 5 seconds with the given framerate.
4. At this point the ring buffer's contents are prepended to the event buffer to provide a seamless *before-event-after* sequence of events.
5. The video and image of the largest frame of movement are saved and then uploaded to the seccam-web instance.
6. The tail end of the event buffer's contents are seeded into the ring buffer so the next event will appear to have been recording continuously.

### Requirements & Installation

Built with Python 3.5.2, you could likely get away with something lower but I'd try for 3.5.

1. OpenCV 3.1.0 with Python support (and Video4Linux support if using under Linux).
    a. If under Linux you will need to add your user to the video group to access cameras (`usermod -a -G video username`).
3. `pip install -r requirements.txt`

### Arguments

Argument | Help
--- | ---
URL | URL of seccam-web instance, such as `http://127.0.0.1:8000`.

### Parameters

Parameter | Default | Help
--- | --- | ---
-h --help | *n/a* | Show help screen.
-s --src | 0 | Camera source.
-f --fps | 5* | Camera and stream framerate.
--stream | False | Stream the camera output continuously.
--addr | `127.0.0.1:8080` | Stream location, access via `/video.mjpg`.
-d --debug | *n/a* | Displays UI window of camera feed.
--name | System hostname | Label for the camera events when saving/uploading.
--noup | *n/a* | Whether or not to upload the event.

*: High framerates require more resources and will consume much more data to store video both in memory and on disk.

[0]: https://github.com/Battleroid/seccam-web