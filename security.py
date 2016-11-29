import imutils as im
import cv2 as cv
from datetime import timedelta, datetime
from time import sleep
from buffer import RingBuffer

# Camera and average frame information
cam = cv.VideoCapture(1)
sleep(0.25)  # Ramp up time
avg = None

# Event info and recording indicator
last_event = None
recording = False
video_count = 0

# Pre and event buffer
pre_buffer = RingBuffer(30 * 5)  # 5 seconds of pre buffer
post_buffer = []

while True:
    ok, frame = cam.read()

    # Camera could not be opened
    if not ok:
        break

    # Check if we are finished recording the event
    if recording:

        # Cutoff point should be last event + n seconds
        cutoff = last_event + timedelta(0, 5)
        if datetime.now() > cutoff:
            name = './video' + str(video_count) + '.avi'
            h, w, layers = post_buffer[0].shape
            tape = pre_buffer.get() + post_buffer
            fourcc = cv.VideoWriter_fourcc(*'MJPG')
            video = cv.VideoWriter(name, fourcc, 30.0, (w, h))
            for f in tape:
                video.write(f)
            video.release()

            # seed pre buffer with last event's information
            tail_frames = post_buffer[-pre_buffer.size:]
            for f in range(pre_buffer.size):
                pre_buffer.append(tail_frames[f])

            # Reset for next event
            post_buffer = []
            recording = False
            video_count += 1
            print('Saved video', name, 'had', str(len(tape)), 'frames')

    # Start processing frame
    frame = im.resize(frame, width=500)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (21, 21), 0)

    # Initialize gray frame if not set
    if avg is None:
        avg = gray.copy().astype('float')
        continue

    # Accumulate frame into the average to help separate background
    cv.accumulateWeighted(gray, avg, 0.5)
    delta = cv.absdiff(gray, cv.convertScaleAbs(avg))
    threshold = cv.threshold(delta, 25, 255, cv.THRESH_BINARY)[1]
    threshold = cv.dilate(threshold, None, iterations=2)
    _, contours, _ = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL,
                                     cv.CHAIN_APPROX_SIMPLE)

    # Check each contour to see if they qualify as movement
    for c in contours:
        if cv.contourArea(c) < 500:
            continue

        # Set last movement event to now
        last_event = datetime.now()
        recording = True
        x, y, w, h = cv.boundingRect(c)
        cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        print('Last event is:', last_event)

    # Send frame to appropriate buffer
    if recording:
        post_buffer.append(frame)
    else:
        pre_buffer.append(frame)

    cv.imshow('Camera', frame)
    cv.imshow('Threshold', threshold)
    cv.waitKey(1)
