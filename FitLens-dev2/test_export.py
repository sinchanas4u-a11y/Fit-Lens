import requests
import json
import os

def test_export():
    print("Testing Measurement Export Endpoints...")
    
    url_base = "http://127.0.0.1:5001/api/download/"
    
    # Dummy results data
    payload = {
        "user_id": "Test_User_123",
        "calibration": {
            "user_height_cm": 175.5
        },
        "results": {
            "front": {
                "success": True,
                "measurements": {
                    "waist": {"value_cm": 85.2, "confidence": 0.92, "source": "MediaPipe"},
                    "hips": {"value_cm": 98.4, "confidence": 0.89, "source": "MediaPipe"}
                }
            },
            "side": {
                "success": True,
                "measurements": {
                    "chest": {"value_cm": 102.1, "confidence": 0.85, "source": "MediaPipe"}
                }
            }
        }
    }

    formats = ["pdf", "docx", "xml"]
    
    for fmt in formats:
        url = url_base + fmt
        print(f"\nRequesting {fmt.upper()} export from {url}...")
        try:
            response = requests.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type')
                content_disposition = response.headers.get('Content-Disposition')
                file_size = len(response.content)
                
                print(f"✓ Content-Type: {content_type}")
                print(f"✓ Content-Disposition: {content_disposition}")
                print(f"✓ File Size: {file_size} bytes")
                
                # Save the file locally for manual check
                filename = f"test_export_result.{fmt}"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✓ Saved to {filename}")
            else:
                print(f"✗ Failed to export {fmt}: {response.text}")
                
        except Exception as e:
            print(f"✗ Error testing {fmt}: {e}")

if __name__ == "__main__":
    test_export()
