import socket
from PIL import Image
import io
import subprocess
import os
import time
import json
IMAGE_DIR = '/home/user/camera'  # Ensure this is the correct directory
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
# Resolve hostname to IP address
hostname = 'raspberrypi'
port = 8080
server_address = (socket.gethostbyname(hostname), port)
server_address = (wlan0_ip, port)
# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(2)
count =1
print(f'Server is listening on {wlan0_ip}:{port}...')
old_address = None
def get_number():
    set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
    with open(set_number_file, 'r+') as f:
        set_number = int(f.read().strip())
    f.close()
    return set_number
toggle = True
CAMERA_CONFIG_FILE = os.path.join(IMAGE_DIR, 'camera_config.json')

def load_camera_config():
    if os.path.exists(CAMERA_CONFIG_FILE):
        with open(CAMERA_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"cameras": {}}

def save_camera_config(config):
    with open(CAMERA_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

camera_config = load_camera_config()
connection_order = []

received_x = False
received_y = False

while True:
    connection, client_address = server_socket.accept()
    try:
        print('Connection from', client_address)
        if old_address != client_address:
            print('Client changed.')
            if toggle:
                toggle = False
                filename = os.path.join(IMAGE_DIR, f'{get_number()}x.jpg')
                received_x = True
            else:
                toggle = True
                filename = os.path.join(IMAGE_DIR, f'{get_number()}y.jpg')
                received_y = True
            
            # Only increment count after both x and y are received
            if received_x and received_y:
                count = count + 1
                # Reset flags for next set
                received_x = False
                received_y = False
                
            old_address = client_address
        else:
            print("count continued", count)
            
        print(filename)
        # Receive the image data in chunks
        image_data = b''
        while True:
            data = connection.recv(2048)
            if not data:
                break
            image_data += data
        
        # Convert the byte data to an image
        image = Image.open(io.BytesIO(image_data))
        # Save the image to the current directory
        
        image.save(filename)
        if (count>=2):
            count=1
        #image.show()
        
        print('Image received.')
        # If we've received both X and Y images for this set, reset for next set
        if len(connection_order) >= 2:
            # Check if both x and y files exist for this set
            x_file = os.path.join(IMAGE_DIR, f'{get_number()}x.jpg')
            y_file = os.path.join(IMAGE_DIR, f'{get_number()}y.jpg')
            if os.path.exists(x_file) and os.path.exists(y_file):
                # Reset connection order for next set
                connection_order = []
                print(f"Set {get_number()} complete. Ready for next set.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()
