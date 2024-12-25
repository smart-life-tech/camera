import cv2
import subprocess

# Start the libcamera-vid process
process = subprocess.Popen(['libcamera-vid', '--codec', 'mjpeg', '-o', '-', '--inline'], stdout=subprocess.PIPE)

# Create a VideoCapture object with the process stdout
cap = cv2.VideoCapture(process.stdout, cv2.CAP_GSTREAMER)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Write the frame to the output file
    out.write(frame)

    # Display the resulting frame
    cv2.imshow('Frame', frame)

    # Press 'q' to exit the video recording
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release everything when the job is finished
cap.release()
out.release()
cv2.destroyAllWindows()

# Stop the libcamera-vid process
process.terminate()
