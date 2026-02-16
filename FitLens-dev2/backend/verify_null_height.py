import requests
import json

url = 'http://localhost:5001/api/process-manual'

payload = {
  "user_height": None,
  "front_landmarks": {"landmarks": []}
}

print("Sending payload with user_height: None")
try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
