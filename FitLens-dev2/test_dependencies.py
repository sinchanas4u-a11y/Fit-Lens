"""
Test script to verify all dependencies are correctly installed.
"""

def test_imports():
    """Test if all required packages can be imported"""
    results = []
    
    # Test MediaPipe
    try:
        import mediapipe as mp
        version = mp.__version__
        results.append(("mediapipe", version, "✓"))
    except Exception as e:
        results.append(("mediapipe", str(e), "✗"))
    
    # Test Protobuf
    try:
        import google.protobuf
        version = google.protobuf.__version__
        results.append(("protobuf", version, "✓"))
    except Exception as e:
        results.append(("protobuf", str(e), "✗"))
    
    # Test ONNX Runtime
    try:
        import onnxruntime as ort
        version = ort.__version__
        results.append(("onnxruntime", version, "✓"))
    except Exception as e:
        results.append(("onnxruntime", str(e), "✗"))
    
    # Test ONNX
    try:
        import onnx
        version = onnx.__version__
        results.append(("onnx", version, "✓"))
    except Exception as e:
        results.append(("onnx", str(e), "✗"))
    
    # Test OpenCV
    try:
        import cv2
        version = cv2.__version__
        results.append(("opencv-python", version, "✓"))
    except Exception as e:
        results.append(("opencv-python", str(e), "✗"))
    
    # Test NumPy
    try:
        import numpy as np
        version = np.__version__
        results.append(("numpy", version, "✓"))
    except Exception as e:
        results.append(("numpy", str(e), "✗"))
    
    # Test Ultralytics
    try:
        import ultralytics
        version = ultralytics.__version__
        results.append(("ultralytics", version, "✓"))
    except Exception as e:
        results.append(("ultralytics", str(e), "✗"))
    
    # Test InsightFace
    try:
        import insightface
        version = insightface.__version__
        results.append(("insightface", version, "✓"))
    except Exception as e:
        results.append(("insightface", str(e), "✗"))
    
    return results


def test_functionality():
    """Test basic functionality of key libraries"""
    print("\n" + "="*60)
    print("TESTING BASIC FUNCTIONALITY")
    print("="*60)
    
    # Test NumPy
    try:
        import numpy as np
        arr = np.array([1, 2, 3])
        print("✓ NumPy: Array creation successful")
    except Exception as e:
        print(f"✗ NumPy: {e}")
    
    # Test OpenCV
    try:
        import cv2
        img = cv2.imread("test.jpg")  # This will fail if file doesn't exist, but import works
        print("✓ OpenCV: Import successful")
    except Exception as e:
        print(f"✗ OpenCV: {e}")
    
    # Test MediaPipe
    try:
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        print("✓ MediaPipe: Pose solution accessible")
    except Exception as e:
        print(f"✗ MediaPipe: {e}")
    
    # Test ONNX Runtime
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        print(f"✓ ONNX Runtime: Available providers: {providers}")
    except Exception as e:
        print(f"✗ ONNX Runtime: {e}")
    
    # Test InsightFace
    try:
        import insightface
        from insightface.app import FaceAnalysis
        print("✓ InsightFace: FaceAnalysis class accessible")
    except Exception as e:
        print(f"✗ InsightFace: {e}")


if __name__ == "__main__":
    print("="*60)
    print("DEPENDENCY VERSION CHECK")
    print("="*60)
    
    results = test_imports()
    
    for package, version, status in results:
        print(f"{status} {package}: {version}")
    
    # Test functionality
    test_functionality()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    success_count = sum(1 for _, _, status in results if status == "✓")
    total_count = len(results)
    print(f"Successfully imported: {success_count}/{total_count} packages")
    
    if success_count == total_count:
        print("\n✓ All dependencies are correctly installed!")
    else:
        print("\n⚠ Some dependencies failed to import. Please check the errors above.")
