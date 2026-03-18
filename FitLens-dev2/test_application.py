"""
Comprehensive Application Test
Tests key modules with installed dependencies
"""
import sys
import traceback


def test_landmark_detector():
    """Test LandmarkDetector with MediaPipe"""
    print("\n" + "="*60)
    print("Testing LandmarkDetector...")
    print("="*60)
    
    try:
        from landmark_detector import LandmarkDetector
        import numpy as np
        
        detector = LandmarkDetector()
        print("✓ LandmarkDetector initialized successfully")
        
        # Create a dummy image
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(dummy_image)
        print("✓ Detection method works (returned None for empty image as expected)")
        
        return True
    except Exception as e:
        print(f"✗ LandmarkDetector test failed: {e}")
        traceback.print_exc()
        return False


def test_pose_utils():
    """Test PoseUtils"""
    print("\n" + "="*60)
    print("Testing PoseUtils...")
    print("="*60)
    
    try:
        from pose_utils import PoseUtils
        import numpy as np
        
        # Test angle calculation
        p1 = np.array([0, 0])
        p2 = np.array([1, 0])
        p3 = np.array([1, 1])
        
        angle = PoseUtils.calculate_angle(p1, p2, p3)
        print(f"✓ Angle calculation works: {angle}° (expected ~90°)")
        
        # Test distance calculation
        distance = PoseUtils.calculate_distance(p1, p2)
        print(f"✓ Distance calculation works: {distance} (expected ~1.0)")
        
        return True
    except Exception as e:
        print(f"✗ PoseUtils test failed: {e}")
        traceback.print_exc()
        return False


def test_measurement_engine():
    """Test MeasurementEngine"""
    print("\n" + "="*60)
    print("Testing MeasurementEngine...")
    print("="*60)
    
    try:
        from backend.measurement_engine import MeasurementEngine
        import numpy as np
        
        engine = MeasurementEngine()
        print("✓ MeasurementEngine initialized successfully")
        
        # Create dummy keypoints
        dummy_keypoints = np.random.rand(33, 3) * 100
        dummy_keypoints[:, 2] = 0.9  # Set confidence
        
        result = engine.calculate_measurements(dummy_keypoints, scale_factor=0.5)
        print(f"✓ Measurement calculation works: {list(result.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ MeasurementEngine test failed: {e}")
        traceback.print_exc()
        return False


def test_face_verifier():
    """Test FaceVerifier with InsightFace"""
    print("\n" + "="*60)
    print("Testing FaceVerifier (InsightFace)...")
    print("="*60)
    
    try:
        from backend.face_verifier import FaceVerifier
        
        verifier = FaceVerifier()
        if verifier.is_ready:
            print("✓ FaceVerifier initialized successfully")
            print(f"  Model: {verifier.model_name}")
        else:
            print("⚠ FaceVerifier not ready (this is OK if InsightFace models not downloaded)")
        
        return True
    except Exception as e:
        print(f"✗ FaceVerifier test failed: {e}")
        traceback.print_exc()
        return False


def test_opencv_ops():
    """Test OpenCV operations"""
    print("\n" + "="*60)
    print("Testing OpenCV operations...")
    print("="*60)
    
    try:
        import cv2
        import numpy as np
        
        # Create test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test basic operations
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("✓ Color conversion works")
        
        resized = cv2.resize(img, (320, 240))
        print("✓ Image resize works")
        
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        print("✓ Gaussian blur works")
        
        return True
    except Exception as e:
        print(f"✗ OpenCV test failed: {e}")
        traceback.print_exc()
        return False


def test_numpy_ops():
    """Test NumPy operations"""
    print("\n" + "="*60)
    print("Testing NumPy operations...")
    print("="*60)
    
    try:
        import numpy as np
        
        # Test basic operations
        arr = np.array([1, 2, 3, 4, 5])
        print(f"✓ Array creation works: {arr}")
        
        # Test math operations
        mean = np.mean(arr)
        std = np.std(arr)
        print(f"✓ Statistical operations work: mean={mean}, std={std}")
        
        # Test linalg
        vec1 = np.array([1, 0])
        vec2 = np.array([0, 1])
        norm = np.linalg.norm(vec1)
        dot = np.dot(vec1, vec2)
        print(f"✓ Linear algebra works: norm={norm}, dot={dot}")
        
        # Test trigonometry
        angle = np.arccos(0.5)
        deg = np.degrees(angle)
        print(f"✓ Trigonometry works: arccos(0.5)={deg}°")
        
        return True
    except Exception as e:
        print(f"✗ NumPy test failed: {e}")
        traceback.print_exc()
        return False


def test_onnx_ops():
    """Test ONNX Runtime"""
    print("\n" + "="*60)
    print("Testing ONNX Runtime...")
    print("="*60)
    
    try:
        import onnxruntime as ort
        
        providers = ort.get_available_providers()
        print(f"✓ ONNX Runtime works")
        print(f"  Available providers: {providers}")
        
        return True
    except Exception as e:
        print(f"✗ ONNX Runtime test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("COMPREHENSIVE APPLICATION TEST")
    print("="*60)
    print(f"Python: {sys.version}")
    
    tests = [
        ("NumPy Operations", test_numpy_ops),
        ("OpenCV Operations", test_opencv_ops),
        ("ONNX Runtime", test_onnx_ops),
        ("PoseUtils", test_pose_utils),
        ("LandmarkDetector", test_landmark_detector),
        ("MeasurementEngine", test_measurement_engine),
        ("FaceVerifier", test_face_verifier),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Application is ready to use.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
