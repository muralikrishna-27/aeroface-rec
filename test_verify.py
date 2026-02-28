import requests
import json

payload = {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
    "lounge_id": "00000000-0000-0000-0000-000000000000"
}

try:
    response = requests.post("http://127.0.0.1:8000/verify", json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
