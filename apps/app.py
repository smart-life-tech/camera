from flask import Flask, request, jsonify, render_template
import json
import os
from flask_cors import CORS, cross_origin
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['CORS_HEADERS'] = 'Content-Type'

# Data file paths
DATA_FILE = 'json.txt'
METRICS_FILE = 'metrics_data.json'
WIFI_CREDENTIALS_FILE = 'wifi_credentials.json'
def load_data(file_path=DATA_FILE):
    """Load the database from the file (or return an empty dict if file not found)."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Error reading file {file_path}:", e)
                return {}
    return {}

def save_data(data, file_path=DATA_FILE):
    """Save the given data dictionary to the file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# API Route: Write data via JSON POST
@app.route('/writejson', methods=['POST'])
@cross_origin()
def write_json_file():
    # Attempt to parse JSON from the request
    data_in = request.get_json(force=True, silent=True)
    if not data_in:
        return jsonify({"message": "No JSON data received"}), 400

    watch_number = data_in.get('watch_number')
    if not watch_number:
        return jsonify({"message": "Missing 'watch_number' in JSON data"}), 400

    data = load_data()
    data[watch_number] = data_in
    save_data(data)
    return jsonify({"message": "Data written successfully!"})

# API Route: Read data for a specific watch number
@app.route('/readjson/<watch_number>', methods=['GET'])
@cross_origin()
def read_by_watch_number(watch_number):
    data = load_data()
    record = data.get(watch_number)
    if record is None:
        return jsonify({"message": "Record not found"}), 404
    return jsonify(record)

@app.route('/write', methods=['POST'])
def write_file():
    data = request.json
    content = data.get('content')
    with open('example.txt', 'w') as file:
        file.write(content)
    return jsonify({"message": "File written successfully!"})

@app.route('/read', methods=['GET'])
def read_file():
    with open('example.txt', 'r') as file:
        content = file.read()
    return jsonify({"content": content})

# New routes for metrics data

# API Route: Submit metrics data
@app.route('/metrics/submit', methods=['POST'])
@cross_origin()
def submit_metrics():
    try:
        data_in = request.get_json(force=True, silent=True)
        if not data_in:
            return jsonify({"message": "No JSON data received"}), 400

        # Generate a unique ID for this metrics entry
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        device_id = data_in.get('device_id', 'unknown')
        metrics_id = f"{device_id}_{timestamp}"

        # Load existing metrics data
        metrics_data = load_data(METRICS_FILE)

        # Add new metrics data with timestamp
        data_in['timestamp'] = timestamp
        metrics_data[metrics_id] = data_in

        # Save updated metrics data
        save_data(metrics_data, METRICS_FILE)

        return jsonify({
            "message": "Metrics data submitted successfully!",
            "id": metrics_id
        })
    except Exception as e:
        return jsonify({"message": f"Error submitting metrics: {str(e)}"}), 500

# API Route: Get all metrics data
@app.route('/metrics', methods=['GET'])
@cross_origin()
def get_all_metrics():
    metrics_data = load_data(METRICS_FILE)
    return jsonify(metrics_data)

# API Route: Get metrics for a specific device
@app.route('/metrics/device/<device_id>', methods=['GET'])
@cross_origin()
def get_device_metrics(device_id):
    metrics_data = load_data(METRICS_FILE)
    device_metrics = {k: v for k, v in metrics_data.items() if v.get('device_id') == device_id}

    if not device_metrics:
        return jsonify({"message": f"No metrics found for device {device_id}"}), 404

    return jsonify(device_metrics)

# API Route: Get latest metrics for a device
@app.route('/metrics/latest/<device_id>', methods=['GET'])
@cross_origin()
def get_latest_device_metrics(device_id):
    metrics_data = load_data(METRICS_FILE)

    # Filter metrics for this device
    device_metrics = {k: v for k, v in metrics_data.items() if v.get('device_id') == device_id}

    if not device_metrics:
        return jsonify({"message": f"No metrics found for device {device_id}"}), 404

    # Find the latest entry based on timestamp
    latest_key = max(device_metrics.keys(), key=lambda k: device_metrics[k].get('timestamp', ''))
    latest_metrics = device_metrics[latest_key]

    return jsonify(latest_metrics)

# API Route: Get metrics within a date range
@app.route('/metrics/range', methods=['GET'])
@cross_origin()
def get_metrics_by_date_range():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    device_id = request.args.get('device_id')

    if not start_date or not end_date:
        return jsonify({"message": "Missing start or end date parameters"}), 400

    metrics_data = load_data(METRICS_FILE)

    # Filter by date range and optionally by device
    filtered_metrics = {}
    for key, value in metrics_data.items():
        timestamp = value.get('timestamp', '')
        if start_date <= timestamp <= end_date:
            if device_id is None or value.get('device_id') == device_id:
                filtered_metrics[key] = value

    if not filtered_metrics:
        return jsonify({"message": "No metrics found for the specified criteria"}), 404

    return jsonify(filtered_metrics)

# API Route: Delete metrics data
@app.route('/metrics/delete/<metrics_id>', methods=['DELETE'])
@cross_origin()
def delete_metrics(metrics_id):
    metrics_data = load_data(METRICS_FILE)

    if metrics_id not in metrics_data:
        return jsonify({"message": f"Metrics ID {metrics_id} not found"}), 404

    del metrics_data[metrics_id]
    save_data(metrics_data, METRICS_FILE)

    return jsonify({"message": f"Metrics ID {metrics_id} deleted successfully"})

# API Route: Get current POS data
@app.route('/metrics/current', methods=['GET'])
@cross_origin()
def get_current_pos_data():
    try:
        current_pos_file = 'current_pos_data.json'
        if not os.path.exists(current_pos_file):
            return jsonify({"message": "Current POS data file not found"}), 404

        with open(current_pos_file, 'r') as f:
            current_data = json.load(f)

        return jsonify(current_data)
    except Exception as e:
        return jsonify({"message": f"Error reading current POS data: {str(e)}"}), 500
@app.route('/wifi/save', methods=['POST'])
def save_wifi_credentials():
    """
    API endpoint to save WiFi credentials to the database
    Expected JSON format: {"ssid": "network_name", "password": "network_password"}
    """
    try:
        data = request.json

        # Validate input
        if not data or 'ssid' not in data or 'password' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required fields: ssid and password"
            }), 400

        ssid = data['ssid']
        password = data['password']


        # Also save to a JSON file as backup
        credentials = {
            "ssid": ssid,
            "password": password
        }

        #with open('wifi_credentials.json', 'w') as f:
        #   json.dump(credentials, f)
        #content = data.get('content')
        with open('wifi_credentials.json', 'w') as file:
            file.write(json.dumps(credentials))

        return jsonify({
            "success": True,
            "message": "WiFi credentials saved successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error retrieving WiFi credentials: {str(e)}"
        }), 500
@app.route('/wifi/latest', methods=['GET'])
def get_latest_wifi():
    """
    API endpoint to retrieve the latest WiFi credentials
    """
    try:
        if os.path.exists(WIFI_CREDENTIALS_FILE):
            with open(WIFI_CREDENTIALS_FILE, 'r') as file:
                credentials = json.load(file)

            return jsonify({
                "success": True,
                "data": {
                    "ssid": credentials.get('ssid'),
                    "password": credentials.get('password')
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "No WiFi credentials found"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error retrieving WiFi credentials: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)