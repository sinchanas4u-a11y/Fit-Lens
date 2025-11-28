"""
Test camera functionality
"""
import cv2

print("Testing camera...")

# Try to open camera
camera = cv2.VideoCapture(0)

if camera.isOpened():
    print("✓ Camera opened successfully")
    
    # Try to read a frame
    ret, frame = camera.read()
    
    if ret:
        print(f"✓ Frame captured: {frame.shape}")
        print("Camera is working!")
    else:
        print("✗ Failed to capture frame")
else:
    print("✗ Failed to open camera")
    print("Possible issues:")
    print("  - Camera is being used by another application")
    print("  - Camera permissions not granted")
    print("  - No camera connected")

camera.release()
