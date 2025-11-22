import cv2

video = cv2.VideoCapture("video2.mp4")
frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
video.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
ret, frame = video.read()

if ret:
    cv2.imwrite("last_frame.png", frame)

video.release()