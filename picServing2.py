import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn, TCPServer
from socketserver import TCPServer
import socket
import subprocess
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

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
        images = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.jpg')]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Modern HTML with CSS and JavaScript for image editing
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Smart Camera Interface</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body {
                    background-color: #f8f9fa;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding-bottom: 50px;
                }
                .navbar {
                    background-color: #343a40;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .card {
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    transition: transform 0.3s;
                }
                .card:hover {
                    transform: translateY(-5px);
                }
                .card-img-top {
                    height: 200px;
                    object-fit: cover;
                    cursor: pointer;
                }
                .btn-group {
                    width: 100%;
                }
                .btn {
                    border-radius: 5px;
                    margin: 2px;
                }
                .modal-content {
                    border-radius: 15px;
                }
                .editor-controls {
                    background-color: #f1f3f5;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 15px;
                }
                .slider-container {
                    margin-bottom: 10px;
                }
                .slider-label {
                    display: inline-block;
                    width: 100px;
                    font-weight: 500;
                }
                .image-container {
                    position: relative;
                    overflow: hidden;
                    margin-bottom: 15px;
                }
                #canvas {
                    max-width: 100%;
                    display: block;
                    margin: 0 auto;
                }
                .anchor-point {
                    position: absolute;
                    width: 10px;
                    height: 10px;
                    background-color: red;
                    border-radius: 50%;
                    cursor: move;
                }
                .effect-btn {
                    margin: 5px;
                    border-radius: 20px;
                }
                .crop-container {
                    display: none;
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark mb-4">
                <div class="container">
                    <a class="navbar-brand" href="#"><i class="fas fa-camera"></i> Smart Camera</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
                            <li class="nav-item">
                                <a class="nav-link" href="/capture"><i class="fas fa-camera-retro"></i> Capture Image</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="#wifiModal" data-bs-toggle="modal" data-bs-target="#wifiModal">
                                    <i class="fas fa-wifi"></i> Wi-Fi Settings
                                </a>
                            </li>
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle" href="#" id="systemDropdown" role="button" data-bs-toggle="dropdown">
                                    <i class="fas fa-cogs"></i> System
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item" href="/reboot"><i class="fas fa-sync"></i> Reboot</a></li>
                                    <li><a class="dropdown-item" href="/shutdown"><i class="fas fa-power-off"></i> Shutdown</a></li>
                                </ul>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>

            <div class="container">
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title"><i class="fas fa-images"></i> Image Gallery</h5>
                                <p class="card-text">Click on an image to edit or use the buttons below each image for other actions.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row" id="gallery">
        """
    
        # Add images to the gallery
        for image in images:
            image_url = f"/{image}"
            download_url = f"/download/{image}"
            html += f"""
                    <div class="col-md-4 col-sm-6 mb-4">
                        <div class="card h-100">
                            <img src="{image_url}" class="card-img-top" alt="{image}" onclick="openEditor('{image_url}', '{image}')">
                            <div class="card-body">
                                <h5 class="card-title">{image}</h5>
                                <div class="btn-group">
                                    <a href="{download_url}" class="btn btn-sm btn-primary"><i class="fas fa-download"></i> Download</a>
                                    <a href="/delete/{image}" class="btn btn-sm btn-danger"><i class="fas fa-trash"></i> Delete</a>
                                    <button class="btn btn-sm btn-success" onclick="openEditor('{image_url}', '{image}')"><i class="fas fa-edit"></i> Edit</button>
                                </div>
                            </div>
                        </div>
                    </div>
            """
        
            html += """
                </div>
            </div>

            <!-- Wi-Fi Settings Modal -->
            <div class="modal fade" id="wifiModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"><i class="fas fa-wifi"></i> Wi-Fi Settings</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="wifiForm" onsubmit="updateWifiCredentials(event)">
                                <div class="mb-3">
                                    <label for="ssid" class="form-label">SSID:</label>
                                    <input type="text" class="form-control" id="ssid" name="ssid" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password:</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary">Update Wi-Fi</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Image Editor Modal -->
            <div class="modal fade" id="editorModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"><i class="fas fa-edit"></i> Image Editor</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="image-container">
                                        <canvas id="canvas"></canvas>
                                        <div id="anchorPoint" class="anchor-point" style="display: none;"></div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="editor-controls">
                                        <h6>Adjustments</h6>
                                        <div class="slider-container">
                                            <span class="slider-label">Brightness:</span>
                                            <input type="range" class="form-range" min="-100" max="100" value="0" id="brightness">
                                        </div>
                                        <div class="slider-container">
                                            <span class="slider-label">Contrast:</span>
                                            <input type="range" class="form-range" min="-100" max="100" value="0" id="contrast">
                                        </div>
                                        <div class="slider-container">
                                            <span class="slider-label">Saturation:</span>
                                            <input type="range" class="form-range" min="-100" max="100" value="0" id="saturation">
                                        </div>
                                        <div class="slider-container">
                                            <span class="slider-label">Exposure:</span>
                                            <input type="range" class="form-range" min="-100" max="100" value="0" id="exposure">
                                        </div>
                                        <div class="slider-container">
                                            <span class="slider-label">Highlights:</span>
                                            <input type="range" class="form-range" min="-100" max="100" value="0" id="highlights">
                                        </div>
                                        <div class="slider-container">
                                            <span class="slider-label">Shadows:</span>
                                            <input type="range" class="form-range" min="-100" max="100" value="0" id="shadows">
                                        </div>
                                        
                                        <hr>
                                        <h6>Transform</h6>
                                        <div class="btn-group mb-3">
                                            <button class="btn btn-outline-secondary" onclick="rotateImage(-90)"><i class="fas fa-undo"></i> Rotate Left</button>
                                            <button class="btn btn-outline-secondary" onclick="rotateImage(90)"><i class="fas fa-redo"></i> Rotate Right</button>
                                            <button class="btn btn-outline-secondary" onclick="toggleCrop()"><i class="fas fa-crop"></i> Crop</button>
                                        </div>
                                        
                                        <div id="cropControls" class="crop-container">
                                            <div class="mb-2">
                                                <button class="btn btn-sm btn-primary" onclick="applyCrop()">Apply Crop</button>
                                                <button class="btn btn-sm btn-secondary" onclick="cancelCrop()">Cancel</button>
                                            </div>
                                        </div>
                                        
                                        <hr>
                                        <h6>Effects</h6>
                                        <div class="d-flex flex-wrap">
                                            <button class="btn btn-sm btn-outline-secondary effect-btn" onclick="applyEffect('normal')">Normal</button>
                                            <button class="btn btn-sm btn-outline-secondary effect-btn" onclick="applyEffect('grayscale')">Grayscale</button>
                                            <button class="btn btn-sm btn-outline-secondary effect-btn" onclick="applyEffect('sepia')">Sepia</button>
                                            <button class="btn btn-sm btn-outline-secondary effect-btn" onclick="applyEffect('vintage')">Vintage</button>
                                            <button class="btn btn-sm btn-outline-secondary effect-btn" onclick="applyEffect('blur')">Blur</button>
                                            <button class="btn btn-sm btn-outline-secondary effect-btn" onclick="applyEffect('sharpen')">Sharpen</button>
                                        </div>
                                        
                                        <hr>
                                        <h6>Anchor Point</h6>
                                        <button class="btn btn-outline-primary mb-3" onclick="toggleAnchorPoint()">
                                            <i class="fas fa-crosshairs"></i> Set Anchor Point
                                        </button>
                                        
                                        <hr>
                                        <h6>Object Removal</h6>
                                        <button class="btn btn-outline-danger mb-3" onclick="toggleObjectRemoval()">
                                            <i class="fas fa-eraser"></i> Remove Object
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-success" onclick="saveImage()">Save Changes</button>
                            <a id="downloadLink" class="btn btn-primary" download="edited_image.jpg">Download Edited Image</a>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                let canvas = document.getElementById('canvas');
                let ctx = canvas.getContext('2d');
                let originalImage = new Image();
                let currentImageName = '';
                let rotation = 0;
                let brightness = 0;
                let contrast = 0;
                let saturation = 0;
                let exposure = 0;
                let highlights = 0;
                let shadows = 0;
                let currentEffect = 'normal';
                let isCropping = false;
                let cropStartX, cropStartY, cropEndX, cropEndY;
                let anchorPointActive = false;
                let anchorX = 0;
                let anchorY = 0;
                let objectRemovalActive = false;
                
                function openEditor(imageUrl, imageName) {
                    currentImageName = imageName;
                    originalImage = new Image();
                    originalImage.crossOrigin = "Anonymous";
                    originalImage.onload = function() {
                        // Reset all parameters
                        rotation = 0;
                        brightness = 0;
                        contrast = 0;
                        saturation = 0;
                        exposure = 0;
                        highlights = 0;
                        shadows = 0;
                        currentEffect = 'normal';
                        isCropping = false;
                        anchorPointActive = false;
                        objectRemovalActive = false;
                        
                        // Reset sliders
                        document.getElementById('brightness').value = 0;
                        document.getElementById('contrast').value = 0;
                        document.getElementById('saturation').value = 0;
                        document.getElementById('exposure').value = 0;
                        document.getElementById('highlights').value = 0;
                        document.getElementById('shadows').value = 0;
                        
                        // Set canvas dimensions
                        canvas.width = originalImage.width;
                        canvas.height = originalImage.height;
                        
                        // Draw image
                        drawImage();
                        
                        // Show modal
                        new bootstrap.Modal(document.getElementById('editorModal')).show();
                    };
                    originalImage.src = imageUrl;
                }
                
                function drawImage() {
                    // Clear canvas
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // Save context
                    ctx.save();
                    
                    // Translate to center of canvas for rotation
                    ctx.translate(canvas.width/2, canvas.height/2);
                    
                    // Rotate
                    ctx.rotate(rotation * Math.PI / 180);
                    
                    // Draw image centered
                    ctx.drawImage(originalImage, -originalImage.width/2, -originalImage.height/2);
                    
                    // Restore context
                    ctx.restore();
                    
                    // Apply adjustments and effects
                    applyAdjustments();
                    
                    // Generate download link
                    updateDownloadLink();
                }
                
                function applyAdjustments() {
                    let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    let data = imageData.data;
                    
                    for (let i = 0; i < data.length; i += 4) {
                        // Apply brightness
                        data[i] = clamp(data[i] + brightness * 2.55);
                        data[i+1] = clamp(data[i+1] + brightness * 2.55);
                        data[i+2] = clamp(data[i+2] + brightness * 2.55);
                        
                        // Apply contrast
                        let factor = (259 * (contrast + 255)) / (255 * (259 - contrast));
                        data[i] = clamp(factor * (data[i] - 128) + 128);
                        data[i+1] = clamp(factor * (data[i+1] - 128) + 128);
                        data[i+2] = clamp(factor * (data[i+2] - 128) + 128);
                        
                        // Apply exposure
                        let expFactor = Math.pow(2, exposure/100);
                        data[i] = clamp(data[i] * expFactor);
                        data[i+1] = clamp(data[i+1] * expFactor);
                        data[i+2] = clamp(data[i+2] * expFactor);
                        
                        // Apply effects
                        if (currentEffect === 'grayscale') {
                            let avg = (data[i] + data[i+1] + data[i+2]) / 3;
                            data[i] = avg;
                            data[i+1] = avg;
                            data[i+2] = avg;
                        } else if (currentEffect === 'sepia') {
                            let r = data[i];
                            let g = data[i+1];
                            let b = data[i+2];
                            data[i] = clamp(r * 0.393 + g * 0.769 + b * 0.189);
                            data[i+1] = clamp(r * 0.349 + g * 0.686 + b * 0.168);
                            data[i+2] = clamp(r * 0.272 + g * 0.534 + b * 0.131);
                        } else if (currentEffect === 'vintage') {
                            let r = data[i];
                            let g = data[i+1];
                            let b = data[i+2];
                            data[i] = clamp(r * 0.62 + g * 0.32 + b * 0.06);
                            data[i+1] = clamp(r * 0.22 + g * 0.62 + b * 0.16);
                            data[i+2] = clamp(r * 0.24 + g * 0.32 + b * 0.44);
                        }
                        
                        // Apply saturation
                        if (saturation !== 0) {
                            let avg = (data[i] + data[i+1] + data[i+2]) / 3;
                            let satFactor = 1 + saturation / 100;
                            data[i] = clamp(avg + (data[i] - avg) * satFactor);
                            data[i+1] = clamp(avg + (data[i+1] - avg) * satFactor);
                            data[i+2] = clamp(avg + (data[i+2] - avg) * satFactor);
                        }
                        
                        // Apply highlights and shadows (simplified)
                        if (highlights !== 0 || shadows !== 0) {
                            let luminance = (data[i] * 0.299 + data[i+1] * 0.587 + data[i+2] * 0.114) / 255;
                            let shadowFactor = shadows / 100;
                            let highlightFactor = highlights / 100;
                            
                            if (luminance < 0.5) {
                                // Shadows
                                let factor = 1 + shadowFactor * (0.5 - luminance) * 2;
                                data[i] = clamp(data[i] * factor);
                                data[i+1] = clamp(data[i+1] * factor);
                                data[i+2] = clamp(data[i+2] * factor);
                            } else {
                                // Highlights
                                let factor = 1 + highlightFactor * (luminance - 0.5) * 2;
                                data[i] = clamp(data[i] * factor);
                                data[i+1] = clamp(data[i+1] * factor);
                                data[i+2] = clamp(data[i+2] * factor);
                            }
                        }
                    }
                    
                    ctx.putImageData(imageData, 0, 0);
                }
                
                function clamp(value) {
                    return Math.max(0, Math.min(255, value));
                }
                
                function rotateImage(degrees) {
                    rotation = (rotation + degrees) % 360;
                    drawImage();
                }
                
                function applyEffect(effect) {
                    currentEffect = effect;
                    drawImage();
                }
                
                function toggleCrop() {
                    isCropping = !isCropping;
                    let cropControls = document.getElementById('cropControls');
                    cropControls.style.display = isCropping ? 'block' : 'none';
                    
                    if (isCropping) {
                        // Set up crop event listeners
                        canvas.addEventListener('mousedown', startCrop);
                        canvas.addEventListener('mousemove', updateCrop);
                        canvas.addEventListener('mouseup', endCrop);
                    } else {
                        // Remove crop event listeners
                        canvas.removeEventListener('mousedown', startCrop);
                        canvas.removeEventListener('mousemove', updateCrop);
                        canvas.removeEventListener('mouseup', endCrop);
                    }
                }
                
                function startCrop(e) {
                    const rect = canvas.getBoundingClientRect();
                    cropStartX = e.clientX - rect.left;
                    cropStartY = e.clientY - rect.top;
                }
                
                function updateCrop(e) {
                    if (!cropStartX) return;
                    
                    const rect = canvas.getBoundingClientRect();
                    cropEndX = e.clientX - rect.left;
                    cropEndY = e.clientY - rect.top;
                    
                    // Redraw image with crop overlay
                    drawImage();
                    ctx.strokeStyle = 'red';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(
                        cropStartX, 
                        cropStartY, 
                        cropEndX - cropStartX, 
                        cropEndY - cropStartY
                    );
                }
                
                function endCrop() {
                    cropEndX = cropEndX || cropStartX;
                    cropEndY = cropEndY || cropStartY;
                }
                
                function applyCrop() {
                    if (!cropStartX || !cropEndX) return;
                    
                    // Ensure correct order of coordinates
                    let [x1, x2] = [cropStartX, cropEndX].sort((a, b) => a - b);
                    let [y1, y2] = [cropStartY, cropEndY].sort((a, b) => a - b);
                    
                    let width = x2 - x1;
                    let height = y2 - y1;
                    
                    if (width < 10 || height < 10) {
                        alert('Crop area too small');
                        return;
                    }
                    
                    // Create a temporary canvas for the cropped image
                    let tempCanvas = document.createElement('canvas');
                    tempCanvas.width = width;
                    tempCanvas.height = height;
                    let tempCtx = tempCanvas.getContext('2d');
                    
                    // Draw the cropped portion
                    tempCtx.drawImage(
                        canvas, 
                        x1, y1, width, height, 
                        0, 0, width, height
                    );
                    
                    // Resize the main canvas
                    canvas.width = width;
                    canvas.height = height;
                    
                    // Draw the cropped image back to the main canvas
                    ctx.drawImage(tempCanvas, 0, 0);
                    
                    // Reset crop variables
                    cropStartX = cropEndX = cropStartY = cropEndY = null;
                    toggleCrop();
                    
                    // Update download link
                    updateDownloadLink();
                }
                
                function cancelCrop() {
                    cropStartX = cropEndX = cropStartY = cropEndY = null;
                    toggleCrop();
                    drawImage();
                }
                
                function toggleAnchorPoint() {
                    anchorPointActive = !anchorPointActive;
                    let anchorPoint = document.getElementById('anchorPoint');
                    anchorPoint.style.display = anchorPointActive ? 'block' : 'none';
                    
                    if (anchorPointActive) {
                        // Set initial position
                        anchorX = canvas.width / 2;
                        anchorY = canvas.height / 2;
                        updateAnchorPointPosition();
                        
                        // Add event listener for dragging
                        canvas.addEventListener('mousedown', startDragAnchor);
                    } else {
                        canvas.removeEventListener('mousedown', startDragAnchor);
                    }
                }
                
                function updateAnchorPointPosition() {
                    let anchorPoint = document.getElementById('anchorPoint');
                    anchorPoint.style.left = (anchorX - 5) + 'px';
                    anchorPoint.style.top = (anchorY - 5) + 'px';
                }
                
                function startDragAnchor(e) {
                    if (!anchorPointActive) return;
                    
                    const rect = canvas.getBoundingClientRect();
                    anchorX = e.clientX - rect.left;
                    anchorY = e.clientY - rect.top;
                    updateAnchorPointPosition();
                }
                
                function toggleObjectRemoval() {
                    objectRemovalActive = !objectRemovalActive;
                    if (objectRemovalActive) {
                        alert('Object removal feature: Click and drag to select the area to remove');
                        canvas.addEventListener('mousedown', startObjectRemoval);
                        canvas.addEventListener('mousemove', updateObjectRemoval);
                        canvas.addEventListener('mouseup', applyObjectRemoval);
                    } else {
                        canvas.removeEventListener('mousedown', startObjectRemoval);
                        canvas.removeEventListener('mousemove', updateObjectRemoval);
                        canvas.removeEventListener('mouseup', applyObjectRemoval);
                    }
                }
                
                let removalStartX, removalStartY, removalEndX, removalEndY;
                
                function startObjectRemoval(e) {
                    if (!objectRemovalActive) return;
                    
                    const rect = canvas.getBoundingClientRect();
                    removalStartX = e.clientX - rect.left;
                    removalStartY = e.clientY - rect.top;
                }
                
                function updateObjectRemoval(e) {
                    if (!removalStartX || !objectRemovalActive) return;
                    
                    const rect = canvas.getBoundingClientRect();
                    removalEndX = e.clientX - rect.left;
                    removalEndY = e.clientY - rect.top;
                    
                    // Redraw image with removal area overlay
                    drawImage();
                    ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
                    ctx.fillRect(
                        removalStartX, 
                        removalStartY, 
                        removalEndX - removalStartX, 
                        removalEndY - removalStartY
                    );
                }
                
                function applyObjectRemoval() {
                    if (!removalStartX || !removalEndX || !objectRemovalActive) return;
                    
                    // Ensure correct order of coordinates
                    let [x1, x2] = [removalStartX, removalEndX].sort((a, b) => a - b);
                    let [y1, y2] = [removalStartY, removalEndY].sort((a, b) => a - b);
                    
                    let width = x2 - x1;
                    let height = y2 - y1;
                    
                    if (width < 5 || height < 5) {
                        alert('Selected area too small');
                        removalStartX = removalEndX = removalStartY = removalEndY = null;
                        drawImage();
                        return;
                    }
                    
                    // Simple content-aware fill (averaging surrounding pixels)
                    let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    let data = imageData.data;
                    
                    // Sample from surrounding area (simplified algorithm)
                    let sampleWidth = Math.min(width * 0.5, 20);
                    let sampleHeight = Math.min(height * 0.5, 20);
                    
                    // Calculate average color from surrounding pixels
                    let totalR = 0, totalG = 0, totalB = 0, count = 0;
                    
                    // Sample from above
                    for (let x = x1; x < x2; x++) {
                        for (let y = Math.max(0, y1 - sampleHeight); y < y1; y++) {
                            let i = (y * canvas.width + x) * 4;
                            totalR += data[i];
                            totalG += data[i+1];
                            totalB += data[i+2];
                            count++;
                        }
                    }
                    
                    // Sample from below
                    for (let x = x1; x < x2; x++) {
                        for (let y = y2; y < Math.min(canvas.height, y2 + sampleHeight); y++) {
                            let i = (y * canvas.width + x) * 4;
                            totalR += data[i];
                            totalG += data[i+1];
                            totalB += data[i+2];
                            count++;
                        }
                    }
                    
                    // Sample from left
                    for (let y = y1; y < y2; y++) {
                        for (let x = Math.max(0, x1 - sampleWidth); x < x1; x++) {
                            let i = (y * canvas.width + x) * 4;
                            totalR += data[i];
                            totalG += data[i+1];
                            totalB += data[i+2];
                            count++;
                        }
                    }
                    
                    // Sample from right
                    for (let y = y1; y < y2; y++) {
                        for (let x = x2; x < Math.min(canvas.width, x2 + sampleWidth); x++) {
                            let i = (y * canvas.width + x) * 4;
                            totalR += data[i];
                            totalG += data[i+1];
                            totalB += data[i+2];
                            count++;
                        }
                    }
                    
                    // Calculate average color
                    let avgR = Math.round(totalR / count);
                    let avgG = Math.round(totalG / count);
                    let avgB = Math.round(totalB / count);
                    
                    // Fill the selected area with the average color
                    for (let y = y1; y < y2; y++) {
                        for (let x = x1; x < x2; x++) {
                            let i = (y * canvas.width + x) * 4;
                            data[i] = avgR;
                            data[i+1] = avgG;
                            data[i+2] = avgB;
                        }
                    }
                    
                    ctx.putImageData(imageData, 0, 0);
                    
                    // Reset variables
                    removalStartX = removalEndX = removalStartY = removalEndY = null;
                    objectRemovalActive = false;
                    
                    // Update download link
                    updateDownloadLink();
                }
                
                function updateDownloadLink() {
                    let downloadLink = document.getElementById('downloadLink');
                    downloadLink.href = canvas.toDataURL('image/jpeg');
                    downloadLink.download = 'edited_' + currentImageName;
                }
                
                function saveImage() {
                    // Convert canvas to blob
                    canvas.toBlob(function(blob) {
                        // Create FormData object
                        let formData = new FormData();
                        formData.append('image', blob, 'edited_' + currentImageName);
                        
                        // Send to server
                        fetch('/save_edited_image', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('Image saved successfully!');
                                // Close modal and refresh gallery
                                document.querySelector('#editorModal .btn-close').click();
                                window.location.reload();
                            } else {
                                alert('Error saving image: ' + data.error);
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error saving image. Please try again.');
                        });
                    }, 'image/jpeg');
                }
                
                function updateWifiCredentials(event) {
                    event.preventDefault();
                    
                    const ssid = document.getElementById('ssid').value;
                    const password = document.getElementById('password').value;
                    
                    if (!ssid || !password) {
                        alert('Please enter both SSID and password');
                        return;
                    }
                    
                    // Send to local server for immediate use
                    fetch('/update_wifi', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `ssid=${encodeURIComponent(ssid)}&password=${encodeURIComponent(password)}`
                    })
                    .then(response => {
                        if (response.ok) {
                            // Now send to PythonAnywhere for storage
                            return fetch('https://christlight.pythonanywhere.com/wifi/save', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    ssid: ssid,
                                    password: password
                                })
                            });
                        } else {
                            throw new Error('Failed to update local WiFi settings');
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('WiFi credentials updated successfully both locally and in the cloud.');
                            document.querySelector('#wifiModal .btn-close').click();
                        } else {
                            alert('Cloud storage update failed: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('updated WiFi credentials. ');
                    });
                }
                
                // Event listeners for sliders
                document.getElementById('brightness').addEventListener('input', function(e) {
                    brightness = parseInt(e.target.value);
                    drawImage();
                });
                
                document.getElementById('contrast').addEventListener('input', function(e) {
                    contrast = parseInt(e.target.value);
                    drawImage();
                });
                
                document.getElementById('saturation').addEventListener('input', function(e) {
                    saturation = parseInt(e.target.value);
                    drawImage();
                });
                
                document.getElementById('exposure').addEventListener('input', function(e) {
                    exposure = parseInt(e.target.value);
                    drawImage();
                });
                
                document.getElementById('highlights').addEventListener('input', function(e) {
                    highlights = parseInt(e.target.value);
                    drawImage();
                });
                
                document.getElementById('shadows').addEventListener('input', function(e) {
                    shadows = parseInt(e.target.value);
                    drawImage();
                });
            </script>
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
        
            # Send the same credentials to PythonAnywhere for storage
            try:
            
                # Prepare data for PythonAnywhere
                data = {
                    'ssid': ssid,
                    'password': password,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'priority': 10,
                    'append': True
                }
            
                # Send to PythonAnywhere
                response = requests.post(
                    'https://christlight.pythonanywhere.com/wifi/save',
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10  # Set a timeout to avoid hanging
                )
                print(response)    
                if response.status_code == 200:
                    print(f"WiFi credentials for '{ssid}' saved   successfully")
                else:
                    print(f"Failed to save WiFi credentials  {response.text}")
                
            except Exception as e:
                print(f"Error sending WiFi credentials : {e}")
                # Continue even if PythonAnywhere update fails
            
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
