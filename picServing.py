import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn, TCPServer
import socket
import subprocess
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import io
import ssl
from http.server import HTTPServer
# Try to import PiCamera - this will work on Raspberry Pi
try:
    from picamera2 import Picamera2
    import RPi.GPIO as GPIO
    
    # Setup the camera
    TRIGGER_PIN = 27  
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIGGER_PIN, GPIO.OUT)
    
    # Initialize the camera
    camera = Picamera2()
    camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))
    camera.start()
    time.sleep(2)  # Allow time for camera to initialize
    
    IS_RASPBERRY_PI = True
except ImportError:
    print("PiCamera not found. Running in development mode without camera functionality.")
    IS_RASPBERRY_PI = False

# Get the local IP address
def get_ip_address(interface=None):
    if interface:
        try:
            result = subprocess.check_output(f'ip addr show {interface}', shell=True).decode('utf-8')
            for line in result.split('\n'):
                if 'inet ' in line:
                    return line.split()[1].split('/')[0]
        except subprocess.CalledProcessError as e:
            print(f"Error getting IP address for interface {interface}: {e}")
            return None
    
    # Fallback to socket method
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

# Get IP address
if IS_RASPBERRY_PI:
    current_ip = get_ip_address('wlan0') or get_ip_address()
else:
    current_ip = get_ip_address() or 'localhost'

print(f"Server IP address: {current_ip}")

# Configuration
if IS_RASPBERRY_PI:
    IMAGE_DIR = '/home/user/camera'  # Path on Raspberry Pi
else:
    IMAGE_DIR ='C:/Users/USER/OneDrive/Pictures/Screenshots'  #  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')  # Local development path

PORT = 5000
WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'

# SSL Certificate paths - you'll need to generate these
CERT_FILE = 'C:/Users/USER/Documents/raspberrypi/camera/server.crt'  # Path to your certificate file
KEY_FILE = 'C:/Users/USER/Documents/raspberrypi/camera/server.key'   # Path to your private key file

# Create image directory if it doesn't exist
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Create set_number.txt if it doesn't exist
set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
if not os.path.exists(set_number_file):
    with open(set_number_file, 'w') as f:
        f.write('1')

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

class MyHTTPRequestHandler(CORSHTTPRequestHandler):
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
            if IS_RASPBERRY_PI:
                GPIO.output(TRIGGER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(TRIGGER_PIN, GPIO.LOW)
            self.capture_images()
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == '/update_wifi':
            self.update_wifi_credentials()
        elif self.path == '/save_edited_image':
            self.save_edited_image()
        else:
            self.send_response(501)
            self.end_headers()
            self.wfile.write(b"Unsupported method ('POST')")

    def save_edited_image(self):
        content_type = self.headers['Content-Type']
        if not content_type.startswith('multipart/form-data'):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"success": false, "error": "Invalid content type"}')
            return
        
        # Get content length
        content_length = int(self.headers['Content-Length'])
        
        # Get boundary
        boundary = content_type.split('=')[1].encode()
        
        # Read the form data
        form_data = self.rfile.read(content_length)
        
        # Parse the form data to get the image
        try:
            # Find the image data in the form
            image_start = form_data.find(b'\r\n\r\n', form_data.find(b'filename')) + 4
            image_end = form_data.rfind(b'--' + boundary + b'--') - 2
            image_data = form_data[image_start:image_end]
            
            # Get the filename
            filename_start = form_data.find(b'filename="') + 10
            filename_end = form_data.find(b'"', filename_start)
            filename = form_data[filename_start:filename_end].decode()
            
            # Save the image
            image_path = os.path.join(IMAGE_DIR, filename)
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success": true}')
        except Exception as e:
            print(f"Error saving edited image: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"success": false, "error": "{str(e)}"}}').encode()

    def list_images(self):
        images = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.jpg') or f.endswith('.png')]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Simple HTML with images
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Camera Images</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .image-container { display: inline-block; margin: 10px; text-align: center; }
                img { max-width: 200px; max-height: 200px; }
            </style>
        </head>
        <body>
            <h1>Camera Images</h1>
        """
        
        for image in images:
            image_url = f"/{image}"
            html += f"""
            <div class="image-container">
                <img src="{image_url}" alt="{image}">
                <div>{image}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())

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
        if not IS_RASPBERRY_PI:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"WiFi settings would be updated (development mode)")
            return
            
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        
        # Parse the form data
        from urllib.parse import parse_qs, unquote
        
        # Parse the query string and extract parameters
        params = parse_qs(post_data)
        
        # Get the first value for each parameter and decode URL encoding
        ssid = unquote(params.get('ssid', [''])[0])
        password = unquote(params.get('password', [''])[0])

        if not ssid or not password:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"SSID and Password are required.")
            return

        try:
            # Read existing configuration
            current_config = ""
            if os.path.exists(WPA_SUPPLICANT_FILE):
                with open(WPA_SUPPLICANT_FILE, 'r') as f:
                    current_config = f.read()
        
            # Check if this network is already configured
            if f'ssid="{ssid}"' in current_config:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"WiFi network '{ssid}' is already configured.".encode())
                return
        
            # If this is a new file, create the header
            if not current_config or current_config.strip() == "":
                new_config = f"""country=US
                    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
                    update_config=1

                    """
            else:
                # Keep the existing config
                new_config = current_config
            
                # Make sure there's a blank line at the end if not already present
                if not new_config.endswith('\n\n'):
                    new_config = new_config.rstrip('\n') + '\n\n'
        
            # Append the new network configuration
            new_config += f"""network={{
                    ssid="{ssid}"
                    psk="{password}"
                    priority=10
                }}
                """
        
            # Write the updated configuration
            with open(WPA_SUPPLICANT_FILE, 'w') as f:
                f.write(new_config)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"WiFi network '{ssid}' added. Please reboot the device.".encode())
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
        
        if IS_RASPBERRY_PI:
            subprocess.run(['sudo', 'reboot'])
        else:
            print("Would reboot if running on Raspberry Pi")

    def shutdown_system(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shutting down system...")
        print("Shutting down system...")
        
        if IS_RASPBERRY_PI:
            subprocess.run(['sudo', 'shutdown', 'now'])
        else:
            print("Would shutdown if running on Raspberry Pi")
            
    def get_number(self):
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        with open(set_number_file, 'r+') as f:
            set_number = int(f.read().strip())
        return set_number
     
    def capture_images(self): 
        if not IS_RASPBERRY_PI:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Image capture would happen here (development mode)")
            print("Would capture image if running on Raspberry Pi")
            return
            
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        with open(set_number_file, 'r+') as f:
            set_number = int(f.read().strip())
            f.seek(0)
            f.truncate()
            f.write(str(set_number + 1))
            
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Image capture in progress...\n")
        print("Capturing...") 
        filename = os.path.join(IMAGE_DIR, f'{self.get_number()}z.jpg')
        camera.capture_file(filename) 
        print(f"Image captured! {self.get_number()}") 
        time.sleep(1) 
        self.wfile.write(b"Image capture done\n")

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True

def start_http_server():
    os.chdir(IMAGE_DIR)
    server_address = ('', PORT)  # Empty string means listen on all available interfaces
    
    # Create HTTPS server
    httpd = ThreadedTCPServer(server_address, MyHTTPRequestHandler)
    
    # Wrap with SSL
    try:
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        
        # Wrap socket with SSL
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        
        print(f"Serving images securely on HTTPS port {PORT}...")
    except Exception as e:
        print(f"Failed to enable HTTPS: {e}")
        print(f"Falling back to HTTP on port {PORT}...")
    
    httpd.serve_forever()

def generate_self_signed_cert():
    """Generate a self-signed certificate if one doesn't exist"""
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        print(f"Using existing SSL certificates: {CERT_FILE} and {KEY_FILE}")
        return
    
    try:
        from OpenSSL import crypto
        
        # Create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)
        
        # Create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "State"
        cert.get_subject().L = "City"
        cert.get_subject().O = "Organization"
        cert.get_subject().OU = "Organizational Unit"
        cert.get_subject().CN = socket.gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')
        
        # Write the certificate and key to files
        with open(CERT_FILE, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        
        with open(KEY_FILE, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
            
        print(f"Generated self-signed SSL certificate: {CERT_FILE} and {KEY_FILE}")
    except ImportError:
        print("PyOpenSSL not installed. Cannot generate self-signed certificate.")
        print("Install with: pip install pyopenssl")
        print("Falling back to HTTP...")
    except Exception as e:
        print(f"Error generating self-signed certificate: {e}")
        print("Falling back to HTTP...")

if __name__ == '__main__':
    try:
        # Generate self-signed certificate if needed
        generate_self_signed_cert()
        
        print(f"Server running at https://{current_ip}:{PORT}/")
        server_thread = threading.Thread(target=start_http_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server interrupted. Shutting down.")
        if IS_RASPBERRY_PI:
            GPIO.cleanup()
