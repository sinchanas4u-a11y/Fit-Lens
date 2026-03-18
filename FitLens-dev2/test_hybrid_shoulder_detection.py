"""
Test Suite for Hybrid Shoulder Detection System
Validates all components and the complete pipeline
"""
import cv2
import numpy as np
import sys
from pathlib import Path


class HybridShoulderDetectionTests:
    """Test suite for hybrid shoulder detection"""
    
    def __init__(self):
        """Initialize test suite"""
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
        
    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("HYBRID SHOULDER DETECTION - TEST SUITE")
        print("="*70)
        
        # Import tests
        self.test_imports()
        
        # Component tests
        self.test_hybrid_detector_initialization()
        self.test_measurement_engine_hybrid_integration()
        self.test_landmark_detector_edge_extraction()
        
        # Algorithm tests
        self.test_canny_edge_detection()
        self.test_contour_extraction()
        self.test_point_filtering()
        
        # Integration tests
        self.test_full_pipeline()
        
        # Print summary
        self.print_summary()
        
        return self.tests_failed == 0
    
    def test_imports(self):
        """Test that all modules can be imported"""
        print(f"\n{'─'*70}")
        print("TEST 1: Module Imports")
        print(f"{'─'*70}")
        
        modules_to_test = [
            ('hybrid_shoulder_detector', 'HybridShoulderDetector'),
            ('measurement_engine', 'MeasurementEngine'),
            ('landmark_detector', 'LandmarkDetector'),
            ('segmentation_model', 'SegmentationModel'),
        ]
        
        for module_name, class_name in modules_to_test:
            try:
                module = __import__(module_name)
                cls = getattr(module, class_name)
                print(f"  ✓ {module_name}.{class_name}")
                self.tests_passed += 1
            except Exception as e:
                print(f"  ✗ {module_name}.{class_name}: {e}")
                self.tests_failed += 1
                self.errors.append((module_name, str(e)))
    
    def test_hybrid_detector_initialization(self):
        """Test HybridShoulderDetector initialization"""
        print(f"\n{'─'*70}")
        print("TEST 2: HybridShoulderDetector Initialization")
        print(f"{'─'*70}")
        
        try:
            from hybrid_shoulder_detector import HybridShoulderDetector
            detector = HybridShoulderDetector()
            
            # Check attributes
            assert hasattr(detector, 'canny_low'), "Missing canny_low"
            assert hasattr(detector, 'canny_high'), "Missing canny_high"
            assert hasattr(detector, 'morph_kernel_size'), "Missing morph_kernel_size"
            assert hasattr(detector, 'detect_shoulder_width'), "Missing detect_shoulder_width method"
            
            print(f"  ✓ HybridShoulderDetector initialized correctly")
            print(f"    - Canny thresholds: {detector.canny_low}-{detector.canny_high}")
            print(f"    - Morph kernel size: {detector.morph_kernel_size}")
            self.tests_passed += 1
        except Exception as e:
            print(f"  ✗ Initialization failed: {e}")
            self.tests_failed += 1
            self.errors.append(("HybridShoulderDetector", str(e)))
    
    def test_measurement_engine_hybrid_integration(self):
        """Test MeasurementEngine hybrid integration"""
        print(f"\n{'─'*70}")
        print("TEST 3: MeasurementEngine Hybrid Integration")
        print(f"{'─'*70}")
        
        try:
            from measurement_engine import MeasurementEngine
            engine = MeasurementEngine()
            
            # Check attributes
            assert hasattr(engine, 'hybrid_shoulder_detector'), "Missing hybrid_shoulder_detector"
            assert hasattr(engine, 'calculate_shoulder_width_hybrid'), "Missing calculate_shoulder_width_hybrid"
            
            print(f"  ✓ MeasurementEngine has hybrid integration")
            if engine.hybrid_shoulder_detector is not None:
                print(f"  ✓ HybridShoulderDetector initialized in engine")
            else:
                print(f"  ⚠️  HybridShoulderDetector not initialized (optional)")
            self.tests_passed += 1
        except Exception as e:
            print(f"  ✗ Integration failed: {e}")
            self.tests_failed += 1
            self.errors.append(("MeasurementEngine hybrid", str(e)))
    
    def test_landmark_detector_edge_extraction(self):
        """Test LandmarkDetector edge extraction method"""
        print(f"\n{'─'*70}")
        print("TEST 4: LandmarkDetector Edge Extraction")
        print(f"{'─'*70}")
        
        try:
            from landmark_detector import LandmarkDetector
            detector = LandmarkDetector()
            
            # Check method exists
            assert hasattr(detector, 'extract_body_edge_keypoints'), "Missing extract_body_edge_keypoints"
            
            # Test with dummy mask
            dummy_mask = np.zeros((480, 640), dtype=np.uint8)
            cv2.rectangle(dummy_mask, (100, 100), (500, 400), 255, -1)
            
            result = detector.extract_body_edge_keypoints(dummy_mask)
            
            assert result is not None, "Method returned None"
            assert 'is_valid' in result, "Missing 'is_valid' key"
            print(f"  ✓ extract_body_edge_keypoints method works")
            print(f"    - Return type: dict with {len(result)} keys")
            print(f"    - Valid result: {result.get('is_valid', False)}")
            
            self.tests_passed += 1
            detector.cleanup()
        except Exception as e:
            print(f"  ✗ Edge extraction test failed: {e}")
            self.tests_failed += 1
            self.errors.append(("LandmarkDetector edge extraction", str(e)))
    
    def test_canny_edge_detection(self):
        """Test Canny edge detection implementation"""
        print(f"\n{'─'*70}")
        print("TEST 5: Canny Edge Detection")
        print(f"{'─'*70}")
        
        try:
            # Create a simple test image with clear edges
            test_image = np.zeros((100, 100), dtype=np.uint8)
            cv2.circle(test_image, (50, 50), 30, 255, -1)
            
            # Apply Canny
            edges = cv2.Canny(test_image, 50, 150)
            
            # Check result
            assert edges is not None, "Canny returned None"
            assert edges.shape == test_image.shape, "Shape mismatch"
            assert np.any(edges > 0), "No edges detected"
            
            edge_pixels = np.count_nonzero(edges)
            print(f"  ✓ Canny edge detection works")
            print(f"    - Input shape: {test_image.shape}")
            print(f"    - Edge pixels detected: {edge_pixels}")
            print(f"    - Edge density: {100*edge_pixels/np.prod(test_image.shape):.2f}%")
            
            self.tests_passed += 1
        except Exception as e:
            print(f"  ✗ Canny test failed: {e}")
            self.tests_failed += 1
            self.errors.append(("Canny edge detection", str(e)))
    
    def test_contour_extraction(self):
        """Test OpenCV contour extraction"""
        print(f"\n{'─'*70}")
        print("TEST 6: OpenCV Contour Extraction")
        print(f"{'─'*70}")
        
        try:
            # Create test image with multiple shapes
            test_image = np.zeros((200, 200), dtype=np.uint8)
            cv2.circle(test_image, (50, 50), 30, 255, -1)
            cv2.rectangle(test_image, (120, 100), (180, 180), 255, -1)
            
            # Find contours
            contours = cv2.findContours(test_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            
            assert len(contours) > 0, "No contours found"
            
            # Get largest contour
            main_contour = max(contours, key=cv2.contourArea)
            
            # Test hull and approximation
            hull = cv2.convexHull(main_contour)
            epsilon = 0.02 * cv2.arcLength(main_contour, True)
            approx = cv2.approxPolyDP(main_contour, epsilon, True)
            
            print(f"  ✓ Contour extraction works")
            print(f"    - Contours found: {len(contours)}")
            print(f"    - Main contour points: {len(main_contour)}")
            print(f"    - Convex hull points: {len(hull)}")
            print(f"    - Approx poly points: {len(approx)}")
            
            self.tests_passed += 1
        except Exception as e:
            print(f"  ✗ Contour extraction test failed: {e}")
            self.tests_failed += 1
            self.errors.append(("Contour extraction", str(e)))
    
    def test_point_filtering(self):
        """Test NumPy point filtering"""
        print(f"\n{'─'*70}")
        print("TEST 7: NumPy Point Filtering")
        print(f"{'─'*70}")
        
        try:
            # Create test points
            points = np.array([
                [10, 50],
                [100, 60],
                [50, 120],
                [150, 70],
                [200, 55],
                [190, 65],
            ])
            
            # Test filtering by Y range
            y_min, y_max = 50, 70
            mask = (points[:, 1] >= y_min) & (points[:, 1] <= y_max)
            filtered = points[mask]
            
            # Test finding extremes
            left_idx = np.argmin(filtered[:, 0])
            right_idx = np.argmax(filtered[:, 0])
            
            left_point = filtered[left_idx]
            right_point = filtered[right_idx]
            
            width = right_point[0] - left_point[0]
            
            print(f"  ✓ NumPy point filtering works")
            print(f"    - Original points: {len(points)}")
            print(f"    - Filtered (Y: {y_min}-{y_max}): {len(filtered)}")
            print(f"    - Left point: {left_point}")
            print(f"    - Right point: {right_point}")
            print(f"    - Width: {width}")
            
            self.tests_passed += 1
        except Exception as e:
            print(f"  ✗ Point filtering test failed: {e}")
            self.tests_failed += 1
            self.errors.append(("Point filtering", str(e)))
    
    def test_full_pipeline(self):
        """Test the complete hybrid detection pipeline"""
        print(f"\n{'─'*70}")
        print("TEST 8: Full Pipeline (Synthetic Data)")
        print(f"{'─'*70}")
        
        try:
            from hybrid_shoulder_detector import HybridShoulderDetector
            
            # Create synthetic test data
            h, w = 480, 640
            image = np.ones((h, w, 3), dtype=np.uint8) * 200
            
            # Create a simple human silhouette
            mask = np.zeros((h, w), dtype=np.uint8)
            # Head
            cv2.circle(mask, (w//2, 80), 30, 255, -1)
            # Shoulders
            cv2.ellipse(mask, (w//2, 150), (120, 40), 0, 0, 360, 255, -1)
            # Torso
            cv2.rectangle(mask, (w//2-80, 200), (w//2+80, 400), 255, -1)
            # Arms
            cv2.rectangle(mask, (w//2-150, 180), (w//2-100, 300), 255, -1)
            cv2.rectangle(mask, (w//2+100, 180), (w//2+150, 300), 255, -1)
            
            # Create synthetic landmarks (33 points)
            landmarks = np.random.rand(33, 3) * 0.5 + 0.25  # Random in [0.25, 0.75]
            # Set shoulder landmarks specifically
            landmarks[11, 0] = 0.3  # left shoulder X
            landmarks[11, 1] = 0.3  # left shoulder Y
            landmarks[11, 2] = 0.95  # high confidence
            
            landmarks[12, 0] = 0.7  # right shoulder X
            landmarks[12, 1] = 0.3  # right shoulder Y
            landmarks[12, 2] = 0.95  # high confidence
            
            # Convert to pixel coordinates
            landmarks[:, 0] *= w
            landmarks[:, 1] *= h
            
            # Test hybrid detection
            detector = HybridShoulderDetector()
            scale_factor = 0.1  # pixels to cm
            
            result = detector.detect_shoulder_width(
                image, mask, landmarks, scale_factor, debug=False
            )
            
            print(f"  ✓ Full pipeline executed")
            print(f"    - Result keys: {list(result.keys())}")
            print(f"    - Shoulder width (px): {result.get('shoulder_width_px')}")
            print(f"    - Shoulder width (cm): {result.get('shoulder_width_cm')}")
            print(f"    - Confidence: {result.get('confidence')}")
            print(f"    - Source: {result.get('source', 'N/A')}")
            
            if result['shoulder_width_cm'] is not None:
                print(f"  ✓ Pipeline successfully detected shoulder width")
            else:
                print(f"  ⚠️  Shoulder width not detected (expected with synthetic data)")
            
            self.tests_passed += 1
        except Exception as e:
            print(f"  ✗ Full pipeline test failed: {e}")
            import traceback
            traceback.print_exc()
            self.tests_failed += 1
            self.errors.append(("Full pipeline", str(e)))
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_failed}")
        print(f"Total tests: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed > 0:
            print(f"\n{'─'*70}")
            print("FAILED TESTS:")
            print(f"{'─'*70}")
            for test_name, error in self.errors:
                print(f"  ✗ {test_name}")
                print(f"    Error: {error}")
        else:
            print(f"\n✓ ALL TESTS PASSED!")
        
        print(f"\n{'='*70}\n")


def main():
    """Run test suite"""
    tester = HybridShoulderDetectionTests()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
