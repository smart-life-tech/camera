import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import socket

IMAGE_DIR = 'C:/Users/USER/Downloads/'  # Ensure this is the correct directory
IMAGE_DIR=input("Enter the directory path to the photos to be served: ")
PORT = 8080

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
        else:
            # Serve the requested image file
            return super().do_GET()

    def list_images(self):
        # List available images and add delete button for each image
        images = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.jpg')]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

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

# Start the server with custom handler
def start_http_server():
    os.chdir(IMAGE_DIR)  # Change directory to the image folder
    with TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Serving images on port {PORT}...")
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


if __name__ == '__main__':
    try:
        print_ip_address()
        # Start the HTTP server in a separate thread
        server_thread = threading.Thread(target=start_http_server)
        server_thread.daemon = True  # Daemonize the thread so it stops on exit
        server_thread.start()
        server_thread.join()  # Make sure the server keeps running
        time.sleep(100)  # Wait for the server to start
    except KeyboardInterrupt:
        print("Server interrupted. Shutting down.")
