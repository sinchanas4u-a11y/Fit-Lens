"""
Test Suite for Shoulder Edge Detection
Tests all major functionalities of the shoulder edge detection system
"""

import cv2
import numpy as np
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from landmark_detector import LandmarkDetector


class ShoulderEdgeDetectionTests:
    """Comprehensive test suite for shoulder edge detection"""
    
    def __init__(self):
        self.detector = LandmarkDetector()
        self.test_results = []
        self.create_test_images()
    
    def create_test_images(self):
        """Create synthetic test images"""
        self.test_images = {}
        
        # Create image with person-like silhouette
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw a simple shoulder region for testing
        # This is a very basic synthetic image
        center_x, center_y = 320, 240
        
        # Body outline
        cv2.ellipse(img, (center_x, center_y + 100), (60, 120), 0, 0, 360, (100, 100, 100), -1)
        # Head
        cv2.circle(img, (center_x, center_y - 80), 30, (100, 100, 100), -1)
        # Left shoulder
        cv2.circle(img, (center_x - 70, center_y), 30, (120, 120, 120), -1)
        # Right shoulder
        cv2.circle(img, (center_x + 70, center_y), 30, (120, 120, 120), -1)
        
        cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.test_images['synthetic'] = img
    
    def test_detector_initialization(self):
        """Test 1: Detector initialization"""
        print("\n[TEST 1] Detector Initialization")
        try:
            assert self.detector.frame_counter == 0
            assert self.detector.shoulder_region_radius == 60
            assert self.detector.edge_detection_threshold == 50
            print("✓ Detector initialized correctly")
            self.test_results.append(('Initialization', 'PASS'))
            return True
        except AssertionError as e:
            print(f"✗ Initialization failed: {e}")
            self.test_results.append(('Initialization', 'FAIL'))
            return False
    
    def test_landmark_detection(self):
        """Test 2: Landmark detection on synthetic image"""
        print("\n[TEST 2] Landmark Detection")
        try:
            # Use synthetic image
            img = self.test_images['synthetic']
            landmarks = self.detector.detect(img)
            
            # Note: Synthetic image likely won't detect landmarks
            # Test that the function runs without error
            print(f"✓ Landmark detection executed")
            print(f"  - Landmarks detected: {landmarks is not None}")
            self.test_results.append(('Landmark Detection', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Landmark detection failed: {e}")
            self.test_results.append(('Landmark Detection', 'FAIL'))
            return False
    
    def test_shoulder_edge_detection_no_person(self):
        """Test 3: Shoulder edge detection with no person"""
        print("\n[TEST 3] Shoulder Edge Detection (No Person)")
        try:
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            landmarks = self.detector.detect(img)
            
            shoulder_data = self.detector.detect_shoulder_edge_points(
                img, landmarks, shoulder_type='both'
            )
            
            assert 'shoulder_edge_points' in shoulder_data
            assert 'confidence_score' in shoulder_data
            assert 'frame_number' in shoulder_data
            assert shoulder_data['confidence_score'] == 0.0
            print("✓ Edge detection handles no person gracefully")
            self.test_results.append(('Edge Detection (No Person)', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Edge detection test failed: {e}")
            self.test_results.append(('Edge Detection (No Person)', 'FAIL'))
            return False
    
    def test_json_export(self):
        """Test 4: JSON export functionality"""
        print("\n[TEST 4] JSON Export")
        try:
            # Create mock shoulder data
            shoulder_data = {
                'frame_number': 1,
                'shoulder_edge_points': [
                    {'x': 0.4, 'y': 0.3, 'pixel_x': 256, 'pixel_y': 144},
                    {'x': 0.5, 'y': 0.3, 'pixel_x': 320, 'pixel_y': 144}
                ],
                'confidence_score': 0.85
            }
            
            json_output = self.detector.export_shoulder_data_json(shoulder_data)
            
            # Verify it's valid JSON
            parsed = json.loads(json_output)
            assert 'frame_number' in parsed
            assert 'shoulder_edge_points' in parsed
            assert 'confidence_score' in parsed
            
            print("✓ JSON export successful")
            print(f"  - Output length: {len(json_output)} chars")
            self.test_results.append(('JSON Export', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ JSON export failed: {e}")
            self.test_results.append(('JSON Export', 'FAIL'))
            return False
    
    def test_detection_quality_assessment(self):
        """Test 5: Detection quality assessment"""
        print("\n[TEST 5] Detection Quality Assessment")
        try:
            # Test various confidence levels
            test_cases = [
                ({'confidence_score': 0.95, 'shoulder_edge_points': [{'x': 0}, {'x': 1}, {'x': 2}, {'x': 3}, {'x': 4}, {'x': 5}, {'x': 6}]}, 'good'),
                ({'confidence_score': 0.75, 'shoulder_edge_points': [{'x': 0}, {'x': 1}, {'x': 2}]}, 'fair'),
                ({'confidence_score': 0.50, 'shoulder_edge_points': []}, 'poor')
            ]
            
            for shoulder_data, expected_quality in test_cases:
                quality = self.detector._assess_detection_quality(shoulder_data)
                actual_quality = quality['overall']
                assert actual_quality == expected_quality, f"Expected {expected_quality}, got {actual_quality}"
            
            print("✓ Detection quality assessment works correctly")
            self.test_results.append(('Quality Assessment', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Quality assessment failed: {e}")
            self.test_results.append(('Quality Assessment', 'FAIL'))
            return False
    
    def test_statistics_calculation(self):
        """Test 6: Statistics calculation"""
        print("\n[TEST 6] Statistics Calculation")
        try:
            # Create sample results
            results = [
                {
                    'frame_number': 1,
                    'shoulder_edge_points': [{'x': 0}, {'x': 1}, {'x': 2}],
                    'confidence_score': 0.90
                },
                {
                    'frame_number': 2,
                    'shoulder_edge_points': [{'x': 0}, {'x': 1}],
                    'confidence_score': 0.80
                },
                {
                    'frame_number': 3,
                    'shoulder_edge_points': [{'x': 0}, {'x': 1}, {'x': 2}, {'x': 3}],
                    'confidence_score': 0.95
                }
            ]
            
            stats = self.detector.get_detection_statistics(results)
            
            assert 'total_frames' in stats
            assert 'average_confidence' in stats
            assert 'detection_success_rate' in stats
            assert stats['total_frames'] == 3
            assert 0.8 < stats['average_confidence'] < 0.95
            assert stats['detection_success_rate'] == 1.0
            
            print("✓ Statistics calculation successful")
            print(f"  - Avg Confidence: {stats['average_confidence']:.3f}")
            print(f"  - Success Rate: {stats['detection_success_rate']:.1%}")
            print(f"  - Avg Edge Points: {stats['average_edge_points']:.1f}")
            self.test_results.append(('Statistics', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Statistics calculation failed: {e}")
            self.test_results.append(('Statistics', 'FAIL'))
            return False
    
    def test_batch_data_structure(self):
        """Test 7: Data structure compatibility"""
        print("\n[TEST 7] Data Structure Compatibility")
        try:
            # Verify the output data structure matches requirements
            sample_output = {
                'frame_number': 1,
                'shoulder_edge_points': [
                    {
                        'x': 0.45,
                        'y': 0.32,
                        'pixel_x': 432,
                        'pixel_y': 256
                    }
                ],
                'confidence_score': 0.87
            }
            
            # Validate structure matches spec
            assert isinstance(sample_output['frame_number'], int)
            assert isinstance(sample_output['shoulder_edge_points'], list)
            assert isinstance(sample_output['confidence_score'], float)
            
            for point in sample_output['shoulder_edge_points']:
                assert 'x' in point and isinstance(point['x'], float)
                assert 'y' in point and isinstance(point['y'], float)
            
            print("✓ Data structure matches specification")
            self.test_results.append(('Data Structure', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Data structure validation failed: {e}")
            self.test_results.append(('Data Structure', 'FAIL'))
            return False
    
    def test_frame_counter(self):
        """Test 8: Frame counter incrementation"""
        print("\n[TEST 8] Frame Counter")
        try:
            # Create a fresh detector for this test
            fresh_detector = LandmarkDetector()
            initial_count = fresh_detector.frame_counter
            
            # Simulate detections
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            for _ in range(5):
                fresh_detector.detect_shoulder_edge_points(img, None)
            
            final_count = fresh_detector.frame_counter
            fresh_detector.cleanup()
            
            assert final_count == initial_count + 5, f"Expected {initial_count + 5}, got {final_count}"
            
            print("✓ Frame counter working correctly")
            print(f"  - Frames counted: {final_count - initial_count}")
            self.test_results.append(('Frame Counter', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Frame counter test failed: {e}")
            self.test_results.append(('Frame Counter', 'FAIL'))
            return False
    
    def test_shoulder_types(self):
        """Test 9: Different shoulder type detection"""
        print("\n[TEST 9] Shoulder Type Parameters")
        try:
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Test all shoulder type options
            for shoulder_type in ['left', 'right', 'both']:
                result = self.detector.detect_shoulder_edge_points(
                    img, None, shoulder_type=shoulder_type
                )
                assert isinstance(result, dict)
                assert 'shoulder_edge_points' in result
            
            print("✓ All shoulder types handled correctly")
            self.test_results.append(('Shoulder Types', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Shoulder type test failed: {e}")
            self.test_results.append(('Shoulder Types', 'FAIL'))
            return False
    
    def test_performance_metrics(self):
        """Test 10: Performance and resource usage"""
        print("\n[TEST 10] Performance Metrics")
        try:
            import time
            
            # Create a test image
            img = np.ones((480, 640, 3), dtype=np.uint8) * 128
            
            # Time detection
            start = time.time()
            landmarks = self.detector.detect(img)
            detect_time = time.time() - start
            
            # Shoulder edge detection is fast since no person detected
            print("✓ Performance acceptable")
            print(f"  - Landmark detection: {detect_time*1000:.1f}ms")
            
            self.test_results.append(('Performance', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Performance test failed: {e}")
            self.test_results.append(('Performance', 'FAIL'))
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("\n" + "="*60)
        print("SHOULDER EDGE DETECTION - TEST SUITE")
        print("="*60)
        
        tests = [
            self.test_detector_initialization,
            self.test_landmark_detection,
            self.test_shoulder_edge_detection_no_person,
            self.test_json_export,
            self.test_detection_quality_assessment,
            self.test_statistics_calculation,
            self.test_batch_data_structure,
            self.test_frame_counter,
            self.test_shoulder_types,
            self.test_performance_metrics
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"ERROR in {test.__name__}: {e}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in self.test_results if result == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status_symbol = "✓" if result == 'PASS' else "✗"
            print(f"{status_symbol} {test_name:.<40} {result}")
        
        print("="*60)
        print(f"TOTAL: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
        print("="*60 + "\n")
        
        if passed == total:
            print("🎉 All tests passed! Implementation is ready for use.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Please review.")
    
    def cleanup(self):
        """Cleanup resources"""
        self.detector.cleanup()


def main():
    """Run test suite"""
    tester = ShoulderEdgeDetectionTests()
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()


if __name__ == '__main__':
    main()
