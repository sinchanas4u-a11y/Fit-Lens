"""
Test script to verify installation and dependencies
"""
import sys

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...\n")
    
    tests = []
    
    # Test PyTorch
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ PyTorch not found: {e}")
        tests.append(False)
    
    # Test torchvision
    try:
        import torchvision
        print(f"✓ torchvision {torchvision.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ torchvision not found: {e}")
        tests.append(False)
    
    # Test Detectron2
    try:
        import detectron2
        from detectron2 import model_zoo
        print(f"✓ Detectron2 {detectron2.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ Detectron2 not found: {e}")
        print("  Install: pip install 'git+https://github.com/facebookresearch/detectron2.git'")
        tests.append(False)
    
    # Test OpenCV
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ OpenCV not found: {e}")
        tests.append(False)
    
    # Test NumPy
    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ NumPy not found: {e}")
        tests.append(False)
    
    # Test Pillow
    try:
        import PIL
        print(f"✓ Pillow {PIL.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ Pillow not found: {e}")
        tests.append(False)
    
    # Test pycocotools
    try:
        import pycocotools
        print(f"✓ pycocotools")
        tests.append(True)
    except ImportError as e:
        print(f"✗ pycocotools not found: {e}")
        tests.append(False)
    
    # Test albumentations
    try:
        import albumentations
        print(f"✓ albumentations {albumentations.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ albumentations not found: {e}")
        tests.append(False)
    
    return all(tests)


def test_camera():
    """Test if camera is accessible"""
    print("\n" + "="*60)
    print("Testing camera access...")
    print("="*60 + "\n")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✓ Camera accessible")
                print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return True
            else:
                print("✗ Camera opened but cannot read frames")
                cap.release()
                return False
        else:
            print("✗ Cannot open camera")
            print("  Try: Close other applications using the camera")
            return False
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False


def test_model_loading():
    """Test if model can be loaded"""
    print("\n" + "="*60)
    print("Testing model loading...")
    print("="*60 + "\n")
    
    try:
        from model_arch import KeypointRCNN
        
        print("Loading Keypoint R-CNN model...")
        model = KeypointRCNN()
        print("✓ Model loaded successfully")
        print(f"  Device: {model.device}")
        return True
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False


def test_synthetic_data():
    """Test synthetic data generation"""
    print("\n" + "="*60)
    print("Testing synthetic data generation...")
    print("="*60 + "\n")
    
    try:
        from dataset import SyntheticDataGenerator
        import cv2
        
        print("Generating synthetic pose...")
        image, keypoints = SyntheticDataGenerator.generate_synthetic_pose()
        
        print(f"✓ Synthetic data generated")
        print(f"  Image shape: {image.shape}")
        print(f"  Keypoints shape: {keypoints.shape}")
        
        # Display
        print("\nDisplaying synthetic pose (press any key to close)...")
        cv2.imshow("Synthetic Pose Test", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return True
    except Exception as e:
        print(f"✗ Synthetic data test failed: {e}")
        return False


def test_modules():
    """Test if custom modules can be imported"""
    print("\n" + "="*60)
    print("Testing custom modules...")
    print("="*60 + "\n")
    
    modules = [
        'config',
        'model_arch',
        'pose_utils',
        'dataset',
        'train',
        'main'
    ]
    
    tests = []
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}.py")
            tests.append(True)
        except Exception as e:
            print(f"✗ {module_name}.py: {e}")
            tests.append(False)
    
    return all(tests)


def main():
    """Run all tests"""
    print("="*60)
    print("INSTALLATION TEST SUITE")
    print("="*60 + "\n")
    
    results = {}
    
    # Test imports
    results['imports'] = test_imports()
    
    # Test modules
    results['modules'] = test_modules()
    
    # Test camera
    results['camera'] = test_camera()
    
    # Test model loading
    results['model'] = test_model_loading()
    
    # Test synthetic data
    results['synthetic'] = test_synthetic_data()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.upper():.<30} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nYou're ready to run the application!")
        print("Run: python main.py")
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease fix the failed tests before running the application.")
        print("See README_RCNN.md for installation instructions.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
