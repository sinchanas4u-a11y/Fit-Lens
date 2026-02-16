
import requests
import base64
import json
import os
import cv2
import numpy as np

# Create a dummy image (black square)
img = np.zeros((100, 100, 3), dtype=np.uint8)
# Draw a "person" (white rectangle)
cv2.rectangle(img, (40, 20), (60, 80), (255, 255, 255), -1)
ret, buffer = cv2.imencode('.png', img)
img_base64 = "data:image/png;base64," + base64.b64encode(buffer).decode('utf-8')

# Manual landmarks
payload = {
    "user_height": 180,
    "front_image": img_base64,
    "side_image": None,
    "front_landmarks": [
        {
            "type": "shoulder",
            "label": "Shoulder Width",
            "points": [
                {"x": 40, "y": 30, "x_norm": 0.4, "y_norm": 0.3},
                {"x": 60, "y": 30, "x_norm": 0.6, "y_norm": 0.3}
            ]
        }
    ]
}

try:
    print("Sending request to http://localhost:5001/api/process-manual")
    response = requests.post("http://localhost:5001/api/process-manual", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("Success!")
        print(f"Mode: {data.get('mode')}")
        
        if 'front' in data['results']:
            front = data['results']['front']
            print(f"Scale Factor: {front.get('scale_factor')}")
            print(f"Height px: {front.get('height_px')}")
            
            measurements = front.get('measurements', {})
            print(f"Measurements: {json.dumps(measurements, indent=2)}")
            
            if measurements.get('shoulder'):
                val_cm = measurements['shoulder']['value_cm']
                val_px = measurements['shoulder']['value_px']
                print(f"Shoulder Width: {val_cm} cm (from {val_px} px)")
                
                # Check if visualization exists
                if front.get('visualization'):
                    print("Visualization image present (base64)")
                else:
                    print("Visualization image MISSING")
            else:
                print("Shoulder measurement missing")
        else:
            print("Front results missing")
            
    else:
        print(f"Failed with status {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Test failed: {e}")
