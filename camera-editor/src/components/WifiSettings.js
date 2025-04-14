import React, { useState } from 'react';
import { Modal, Button, Form, Spinner, Alert } from 'react-bootstrap';
import axios from 'axios';

function WifiSettings({ show, onHide, cameraIP, cameraPort }) {
  const [ssid, setSsid] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!ssid || !password) {
      setError('Please enter both SSID and password');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess(false);
    
    try {
      const formData = new URLSearchParams();
      formData.append('ssid', ssid);
      formData.append('password', password);
      
      const response = await axios.post(
        `http://${cameraIP}:${cameraPort}/update_wifi`,
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );
      
      if (response.status === 200) {
        setSuccess(true);
        setSsid('');
        setPassword('');
      } else {
        setError('Failed to update WiFi settings');
      }
    } catch (err) {
      console.error('Error updating WiFi:', err);
      setError('Error connecting to camera. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide}>
      <Modal.Header closeButton>
        <Modal.Title>WiFi Settings</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {success && <Alert variant="success">WiFi settings updated successfully! You may need to reboot the camera for changes to take effect.</Alert>}
        
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>SSID (Network Name)</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter WiFi network name"
              value={ssid}
              onChange={(e) => setSsid(e.target.value)}
              required
            />
          </Form.Group>
          
          <Form.Group className="mb-3">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter WiFi password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Form.Group>
          
          <Button 
            variant="primary" 
            type="submit" 
            disabled={loading}
          >
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" /> Updating...
              </>
            ) : (
              'Update WiFi Settings'
            )}
          </Button>
        </Form>
      </Modal.Body>
    </Modal>
  );
}

export default WifiSettings;
