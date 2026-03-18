"""
Simple test for upload processing
"""
import cv2
import numpy as np
from landmark_detector import LandmarkDetector
from measurement_engine import MeasurementEngine
from reference_detector import ReferenceDetector

print("=" * 60)
print("Testing Upload Processing")
print("=" * 60)

# Test 1: Create a simple test image
print("\n1. Creating test image...")
test_img = np.ones((720, 1280, 3), dtype=np.uint8) * 200
print(f"   Test image shape: {test_img.shape}")

# Test 2: Initialize detectors
print("\n2. Initializing detectors...")
try:
    landmark_detector = LandmarkDetector()
    print("   ✓ Landmark detector initialized")
except Exception as e:
    print(f"   ✗ Landmark detector failed: {e}")
    exit(1)

try:
    measurement_engine = MeasurementEngine()
    print("   ✓ Measurement engine initialized")
except Exception as e:
    print(f"   ✗ Measurement engine failed: {e}")
    exit(1)

try:
    reference_detector = ReferenceDetector()
    print("   ✓ Reference detector initialized")
except Exception as e:
    print(f"   ✗ Reference detector failed: {e}")
    exit(1)

# Test 3: Test landmark detection
print("\n3. Testing landmark detection...")
landmarks = landmark_detector.detect(test_img)
print(f"   Landmarks detected: {landmarks is not None}")
if landmarks is not None:
    print(f"   Number of landmarks: {len(landmarks)}")
else:
    print("   Note: No person in test image (expected)")

# Test 4: Test with real image (if you have one)
print("\n4. Testing with real image...")
print("   Please provide path to a full-body photo:")
print("   (Press Enter to skip)")

image_path = input("   Path: ").strip()

if image_path and image_path != "":
    try:
        real_img = cv2.imread(image_path)
        if real_img is None:
            print(f"   ✗ Could not load image: {image_path}")
        else:
            print(f"   ✓ Image loaded: {real_img.shape}")
            
            # Detect landmarks
            landmarks = landmark_detector.detect(real_img)
            print(f"   Landmarks detected: {landmarks is not None}")
            
            if landmarks is not None:
                print(f"   Number of landmarks: {len(landmarks)}")
                
                # Calculate measurements
                scale_factor = 0.066  # Example scale
                measurements = measurement_engine.calculate_measurements_with_confidence(
                    landmarks, scale_factor, 'front'
                )
                
                print(f"   Measurements calculated: {len(measurements)}")
                
                if measurements:
                    print("\n   Measurements:")
                    for name, val in measurements.items():
                        cm_value, confidence, source = val
                        print(f"     {name}: {cm_value:.2f} cm (confidence: {confidence:.2f})")
                else:
                    print("   ✗ No measurements calculated")
                    print("   Possible reasons:")
                    print("     - Required landmarks not visible")
                    print("     - Person not facing camera")
                    print("     - Arms not visible")
            else:
                print("   ✗ No person detected in image")
                print("   Possible reasons:")
                print("     - Image too dark")
                print("     - Person not clearly visible")
                print("     - Image quality too low")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
print("\nIf landmarks were detected but no measurements:")
print("  - Ensure full body is visible (head to feet)")
print("  - Person should face camera")
print("  - Arms should be visible")
print("  - Good lighting")
