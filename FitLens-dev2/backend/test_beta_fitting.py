import requests
import base64
import os
import json

def test_process():
    url = "http://127.0.0.1:5001/api/process"
    
    # Use existing images from measurement_images
    img_dir = "measurement_images"
    front_img_path = os.path.join(img_dir, "20260215_113356_047677_upload_front.png")
    side_img_path = os.path.join(img_dir, "20260215_113356_200342_upload_side.png")
    
    if not os.path.exists(front_img_path):
        print(f"Error: {front_img_path} not found")
        return

    with open(front_img_path, "rb") as f:
        front_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    side_b64 = None
    if os.path.exists(side_img_path):
        with open(side_img_path, "rb") as f:
            side_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "front_image": front_b64,
        "side_image": side_b64,
        "user_height": 175.0,
        "height_unit": "cm",
        "gender": "neutral"
    }
    
    print("Sending request to /api/process...")
    try:
        response = requests.post(url, json=payload, timeout=300)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            # Check for betas_fitted in metadata
            if 'mesh_data' in result and result['mesh_data']:
                meta = result['mesh_data'].get('metadata', {})
                print(f"Betas fitted: {meta.get('betas_fitted')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_process()
