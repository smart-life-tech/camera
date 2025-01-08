import time
import socket
import os
import RPi.GPIO as GPIO
from picamera2 import Picamera2
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import TCPServer
import shutil
import subprocess
# Configuration
IMAGE_DIR = '/home/user/camera'
PORT = 8080  # HTTP server port for file transfers and commands
CAMERA_PORT = 8080  # Port for Pi-to-Pi communication
WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'
# Setup Pi3 camera
# Initialize the camera
camera = Picamera2()
# Configure the camera with default settings
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))

# Start the camera
camera.start()


# Define static IP addresses of Pi1 and Pi2
PI1_IP = '192.168.233.194'
PI2_IP = '192.168.233.194'

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
            data = client_socket.recv(2048)
            if not data:
                break
            f.write(data)
    print(f"Received image {filename} from Pi.")

# Start server to receive images from Pi1 and Pi2
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('192.168.233.194', CAMERA_PORT))
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
        if self.path == '/':
            # Serve index page with images list
            self.list_images()
        elif self.path.startswith('/delete/'):
            # Handle image deletion
            image_name = self.path.split('/')[-1]
            self.delete_image(image_name)
            # After deletion, serve the updated list
            self.list_images()
        elif self.path.startswith('/download/'):
            # Handle image download
            image_name = self.path.split('/')[-1]
            self.download_image(image_name)
        elif self.path == '/reboot':
            self.reboot_system()
        elif self.path == '/shutdown':
            self.shutdown_system()
        else:
            # Serve the requested image file
            return super().do_GET()

    def list_images(self):
        # List available images and add delete button for each image
        images = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.jpg')]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(b"<h3>Update Wi-Fi Credentials</h3>")
        self.wfile.write(b"""
        <form action="/update_wifi" method="POST">
            <label for="ssid">SSID:</label><br>
            <input type="text" id="ssid" name="ssid" required><br>
            <label for="password">Password:</label><br>
            <input type="password" id="password" name="password" required><br><br>
            <input type="submit" value="Update Wi-Fi">
        </form>
        """)

        self.wfile.write(b"<br><h3>System Controls</h3>")
        self.wfile.write(b'<a href="/reboot">Reboot</a> | <a href="/shutdown">Shutdown</a>')
        self.wfile.write(b"</body></html>")
        
        self.wfile.write(b"<html><head><title>Images</title>")
        self.wfile.write(b"<style>img { width: 150px; margin: 10px; } </style></head><body>")
        self.wfile.write(b"<h2>Captured Images</h2>")
        
        # Display images as thumbnails and links to delete them
        for image in images:
            image_url = f"/{image}"
            download_url = f"/download/{image}"  # Download URL
            self.wfile.write(f'<div style="display:inline-block; text-align:center; margin:10px;">'.encode())
            self.wfile.write(f'<a href="{image_url}"><img src="{image_url}" alt="{image}"></a><br>'.encode())
            self.wfile.write(f'<a href="/delete/{image}">Delete</a>'.encode())
            self.wfile.write(f'<a href="{download_url}">Download</a>'.encode())  # Add download link
            self.wfile.write(b"</div>")

        self.wfile.write(b"</body></html>")

    def delete_image(self, image_name):
        image_path = os.path.join(IMAGE_DIR, image_name)
        try:
            os.remove(image_path)
            print(f"Deleted image: {image_name}")
        except Exception as e:
            print(f"Error deleting image: {e}")
    def download_image(self, image_name):
        """Serve the image as a download."""
        file_path = os.path.join(IMAGE_DIR, image_name)  # Get full path of the image
        if os.path.isfile(file_path):
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')  # Set content type for download
            self.send_header('Content-Disposition', f'attachment; filename={image_name}')  # Force download
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            # If the file doesn't exist, send 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Image not found.")
    
    def update_wifi_credentials(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = dict(p.split('=') for p in post_data.split('&'))

        ssid = params.get('ssid')
        password = params.get('password')

        if not ssid or not password:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"SSID and Password are required.")
            return

        # Update wpa_supplicant.conf
        try:
            with open(WPA_SUPPLICANT_FILE, 'w') as f:
                f.write(f"""country=US
                ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
                update_config=1

                network={{
                    ssid="{ssid}"
                    psk="{password}"
                }}
                """)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Wi-Fi credentials updated. Please reboot the device.")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Failed to update Wi-Fi credentials.")
            print(f"Error: {e}")

    def reboot_system(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Rebooting system...")
        print("Rebooting system...")
        subprocess.run(['sudo', 'reboot'])

    def shutdown_system(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shutting down system...")
        print("Shutting down system...")
        subprocess.run(['sudo', 'shutdown', 'now'])
# Function to start the HTTP server
def start_http_server():
    os.chdir(IMAGE_DIR)  # Change directory to the image folder
    handler = MyHTTPRequestHandler
    with HTTPServer(("192.168.233.194", PORT), handler) as httpd:
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
