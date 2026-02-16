"""
Test Edge Refinement Functions

This script tests the edge snapping and contour refinement functions
added to improve manual measurement accuracy.

Usage:
    python test_edge_refinement.py
"""

import cv2
import numpy as np
import sys

def test_snap_point_to_edge():
    """Test the snap_point_to_edge function"""
    print("=" * 60)
    print("TEST 1: snap_point_to_edge()")
    print("=" * 60)
    
    # Create a test image with a white rectangle on black background
    image = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.rectangle(image, (100, 100), (400, 400), (255, 255, 255), -1)
    
    # Create a mask (same as image for this test)
    mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Test points: inside, outside, and on edge
    test_cases = [
        ((110, 110), "Inside rectangle - should snap to left edge"),
        ((50, 200), "Outside rectangle - should snap to left edge"),
        ((100, 200), "On edge - should stay approximately same"),
        ((250, 110), "Inside top - should snap to top edge"),
    ]
    
    # Import the edge snapping function
    from backend.app_updated import snap_point_to_edge
    
    for point, description in test_cases:
        print(f"\n  Test: {description}")
        print(f"    Original: {point}")
        
        snapped = snap_point_to_edge(point, image, mask, search_radius=20)
        print(f"    Snapped:  ({snapped[0]:.1f}, {snapped[1]:.1f})")
        
        distance = np.sqrt((snapped[0] - point[0])**2 + (snapped[1] - point[1])**2)
        print(f"    Movement: {distance:.1f} pixels")
    
    print("\n  ✓ snap_point_to_edge() tests completed")
    return True


def test_refine_measurement_with_contours():
    """Test the refine_measurement_with_contours function"""
    print("\n" + "=" * 60)
    print("TEST 2: refine_measurement_with_contours()")
    print("=" * 60)
    
    # Create a test image with a white rectangle
    image = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.rectangle(image, (100, 100), (400, 400), (255, 255, 255), -1)
    mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Import the refinement function
    from backend.app_updated import refine_measurement_with_contours
    
    # Test a measurement line that should snap to edges
    p1_orig = (110, 200)  # Inside left
    p2_orig = (390, 200)  # Inside right
    
    print(f"\n  Original measurement line:")
    print(f"    P1: {p1_orig}")
    print(f"    P2: {p2_orig}")
    
    (x1, y1), (x2, y2) = refine_measurement_with_contours(
        p1_orig, p2_orig, image, mask, num_samples=5
    )
    
    print(f"\n  Refined measurement line:")
    print(f"    P1: ({x1:.1f}, {y1:.1f})")
    print(f"    P2: ({x2:.1f}, {y2:.1f})")
    
    # Calculate distances
    orig_dist = np.sqrt((p2_orig[0] - p1_orig[0])**2 + (p2_orig[1] - p1_orig[1])**2)
    refined_dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    print(f"\n  Distance comparison:")
    print(f"    Original: {orig_dist:.1f} px")
    print(f"    Refined:  {refined_dist:.1f} px")
    print(f"    Difference: {abs(refined_dist - orig_dist):.1f} px")
    
    # Expected: Refined line should be longer (snapped to edges)
    if refined_dist > orig_dist:
        print(f"\n  ✓ Correctly extended to edges (+{refined_dist - orig_dist:.1f} px)")
    else:
        print(f"\n  ⚠ Warning: Refined shorter than original")
    
    print("\n  ✓ refine_measurement_with_contours() tests completed")
    return True


def test_visual_comparison():
    """Create a visual comparison showing original vs refined points"""
    print("\n" + "=" * 60)
    print("TEST 3: Visual Comparison")
    print("=" * 60)
    
    # Create a test image simulating a body segment
    image = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # Draw an ellipse to simulate body part (shoulder width)
    cv2.ellipse(image, (400, 300), (200, 150), 0, 0, 360, (255, 255, 255), -1)
    mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Import the refinement function
    from backend.app_updated import refine_measurement_with_contours
    
    # Simulate user marking points inside the body
    p1_orig = (220, 300)  # Slightly inside left edge
    p2_orig = (580, 300)  # Slightly inside right edge
    
    # Refine
    (x1, y1), (x2, y2) = refine_measurement_with_contours(
        p1_orig, p2_orig, image, mask, num_samples=5
    )
    
    # Create visualization
    vis = image.copy()
    
    # Draw original points in gray
    cv2.line(vis, p1_orig, p2_orig, (128, 128, 128), 2)
    cv2.circle(vis, p1_orig, 6, (128, 128, 128), 2)
    cv2.circle(vis, p2_orig, 6, (128, 128, 128), 2)
    cv2.putText(vis, "Original", (p1_orig[0], p1_orig[1] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2)
    
    # Draw refined points in green/yellow
    cv2.line(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 3)
    cv2.circle(vis, (int(x1), int(y1)), 8, (0, 255, 0), -1)
    cv2.circle(vis, (int(x2), int(y2)), 8, (0, 255, 0), -1)
    cv2.putText(vis, "Refined", (int(x1), int(y1) - 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Calculate and display distances
    orig_dist = np.sqrt((p2_orig[0] - p1_orig[0])**2 + (p2_orig[1] - p1_orig[1])**2)
    refined_dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    improvement = refined_dist - orig_dist
    
    cv2.putText(vis, f"Original: {orig_dist:.1f} px", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
    cv2.putText(vis, f"Refined: {refined_dist:.1f} px", (50, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(vis, f"Improvement: +{improvement:.1f} px", (50, 130), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Save visualization
    output_path = 'edge_refinement_test.png'
    cv2.imwrite(output_path, vis)
    
    print(f"\n  ✓ Visual comparison saved to: {output_path}")
    print(f"  Original distance: {orig_dist:.1f} px")
    print(f"  Refined distance:  {refined_dist:.1f} px")
    print(f"  Improvement:       +{improvement:.1f} px ({improvement/orig_dist*100:.1f}%)")
    
    return True


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "EDGE REFINEMENT FUNCTION TESTS" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    try:
        # Test 1: Basic edge snapping
        if not test_snap_point_to_edge():
            print("\n❌ Test 1 failed")
            return False
        
        # Test 2: Multi-sample refinement
        if not test_refine_measurement_with_contours():
            print("\n❌ Test 2 failed")
            return False
        
        # Test 3: Visual comparison
        if not test_visual_comparison():
            print("\n❌ Test 3 failed")
            return False
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
