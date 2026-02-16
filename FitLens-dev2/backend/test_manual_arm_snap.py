"""
Test Suite for Manual Arm Landmark Snap Functionality
Tests the backend shared point detection logic with various coordinate scenarios
"""

import sys
import os
import numpy as np

# Add parent directory to path to import app_updated
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_updated import detect_shared_shoulder_arm_points


def test_exact_match():
    """Test 1: Exact coordinate match (0px difference)"""
    print("\n" + "="*60)
    print("TEST 1: Exact Coordinate Match")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.0, 'y': 200.0},  # Left shoulder
                {'x': 300.0, 'y': 200.0}   # Right shoulder
            ]
        },
        {
            'type': 'arm',
            'points': [
                {'x': 100.0, 'y': 200.0},  # Arm start - EXACT match with left shoulder
                {'x': 120.0, 'y': 350.0}   # Wrist
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is not None, "Should detect shared point"
    assert result['has_shared_point'] == True, "Should have shared point"
    assert result['side'] == 'left', "Should match left shoulder"
    assert result['arm_shoulder_point_idx'] == 0, "Should be arm start"
    assert result['shoulder_point_idx'] == 0, "Should be left shoulder"
    
    print("✓ TEST 1 PASSED: Exact match detected correctly\n")


def test_sub_pixel_match():
    """Test 2: Sub-pixel difference (< 1px)"""
    print("\n" + "="*60)
    print("TEST 2: Sub-Pixel Coordinate Match")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.00, 'y': 200.00},
                {'x': 300.00, 'y': 200.00}
            ]
        },
        {
            'type': 'arm',
            'points': [
                {'x': 100.45, 'y': 200.32},  # 0.55px difference
                {'x': 120.0, 'y': 350.0}
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is not None, "Should detect shared point"
    assert result['has_shared_point'] == True, "Should match with sub-pixel difference"
    assert result['side'] == 'left', "Should match left shoulder"
    
    print("✓ TEST 2 PASSED: Sub-pixel match detected correctly\n")


def test_within_tolerance():
    """Test 3: Within 10px tolerance"""
    print("\n" + "="*60)
    print("TEST 3: Within Tolerance (5px difference)")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.0, 'y': 200.0},
                {'x': 300.0, 'y': 200.0}
            ]
        },
        {
            'type': 'arm',
            'points': [
                {'x': 105.0, 'y': 203.0},  # ~5.83px difference
                {'x': 120.0, 'y': 350.0}
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is not None, "Should detect shared point"
    assert result['has_shared_point'] == True, "Should match within 10px tolerance"
    
    print("✓ TEST 3 PASSED: Match within tolerance detected correctly\n")


def test_outside_tolerance():
    """Test 4: Outside 10px tolerance"""
    print("\n" + "="*60)
    print("TEST 4: Outside Tolerance (15px difference)")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.0, 'y': 200.0},
                {'x': 300.0, 'y': 200.0}
            ]
        },
        {
            'type': 'arm',
            'points': [
                {'x': 115.0, 'y': 200.0},  # 15px difference
                {'x': 120.0, 'y': 350.0}
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is not None, "Should return result"
    assert result['has_shared_point'] == False, "Should NOT match outside tolerance"
    
    print("✓ TEST 4 PASSED: No match outside tolerance (as expected)\n")


def test_right_shoulder_match():
    """Test 5: Match with right shoulder"""
    print("\n" + "="*60)
    print("TEST 5: Right Shoulder Match")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.0, 'y': 200.0},  # Left
                {'x': 300.0, 'y': 200.0}   # Right
            ]
        },
        {
            'type': 'arm',
            'points': [
                {'x': 300.0, 'y': 200.0},  # Arm start - matches RIGHT shoulder
                {'x': 320.0, 'y': 350.0}
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is not None, "Should detect shared point"
    assert result['has_shared_point'] == True, "Should have shared point"
    assert result['side'] == 'right', "Should match RIGHT shoulder"
    assert result['shoulder_point_idx'] == 1, "Should be right shoulder (index 1)"
    
    print("✓ TEST 5 PASSED: Right shoulder match detected correctly\n")


def test_arm_end_at_shoulder():
    """Test 6: Arm END point at shoulder (reverse direction)"""
    print("\n" + "="*60)
    print("TEST 6: Arm End at Shoulder")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.0, 'y': 200.0},
                {'x': 300.0, 'y': 200.0}
            ]
        },
        {
            'type': 'arm',
            'points': [
                {'x': 120.0, 'y': 350.0},  # Wrist (start)
                {'x': 100.0, 'y': 200.0}   # Shoulder (end) - matches left shoulder
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is not None, "Should detect shared point"
    assert result['has_shared_point'] == True, "Should have shared point"
    assert result['arm_shoulder_point_idx'] == 1, "Should be arm END (index 1)"
    assert result['side'] == 'left', "Should match left shoulder"
    
    print("✓ TEST 6 PASSED: Arm end at shoulder detected correctly\n")


def test_no_shoulder_landmark():
    """Test 7: No shoulder landmark present"""
    print("\n" + "="*60)
    print("TEST 7: No Shoulder Landmark")
    print("="*60)
    
    landmarks = [
        {
            'type': 'arm',
            'points': [
                {'x': 100.0, 'y': 200.0},
                {'x': 120.0, 'y': 350.0}
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is None, "Should return None when no shoulder landmark"
    
    print("✓ TEST 7 PASSED: Correctly handles missing shoulder landmark\n")


def test_no_arm_landmark():
    """Test 8: No arm landmark present"""
    print("\n" + "="*60)
    print("TEST 8: No Arm Landmark")
    print("="*60)
    
    landmarks = [
        {
            'type': 'shoulder',
            'points': [
                {'x': 100.0, 'y': 200.0},
                {'x': 300.0, 'y': 200.0}
            ]
        }
    ]
    
    result = detect_shared_shoulder_arm_points(landmarks)
    
    assert result is None, "Should return None when no arm landmark"
    
    print("✓ TEST 8 PASSED: Correctly handles missing arm landmark\n")


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*60)
    print("MANUAL ARM SNAP - BACKEND TEST SUITE")
    print("="*60)
    print("Testing detect_shared_shoulder_arm_points() function")
    print("="*60)
    
    tests = [
        test_exact_match,
        test_sub_pixel_match,
        test_within_tolerance,
        test_outside_tolerance,
        test_right_shoulder_match,
        test_arm_end_at_shoulder,
        test_no_shoulder_landmark,
        test_no_arm_landmark
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ TEST FAILED: {test.__name__}")
            print(f"  Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ TEST ERROR: {test.__name__}")
            print(f"  Error: {e}\n")
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed. Please review.\n")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
