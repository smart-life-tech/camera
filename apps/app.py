from flask import Flask, request, jsonify
import json
app = Flask(__name__)

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
            "message": f"Error saving WiFi credentials: {str(e)}"
        }), 500
        
        
if __name__ == '__main__':
    app.run(debug=True, port=8080)
