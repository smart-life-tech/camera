# Smart Camera Editor

A web-based image editor for Raspberry Pi cameras that offloads the processing-intensive editing tasks to the client's browser.

## Features

- Connect to your Raspberry Pi camera server
- View and download captured images
- Edit images with professional tools:
  - Adjust brightness, contrast, saturation, exposure, highlights, and shadows
  - Apply effects like grayscale, sepia, and vintage
  - Rotate images
  - Save edited images back to the camera
- Configure WiFi settings
- Control camera system (reboot/shutdown)

## Setup

### Prerequisites

- Node.js and npm
- A Raspberry Pi running the camera server (picServing2.py)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   npm install
   ```
3. Start the development server:
   ```
   npm start
   ```

### Deployment

This application is ready to deploy to Vercel:

```
vercel
```

## Usage

1. Enter your Raspberry Pi's IP address and port (default: 5000)
2. Connect to the camera
3. Browse, capture, and edit images
4. Download edited images or save them back to the camera

## Technologies Used

- React.js
- Bootstrap
- Canvas API for image editing
- Axios for HTTP requests
```

## Step 8: Configure the package.json for Vercel deployment

Update your `package.json` file to include the necessary scripts and dependencies:

```json:package.json
{
  "name": "camera-editor",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@fortawesome/fontawesome-svg-core": "^6.4.0",
    "@fortawesome/free-solid-svg-icons": "^6.4.0",
    "@fortawesome/react-fontawesome": "^0.2.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "axios": "^1.4.0",
    "bootstrap": "^5.3.0",
    "react": "^18.2.0",
    "react-bootstrap": "^2.8.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
