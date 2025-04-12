import time
from picamera2 import Picamera2
import socket
import os
import RPi.GPIO as GPIO
import requests
import json
import subprocess

current_ip = None
# Define the server (Pi3rd) IP and port for communication
file_path = '/home/user/camera/example.txt'
WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'

# Function to write the new IP address to the file
def write_ip_to_file(file_path, ip):
    with open(file_path, 'w') as file:
        file.write(ip)

# Function to check for IP address updates
def checks():
    global current_ip
    while True:
        try:
            url = 'https://christlight.pythonanywhere.com/read'
            response = requests.get(url)
            print("read content", response.json().get('content'))
            current_ip = response.json().get('content')
            write_ip_to_file(file_path, current_ip)
            if response.status_code == 200:
                print("IP address read successfully.")
                break
        except Exception as e:
            print(f"Error: {e}")

# Function to check for WiFi credential updates
def check_wifi_credentials():
    try:
        # Get the latest WiFi credentials from PythonAnywhere
        url = 'https://christlight.pythonanywhere.com/wifi/latest'
        response = requests.get(url)
        print("wifi credentials", response.json())
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                wifi_data = data.get('data')
                ssid = wifi_data.get('ssid')
                password = wifi_data.get('password')
                
                # Check if we need to update the wpa_supplicant file
                if ssid and password:
                    update_wpa_supplicant(ssid, password)
                    return True
        
        return False
    except Exception as e:
        print(f"Error checking WiFi credentials: {e}")
        return False

# Function to update wpa_supplicant.conf
def update_wpa_supplicant(ssid, password):
    try:
        # Check if the current configuration already has these credentials
        current_config = ""
        if os.path.exists(WPA_SUPPLICANT_FILE):
            with open(WPA_SUPPLICANT_FILE, 'r') as f:
                current_config = f.read()
        
        # If the SSID is already in the config, don't update
        if f'ssid="{ssid}"' in current_config:
            print(f"WiFi network {ssid} already configured.")
            return
        
        # Create new wpa_supplicant.conf content
        new_config = f"""country=US
            ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
            update_config=1

            network={{
                ssid="{ssid}"
                psk="{password}"
            }}
            """
        
        # Write to a temporary file first (since we might need sudo)
        temp_file = '/tmp/wpa_supplicant.conf'
        with open(temp_file, 'w') as f:
            f.write(new_config)
        
        # Use sudo to copy the file to the correct location
        subprocess.run(['sudo', 'cp', temp_file, WPA_SUPPLICANT_FILE])
        subprocess.run(['sudo', 'chmod', '600', WPA_SUPPLICANT_FILE])
        
        print(f"Updated WiFi configuration for network: {ssid}")
        
        # # Restart the wireless interface to apply changes
        # subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])
        # subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'])
        
        # Wait for the network to reconnect
        print("Waiting for network to reconnect...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error updating wpa_supplicant: {e}")

# Setup GPIO
INPUT_PIN = 27  # Same pin as used for the trigger
GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_PIN, GPIO.IN)

# Setup the camera
camera = Picamera2()
# Configure the camera with default settings 
camera.configure(camera.create_still_configuration(main={"size": camera.sensor_resolution}))
# Start the camera 
camera.start()

# Check for IP address updates
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
    
# Check for WiFi credential updates
check_wifi_credentials()
    
PI3_IP = read_stored_ip(file_path)  # Pi3's fixed IP address
PORT = 5000
print("pi 3 ip address is: ", PI3_IP)

def capture_image(filename):
    print("capturing image")
    # Capture and save the image 
    camera.capture_file(filename)

def send_image_to_pi3(image_path):
    try:
        print("sending image to pi3")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((PI3_IP, 8080))
            print("connected to pi3")
            with open(image_path, 'rb') as f:
                    while True:
                        chunk = f.read(2048)
                        if not chunk:
                            break
                        s.sendall(chunk)  # Send image file to Pi3
                    print("Image file sent.")
                    os.remove(image_path)
    except BrokenPipeError:
        print("Connection closed by the receiver before sending was complete.")
    except Exception as e:
        print(f"An error occurred: {e}")

def wait_for_trigger():
    last_wifi_check = time.time()
    
    while True:
        try:
            # Check for WiFi credential updates every 5 minutes
            current_time = time.time()
            if current_time - last_wifi_check > 300:  # 300 seconds = 5 minutes
                check_wifi_credentials()
                last_wifi_check = current_time
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(INPUT_PIN, GPIO.IN)
            if GPIO.input(INPUT_PIN) == GPIO.HIGH:
                filename = f"/home/user/camera/captured_image_{int(time.time())}.jpg"
                capture_image(filename)
                send_image_to_pi3(filename)
                
            # Small delay to prevent CPU overuse
            time.sleep(0.1)
                
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)
        finally:
            # Cleanup GPIO
            GPIO.cleanup()

if __name__ == '__main__':
    wait_for_trigger()
