import socket
from PIL import Image
import io

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
hostname = 'hostname'
port = 65432
server_address = (socket.gethostbyname(hostname), port)

# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(server_address)

try:
    # Send the image data
    client_socket.sendall(image_bytes)
    print('Image sent.')
finally:
    client_socket.close()
