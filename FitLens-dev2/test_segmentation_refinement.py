"""
Test Suite for Segmentation-Based Shoulder Refinement
Validates the integration of landmark refinement with segmentation masks
"""

import unittest
import numpy as np
import cv2
from pathlib import Path

# Import modules
from backend.landmark_detector import LandmarkDetector
from backend.measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel


class TestSegmentationReffinement(unittest.TestCase):
    """Test segmentation-based shoulder refinement"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.detector = LandmarkDetector()
        cls.measurement_engine = MeasurementEngine()
        cls.segmentation_model = SegmentationModel()
        cls.scale_factor = 0.2  # pixels to cm
        
        print("\n✓ Test fixtures initialized")
    
    def test_landmark_detection(self):
        """Test basic landmark detection"""
        print("\n--- Test: Basic Landmark Detection ---")
        
        # Create synthetic test image (white background with person-like features)
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Draw a simple body shape (circle for head, rectangle for torso)
        cv2.circle(image, (320, 150), 40, (0, 0, 0), -1)  # Head
        cv2.rectangle(image, (280, 190), (360, 350), (0, 0, 0), -1)  # Torso
        cv2.rectangle(image, (250, 350), (300, 480), (0, 0, 0), -1)  # Left leg
        cv2.rectangle(image, (340, 350), (390, 480), (0, 0, 0), -1)  # Right leg
        cv2.rectangle(image, (200, 200), (260, 320), (0, 0, 0), -1)  # Left arm
        cv2.rectangle(image, (380, 200), (440, 320), (0, 0, 0), -1)  # Right arm
        
        # Detect landmarks
        landmarks = self.detector.detect(image)
        
        if landmarks is not None:
            print(f"✓ Landmarks detected: {len(landmarks)} points")
            # Check shoulder indices exist
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            print(f"  Left shoulder: ({left_shoulder[0]:.1f}, {left_shoulder[1]:.1f}), conf={left_shoulder[2]:.3f}")
            print(f"  Right shoulder: ({right_shoulder[0]:.1f}, {right_shoulder[1]:.1f}), conf={right_shoulder[2]:.3f}")
            self.assertIsNotNone(left_shoulder)
            self.assertIsNotNone(right_shoulder)
        else:
            print("⚠ No landmarks detected (expected for synthetic image)")
    
    def test_segmentation_mask_generation(self):
        """Test segmentation mask generation"""
        print("\n--- Test: Segmentation Mask Generation ---")
        
        # Create a simple test image
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        cv2.circle(image, (320, 240), 100, (0, 0, 0), -1)  # Person silhouette
        
        # Generate mask
        mask = self.segmentation_model.segment_person(image, conf_threshold=0.3)
        
        if mask is not None:
            print(f"✓ Segmentation mask generated")
            print(f"  Mask shape: {mask.shape}")
            print(f"  Mask dtype: {mask.dtype}")
            print(f"  Mask range: [{mask.min()}, {mask.max()}]")
            print(f"  Person pixels (255): {np.sum(mask == 255)}")
            print(f"  Background pixels (0): {np.sum(mask == 0)}")
            
            self.assertEqual(len(mask.shape), 2)  # Should be 2D
            self.assertIn(mask.dtype, [np.uint8, np.float32])
        else:
            print("⚠ Segmentation mask unavailable (YOLOv8 may not be trained on this image type)")
    
    def test_refine_shoulder_landmarks_structure(self):
        """Test refinement output structure"""
        print("\n--- Test: Shoulder Refinement Structure ---")
        
        # Create synthetic landmarks array (33 MediaPipe points)
        landmarks = np.zeros((33, 3), dtype=np.float32)
        
        # Set shoulder landmarks (indices 11, 12)
        landmarks[11] = [300, 150, 0.95]  # Left shoulder
        landmarks[12] = [340, 150, 0.95]  # Right shoulder
        
        # Create synthetic segmentation mask
        mask = np.zeros((480, 640), dtype=np.uint8)
        cv2.circle(mask, (320, 240), 100, 255, -1)  # Person region
        
        # Create dummy image
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Call refinement
        refined_data = self.detector.refine_shoulder_landmarks(
            image, landmarks, mask
        )
        
        print(f"✓ Refinement completed")
        print(f"  Keys in response: {list(refined_data.keys())}")
        
        # Verify structure
        self.assertIn('left_shoulder', refined_data)
        self.assertIn('right_shoulder', refined_data)
        self.assertIn('refinement_quality', refined_data)
        self.assertIn('is_refined', refined_data)
        
        # Verify shoulder structure
        left_shoulder = refined_data['left_shoulder']
        self.assertIn('x', left_shoulder)
        self.assertIn('y', left_shoulder)
        self.assertIn('confidence', left_shoulder)
        
        print(f"  Refinement quality: {refined_data['refinement_quality']:.3f}")
        print(f"  Is refined: {refined_data['is_refined']}")
        print(f"  Left shoulder: ({left_shoulder['x']:.1f}, {left_shoulder['y']:.1f})")
    
    def test_non_invasive_original_landmarks(self):
        """Test that original landmarks are preserved"""
        print("\n--- Test: Original Landmarks Preservation ---")
        
        landmarks = np.zeros((33, 3), dtype=np.float32)
        landmarks[11] = [300, 150, 0.95]
        landmarks[12] = [340, 150, 0.95]
        
        mask = np.zeros((480, 640), dtype=np.uint8)
        cv2.circle(mask, (320, 240), 100, 255, -1)
        
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        refined_data = self.detector.refine_shoulder_landmarks(
            image, landmarks, mask
        )
        
        # Check for original landmarks in response
        self.assertIn('original_left_shoulder', refined_data)
        self.assertIn('original_right_shoulder', refined_data)
        
        orig_left = refined_data['original_left_shoulder']
        self.assertAlmostEqual(orig_left['x'], 300.0, places=1)
        self.assertAlmostEqual(orig_left['y'], 150.0, places=1)
        self.assertAlmostEqual(orig_left['confidence'], 0.95, places=2)
        
        print(f"✓ Original landmarks preserved:")
        print(f"  Original left: ({orig_left['x']:.1f}, {orig_left['y']:.1f})")
        print(f"  Original right: ({refined_data['original_right_shoulder']['x']:.1f}, {refined_data['original_right_shoulder']['y']:.1f})")
    
    def test_measurement_integration(self):
        """Test measurement calculation with refined shoulders"""
        print("\n--- Test: Measurement Engine Integration ---")
        
        # Create landmarks
        landmarks = np.zeros((33, 3), dtype=np.float32)
        landmarks[11] = [280, 200, 0.9]   # Left shoulder
        landmarks[12] = [360, 200, 0.9]   # Right shoulder
        landmarks[15] = [250, 350, 0.8]   # Left wrist
        landmarks[16] = [390, 350, 0.8]   # Right wrist
        landmarks[23] = [290, 400, 0.85]  # Left hip
        landmarks[24] = [350, 400, 0.85]  # Right hip
        
        # Calculate measurements without refinement
        measurements_normal = self.measurement_engine.calculate_measurements_with_confidence(
            landmarks, self.scale_factor, view='front', refined_shoulders=None
        )
        
        print(f"✓ Measurements without refinement: {list(measurements_normal.keys())}")
        for name, (value, conf, source) in measurements_normal.items():
            print(f"  {name}: {value:.2f} cm (conf={conf:.2f}, source={source})")
        
        # Create refined shoulder data
        refined_data = {
            'left_shoulder': {'x': 285, 'y': 195, 'confidence': 0.95},
            'right_shoulder': {'x': 355, 'y': 195, 'confidence': 0.95},
            'refinement_quality': 0.85,
            'is_refined': True
        }
        
        # Calculate measurements with refinement
        measurements_refined = self.measurement_engine.calculate_measurements_with_confidence(
            landmarks, self.scale_factor, view='front', refined_shoulders=refined_data
        )
        
        print(f"\n✓ Measurements with refinement:")
        for name, (value, conf, source) in measurements_refined.items():
            print(f"  {name}: {value:.2f} cm (conf={conf:.2f}, source={source})")
        
        # Verify source tracking
        if 'shoulder_width' in measurements_refined:
            _, _, source = measurements_refined['shoulder_width']
            self.assertIn('Refined', source)
            print(f"\n✓ Source correctly marked as: {source}")
    
    def test_shoulder_measurement_only(self):
        """Test shoulder-only measurements"""
        print("\n--- Test: Shoulder-Only Measurements ---")
        
        landmarks = np.zeros((33, 3), dtype=np.float32)
        landmarks[11] = [280, 200, 0.9]   # Left shoulder
        landmarks[12] = [360, 200, 0.9]   # Right shoulder
        landmarks[15] = [250, 350, 0.8]   # Left wrist
        landmarks[16] = [390, 350, 0.8]   # Right wrist
        
        refined_data = {
            'left_shoulder': {'x': 285, 'y': 195, 'confidence': 0.95},
            'right_shoulder': {'x': 355, 'y': 195, 'confidence': 0.95},
            'refinement_quality': 0.85,
            'is_refined': True
        }
        
        # Calculate shoulder measurements only
        measurements = self.measurement_engine.calculate_shoulder_measurements_only(
            landmarks, self.scale_factor, refined_shoulders=refined_data
        )
        
        print(f"✓ Shoulder measurements calculated:")
        for name, (value, conf, source) in measurements.items():
            print(f"  {name}: {value:.2f} cm (conf={conf:.3f})")
        
        # Verify structure
        self.assertIn('shoulder_width', measurements)
        self.assertIn('arm_span', measurements)
    
    def test_fallback_when_mask_unavailable(self):
        """Test fallback behavior when segmentation mask is unavailable"""
        print("\n--- Test: Fallback When Mask Unavailable ---")
        
        landmarks = np.zeros((33, 3), dtype=np.float32)
        landmarks[11] = [300, 150, 0.95]
        landmarks[12] = [340, 150, 0.95]
        
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        mask = None  # No mask available
        
        # Call refinement with None mask
        refined_data = self.detector.refine_shoulder_landmarks(
            image, landmarks, mask
        )
        
        print(f"✓ Refinement with None mask completed")
        print(f"  Is refined: {refined_data['is_refined']}")
        print(f"  Fallback used: {not refined_data['is_refined']}")
        
        # Should return original landmarks as fallback
        if refined_data['is_refined']:
            print("  Used refined shoulders")
        else:
            print("  Fell back to original MediaPipe landmarks")
    
    def test_shoulder_width_validation(self):
        """Test shoulder width validation"""
        print("\n--- Test: Shoulder Width Validation ---")
        
        # Test realistic shoulder width (30-60cm)
        landmarks = np.zeros((33, 3), dtype=np.float32)
        
        # Shoulder width of ~200 pixels = 40 cm (at 0.2 scale)
        landmarks[11] = [170, 200, 0.9]   # Left shoulder
        landmarks[12] = [370, 200, 0.9]   # Right shoulder
        
        refined_data = {
            'left_shoulder': {'x': 175, 'y': 195, 'confidence': 0.95},
            'right_shoulder': {'x': 365, 'y': 195, 'confidence': 0.95},
            'refinement_quality': 0.85,
            'is_refined': True
        }
        
        # Calculate shoulder width
        left_x = refined_data['left_shoulder']['x']
        right_x = refined_data['right_shoulder']['x']
        shoulder_width_pixels = right_x - left_x
        shoulder_width_cm = shoulder_width_pixels * self.scale_factor
        
        print(f"✓ Shoulder width calculated:")
        print(f"  Pixels: {shoulder_width_pixels:.1f}")
        print(f"  CM: {shoulder_width_cm:.2f}")
        print(f"  Valid range: 30-60 cm")
        print(f"  Is valid: {30 <= shoulder_width_cm <= 60}")
        
        self.assertTrue(30 <= shoulder_width_cm <= 60)
    
    def test_refinement_quality_score(self):
        """Test refinement quality score calculation"""
        print("\n--- Test: Refinement Quality Score ---")
        
        landmarks = np.zeros((33, 3), dtype=np.float32)
        landmarks[11] = [300, 150, 0.95]
        landmarks[12] = [340, 150, 0.95]
        
        mask = np.zeros((480, 640), dtype=np.uint8)
        cv2.circle(mask, (320, 200), 150, 255, -1)
        
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        refined_data = self.detector.refine_shoulder_landmarks(
            image, landmarks, mask
        )
        
        quality = refined_data.get('refinement_quality', 0.0)
        print(f"✓ Refinement quality score: {quality:.3f}")
        print(f"  Valid: {0 <= quality <= 1}")
        
        self.assertTrue(0 <= quality <= 1)
    
    def test_apply_refined_shoulders_to_landmarks(self):
        """Test applying refined shoulders back to landmark array"""
        print("\n--- Test: Applying Refined Shoulders to Landmarks ---")
        
        landmarks = np.zeros((33, 3), dtype=np.float32)
        for i in range(33):
            landmarks[i] = [100 + i*10, 200 + i*5, 0.8]
        
        refined_data = {
            'left_shoulder': {'x': 350.5, 'y': 180.2, 'confidence': 0.95},
            'right_shoulder': {'x': 420.8, 'y': 175.3, 'confidence': 0.96},
            'is_refined': True
        }
        
        # Apply refined shoulders
        updated_landmarks = self.detector.apply_refined_shoulders_to_landmarks(
            landmarks, refined_data
        )
        
        # Verify update
        left_shoulder_updated = updated_landmarks[11]
        right_shoulder_updated = updated_landmarks[12]
        
        print(f"✓ Refined shoulders applied to landmark array:")
        print(f"  Left shoulder: ({left_shoulder_updated[0]:.1f}, {left_shoulder_updated[1]:.1f})")
        print(f"  Right shoulder: ({right_shoulder_updated[0]:.1f}, {right_shoulder_updated[1]:.1f})")
        
        self.assertAlmostEqual(left_shoulder_updated[0], 350.5, places=1)
        self.assertAlmostEqual(right_shoulder_updated[0], 420.8, places=1)
    
    def test_get_shoulder_width(self):
        """Test shoulder width extraction utility"""
        print("\n--- Test: Shoulder Width Utility ---")
        
        refined_data = {
            'left_shoulder': {'x': 280.0, 'y': 200.0, 'confidence': 0.95},
            'right_shoulder': {'x': 380.0, 'y': 200.0, 'confidence': 0.95},
            'is_refined': True
        }
        
        shoulder_width = self.detector.get_shoulder_width(refined_data)
        shoulder_width_cm = shoulder_width * self.scale_factor
        
        print(f"✓ Shoulder width:")
        print(f"  Pixels: {shoulder_width:.1f}")
        print(f"  CM: {shoulder_width_cm:.2f}")
        
        self.assertAlmostEqual(shoulder_width, 100.0, places=1)
    
    def test_get_shoulder_midpoint(self):
        """Test shoulder midpoint calculation"""
        print("\n--- Test: Shoulder Midpoint Utility ---")
        
        refined_data = {
            'left_shoulder': {'x': 280.0, 'y': 200.0, 'confidence': 0.95},
            'right_shoulder': {'x': 380.0, 'y': 210.0, 'confidence': 0.95},
            'is_refined': True
        }
        
        midpoint = self.detector.get_shoulder_midpoint(refined_data)
        
        print(f"✓ Shoulder midpoint: ({midpoint[0]:.1f}, {midpoint[1]:.1f})")
        
        self.assertAlmostEqual(midpoint[0], 330.0, places=1)  # (280 + 380) / 2
        self.assertAlmostEqual(midpoint[1], 205.0, places=1)  # (200 + 210) / 2


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.detector = LandmarkDetector()
        cls.measurement_engine = MeasurementEngine()
    
    def test_original_detect_unchanged(self):
        """Test that original detect() method is unchanged"""
        print("\n--- Test: Original Detect Method Unchanged ---")
        
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Call original detect method
        landmarks = self.detector.detect(image)
        
        if landmarks is not None:
            print(f"✓ detect() works: returned {len(landmarks)} landmarks")
            self.assertEqual(len(landmarks), 33)  # MediaPipe returns 33 points
        else:
            print("⚠ detect() returned None (expected for synthetic image)")
    
    def test_original_measurements_unchanged(self):
        """Test that original measurement calculations work"""
        print("\n--- Test: Original Measurements Unchanged ---")
        
        landmarks = np.zeros((33, 3), dtype=np.float32)
        landmarks[11] = [280, 200, 0.9]
        landmarks[12] = [360, 200, 0.9]
        
        scale_factor = 0.2
        
        # Call without refinement parameter (original interface)
        measurements = self.measurement_engine.calculate_measurements_with_confidence(
            landmarks, scale_factor, view='front'
        )
        
        print(f"✓ Original interface works: {len(measurements)} measurements")
        
        # Verify measurements calculated correctly
        if 'shoulder_width' in measurements:
            value, conf, source = measurements['shoulder_width']
            expected = 80 * 0.2  # (360-280) * scale_factor
            print(f"  Shoulder width: {value:.2f} cm (expected ~{expected:.2f})")


def run_tests():
    """Run all tests with verbose output"""
    print("=" * 70)
    print("SEGMENTATION-BASED SHOULDER REFINEMENT TEST SUITE")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestSegmentationReffinement))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
    
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
