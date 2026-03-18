import requests
import base64
import numpy as np
import cv2
import os

# Create dummy white image
img = np.ones((100, 100, 3), dtype=np.uint8) * 255
_, buffer = cv2.imencode('.png', img)
img_base64 = "data:image/png;base64," + base64.b64encode(buffer).decode('utf-8')

payload = {
    "front_image": img_base64,
    "side_image": img_base64,
    "user_height": 170
}

print("Sending request to http://localhost:5001/api/process...")
try:
    response = requests.post("http://localhost:5001/api/process", json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print("Response:", response.json().keys())
    else:
        print("Error:", response.text)
except Exception as e:
    print("Request failed:", e)

# Check if directory exists
images_dir = "measurement_images"
if os.path.exists(images_dir):
    print(f"\nChecked '{images_dir}': Exists")
    files = os.listdir(images_dir)
    print(f"Files in directory ({len(files)}):")
    for f in files:
        print(f" - {f}")
else:
    print(f"\nChecked '{images_dir}': DOES NOT EXIST")
