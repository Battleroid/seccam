import cv2
import imutils as im

cam = cv2.VideoCapture(0)
avg = None
motion = False
finished_moving = False
frames = []
vid_cnt = 0

while True:
    motion = False
    good, frame = cam.read()

    if not good:
        break

    # create video if there is no more motion
    if finished_moving and len(frames) > 0:
        vid_cnt += 1
        name = './video' + str(vid_cnt) + '.avi'
        h, w, layers = frames[0].shape
        codec = cv2.VideoWriter_fourcc(*'MJPG')
        video = cv2.VideoWriter(name, codec, 5.0, (w, h))
        for f in frames:
            video.write(f)
        video.release()
        frames = []

    # use smaller, blurred version of frame for difference masks
    frame = im.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # set this as our background if it is the first frame
    if avg is None:
        avg = gray.copy().astype('float')
        continue

    # accumulate frame into average to help separate background
    cv2.accumulateWeighted(gray, avg, 0.5)
    delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    threshold = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
    threshold = cv2.dilate(threshold, None, iterations=2)
    _, contours, _ = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # for each contour check area for movement
    for c in contours:
        if cv2.contourArea(c) < 5000:
            continue

        # draw bounding box over contour area of movement
        motion = True
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if motion:
        finished_moving = False
        frames.append(frame)
    else:
        finished_moving = True

    # debug windows
    cv2.imshow('Camera', frame)
    cv2.imshow('Threshold', threshold)
    cv2.imshow('Delta', delta)
    cv2.waitKey(1)
