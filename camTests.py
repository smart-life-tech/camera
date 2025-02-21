from picamera2 import Picamera2
import time

# Initialize the camera
camera = Picamera2()
config = camera.create_still_configuration(main={"size": camera.sensor_resolution}, controls={
    "ExposureTime": 10000,  # Adjust this value as needed
    "AnalogueGain": 1.0,    # Adjust this value as needed
    "AwbEnable": True       # Enable auto white balance
})
camera.configure(config)
# Configure the camera with default settings
#camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))

# Start the camera
camera.start()

# Allow some time for the camera to initialize
time.sleep(2)
count = 0
while True:
    # Capture and save the image
    camera.capture_file(f'high_res_image{count}.jpg')
    count += 1
    print("Image captured!")
    time.sleep(1)  # Wait for 1 second before capturing the next image
    # Capture and save the image
    

# Stop the camera
camera.stop()
