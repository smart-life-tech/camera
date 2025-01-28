import time
from picamera2 import Picamera2
import socket
import os
import RPi.GPIO as GPIO
INPUT_PIN = 17  # Same pin as used for the trigger
GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_PIN, GPIO.IN)
# Setup the camera
camera = Picamera2()
# Configure the camera with default settings 
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))
# Start the camera 
camera.start()
# Define the server (Pi3rd) IP and port for communication
file_path = 'C:\\Users\\USER\\Documents\\raspberrypi\\camera\\example.txt'
def read_stored_ip(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    return None

PI3_IP = read_stored_ip()  # Pi3's fixed IP address
PORT = 5000

def capture_image(filename):
    # Capture and save the image 
    camera.capture_file(filename)

def send_image_to_pi3(image_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((PI3_IP, PORT))
        with open(image_path, 'rb') as f:
            s.sendfile(f)  # Send image file to Pi3
        print(f"Image {image_path} sent to Pi3.")

def wait_for_trigger():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((PI3_IP, PORT))
        while True:
            data = s.recv(1024)
            if data.decode('utf-8') == 'capture' or GPIO.input(INPUT_PIN) == GPIO.HIGH:
                filename = f"/home/user/camera/captured_image_{int(time.time())}.jpg"
                capture_image(filename)
                send_image_to_pi3(filename)
                break

if __name__ == '__main__':
    wait_for_trigger()
