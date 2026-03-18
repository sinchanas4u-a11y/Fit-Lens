import requests
import json

url = 'http://localhost:5001/api/process-manual'

test_cases = [
    {
        "name": "Invalid user_height (string)",
        "payload": {
            "user_height": "invalid",
            "front_landmarks": {"landmarks": []}
        }
    },
    {
        "name": "front_landmarks as list",
        "payload": {
            "user_height": 180,
            "front_landmarks": []  # Should be dict or None
        }
    },
    {
        "name": "front_landmarks missing keys",
        "payload": {
            "user_height": 180,
            "front_landmarks": {"landmarks": [{"type": "test"}]}  # Missing 'points'
        }
    },
    {
        "name": "Points missing x/y",
        "payload": {
            "user_height": 180,
            "front_landmarks": {
                "landmarks": [{
                    "type": "test", 
                    "points": [{"x": 10}, {"y": 20}]
                }]
            }
        }
    },
     {
        "name": "Points as None",
        "payload": {
            "user_height": 180,
            "front_landmarks": {
                "landmarks": [{
                    "type": "test", 
                    "points": None
                }]
            }
        }
    }
]

for test in test_cases:
    print(f"\nTesting: {test['name']}")
    try:
        response = requests.post(url, json=test['payload'])
        print(f"Status: {response.status_code}")
        if response.status_code == 500:
            print("Response:", response.text)
    except Exception as e:
        print(f"Request Error: {e}")
