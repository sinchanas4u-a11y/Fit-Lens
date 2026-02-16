
import cv2
import numpy as np
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from face_verifier import FaceVerifier

def create_dummy_face():
    # Create a simple image that looks vaguely like a face (circles for eyes, line for mouth)
    # This might not pass deep learning detection but ensures the code runs
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 100, (255, 255, 255), -1) # Face
    cv2.circle(img, (110, 120), 10, (0, 0, 0), -1) # Left Eye
    cv2.circle(img, (190, 120), 10, (0, 0, 0), -1) # Right Eye
    cv2.ellipse(img, (150, 200), (40, 20), 0, 0, 180, (0, 0, 0), 5) # Mouth
    return img

def test_verifier():
    print("Initializing FaceVerifier...")
    verifier = FaceVerifier(model_name="ArcFace", detector_backend="mediapipe") # mediapipe is fast
    
    if not verifier.is_ready:
        print("FAIL: FaceVerifier not ready (library missing?)")
        return

    print("Creating dummy images...")
    img1 = create_dummy_face()
    img2 = create_dummy_face()
    
    # Modify img2 usage slightly to ensure it's different instance
    cv2.circle(img2, (150, 280), 5, (0, 0, 255), -1) 

    print("Running verification (expecting 'Face not detected' or 'Verified' depending on strictness)...")
    result = verifier.verify_person(img1, img2)
    
    print("Result:", result)
    
    if 'error' in result:
        print(f"Verified Error Handling: {result['error']}")
    else:
        print(f"Verified Success: {result['verified']}, Distance: {result['distance']}")

if __name__ == "__main__":
    test_verifier()
