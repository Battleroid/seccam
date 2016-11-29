import cv2 as cv
import imutils as im
from event import EventRecorder

# Camera
cam = cv.VideoCapture(0)
avg = None

# Frame counts
cons_frames = 0

# Event recording
er = EventRecorder()
video_cnt = 0

while True:
    good, frame = cam.read()

    if not good:
        break

    update_frames = True
    frame = im.resize(frame, width=500)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (21, 21), 0)

    if avg is None:
        avg = gray.copy().astype('float')
        continue

    cv.accumulateWeighted(gray, avg, 0.5)
    delta = cv.absdiff(gray, cv.convertScaleAbs(avg))
    threshold = cv.threshold(delta, 25, 255, cv.THRESH_BINARY)[1]
    threshold = cv.dilate(threshold, None, iterations=2)
    _, contours, _ = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL,
                                     cv.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        c = max(contours, key=cv.contourArea)
        area = cv.contourArea(c)
        update_frames = area <= 2000
        if area > 2000:
            cons_frames = 0

            if not er.recording:
                er.start('video' + str(video_cnt) + '.avi')

    if update_frames:
        cons_frames += 1

    er.update(frame)

    if er.recording and cons_frames == er.frames.maxlen:
        er.finish()
        video_cnt += 1
        print 'Saved video', video_cnt

    cv.imshow('Camera', frame)
    cv.waitKey(1)
