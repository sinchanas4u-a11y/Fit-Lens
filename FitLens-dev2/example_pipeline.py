"""
Example: Exact Pipeline Implementation
Demonstrates the complete YOLOv8-seg + MediaPipe + Canny pipeline with height-based scaling
"""
import cv2
import numpy as np
from segmentation_model import SegmentationModel
from backend.landmark_detector import LandmarkDetector
from backend.measurement_engine import MeasurementEngine


def demonstrate_pipeline(image_path: str, user_height_cm: float = 170.0):
    """
    Demonstrate the exact pipeline:
    1. YOLOv8-seg for precise human body masking (remove background)
    2. Feed masked image to MediaPipe Pose for all 33 landmarks (shoulders=11/12, hips=23/24)
    3. Canny edge detection + findContours on mask for body edge keypoints
    4. Compute measurements with OpenCV distances + NumPy scaling (user_height_cm / height_px)
    
    Args:
        image_path: Path to input image
        user_height_cm: User's actual height in centimeters (e.g., 170)
    """
    print("\n" + "="*70)
    print("EXACT PIPELINE DEMONSTRATION")
    print("="*70)
    
    # Initialize components
    print("\nInitializing components...")
    segmenter = SegmentationModel(model_size='n')
    detector = LandmarkDetector()
    measurer = MeasurementEngine()
    print("✓ Components initialized")
    
    # Load image
    print(f"\nLoading image: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print("✗ Failed to load image")
        return
    
    h, w = image.shape[:2]
    print(f"✓ Image loaded: {w}x{h} pixels")
    
    # STEP 1: YOLOv8-seg for precise masking
    print("\n" + "-"*70)
    print("STEP 1: YOLOv8-seg for precise human body masking")
    print("-"*70)
    mask = segmenter.segment_person(image, conf_threshold=0.5)
    
    if mask is None:
        print("✗ No person detected")
        return
    
    print("✓ Human body segmented")
    print("  - Background noise removed")
    print("  - Binary mask generated (255=person, 0=background)")
    
    # Apply mask to remove background
    masked_image = segmenter.apply_mask(image, mask, background_mode='remove')
    print("✓ Masked image created")
    
    # STEP 2: MediaPipe Pose for all 33 landmarks
    print("\n" + "-"*70)
    print("STEP 2: Feed masked image to MediaPipe Pose")
    print("-"*70)
    print("Detecting all 33 body landmarks...")
    print("  - Shoulders: indices 11 (left), 12 (right)")
    print("  - Hips: indices 23 (left), 24 (right)")
    print("  - Plus elbows, wrists, knees, ankles, etc.")
    
    landmarks = detector.detect(masked_image, mask=mask)
    
    if landmarks is None:
        print("✗ No landmarks detected")
        return
    
    print(f"✓ Detected {len(landmarks)} landmarks")
    print(f"  - Landmark shape: {landmarks.shape}")
    print(f"  - Each landmark: [x_pixels, y_pixels, confidence]")
    print(f"\nSample landmarks:")
    print(f"  Left shoulder (11):  x={landmarks[11][0]:.1f}, y={landmarks[11][1]:.1f}, conf={landmarks[11][2]:.2f}")
    print(f"  Right shoulder (12): x={landmarks[12][0]:.1f}, y={landmarks[12][1]:.1f}, conf={landmarks[12][2]:.2f}")
    print(f"  Left hip (23):       x={landmarks[23][0]:.1f}, y={landmarks[23][1]:.1f}, conf={landmarks[23][2]:.2f}")
    print(f"  Right hip (24):      x={landmarks[24][0]:.1f}, y={landmarks[24][1]:.1f}, conf={landmarks[24][2]:.2f}")
    
    # STEP 3: Canny edge detection + findContours
    print("\n" + "-"*70)
    print("STEP 3: OpenCV Canny edge detection + findContours")
    print("-"*70)
    print("Extracting body edge keypoints from mask...")
    
    edge_keypoints = detector.extract_body_edge_keypoints(mask, landmarks)
    
    if not edge_keypoints.get('is_valid'):
        print("✗ Edge keypoint extraction failed")
        return
    
    height_px = edge_keypoints['height_px']
    print(f"✓ Body edge keypoints extracted")
    print(f"  - Head-to-toe height: {height_px:.1f} pixels")
    print(f"  - Contours found: {len(edge_keypoints.get('contours', []))}")
    print(f"\nEdge keypoints at key body heights:")
    print(f"  Shoulder left:  {edge_keypoints.get('shoulder_left')}")
    print(f"  Shoulder right: {edge_keypoints.get('shoulder_right')}")
    print(f"  Chest left:     {edge_keypoints.get('chest_left')}")
    print(f"  Chest right:    {edge_keypoints.get('chest_right')}")
    print(f"  Waist left:     {edge_keypoints.get('waist_left')}")
    print(f"  Waist right:    {edge_keypoints.get('waist_right')}")
    print(f"  Hip left:       {edge_keypoints.get('hip_left')}")
    print(f"  Hip right:      {edge_keypoints.get('hip_right')}")
    
    # STEP 4: Compute measurements with height-based scaling
    print("\n" + "-"*70)
    print("STEP 4: Compute measurements")
    print("-"*70)
    print("Formula: measurement_cm = pixel_distance * (user_height_cm / height_px)")
    print(f"\nCalculating scale factor:")
    print(f"  user_height_cm = {user_height_cm} cm")
    print(f"  height_px = {height_px:.1f} pixels")
    
    scale_factor = user_height_cm / height_px
    print(f"  scale_factor = {user_height_cm} / {height_px:.1f} = {scale_factor:.4f} cm/pixel")
    
    print(f"\nCalculating measurements...")
    measurements = measurer.calculate_measurements_with_confidence(
        landmarks=landmarks,
        scale_factor=scale_factor,
        view='front',
        edge_reference_points=edge_keypoints,
        user_height_cm=user_height_cm
    )
    
    print(f"✓ Calculated {len(measurements)} measurements")
    
    # Display measurements
    print("\n" + "="*70)
    print("MEASUREMENTS RESULTS")
    print("="*70)
    print(f"{'Measurement':<20} {'Value':<12} {'Confidence':<12} {'Source':<30}")
    print("-"*70)
    
    for name, (value, confidence, source) in measurements.items():
        print(f"{name:<20} {value:>6.1f} cm    {confidence:>5.1%}       {source:<30}")
    
    # Calculate some derived measurements
    if 'shoulder_width' in measurements and 'hip_width' in measurements:
        shoulder_cm = measurements['shoulder_width'][0]
        hip_cm = measurements['hip_width'][0]
        ratio = shoulder_cm / hip_cm if hip_cm > 0 else 0
        print(f"\n{'Shoulder/Hip Ratio':<20} {ratio:>6.2f}")
    
    # Visualize results
    print("\n" + "="*70)
    print("VISUALIZATION")
    print("="*70)
    
    # Draw landmarks on masked image
    vis_image = masked_image.copy()
    vis_image = detector.draw_landmarks(vis_image, landmarks)
    
    # Draw edge contours
    if edge_keypoints.get('contours'):
        cv2.drawContours(vis_image, edge_keypoints['contours'], -1, (0, 255, 0), 2)
    
    # Draw edge keypoints
    for key in ['shoulder_left', 'shoulder_right', 'chest_left', 'chest_right',
                'waist_left', 'waist_right', 'hip_left', 'hip_right']:
        point = edge_keypoints.get(key)
        if point and point != (0, 0):
            cv2.circle(vis_image, point, 6, (0, 255, 255), -1)
    
    # Add text overlay
    y_offset = 30
    cv2.putText(vis_image, f"Height: {user_height_cm} cm", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    y_offset += 30
    cv2.putText(vis_image, f"Scale: {scale_factor:.4f} cm/px", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    y_offset += 30
    
    for name, (value, confidence, source) in list(measurements.items())[:5]:
        text = f"{name}: {value:.1f} cm"
        cv2.putText(vis_image, text, (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        y_offset += 25
    
    # Save visualization
    output_path = "output/pipeline_demo.png"
    import os
    os.makedirs("output", exist_ok=True)
    cv2.imwrite(output_path, vis_image)
    print(f"✓ Visualization saved: {output_path}")
    
    print("\n" + "="*70)
    print("✓ PIPELINE DEMONSTRATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python example_pipeline.py <image_path> [user_height_cm]")
        print("Example: python example_pipeline.py photo.jpg 170")
        sys.exit(1)
    
    image_path = sys.argv[1]
    user_height = float(sys.argv[2]) if len(sys.argv) > 2 else 170.0
    
    demonstrate_pipeline(image_path, user_height)
