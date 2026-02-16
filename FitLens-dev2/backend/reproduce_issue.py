import requests
import json

url = 'http://localhost:5001/api/process-manual'

payload = {
  "user_height": 180,
  "front_landmarks": {
    "landmarks": [
      {
        "type": "shoulder",
        "label": "Shoulder Width",
        "points": [
          {"x": 100, "y": 100},
          {"x": 200, "y": 100}
        ]
      }
    ],
    "imageWidth": 1000,
    "imageHeight": 1000
  },
  "side_landmarks": None
}

headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
