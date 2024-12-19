import time
from picamera import PiCamera
import socket

# Setup the camera
camera = PiCamera()
camera.resolution = (2048, 2048)
camera.framerate = 15

# Define the server (Pi3rd) IP and port for communication
PI3_IP = '192.168.0.3'  # Pi3's fixed IP address
PORT = 5000

def capture_image(filename):
    camera.start_preview()
    time.sleep(2)  # Allow the camera to adjust exposure
    camera.capture(filename)
    camera.stop_preview()

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
            if data.decode('utf-8') == 'capture':
                filename = f"/home/pi/captured_image_{int(time.time())}.jpg"
                capture_image(filename)
                send_image_to_pi3(filename)
                break

if __name__ == '__main__':
    wait_for_trigger()
