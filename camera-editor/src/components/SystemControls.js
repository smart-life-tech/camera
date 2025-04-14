import React, { useState } from 'react';
import { Button, Modal, Alert, Spinner } from 'react-bootstrap';
import axios from 'axios';

function SystemControls({ cameraIP, cameraPort }) {
  const [showRebootModal, setShowRebootModal] = useState(false);
  const [showShutdownModal, setShowShutdownModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleReboot = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await axios.get(`http://${cameraIP}:${cameraPort}/reboot`);
      setSuccess('Reboot command sent successfully. The camera will restart shortly.');
      setShowRebootModal(false);
    } catch (err) {
      console.error('Error rebooting:', err);
      setError('Failed to reboot the camera. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleShutdown = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await axios.get(`http://${cameraIP}:${cameraPort}/shutdown`);
      setSuccess('Shutdown command sent successfully. The camera will power off shortly.');
      setShowShutdownModal(false);
    } catch (err) {
      console.error('Error shutting down:', err);
      setError('Failed to shut down the camera. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      
      <div className="d-flex mb-3">
        <Button 
          variant="warning" 
          onClick={() => setShowRebootModal(true)}
          className="me-2"
        >
          Reboot Camera
        </Button>
        <Button 
          variant="danger" 
          onClick={() => setShowShutdownModal(true)}
        >
          Shutdown Camera
        </Button>
      </div>
      
      {/* Reboot Confirmation Modal */}
      <Modal show={showRebootModal} onHide={() => setShowRebootModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Reboot</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to reboot the camera? This will disconnect all current users.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRebootModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="warning" 
            onClick={handleReboot}
            disabled={loading}
          >
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" /> Rebooting...
              </>
            ) : (
              'Yes, Reboot Camera'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
      
      {/* Shutdown Confirmation Modal */}
      <Modal show={showShutdownModal} onHide={() => setShowShutdownModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Shutdown</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to shut down the camera? You will need physical access to turn it back on.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowShutdownModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="danger" 
            onClick={handleShutdown}
            disabled={loading}
          >
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" /> Shutting down...
              </>
            ) : (
              'Yes, Shutdown Camera'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default SystemControls;
