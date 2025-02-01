import time
from picamera2 import Picamera2
import socket
import os
import RPi.GPIO as GPIO
import requests
current_ip = None
# Define the server (Pi3rd) IP and port for communication
file_path = 'C:\\Users\\USER\\Documents\\raspberrypi\\camera\\example.txt'
file_path = '/home/user/camera/example.txt'
# Post the new IP address

def write_ip_to_file(file_path, ip):
    with open(file_path, 'w') as file:
        file.write(ip)
def checks():
    global current_ip
    while True:
        try:
            url = 'https://christlight.pythonanywhere.com/read'
            response = requests.get(url)
            print("read content", response.json().get('content'))
            current_ip = response.json().get('content')
            write_ip_to_file(file_path,current_ip)
            if response.status_code == 200:
                print("IP address read successfully.")
                break
        except Exception as e:
            print(f"Error: {e}")
            
INPUT_PIN = 17  # Same pin as used for the trigger
GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_PIN, GPIO.IN)
# Setup the camera
camera = Picamera2()
# Configure the camera with default settings 
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))
# Start the camera 
camera.start()

checks()
def read_stored_ip(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    return None

# Read the stored IP address
stored_ip = read_stored_ip(file_path)

# Check if the IP address has changed
if stored_ip != current_ip:
    
    # Update the stored IP address
    write_ip_to_file(file_path, current_ip)
else:
    print("IP address has not changed.")
    
    
PI3_IP = read_stored_ip(file_path)  # Pi3's fixed IP address
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
