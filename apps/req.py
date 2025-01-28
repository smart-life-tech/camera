# write_to_api.py
import requests

url = 'https://christlight.pythonanywhere.com/write'
data = {'content': 'Hello from Pi 1'}
response = requests.post(url, json=data)
print(response.json().get('message'))

url = 'https://christlight.pythonanywhere.com/read'
response = requests.get(url)
print(response.json().get('content'))