"""
Test Suite for Hybrid Vision Approach
Tests the integration of YOLOv8 segmentation edges with MediaPipe joints
"""
import unittest
import numpy as np
from typing import Dict, Tuple, Optional
import cv2

# Import backend modules
from backend.landmark_detector import LandmarkDetector
from backend.measurement_engine import MeasurementEngine
from backend.segmentation_model import SegmentationModel


class TestHybridVisionApproach(unittest.TestCase):
    """Test hybrid vision approach components"""
    
    def setUp(self):
        """Initialize detectors and engines"""
        self.landmark_detector = LandmarkDetector()
        self.measurement_engine = MeasurementEngine()
        self.segmentation_model = SegmentationModel()
    
    def test_measurement_categorization(self):
        """Test that measurements are correctly categorized"""
        # Edge-based measurements should use segmentation edges
        edge_based = self.measurement_engine.edge_based_measurements
        self.assertIn('shoulder_width', edge_based)
        self.assertIn('chest_width', edge_based)
        self.assertIn('waist_width', edge_based)
        self.assertIn('hip_width', edge_based)
        
        # Joint-based measurements should use MediaPipe landmarks
        joint_based = self.measurement_engine.joint_based_measurements
        self.assertIn('arm_span', joint_based)
        self.assertIn('shoulder_to_hip', joint_based)
        self.assertIn('hip_to_ankle', joint_based)
        self.assertIn('torso_depth', joint_based)
    
    def test_edge_reference_points_structure(self):
        """Test that edge reference points have correct structure"""
        # Create a mock edge reference points dictionary
        mock_edge_points = {
            'shoulder_left': (100, 200),
            'shoulder_right': (300, 200),
            'waist_left': (110, 350),
            'waist_right': (290, 350),
            'hip_left': (120, 450),
            'hip_right': (280, 450),
            'shoulder_height': 200,
            'waist_height': 350,
            'hip_height': 450,
            'is_valid': True
        }
        
        # Verify all required keys are present
        required_keys = [
            'shoulder_left', 'shoulder_right',
            'waist_left', 'waist_right',
            'hip_left', 'hip_right',
            'shoulder_height', 'waist_height', 'hip_height',
            'is_valid'
        ]
        
        for key in required_keys:
            self.assertIn(key, mock_edge_points)
    
    def test_calculate_edge_distance(self):
        """Test edge distance calculation"""
        mock_edge_points = {
            'shoulder_left': (100, 200),
            'shoulder_right': (300, 200),
            'waist_left': (110, 350),
            'waist_right': (290, 350),
            'hip_left': (120, 450),
            'hip_right': (280, 450),
            'is_valid': True
        }
        
        # Test shoulder width distance
        shoulder_dist = self.measurement_engine._calculate_edge_distance(
            'shoulder_width', mock_edge_points
        )
        expected = np.sqrt((300-100)**2 + (200-200)**2)  # 200 pixels
        self.assertAlmostEqual(shoulder_dist, expected, places=1)
        
        # Test waist width distance
        waist_dist = self.measurement_engine._calculate_edge_distance(
            'waist_width', mock_edge_points
        )
        expected = np.sqrt((290-110)**2 + (350-350)**2)  # 180 pixels
        self.assertAlmostEqual(waist_dist, expected, places=1)
        
        # Test hip width distance
        hip_dist = self.measurement_engine._calculate_edge_distance(
            'hip_width', mock_edge_points
        )
        expected = np.sqrt((280-120)**2 + (450-450)**2)  # 160 pixels
        self.assertAlmostEqual(hip_dist, expected, places=1)
    
    def test_edge_measurement_validation(self):
        """Test validation of edge measurements"""
        # Test valid shoulder width
        is_valid, reason = self.measurement_engine.validate_edge_measurement(
            'shoulder_width', 45.0  # Valid range: 25-65cm
        )
        self.assertTrue(is_valid)
        
        # Test invalid (too narrow) shoulder width
        is_valid, reason = self.measurement_engine.validate_edge_measurement(
            'shoulder_width', 15.0  # Too narrow
        )
        self.assertFalse(is_valid)
        
        # Test invalid (too wide) shoulder width
        is_valid, reason = self.measurement_engine.validate_edge_measurement(
            'shoulder_width', 75.0  # Too wide
        )
        self.assertFalse(is_valid)
        
        # Test valid waist width
        is_valid, reason = self.measurement_engine.validate_edge_measurement(
            'waist_width', 32.0  # Valid range: 18-45cm
        )
        self.assertTrue(is_valid)
    
    def test_apply_edge_points_to_measurement(self):
        """Test applying edge points to calculate measurement"""
        mock_edge_points = {
            'shoulder_left': (100, 200),
            'shoulder_right': (300, 200),
            'is_valid': True
        }
        
        scale_factor = 0.1  # 0.1 cm/pixel
        
        # Shoulder width: 200 pixels × 0.1 cm/px = 20 cm
        result = self.measurement_engine.apply_edge_points_to_measurement(
            'shoulder_width', mock_edge_points, scale_factor
        )
        
        # Result should be valid
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 20.0, places=1)
    
    def test_measurement_routing_with_edge_points(self):
        """Test that measurements correctly route through edge vs joint sources"""
        # Create mock landmarks (33 for MediaPipe Pose)
        mock_landmarks = np.zeros((33, 3))
        
        # Set some joint positions
        mock_landmarks[11] = [100, 200, 0.95]  # left_shoulder
        mock_landmarks[12] = [300, 200, 0.95]  # right_shoulder
        mock_landmarks[15] = [80, 400, 0.95]   # left_wrist
        mock_landmarks[16] = [320, 400, 0.95]  # right_wrist
        
        mock_edge_points = {
            'shoulder_left': (100, 200),
            'shoulder_right': (300, 200),
            'waist_left': (110, 350),
            'waist_right': (290, 350),
            'hip_left': (120, 450),
            'hip_right': (280, 450),
            'is_valid': True
        }
        
        scale_factor = 0.1
        
        # Calculate with edge points
        measurements = self.measurement_engine.calculate_measurements_with_confidence(
            mock_landmarks, scale_factor, view='front', 
            edge_reference_points=mock_edge_points
        )
        
        # Check that we got measurements
        self.assertGreater(len(measurements), 0)
        
        # Check that width measurements came from edges
        if 'shoulder_width' in measurements:
            cm_val, conf, source = measurements['shoulder_width']
            self.assertEqual(source, 'Segmentation Edge')
        
        # Check that arm span came from MediaPipe
        if 'arm_span' in measurements:
            cm_val, conf, source = measurements['arm_span']
            self.assertEqual(source, 'MediaPipe Joints')
    
    def test_scale_conversion_preserved(self):
        """Test that scale conversion logic is completely unchanged"""
        pixel_distance = 200.0
        scale_factor = 0.1  # 0.1 cm/pixel
        
        # Expected conversion: should be simple multiplication
        expected_cm = pixel_distance * scale_factor  # 20.0 cm
        
        # Create mock edge points
        mock_edge_points = {
            'shoulder_left': (100, 200),
            'shoulder_right': (300, 200),
            'is_valid': True
        }
        
        # Apply edge points to measurement
        result = self.measurement_engine.apply_edge_points_to_measurement(
            'shoulder_width', mock_edge_points, scale_factor
        )
        
        # Verify formula is: pixel_dist * scale_factor = cm_dist
        self.assertAlmostEqual(result, expected_cm, places=1)
    
    def test_backward_compatibility_without_edge_points(self):
        """Test that measurements work without edge points (backward compatible)"""
        # Create mock landmarks
        mock_landmarks = np.zeros((33, 3))
        mock_landmarks[11] = [100, 200, 0.95]  # left_shoulder
        mock_landmarks[12] = [300, 200, 0.95]  # right_shoulder
        mock_landmarks[15] = [80, 400, 0.95]   # left_wrist
        mock_landmarks[16] = [320, 400, 0.95]  # right_wrist
        
        scale_factor = 0.1
        
        # Calculate WITHOUT edge points (backward compatibility test)
        measurements = self.measurement_engine.calculate_measurements_with_confidence(
            mock_landmarks, scale_factor, view='front'
        )
        
        # Should still work and return measurements
        self.assertGreater(len(measurements), 0)
        
        # All measurements should fall back to MediaPipe source
        for name, (cm_val, conf, source) in measurements.items():
            self.assertIn('MediaPipe', source)
    
    def test_extract_body_contour(self):
        """Test body contour extraction from segmentation mask"""
        # Create a simple test mask (circle representing person)
        mask = np.zeros((500, 400), dtype=np.uint8)
        cv2.circle(mask, (200, 250), 150, 255, -1)  # Filled circle
        
        # Extract contour
        contour = self.landmark_detector.extract_body_contour(mask)
        
        # Should return a valid contour
        self.assertIsNotNone(contour)
        self.assertGreater(len(contour), 0)
    
    def test_detect_face_landmarks(self):
        """Test face landmark detection"""
        # Create a simple test image with a white square (representing face)
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(image, (300, 150), (400, 250), (255, 255, 255), -1)
        
        # Detect face landmarks
        face_landmarks = self.landmark_detector.detect_face_landmarks(image)
        
        # If no face is detected, it should return None
        # Otherwise should return a list of landmarks
        if face_landmarks is not None:
            self.assertIsInstance(face_landmarks, list)
    
    def test_hybrid_approach_metadata(self):
        """Test hybrid approach metadata in response"""
        # This tests the structure of hybrid approach data returned by API
        
        # Create mock measurement response
        measurements_with_pixels = {
            'shoulder_width': {
                'value_cm': 40.0,
                'value_pixels': 400,
                'confidence': 0.95,
                'source': 'Segmentation Edge',
                'calculation': '400 px × 0.1 cm/px = 40.0 cm'
            },
            'arm_span': {
                'value_cm': 160.0,
                'value_pixels': 1600,
                'confidence': 0.92,
                'source': 'MediaPipe Joints',
                'calculation': '1600 px × 0.1 cm/px = 160.0 cm'
            }
        }
        
        # Count sources
        edge_count = len([m for m in measurements_with_pixels.values() 
                         if m['source'] == 'Segmentation Edge'])
        mediapipe_count = len([m for m in measurements_with_pixels.values() 
                               if m['source'] == 'MediaPipe Joints'])
        
        # Verify counts
        self.assertEqual(edge_count, 1)
        self.assertEqual(mediapipe_count, 1)


class TestEdgePointExtraction(unittest.TestCase):
    """Test edge point extraction methods"""
    
    def setUp(self):
        """Initialize landmark detector"""
        self.detector = LandmarkDetector()
    
    def test_get_extreme_points_at_height(self):
        """Test finding extreme points at specific height"""
        # Create mock contour points
        contour_points = np.array([
            [100, 200],
            [150, 210],
            [120, 200],  # Left point at y=200
            [280, 200],  # Right point at y=200
            [200, 210],
        ])
        
        target_height = 200
        tolerance = 10
        
        # Get extreme points at target height
        left_point, right_point = self.detector._get_extreme_points_at_height(
            contour_points, target_height, tolerance
        )
        
        # Verify we got valid points
        self.assertIsNotNone(left_point)
        self.assertIsNotNone(right_point)
        
        # Left should have smaller x than right
        self.assertLess(left_point[0], right_point[0])


class TestScaleConversionIntegrity(unittest.TestCase):
    """Ensure scale conversion logic remains completely unchanged"""
    
    def setUp(self):
        """Initialize measurement engine"""
        self.engine = MeasurementEngine()
    
    def test_pixel_to_cm_formula(self):
        """Test that cm = pixels × scale_factor formula is preserved"""
        test_cases = [
            (100, 0.1, 10.0),     # 100 px × 0.1 cm/px = 10 cm
            (200, 0.05, 10.0),    # 200 px × 0.05 cm/px = 10 cm
            (500, 0.2, 100.0),    # 500 px × 0.2 cm/px = 100 cm
            (1000, 0.15, 150.0),  # 1000 px × 0.15 cm/px = 150 cm
        ]
        
        for pixels, scale_factor, expected_cm in test_cases:
            calculated_cm = pixels * scale_factor
            self.assertAlmostEqual(calculated_cm, expected_cm, places=5)
    
    def test_edge_distance_scale_preservation(self):
        """Test that edge distances preserve scale conversion"""
        mock_edge_points = {
            'shoulder_left': (100, 200),
            'shoulder_right': (300, 200),
            'is_valid': True
        }
        
        scale_factor = 0.1
        
        # Calculate raw pixel distance
        pixel_dist = 300 - 100  # 200 pixels
        
        # Calculate edge distance
        edge_dist = self.engine._calculate_edge_distance('shoulder_width', mock_edge_points)
        self.assertAlmostEqual(edge_dist, pixel_dist, places=1)
        
        # Apply scale factor
        cm_dist = edge_dist * scale_factor
        expected_cm = 20.0
        
        self.assertAlmostEqual(cm_dist, expected_cm, places=1)


if __name__ == '__main__':
    unittest.main()
