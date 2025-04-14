import React, { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Card, Button, Spinner, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCamera, faWifi, faCogs, faDownload, faTrash, faEdit } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';
import ImageEditor from './components/ImageEditor';
import ConnectForm from './components/ConnectForm';
import WifiSettings from './components/WifiSettings';
import SystemControls from './components/SystemControls';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

function App() {
  const [connected, setConnected] = useState(false);
  const [cameraIP, setCameraIP] = useState('');
  const [cameraPort, setCameraPort] = useState('5000');
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [showEditor, setShowEditor] = useState(false);
  const [showWifiSettings, setShowWifiSettings] = useState(false);
  const [fetchingIP, setFetchingIP] = useState(false);

  // Function to fetch the camera IP from the remote service
  const fetchCameraIP = useCallback(async () => {
    setFetchingIP(true);
    try {
      const response = await axios.get('https://christlight.pythonanywhere.com/read');
    
      console.log('Response data type:', typeof response.data);
      console.log('Response data:', response.data);
    
      let ip = null;
    
      // Handle the specific response format {content: '192.168.137.1'}
      if (response.data && response.data.content) {
        ip = response.data.content;
        console.log(`Retrieved camera IP from remote service: ${ip}`);
      
        // Update state and localStorage
        setCameraIP(ip);
        localStorage.setItem('cameraIP', ip);
      
        return ip;
      }
    
      return null;
    } catch (err) {
      console.error('Error fetching camera IP from remote service:', err);
      return null;
    } finally {
      setFetchingIP(false);
    }
  }, []);  // Remove cameraIP from dependencies to avoid unnecessary re-renders

  // Define fetchImages with useCallback
  const fetchImages = useCallback(async (ip = cameraIP, port = cameraPort) => {
    try {
      // Use the full ngrok URL instead of constructing it with IP and port
      const baseUrl = cameraIP.includes('ngrok') ? cameraIP : `http://${ip}:${port}`;
      //const response = await axios.get(`${baseUrl}/`);
      const ngrokUrl = "https://9e2b-102-89-23-37.ngrok-free.app"; // Replace with your actual ngrok URL
      const response = await axios.get(`${ngrokUrl}/`);
      // Parse the HTML to extract image URLs
      const html = response.data;
      // Updated regex to match both .jpg and .png files
      const imageRegex = /<img src="\/([^"]+\.(jpg|png))"/g;
      const matches = [...html.matchAll(imageRegex)];
      
      const imageList = matches.map(match => match[1]).filter(Boolean);
      setImages(imageList);
      return imageList;
    } catch (err) {
      console.error('Error fetching images:', err);
      throw err;
    }
  }, [cameraIP, cameraPort]);

  // Then define handleConnect with useCallback
  const handleConnect = useCallback(async () => {
    if (!cameraIP) {
      setError('Please enter the camera IP address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Save connection details to localStorage
      localStorage.setItem('cameraIP', cameraIP);
      localStorage.setItem('cameraPort', cameraPort);

      // Test connection by fetching images
      await fetchImages();
      setConnected(true);
    } catch (err) {
      console.error('Connection error:', err);
      setError(`Failed to connect to camera at ${cameraIP}:${cameraPort}. Please check the IP address and port.`);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  }, [cameraIP, cameraPort, fetchImages]);

  // Add a function to auto-connect using the fetched IP
  const autoConnect = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const ip = await fetchCameraIP();
      if (ip) {
        // Test connection by fetching images with the new IP
        await fetchImages(ip, cameraPort);
        setConnected(true);
        console.log(`Auto-connected to camera at ${ip}:${cameraPort}`);
      } else {
        throw new Error('Could not retrieve a valid camera IP');
      }
    } catch (err) {
      console.error('Auto-connect error:', err);
      setError(`Failed to auto-connect to camera. ${err.message}`);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  }, [fetchCameraIP, fetchImages, cameraPort]);

  useEffect(() => {
    // Load saved connection details from localStorage
    const savedIP = localStorage.getItem('cameraIP');
    const savedPort = localStorage.getItem('cameraPort');
    
    if (savedIP) {
      setCameraIP(savedIP);
    }
    
    if (savedPort) {
      setCameraPort(savedPort);
    }
    
    // If we don't have a saved IP or we want to always check for the latest IP
    if (!savedIP || true) {
      fetchCameraIP();
    }
  }, [fetchCameraIP]);

  const handleDownload = useCallback((imageName) => {
    const baseUrl = cameraIP.includes('ngrok') ? cameraIP : `http://${cameraIP}:${cameraPort}`;
    window.open(`${baseUrl}/download/${imageName}`, '_blank');
  }, [cameraIP, cameraPort]);

  const handleDelete = useCallback(async (imageName) => {
    if (!window.confirm(`Are you sure you want to delete ${imageName}?`)) {
      return;
    }

    setLoading(true);
    try {
      const baseUrl = cameraIP.includes('ngrok') ? cameraIP : `http://${cameraIP}:${cameraPort}`;
      await axios.get(`${baseUrl}/delete/${imageName}`);
      await fetchImages();
    } catch (err) {
      console.error('Error deleting image:', err);
      setError('Failed to delete image. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [cameraIP, cameraPort, fetchImages]);

  const handleEdit = useCallback((imageName) => {
    setSelectedImage(imageName);
    setShowEditor(true);
  }, []);

  const handleCloseEditor = useCallback(() => {
    setShowEditor(false);
    setSelectedImage(null);
    // Refresh images after editing
    fetchImages();
  }, [fetchImages]);

  const handleCapture = useCallback(async () => {
    setLoading(true);
    try {
      const baseUrl = cameraIP.includes('ngrok') ? cameraIP : `http://${cameraIP}:${cameraPort}`;
      await axios.get(`${baseUrl}/capture`);
      await fetchImages();
    } catch (err) {
      console.error('Error capturing image:', err);
      setError('Failed to capture image. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [cameraIP, cameraPort, fetchImages]);

  return (
    <div className="app">
      <header className="bg-dark text-white p-3 mb-4">
        <Container>
          <h1><FontAwesomeIcon icon={faCamera} /> Smart Camera Editor</h1>
        </Container>
      </header>

      <Container>
        {!connected ? (
          <div>
            <ConnectForm 
              cameraIP={cameraIP}
              setCameraIP={setCameraIP}
              cameraPort={cameraPort}
              setCameraPort={setCameraPort}
              handleConnect={handleConnect}
              loading={loading}
            />
            
            <div className="mt-4 text-center">
              <p>- OR -</p>
              <Button 
                variant="success" 
                onClick={autoConnect} 
                disabled={loading || fetchingIP}
              >
                {(loading || fetchingIP) ? (
                  <>
                    <Spinner as="span" animation="border" size="sm" /> Auto-Connecting...
                  </>
                ) : (
                  'Auto-Connect to Camera'
                )}
              </Button>
              <p className="mt-2 text-muted small">
                This will fetch the camera's IP address from the remote service
              </p>
            </div>
          </div>
        ) : (
          <>
            {error && <Alert variant="danger">{error}</Alert>}

            <Card className="mb-4">
              <Card.Body>
                <Card.Title>Connected to Camera at {cameraIP}:{cameraPort}</Card.Title>
                <div className="d-flex flex-wrap">
                  <Button
                    variant="primary"
                    onClick={handleCapture}
                    disabled={loading}
                    className="me-2 mb-2"
                  >
                    {loading ? (
                      <>
                        <Spinner as="span" animation="border" size="sm" /> Capturing...
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon icon={faCamera} /> Capture Image
                      </>
                    )}
                  </Button>

                  {/* Add WiFi Settings button */}
                  <Button
                    variant="info"
                    onClick={() => setShowWifiSettings(true)}
                    className="me-2 mb-2"
                  >
                    <FontAwesomeIcon icon={faWifi} /> WiFi Settings
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={() => {
                      setConnected(false);
                      setImages([]);
                    }}
                    className="mb-2"
                  >
                    Disconnect
                  </Button>
                </div>
              </Card.Body>
            </Card>

            {/* Add SystemControls component */}
            <Card className="mb-4">
              <Card.Body>
                <Card.Title><FontAwesomeIcon icon={faCogs} /> System Controls</Card.Title>
                <SystemControls
                  cameraIP={cameraIP}
                  cameraPort={cameraPort}
                />
              </Card.Body>
            </Card>

            <h2>Image Gallery</h2>
            {loading && <Spinner animation="border" />}

            <Row>
              {images.map((image) => (
                <Col md={4} sm={6} className="mb-4" key={image}>
                  <Card>
                    <Card.Img
                      variant="top"
                      src={`https://${cameraIP}:${cameraPort}/${image}`}
                      alt={image}
                      style={{ height: '200px', objectFit: 'cover', cursor: 'pointer' }}
                      onClick={() => handleEdit(image)}
                    />
                    <Card.Body>
                      <Card.Title>{image}</Card.Title>
                      <div className="d-grid gap-2">
                        <Button variant="primary" onClick={() => handleDownload(image)}>
                          <FontAwesomeIcon icon={faDownload} /> Download
                        </Button>
                        <Button variant="success" onClick={() => handleEdit(image)}>
                          <FontAwesomeIcon icon={faEdit} /> Edit
                        </Button>
                        <Button variant="danger" onClick={() => handleDelete(image)}>
                          <FontAwesomeIcon icon={faTrash} /> Delete
                        </Button>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>

            {images.length === 0 && !loading && (
              <Alert variant="info">No images found. Capture some images to get started.</Alert>
            )}
          </>
        )}
      </Container>

      {/* Include the WifiSettings modal */}
      <WifiSettings
        show={showWifiSettings}
        onHide={() => setShowWifiSettings(false)}
        cameraIP={cameraIP}
        cameraPort={cameraPort}
      />

      {showEditor && selectedImage && (
        <ImageEditor
          show={showEditor}
          onHide={handleCloseEditor}
          imageUrl={`https://${cameraIP}:${cameraPort}/${selectedImage}`}
          imageName={selectedImage}
          cameraIP={cameraIP}
          cameraPort={cameraPort}
        />
      )}
    </div>
  );
}

export default App;
