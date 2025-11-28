"""
Test YOLOv8 + MediaPipe Setup
Verifies that all dependencies are installed correctly
"""
import sys

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...\n")
    
    results = {}
    
    # Test OpenCV
    try:
        import cv2
        print(f"✓ OpenCV: {cv2.__version__}")
        results['opencv'] = True
    except ImportError as e:
        print(f"✗ OpenCV: Not installed - {e}")
        results['opencv'] = False
    
    # Test NumPy
    try:
        import numpy as np
        print(f"✓ NumPy: {np.__version__}")
        results['numpy'] = True
    except ImportError as e:
        print(f"✗ NumPy: Not installed - {e}")
        results['numpy'] = False
    
    # Test MediaPipe
    try:
        import mediapipe as mp
        print(f"✓ MediaPipe: {mp.__version__}")
        results['mediapipe'] = True
    except ImportError as e:
        print(f"✗ MediaPipe: Not installed - {e}")
        results['mediapipe'] = False
    
    # Test Ultralytics (YOLOv8)
    try:
        import ultralytics
        print(f"✓ Ultralytics (YOLOv8): {ultralytics.__version__}")
        results['ultralytics'] = True
    except ImportError as e:
        print(f"✗ Ultralytics (YOLOv8): Not installed - {e}")
        results['ultralytics'] = False
    
    # Test PIL
    try:
        from PIL import Image
        print(f"✓ Pillow: {Image.__version__}")
        results['pillow'] = True
    except ImportError as e:
        print(f"✗ Pillow: Not installed - {e}")
        results['pillow'] = False
    
    return results


def test_models():
    """Test if models can be loaded"""
    print("\n" + "="*60)
    print("Testing model initialization...")
    print("="*60 + "\n")
    
    results = {}
    
    # Test YOLOv8
    try:
        from ultralytics import YOLO
        print("Loading YOLOv8 model (this may take a moment on first run)...")
        model = YOLO('yolov8n-seg.pt')
        print("✓ YOLOv8 model loaded successfully")
        results['yolo'] = True
    except Exception as e:
        print(f"✗ YOLOv8 model failed to load: {e}")
        results['yolo'] = False
    
    # Test MediaPipe
    try:
        import mediapipe as mp
        print("Initializing MediaPipe Pose...")
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5
        )
        print("✓ MediaPipe Pose initialized successfully")
        pose.close()
        results['mediapipe_pose'] = True
    except Exception as e:
        print(f"✗ MediaPipe Pose failed to initialize: {e}")
        results['mediapipe_pose'] = False
    
    return results


def test_custom_modules():
    """Test if custom modules can be imported"""
    print("\n" + "="*60)
    print("Testing custom modules...")
    print("="*60 + "\n")
    
    results = {}
    
    # Test SegmentationModel
    try:
        from segmentation_model import SegmentationModel
        seg_model = SegmentationModel(model_size='n')
        print("✓ SegmentationModel imported and initialized")
        results['segmentation_model'] = True
    except Exception as e:
        print(f"✗ SegmentationModel failed: {e}")
        results['segmentation_model'] = False
    
    # Test LandmarkDetector
    try:
        from landmark_detector import LandmarkDetector
        landmark_detector = LandmarkDetector()
        print("✓ LandmarkDetector imported and initialized")
        results['landmark_detector'] = True
    except Exception as e:
        print(f"✗ LandmarkDetector failed: {e}")
        results['landmark_detector'] = False
    
    # Test MeasurementEngine
    try:
        from measurement_engine import MeasurementEngine
        measurement_engine = MeasurementEngine()
        print("✓ MeasurementEngine imported and initialized")
        results['measurement_engine'] = True
    except Exception as e:
        print(f"✗ MeasurementEngine failed: {e}")
        results['measurement_engine'] = False
    
    # Test ImageProcessor
    try:
        from process_images_yolo import ImageProcessor
        print("✓ ImageProcessor imported")
        results['image_processor'] = True
    except Exception as e:
        print(f"✗ ImageProcessor failed: {e}")
        results['image_processor'] = False
    
    return results


def print_summary(import_results, model_results, module_results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")
    
    all_results = {**import_results, **model_results, **module_results}
    
    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Prepare your images (front, side, back views)")
        print("  2. Run: python process_images_yolo.py image1.jpg")
        print("  3. Check the 'output' folder for results")
        print("\nFor more information, see YOLO_GUIDE.md")
        return True
    else:
        print("\n✗ Some tests failed. Please install missing dependencies:")
        print("\n  pip install -r requirements.txt")
        
        if not import_results.get('ultralytics', True):
            print("\n  Specifically for YOLOv8:")
            print("  pip install ultralytics")
        
        return False


def main():
    """Main test function"""
    print("="*60)
    print("YOLOv8 + MediaPipe Setup Test")
    print("="*60 + "\n")
    
    # Run tests
    import_results = test_imports()
    
    # Only test models if imports succeeded
    if all(import_results.values()):
        model_results = test_models()
        module_results = test_custom_modules()
    else:
        print("\n⚠ Skipping model tests due to import failures")
        model_results = {}
        module_results = {}
    
    # Print summary
    success = print_summary(import_results, model_results, module_results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
