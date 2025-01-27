import socket
from PIL import Image
import io
import socket
import subprocess

# Configuration
base_ip = "192.168."  # Base IP to scan
port = 8080           # Port to check for connections

def ping_host(ip):
    """Ping the given IP to check if it's reachable."""
    try:
        # Execute the ping command
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],  # For Windows, use ["ping", "-n", "1", ip]
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return False

def check_port(ip, port):
    """Check if the given port is open on the given IP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)  # Timeout for connection attempt
        try:
            sock.connect((ip, port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False

def find_servers(base, port):
    """Scan the IP range for available servers."""
    available_servers = []
    for subnet in range(0, 256):  # Iterate over all possible subnets
        for host in range(1, 255):  # Iterate over hosts in the subnet
            ip = f"{base}{subnet}.{host}"
            print(f"Scanning {ip}...")
            if ping_host(ip) and check_port(ip, port):
                available_servers.append(ip)
                print(f"Server found: {ip}:{port}")
    return available_servers



# Load an image
image_path = '/home/user/camera/Pictures/img1.jpg'
image = Image.open(image_path)
# Convert image to RGB if it is in RGBA mode 
if image.mode == 'RGBA': 
    image = image.convert('RGB')
# Convert image to bytes
byte_arr = io.BytesIO()
image.save(byte_arr, format='JPEG')
image_bytes = byte_arr.getvalue()

# Resolve hostname to IP address
hostname = 'raspberrypi'
port = 8080
server_address = ('192.168.137.98', port)
print(server_address)
# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if __name__ == "__main__":
    print(f"Scanning {base_ip}x.x for servers on port {port}...")
    servers = find_servers(base_ip, port)
    if servers:
        print("\nAvailable servers:")
        for server in servers:
            print(f"{server}:{port}")
    else:
        print("No available servers found.")
    try:
        # Send the image data
        client_socket.connect(server_address)
        client_socket.sendall(image_bytes)
        print('Image sent.')
    finally:
        client_socket.close()
