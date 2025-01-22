import socket
from PIL import Image
import io

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('0.0.0.0', 65432)
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
        
        # Convert the byte data to an image
        image = Image.open(io.BytesIO(image_data))
        # Save the image to the current directory
        image.save('received_image.png')
        image.show()
        
        print('Image received and displayed.')
        
    finally:
        connection.close()
