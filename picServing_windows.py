import time
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn, TCPServer
import socket
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

# Define the directory where images will be stored
IMAGE_DIR = 'C:/Users/USER/OneDrive/Pictures/Screenshots/'
PORT = 5000
IS_RASPBERRY_PI = False

# Get the local IP address
def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

current_ip = get_ip_address()
print(f"Server IP address: {current_ip}")

# Make sure the image directory exists
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Create a set_number.txt file if it doesn't exist
set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
if not os.path.exists(set_number_file):
    with open(set_number_file, 'w') as f:
        f.write('0')

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
        elif self.path == '/capture':
            self.capture_dummy_image()
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == '/save_edited_image':
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

        # HTML content (same as in the original file)
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

    def get_number(self):
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        with open(set_number_file, 'r') as f:
            set_number = int(f.read().strip())
        return set_number

    def capture_dummy_image(self):
        # For Windows, we'll create a dummy image since we don't have a camera
        from PIL import Image
        
        # Create a set_number.txt file if it doesn't exist
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        if not os.path.exists(set_number_file):
            with open(set_number_file, 'w') as f:
                f.write('0')
        
        # Read and increment the set number
        with open(set_number_file, 'r+') as f:
            set_number = int(f.read().strip())
            f.seek(0)
            f.truncate()
            f.write(str(set_number + 1))
        
        # Create a dummy image (colored gradient)
        width, height = 640, 480
        image = Image.new('RGB', (width, height), color='white')
        
        # Draw a simple gradient
        pixels = image.load()
        for i in range(width):
            for j in range(height):
                r = int(255 * i / width)
                g = int(255 * j / height)
                b = int(255 * (i + j) / (width + height))
                pixels[i, j] = (r, g, b)
        
        # Save the image
        filename = f'{set_number}z.jpg'
        image_path = os.path.join(IMAGE_DIR, filename)
        image.save(image_path)
        
        print(f"Dummy image captured: {filename}")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Dummy image captured. <a href='/'>Return to gallery</a>")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True

def start_http_server():
    os.chdir(IMAGE_DIR)
    server_address = ('', PORT)
    with ThreadedTCPServer(server_address, MyHTTPRequestHandler) as httpd:
        print(f"Serving images on http://{current_ip}:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    try:
        print(f"Server IP address: {current_ip}")
        print(f"Image directory: {IMAGE_DIR}")
        
        # Create set_number.txt if it doesn't exist
        set_number_file = os.path.join(IMAGE_DIR, 'set_number.txt')
        if not os.path.exists(set_number_file):
            with open(set_number_file, 'w') as f:
                f.write('0')
        
        # Start the server
        start_http_server()
    except KeyboardInterrupt:
        print("Server interrupted. Shutting down.")