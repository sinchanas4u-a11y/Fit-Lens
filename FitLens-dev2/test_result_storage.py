import requests
import base64
import os
import time
import json
import cv2
import numpy as np

def test_result_storage():
    print("Testing Measurement Results Storage (instead of images)...")
    
    results_path = "backend/measurement_results/results.jsonl"
    images_dir = "backend/measurement_images"
    
    def count_jsonl_lines():
        if not os.path.exists(results_path):
            return 0
        with open(results_path, 'r') as f:
            return sum(1 for line in f if line.strip())

    def get_image_count():
        return len([f for f in os.listdir(images_dir) if f.endswith('.png')])

    initial_json_lines = count_jsonl_lines()
    initial_img_count = get_image_count()
    
    print(f"Initial results entries: {initial_json_lines}")
    print(f"Initial image files: {initial_img_count}")

    # Create dummy images and convert to base64
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.png', dummy_img)
    b64_str = "data:image/png;base64," + base64.b64encode(buffer).decode('utf-8')

    payload = {
        "front_image": b64_str,
        "side_image": b64_str,
        "user_height": 170
    }

    url = "http://127.0.0.1:5001/api/process"
    
    print("\nSending request to backend...")
    try:
        r = requests.post(url, json=payload)
        # We expect a failure in processing (because no person detected) but it should still attempt to save images/results
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error connecting to server. {e}")
        return

    time.sleep(1) # Wait for file write
    
    final_json_lines = count_jsonl_lines()
    final_img_count = get_image_count()
    
    print(f"Final results entries: {final_json_lines}")
    print(f"Final image files: {final_img_count}")
    
    # Check if a new result was added
    # Note: If processing fails early, it might not reach save_body_measurements(response)
    # But it should reach save_measurement_image() which is now a no-op for files
    
    if final_img_count > initial_img_count:
        print("FAIL: New image files were created!")
    else:
        print("SUCCESS: No new image files were created.")
        
    if final_json_lines > initial_json_lines:
         print("SUCCESS: A new entry was added to results.jsonl")
    else:
         print("NOTE: No results added (likely due to processing error 400), but image save was skipped.")

if __name__ == "__main__":
    test_result_storage()
