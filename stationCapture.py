import time
import socket
import os
import RPi.GPIO as GPIO
from picamera2 import Picamera2
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import TCPServer
import shutil

# Configuration
IMAGE_DIR = '/home/pi/images'
PORT = 8080  # HTTP server port for file transfers and commands
CAMERA_PORT = 5000  # Port for Pi-to-Pi communication

# Setup Pi3 camera
# Initialize the camera
camera = Picamera2()
# Configure the camera with default settings
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))

# Start the camera
camera.start()


# Define static IP addresses of Pi1 and Pi2
PI1_IP = '192.168.0.1'
PI2_IP = '192.168.0.2'

# GPIO settings for the button
BUTTON_PIN = 17  # GPIO pin 17 for the button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Ensure the directory to store captured images exists
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Capture image on Pi3
def capture_image(filename):
    camera.capture_file(filename)

# Send capture trigger to Pi1 and Pi2
def send_trigger_to_pis():
    for ip in [PI1_IP, PI2_IP]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, CAMERA_PORT))
            s.sendall(b'capture')  # Send capture command to Pi1 and Pi2

# Receive images from Pi1 and Pi2
def receive_image_from_pis(client_socket, filename):
    with open(filename, 'wb') as f:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            f.write(data)
    print(f"Received image {filename} from Pi.")

# Start server to receive images from Pi1 and Pi2
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', CAMERA_PORT))
        s.listen(2)
        print("Waiting for connections from Pi1 and Pi2...")

        # Trigger Pi1 and Pi2 to capture images
        send_trigger_to_pis()

        # Capture image on Pi3
        pi3_image_path = f"{IMAGE_DIR}/pi3_image_{int(time.time())}.jpg"
        capture_image(pi3_image_path)
        print(f"Captured image on Pi3: {pi3_image_path}")

        # Receive images from Pi1 and Pi2
        pi_images = [pi3_image_path]
        for _ in range(2):
            conn, addr = s.accept()
            filename = f"{IMAGE_DIR}/image_{addr[0]}_{int(time.time())}.jpg"
            receive_image_from_pis(conn, filename)
            pi_images.append(filename)

        return pi_images

# Custom HTTP handler for commands and file serving
class MyHTTPRequestHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/capture':
            print("Received capture command from phone.")
            images = start_server()
            send_images_to_phone(images)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Images captured and sent to phone.")
        elif self.path.startswith('/delete'):
            print("Received delete command.")
            folder_to_delete = self.path.split('/')[-1]
            folder_path = os.path.join(IMAGE_DIR, folder_to_delete)
            if os.path.exists(folder_path):
                os.system(f'rm -rf {folder_path}')
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"Deleted folder: {folder_to_delete}".encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Folder not found")
        else:
            # Serve images for download
            super().do_GET()

# Function to start the HTTP server
def start_http_server():
    os.chdir(IMAGE_DIR)  # Change directory to the image folder
    handler = MyHTTPRequestHandler
    with HTTPServer(("", PORT), handler) as httpd:
        print(f"Serving files and commands on port {PORT}...")
        httpd.serve_forever()

# Function to send images to the phone
def send_images_to_phone(images):
    # Transfer images to the phone via HTTP (Wi-Fi)
    print("Transferring images to phone...")
    for image in images:
        print(f"Transferring {image} to phone...")
        shutil.copy(image, "/var/www/html/")  # Copy image to web server directory
        time.sleep(1)  # Simulate transfer delay

# Function to wait for button press to trigger capture
def wait_for_button_press():
    print("Waiting for button press to trigger capture...")
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Detect button press
            print("Button pressed! Capturing images...")
            images = start_server()
            send_images_to_phone(images)
            time.sleep(0.5)  # Debounce to avoid multiple triggers

# Main function
if __name__ == '__main__':
    try:
        # Start the HTTP server in a separate thread
        server_thread = threading.Thread(target=start_http_server)
        server_thread.daemon = True  # Daemonize the thread so it stops on exit
        server_thread.start()

        wait_for_button_press()  # Wait for button press to trigger capture

    except KeyboardInterrupt:
        GPIO.cleanup()  # Clean up GPIO settings on exit
