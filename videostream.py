import cv2

# Define the video capture object (0 usually refers to the default camera)
cap = cv2.VideoCapture(0)

# Define the codec and create a VideoWriter object to save the video
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open video device.")
    exit()

# Capture video stream
while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # Write the frame to the output file
        out.write(frame)

        # Display the resulting frame
        cv2.imshow('Frame', frame)

        # Press 'q' to exit the video recording
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# Release everything when the job is finished
cap.release()
out.release()
cv2.destroyAllWindows()
