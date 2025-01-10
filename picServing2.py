import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import socket
import subprocess

from picamera2 import Picamera2

# Initialize the camera
camera = Picamera2()

# Configure the camera with default settings
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))

# Start the camera
camera.start()

# Allow some time for the camera to initialize
time.sleep(2)
count = 0

IMAGE_DIR = '/home/user/camera'  # Ensure this is the correct directory
PORT = 8080
WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'
os.system('sudo ip addr add 192.168.233.194/24 dev wlan0')
time.sleep(5)
def get_ip_address():
    hostname = socket.gethostname()  # Get the hostname of the Pi
    ip_address = socket.gethostbyname(hostname)  # Get the corresponding IP address
    return ip_address

def print_ip_address():
    ip_address = get_ip_address()
    print(f"Raspberry Pi IP Address: {ip_address}")

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.list_images()
        elif self.path.startswith('/delete/'):
            image_name = self.path.split('/')[-1]
            self.delete_image(image_name)
            self.list_images()
        elif self.path.startswith('/download/'):
            image_name = self.path.split('/')[-1]
            self.download_image(image_name)
        elif self.path == '/reboot':
            self.reboot_system()
        elif self.path == '/shutdown':
            self.shutdown_system()
        elif self.path == '/capture':
            self.capture_images()
        else:
            return super().do_GET()

    def list_images(self):
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
        self.wfile.write(b'<a href="/reboot">Reboot</a> | <a href="/shutdown">Shutdown</a> | <a href="/capture">capture image</a>')
        self.wfile.write(b"</body></html>")
        
        self.wfile.write(b"<html><head><title>Images</title>")
        self.wfile.write(b"<style>img { width: 150px; margin: 10px; } </style></head><body>")
        self.wfile.write(b"<h2>Captured Images</h2>")
        
        for image in images:
            image_url = f"/{image}"
            download_url = f"/download/{image}"
            self.wfile.write(f'<div style="display:inline-block; text-align:center; margin:10px;">'.encode())
            self.wfile.write(f'<a href="{image_url}"><img src="{image_url}" alt="{image}"></a><br>'.encode())
            self.wfile.write(f'<a href="/delete/{image}">Delete</a>'.encode())
            self.wfile.write(f'<a href="{download_url}">Download</a>'.encode())
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
        file_path = os.path.join(IMAGE_DIR, image_name)
        if os.path.isfile(file_path):
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename={image_name}')
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
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
        
    
    def capture_images(self): 
        global count 
        #while True: 
        # Capture and save the image
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"image captured...")
        print("capturing...") 
        camera.capture_file(f'high_res_image{count}.jpg') 
        count += 9 
        print("Image captured!") 
        time.sleep(1) 
        # Wait for 1 second before capturing the next image

def start_http_server():
    os.chdir(IMAGE_DIR)
    with TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Serving images on port {PORT}...")
        httpd.serve_forever()

def send_images_to_phone(images):
    print("Images available for download:")
    for image in images:
        print(f"Image: {image}")

def delete_image(image_path):
    try:
        os.remove(image_path)
        print(f"Deleted image: {image_path}")
    except Exception as e:
        print(f"Error deleting image: {e}")

def capture_images(): 
    global count 
    #while True: 
    # Capture and save the image 
    camera.capture_file(f'high_res_image{count}.jpg') 
    count += 1 
    print("Image captured!") 
    time.sleep(1) 
    # Wait for 1 second before capturing the next image
if __name__ == '__main__':
    try:
        print_ip_address()
        server_thread = threading.Thread(target=start_http_server)
        server_thread.daemon = True
        server_thread.start()
        server_thread.join()
        time.sleep(100)
    except KeyboardInterrupt:
        print("Server interrupted. Shutting down.")
