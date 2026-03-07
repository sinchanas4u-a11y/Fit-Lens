import requests
import base64
import os
import time

def test_duplicate_upload():
    print("Testing Duplicate Upload Prevention...")
    
    # 1. Start the app in the background (assumed running locally on port 5000)
    # 2. Check current number of lines in metadata.jsonl
    metadata_path = "backend/measurement_images/metadata.jsonl"
    
    def count_lines():
        if not os.path.exists(metadata_path):
            return 0
        with open(metadata_path, 'r') as f:
            return sum(1 for line in f if line.strip())

    initial_lines = count_lines()
    print(f"Initial lines in metadata.jsonl: {initial_lines}")

    # Create dummy images and convert to base64
    # We will use small black squares
    import cv2
    import numpy as np
    
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.png', dummy_img)
    b64_str = "data:image/png;base64," + base64.b64encode(buffer).decode('utf-8')

    payload = {
        "front_image": b64_str,
        "side_image": b64_str, # Use same for side for simplicity
        "user_height": 170
    }

    url = "http://127.0.0.1:5001/api/process"
    
    print("\nSending first request (should save)...")
    try:
        r1 = requests.post(url, json=payload)
        print(f"Status: {r1.status_code}")
    except Exception as e:
        print(f"Error connecting to server. Is app_updated.py running? {e}")
        return

    time.sleep(1) # Wait for file write
    
    lines_after_first = count_lines()
    print(f"Lines in metadata.jsonl after first request: {lines_after_first}")
    
    if lines_after_first <= initial_lines:
        print("Wait, did it even save the first time? Check server logs.")

    print("\nSending second request (EXACT SAME IMAGES, should NOT save)...")
    r2 = requests.post(url, json=payload)
    print(f"Status: {r2.status_code}")
    
    time.sleep(1) # Wait in case it was written

    lines_after_second = count_lines()
    print(f"Lines in metadata.jsonl after second request: {lines_after_second}")
    
    if lines_after_second > lines_after_first:
        print("FAIL: Duplicate images were saved!")
    else:
        print("SUCCESS: Duplicate images were NOT saved!")

if __name__ == "__main__":
    test_duplicate_upload()
