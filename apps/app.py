from flask import Flask, request, jsonify

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

if __name__ == '__main__':
    app.run(debug=True, port=8080)
