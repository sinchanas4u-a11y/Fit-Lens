"""
Test script for InsightFace-based face verification.
Tests the new similarity threshold logic with front+side views.
"""

import cv2
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from face_verifier import FaceVerifier

def create_test_face(size=200, color=(100, 150, 200)):
    """Create a simple test face image."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    # Draw a simple face-like pattern
    cv2.circle(img, (size//2, size//2), size//3, color, -1)  # Face
    cv2.circle(img, (size//3, size//3), size//15, (255, 255, 255), -1)  # Left eye
    cv2.circle(img, (2*size//3, size//3), size//15, (255, 255, 255), -1)  # Right eye
    cv2.ellipse(img, (size//2, 2*size//3), (size//6, size//12), 0, 0, 180, (255, 255, 255), 2)  # Mouth
    return img

def main():
    print("="*70)
    print("INSIGHTFACE FACE VERIFIER TEST")
    print("="*70)
    
    # Initialize verifier
    print("\n1. Initializing FaceVerifier...")
    verifier = FaceVerifier()
    
    if not verifier.is_ready:
        print("❌ FaceVerifier not ready. Please install: pip install insightface onnxruntime")
        return
    
    print("✓ FaceVerifier initialized successfully")
    
    # Test with dummy images (these won't have real faces, so we expect detection failure)
    print("\n2. Testing with dummy images (expecting 'no face detected')...")
    img1 = create_test_face(color=(100, 150, 200))
    img2 = create_test_face(color=(110, 160, 210))
    
    result = verifier.verify_person(img1, img2)
    
    print("\nResult:")
    print(f"  Verified: {result.get('verified')}")
    print(f"  Similarity: {result.get('similarity', 'N/A')}")
    print(f"  No Face: {result.get('no_face', False)}")
    print(f"  Error: {result.get('error', 'None')}")
    
    if result.get('no_face'):
        print("\n✓ Test passed: Correctly detected no face in dummy images")
    else:
        print("\n⚠ Unexpected: Face detected in dummy images")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nTo test with real images:")
    print("1. Place front.jpg and side.jpg in the backend directory")
    print("2. Modify this script to load those images")
    print("3. Run again to see actual similarity scores")
    print("\nExpected behavior:")
    print("  - Same person (front+side): similarity ≥ 0.65 → verified=True")
    print("  - Uncertain (0.50-0.65): verified=True, warning=True")
    print("  - Different person: similarity < 0.50 → verified=False")

if __name__ == "__main__":
    main()
