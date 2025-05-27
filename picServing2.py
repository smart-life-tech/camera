import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn, TCPServer
from socketserver import TCPServer
import socket
import subprocess
import requests
from PIL import Image

from picamera2 import Picamera2
import RPi.GPIO as GPIO
# Setup the camera
TRIGGER_PIN = 27  
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
# Get the local IP address of the Raspberry Pi
hostname = socket.gethostname()
current_ip = socket.gethostbyname(hostname)
def get_ip_address(interface):
    try:
        result = subprocess.check_output(f'ip addr show {interface}', shell=True).decode('utf-8')
        for line in result.split('\n'):
            if 'inet ' in line:
                return line.split()[1].split('/')[0]
    except subprocess.CalledProcessError as e:
        print(f"Error getting IP address for interface {interface}: {e}")
        return None

wlan0_ip = get_ip_address('wlan0')
print(current_ip,wlan0_ip)
current_ip = wlan0_ip
file_path = '/home/user/camera/example.txt'
def read_stored_ip(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    return None

# Function to write the new IP address to the file
def write_ip_to_file(file_path, ip):
    with open(file_path, 'w') as file:
        file.write(ip)
    while True:
        try:
            url = 'https://christlight.pythonanywhere.com/write'
            data = {'content': ip}
            response = requests.post(url, json=data)
            print(response.json())
            if response.status_code == 200:
                print("IP address sent successfully.")
                break
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
        time.sleep(10)

# Read the stored IP address
stored_ip = read_stored_ip(file_path)

# Check if the IP address has changed
if stored_ip != current_ip:
    # Post the new IP address
    # url = 'https://christlight.pythonanywhere.com/read'
    # data = {'ip': current_ip}
    #/home/user/camera/set_number.txt
    # response = requests.post(url, json=data)
    # print(response.json())

    # Update the stored IP address
    write_ip_to_file(file_path, current_ip)
else:
    print("IP address has not changed.")
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
PORT = 5000
WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'
# os.system('sudo ip addr add 192.168.233.194/24 dev wlan0')
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
        elif self.path == '/refresh':
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
            GPIO.output(TRIGGER_PIN, GPIO.HIGH)
            time.sleep(0.5)  # Keep the pin HIGH for 1 second
            GPIO.output(TRIGGER_PIN, GPIO.LOW)
            self.capture_images()
        else:
            return super().do_GET()
            #self.list_images()

    def do_POST(self):
        if self.path == '/update_wifi':
            self.update_wifi_credentials()
        else:
            self.send_response(501)
            self.end_headers()
            self.wfile.write(b"Unsupported method ('POST')")

    def list_images(self):
        images = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.jpg')]
        # Sort images alphabetically
        images.sort()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Start HTML with better styling
        self.wfile.write(b"""
        <html>
        <head>
            <title>Camera Images</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .image-container { 
                    display: flex; 
                    flex-wrap: wrap; 
                    gap: 15px; 
                    margin: 20px 0; 
                }
                .image-item { 
                    border: 1px solid #ddd; 
                    border-radius: 8px; 
                    padding: 10px; 
                    text-align: center; 
                    background-color: #f9f9f9;
                    width: 200px;
                }
                .image-item img { 
                    width: 180px; 
                    height: 135px; 
                    object-fit: cover; 
                    border-radius: 4px;
                }
                .image-name { 
                    font-weight: bold; 
                    margin: 8px 0; 
                    font-size: 14px;
                }
                .image-actions { 
                    display: flex; 
                    justify-content: space-around; 
                    margin-top: 8px;
                }
                .image-actions a { 
                    text-decoration: none; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 12px;
                }
                .delete-btn { background-color: #ff4444; color: white; }
                .download-btn { background-color: #4CAF50; color: white; }
                .view-btn { background-color: #2196F3; color: white; }
                .controls { 
                    background-color: #f0f0f0; 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin-bottom: 20px;
                }
                .wifi-form { 
                    background-color: #e8f4f8; 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin-bottom: 20px;
                }
                .wifi-form input[type="text"], .wifi-form input[type="password"] {
                    width: 200px; 
                    padding: 5px; 
                    margin: 5px;
                }
                .system-controls a {
                    margin-right: 15px;
                    padding: 8px 12px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
        """)

        # Wi-Fi Configuration Section
        self.wfile.write(b"""
        <div class="wifi-form">
            <h3>Update Wi-Fi Credentials</h3>
            <form action="/update_wifi" method="POST">
                <label for="ssid">SSID:</label><br>
                <input type="text" id="ssid" name="ssid" required><br>
                <label for="password">Password:</label><br>
                <input type="password" id="password" name="password" required><br><br>
                <input type="submit" value="Update Wi-Fi">
            </form>
        </div>
        """)

        # System Controls Section
        self.wfile.write(b"""
        <div class="controls">
            <h3>System Controls</h3>
            <div class="system-controls">
                <a href="/reboot">Reboot</a>
                <a href="/shutdown">Shutdown</a>
                <a href="/capture">Capture Image</a>
                <a href="/refresh">Refresh Page</a>
            </div>
        </div>
        """)
        
        # Images Section
        self.wfile.write(f"<h2>Captured Images ({len(images)} total)</h2>".encode())
        
        if not images:
            self.wfile.write(b"<p>No images found. Click 'Capture Image' to take a photo.</p>")
        else:
            self.wfile.write(b'<div class="image-container">')
            
            for image in images:
                image_url = f"/{image}"
                download_url = f"/download/{image}"
                delete_url = f"/delete/{image}"
                
                self.wfile.write(f"""
                <div class="image-item">
                    <a href="{image_url}" target="_blank" class="view-btn">
                        <img src="{image_url}" alt="{image}" title="Click to view full size">
                    </a>
                    <div class="image-name">{image}</div>
                    <div class="image-actions">
                        <a href="{delete_url}" class="delete-btn" onclick="return confirm('Delete {image}?')">Delete</a>
                        <a href="{download_url}" class="download-btn">Download</a>
                    </div>
                </div>
                """.encode())
            
            self.wfile.write(b'</div>')

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
    def get_number(self):
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        with open(set_number_file, 'r+') as f:
            set_number = int(f.read().strip())
        return set_number
     
    
    def capture_images(self): 
        global count 
        #while True: 
        # Capture and save the 
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        with open(set_number_file, 'r+') as f:
            set_number = int(f.read().strip())
            f.seek(0)
            f.truncate()
            f.write(str(set_number + 1))
            f.close()
            
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"image capture in progress... \n")
        print("capturing...") 
        filename = os.path.join(IMAGE_DIR, f'{self.get_number()}z.jpg')
        camera.capture_file(filename) 
        count =count + 1
        print("Image captured!",self.get_number()) 
        time.sleep(1) 
        self.wfile.write(b"image capture done \n")
        #self.wfile.write(b'<a href="/refresh">back home</a>')
        # Wait for 1 second before capturing the next image
class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass
def start_http_server():
    os.chdir(IMAGE_DIR)
    server_address = (current_ip, PORT)
    with ThreadedTCPServer(server_address, MyHTTPRequestHandler) as httpd:
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
