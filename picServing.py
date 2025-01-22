import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import socket
import subprocess
from PIL import Image
import io
from picamera2 import Picamera2

# Setup the camera
camera = Picamera2()
# Configure the camera with default settings 
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))
# Start the camera 
camera.start()
IMAGE_DIR = '/home/user/camera'  # Ensure this is the correct directory
#IMAGE_DIR=input("Enter the directory path to the photos to be served: ")
PORT = 8080
WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'
os.system('sudo ip addr add 192.168.233.194/24 dev wlan0')
def get_ip_address():
    # Get the IP address of the Raspberry Pi
    hostname = socket.gethostname()  # Get the hostname of the Pi
    ip_address = socket.gethostbyname(hostname)  # Get the corresponding IP address
    return ip_address

def print_ip_address():
    ip_address = get_ip_address()
    print(f"Raspberry Pi IP Address: {ip_address}")

# Directory to store captured images
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

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
        elif self.path == '/capture':
            self.capture_image()
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
        self.wfile.write(b"<br><h3>Capture Image</h3>")
        self.wfile.write(b'<a href="/capture">Capture Image</a>')
        self.wfile.write(b"<br><h3>Images</h3>")
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
    
    def capture_image(self):
        # Capture an image using the PiCamera
         # Capture and save the image 
        filename = f"/home/user/camera/captured_image_{int(time.time())}.jpg"
        camera.capture_file(filename)
        self.wfile.write(b"caprure")
        print("Image captured and saved.")

# def start_http_server():
#     os.chdir(IMAGE_DIR)
#     with TCPServer(("192.168.232.194", PORT), MyHTTPRequestHandler) as httpd:
#         print(f"Serving images on port {PORT}...")
#         httpd.serve_forever()
# Start the server with custom handler
def start_http_server():
    print("Starting HTTP server...")
    os.chdir(IMAGE_DIR)  # Change directory to the image folder
    with TCPServer(("localhost", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Serving images on portss {PORT}...")
        httpd.serve_forever()


def send_images_to_phone(images):
    print("Images available for download:")
    for image in images:
        print(f"Image: {image}")
        # List images for user to select, preview, and delete if needed.
        # This will be handled through the HTTP interface.

def delete_image(image_path):
    try:
        os.remove(image_path)
        print(f"Deleted image: {image_path}")
    except Exception as e:
        print(f"Error deleting image: {e}")

def serving():
    print("waiting for  images to be received...")
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 65432)
    server_socket.bind(server_address)

    # Listen for incoming connections
    server_socket.listen(2)

    print('Server is listening...')

    while True:
        connection, client_address = server_socket.accept()
        try:
            print('Connection from', client_address)
            
            # Receive the image data in chunks
            image_data = b''
            while True:
                data = connection.recv(2048)
                if not data:
                    break
                image_data += data
            # Save the image to the current directory
            image.save('received_image.png')
            # Convert the byte data to an image
            image = Image.open(io.BytesIO(image_data))
            image.show()
            
            print('Image received and displayed.')
            
        finally:
            connection.close()

if __name__ == '__main__':
    try:
        print_ip_address()
        serving()
        # Start the HTTP server in a separate thread
        server_thread = threading.Thread(target=start_http_server)
        server_thread.daemon = True  # Daemonize the thread so it stops on exit
        server_thread.start()
        server_thread.join()  # Make sure the server keeps running
        time.sleep(10)  # Wait for the server to start
        
    except KeyboardInterrupt:
        print("Server interrupted. Shutting down.")
