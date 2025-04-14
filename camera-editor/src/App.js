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
  const [do_once, setDonce] = useState(true);
  // Add state for WiFi settings modal
  const [showWifiSettings, setShowWifiSettings] = useState(false);

  // Define fetchImages first with useCallback
  const fetchImages = useCallback(async () => {
    try {
      // This is a workaround since we can't directly parse the HTML response
      // In a production app, you would have an API endpoint that returns JSON
      const response = await axios.get(`https://${cameraIP}:${cameraPort}/`);

      // Parse the HTML to extract image URLs
      const html = response.data;
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

  useEffect(() => {
    // Load saved connection details from localStorage
    const savedIP = localStorage.getItem('cameraIP');
    const savedPort = localStorage.getItem('cameraPort');

    if (savedIP && savedPort && !do_once) {
      setCameraIP(savedIP);
      setCameraPort(savedPort);
      setDonce(false);
      // Optionally auto-connect
      // handleConnect();
    }
  }, [handleConnect]);

  const handleDownload = useCallback((imageName) => {
    window.open(`https://${cameraIP}:${cameraPort}/download/${imageName}`, '_blank');
  }, [cameraIP, cameraPort]);

  const handleDelete = useCallback(async (imageName) => {
    if (!window.confirm(`Are you sure you want to delete ${imageName}?`)) {
      return;
    }

    setLoading(true);
    try {
      await axios.get(`https://${cameraIP}:${cameraPort}/delete/${imageName}`);
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
      await axios.get(`https://${cameraIP}:${cameraPort}/capture`);
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
          <ConnectForm
            cameraIP={cameraIP}
            setCameraIP={setCameraIP}
            cameraPort={cameraPort}
            setCameraPort={setCameraPort}
            handleConnect={handleConnect}
            loading={loading}
          />
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
