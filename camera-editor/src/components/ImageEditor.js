  import React, { useEffect, useRef, useState,useCallback } from 'react';
  import { Modal, Button, Row, Col, Form } from 'react-bootstrap';
  import axios from 'axios';

  function ImageEditor({ show, onHide, imageUrl, imageName, cameraIP, cameraPort }) {
    const canvasRef = useRef(null);
    const [originalImage, setOriginalImage] = useState(null);
    const [brightness, setBrightness] = useState(0);
    const [contrast, setContrast] = useState(0);
    const [saturation, setSaturation] = useState(0);
    const [exposure, setExposure] = useState(0);
    const [highlights, setHighlights] = useState(0);
    const [shadows, setShadows] = useState(0);
    const [rotation, setRotation] = useState(0);
    const [currentEffect, setCurrentEffect] = useState('normal');
    const [saving, setSaving] = useState(false);

    // Helper function for clamping values
    const clamp = useCallback((value) => {
      return Math.max(0, Math.min(255, value));
    }, []);

    // Define applyAdjustments first with useCallback
    const applyAdjustments = useCallback(() => {
      if (!canvasRef.current) return;
    
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
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
      
        // Apply highlights and shadows
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
    }, [brightness, contrast, saturation, exposure, highlights, shadows, currentEffect, clamp]);

    // Then define drawImage with useCallback, now that applyAdjustments is defined
    const drawImage = useCallback(() => {
      if (!originalImage || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

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
    }, [originalImage, rotation, applyAdjustments]);

    useEffect(() => {
      if (show) {
        const img = new Image();
        img.crossOrigin = "Anonymous";
        img.onload = function() {
          setOriginalImage(img);
          const canvas = canvasRef.current;
          canvas.width = img.width;
          canvas.height = img.height;
          drawImage();
        };
        img.src = imageUrl;
      }
    }, [show, imageUrl, drawImage]);

    useEffect(() => {
      if (originalImage) {
        drawImage();
      }
    }, [brightness, contrast, saturation, exposure, highlights, shadows, rotation, currentEffect, originalImage, drawImage]);

    const rotateImage = useCallback((degrees) => {
      setRotation((prevRotation) => (prevRotation + degrees) % 360);
    }, []);

    const applyEffect = useCallback((effect) => {
      setCurrentEffect(effect);
    }, []);

    const resetAdjustments = useCallback(() => {
      setBrightness(0);
      setContrast(0);
      setSaturation(0);
      setExposure(0);
      setHighlights(0);
      setShadows(0);
      setRotation(0);
      setCurrentEffect('normal');
    }, []);

    const saveImage = useCallback(async () => {
      if (!canvasRef.current) return;
    
      setSaving(true);
      try {
        // Convert canvas to blob
        const blob = await new Promise(resolve => {
          canvasRef.current.toBlob(resolve, 'image/jpeg');
        });
      
        // Create FormData
        const formData = new FormData();
        formData.append('image', blob, `edited_${imageName}`);
      
        // Send to server
        await axios.post(
          `https://${cameraIP}:${cameraPort}/save_edited_image`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        );
      
        alert('Image saved successfully!');
        onHide();
      } catch (error) {
        console.error('Error saving image:', error);
        alert('Error saving image. Please try again.');
      } finally {
        setSaving(false);
      }
    }, [cameraIP, cameraPort, imageName, onHide]);

    const downloadImage = useCallback(() => {
      if (!canvasRef.current) return;
    
      const link = document.createElement('a');
      link.download = `edited_${imageName}`;
      link.href = canvasRef.current.toDataURL('image/jpeg');
      link.click();
    }, [imageName]);

    return (
      <Modal show={show} onHide={onHide} size="xl" centered>
        <Modal.Header closeButton>
          <Modal.Title>Image Editor - {imageName}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row>
            <Col md={8}>
              <div className="image-container">
                <canvas ref={canvasRef} style={{ maxWidth: '100%' }}></canvas>
              </div>
            </Col>
            <Col md={4}>
              <div className="editor-controls">
                <h6>Adjustments</h6>
                <Form.Group className="mb-3">
                  <Form.Label>Brightness</Form.Label>
                  <Form.Range 
                    min="-100" 
                    max="100" 
                    value={brightness} 
                    onChange={(e) => setBrightness(parseInt(e.target.value))} 
                  />
                </Form.Group>
              
                <Form.Group className="mb-3">
                  <Form.Label>Contrast</Form.Label>
                  <Form.Range 
                    min="-100" 
                    max="100" 
                    value={contrast} 
                    onChange={(e) => setContrast(parseInt(e.target.value))} 
                  />
                </Form.Group>
              
                <Form.Group className="mb-3">
                  <Form.Label>Saturation</Form.Label>
                  <Form.Range 
                    min="-100" 
                    max="100" 
                    value={saturation} 
                    onChange={(e) => setSaturation(parseInt(e.target.value))} 
                  />
                </Form.Group>
              
                <Form.Group className="mb-3">
                  <Form.Label>Exposure</Form.Label>
                  <Form.Range 
                    min="-100" 
                    max="100" 
                    value={exposure} 
                    onChange={(e) => setExposure(parseInt(e.target.value))} 
                  />
                </Form.Group>
              
                <Form.Group className="mb-3">
                  <Form.Label>Highlights</Form.Label>
                  <Form.Range 
                    min="-100" 
                    max="100" 
                    value={highlights} 
                    onChange={(e) => setHighlights(parseInt(e.target.value))} 
                  />
                </Form.Group>
              
                <Form.Group className="mb-3">
                  <Form.Label>Shadows</Form.Label>
                  <Form.Range 
                    min="-100" 
                    max="100" 
                    value={shadows} 
                    onChange={(e) => setShadows(parseInt(e.target.value))} 
                  />
                </Form.Group>
              
                <hr />
                <h6>Transform</h6>
                <div className="d-flex mb-3">
                  <Button variant="outline-secondary" onClick={() => rotateImage(-90)} className="me-2">
                    Rotate Left
                  </Button>
                  <Button variant="outline-secondary" onClick={() => rotateImage(90)}>
                    Rotate Right
                  </Button>
                </div>
              
                <hr />
                <h6>Effects</h6>
                <div className="d-flex flex-wrap">
                  <Button 
                    variant={currentEffect === 'normal' ? 'secondary' : 'outline-secondary'} 
                    onClick={() => applyEffect('normal')}
                    className="me-2 mb-2"
                  >
                    Normal
                  </Button>
                  <Button 
                    variant={currentEffect === 'grayscale' ? 'secondary' : 'outline-secondary'} 
                    onClick={() => applyEffect('grayscale')}
                    className="me-2 mb-2"
                  >
                    Grayscale
                  </Button>
                  <Button 
                    variant={currentEffect === 'sepia' ? 'secondary' : 'outline-secondary'} 
                    onClick={() => applyEffect('sepia')}
                    className="me-2 mb-2"
                  >
                    Sepia
                  </Button>
                  <Button 
                    variant={currentEffect === 'vintage' ? 'secondary' : 'outline-secondary'} 
                    onClick={() => applyEffect('vintage')}
                    className="me-2 mb-2"
                  >
                    Vintage
                  </Button>
                </div>
              
                <hr />
                <Button variant="warning" onClick={resetAdjustments} className="w-100 mb-3">
                  Reset All Adjustments
                </Button>
              </div>
            </Col>
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Close
          </Button>
          <Button variant="primary" onClick={downloadImage}>
            Download Edited Image
          </Button>
          <Button 
            variant="success" 
            onClick={saveImage}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save to Camera'}
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }

  export default ImageEditor;
