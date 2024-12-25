import cv2
import subprocess
import os

# Define the output video file name
video_file = 'output.h264'

# Start the libcamera-vid process
process = subprocess.Popen(['libcamera-vid', '--codec', 'h264', '-o', video_file, '--inline'], stdout=subprocess.PIPE)

# Wait a few seconds to ensure the video file is created
import time
time.sleep(5)  # Adjust the sleep time as needed

# Release the libcamera-vid process
process.terminate()

# Verify if the video file exists
if not os.path.exists(video_file):
    print(f"Error: {video_file} not found.")
    exit()

# Open the video file using OpenCV
cap = cv2.VideoCapture(video_file)

if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Display the resulting frame
    cv2.imshow('Frame', frame)

    # Press 'q' to exit the video display
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release everything when the job is finished
cap.release()
cv2.destroyAllWindows()
