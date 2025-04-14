import React from 'react';
import { Card, Form, Button, Spinner } from 'react-bootstrap';

function ConnectForm({ cameraIP, setCameraIP, cameraPort, setCameraPort, handleConnect, loading }) {
  return (
    <Card className="mb-4">
      <Card.Body>
        <Card.Title>Connect to Camera</Card.Title>
        <Form onSubmit={(e) => {
          e.preventDefault();
          handleConnect();
        }}>
          <Form.Group className="mb-3">
            <Form.Label>Camera IP Address</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter IP address (e.g., 192.168.1.100)"
              value={cameraIP}
              onChange={(e) => setCameraIP(e.target.value)}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Port</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter port (default: 5000)"
              value={cameraPort}
              onChange={(e) => setCameraPort(e.target.value)}
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
                <Spinner as="span" animation="border" size="sm" /> Connecting...
              </>
            ) : (
              'Connect'
            )}
          </Button>
        </Form>
      </Card.Body>
    </Card>
  );
}

export default ConnectForm;
