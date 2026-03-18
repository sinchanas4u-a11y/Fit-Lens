"""
Hybrid Shoulder Width Detection Example
Demonstrates MediaPipe + YOLOv8 + OpenCV contour approach
"""
import cv2
import numpy as np
from pathlib import Path

# Import the required modules
try:
    from segmentation_model import SegmentationModel
    from landmark_detector import LandmarkDetector
    from measurement_engine import MeasurementEngine
    from hybrid_shoulder_detector import HybridShoulderDetector
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Error importing modules: {e}")
    exit(1)


def run_hybrid_shoulder_detection(image_path: str, user_height_cm: float = None):
    """
    Run complete hybrid shoulder detection pipeline
    
    Pipeline:
    1. Load image with YOLOv8 segmentation
    2. Detect landmarks with MediaPipe
    3. Extract body edges with OpenCV
    4. Find shoulder points using contour extraction
    5. Calculate shoulder width using edge points
    """
    
    print(f"\n{'='*70}")
    print(f"HYBRID SHOULDER DETECTION PIPELINE")
    print(f"{'='*70}")
    print(f"\nInput image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"✗ Failed to load image: {image_path}")
        return None
    
    h, w = image.shape[:2]
    print(f"Image size: {w}x{h} pixels")
    
    print(f"\n{'─'*70}")
    print("STEP 1: YOLOv8-SEG FOR BODY SEGMENTATION")
    print(f"{'─'*70}")
    
    # Initialize and run YOLOv8 segmentation
    seg_model = SegmentationModel(model_size='n')
    mask = seg_model.segment_person(image, conf_threshold=0.5)
    
    if mask is None:
        print("✗ No person detected by YOLOv8")
        return None
    
    print(f"✓ Person segmented successfully")
    print(f"  Mask size: {mask.shape}")
    mask_pixels = np.count_nonzero(mask)
    print(f"  Person pixels: {mask_pixels:,} ({100*mask_pixels/(h*w):.1f}% of image)")
    
    # Apply mask to clean image
    masked_image = seg_model.apply_mask(image, mask, background_mode='remove')
    
    print(f"\n{'─'*70}")
    print("STEP 2: MEDIAPIPE POSE FOR KEYPOINT DETECTION")
    print(f"{'─'*70}")
    
    # Initialize and run MediaPipe
    landmark_detector = LandmarkDetector()
    landmarks = landmark_detector.detect(masked_image)
    
    if landmarks is None:
        print("✗ No landmarks detected by MediaPipe")
        return None
    
    print(f"✓ {len(landmarks)} landmarks detected")
    
    # Get shoulder landmarks
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    print(f"  Left shoulder (11): ({left_shoulder[0]:.1f}, {left_shoulder[1]:.1f}) conf={left_shoulder[2]:.2f}")
    print(f"  Right shoulder (12): ({right_shoulder[0]:.1f}, {right_shoulder[1]:.1f}) conf={right_shoulder[2]:.2f}")
    print(f"  Shoulder Y-level: {(left_shoulder[1] + right_shoulder[1])/2:.1f}")
    
    print(f"\n{'─'*70}")
    print("STEP 3: OPENCV CANNY + CONTOUR EXTRACTION")
    print(f"{'─'*70}")
    
    # Extract body edge keypoints using OpenCV
    edge_keypoints = landmark_detector.extract_body_edge_keypoints(mask, landmarks)
    
    if edge_keypoints['is_valid']:
        print(f"✓ Body contours extracted")
        print(f"  Height: {edge_keypoints['height_px']:.1f} pixels")
        print(f"  Topmost point: {edge_keypoints['topmost']}")
        print(f"  Bottommost point: {edge_keypoints['bottommost']}")
        print(f"  Leftmost point: {edge_keypoints['leftmost']}")
        print(f"  Rightmost point: {edge_keypoints['rightmost']}")
        print(f"  Shoulder Y-level (from edges): {edge_keypoints['shoulder_y']}")
        print(f"  Left shoulder edge: {edge_keypoints['left_shoulder_edge']}")
        print(f"  Right shoulder edge: {edge_keypoints['right_shoulder_edge']}")
        print(f"  Shoulder width (edges): {edge_keypoints['shoulder_width_px']:.1f} pixels")
    else:
        print(f"⚠️ {edge_keypoints.get('error', 'Unknown error')}")
    
    print(f"\n{'─'*70}")
    print("STEP 4: HYBRID SHOULDER DETECTION")
    print(f"{'─'*70}")
    
    # Calculate scale factor from user height if provided
    if user_height_cm is not None:
        # Find body height in pixels
        body_top = np.min(np.where(np.any(mask, axis=1))[0])
        body_bottom = np.max(np.where(np.any(mask, axis=1))[0])
        body_height_px = body_bottom - body_top
        scale_factor = user_height_cm / body_height_px
        print(f"User height: {user_height_cm} cm")
        print(f"Body height (pixels): {body_height_px}")
        print(f"Scale factor: {scale_factor:.4f} cm/pixel")
    else:
        # Default estimate: assume average human = 170 cm
        body_top = np.min(np.where(np.any(mask, axis=1))[0])
        body_bottom = np.max(np.where(np.any(mask, axis=1))[0])
        body_height_px = body_bottom - body_top
        user_height_cm = 170
        scale_factor = user_height_cm / body_height_px
        print(f"Estimated user height: {user_height_cm} cm (default)")
        print(f"Body height (pixels): {body_height_px}")
        print(f"Scale factor: {scale_factor:.4f} cm/pixel")
    
    # Initialize measurement engine and hybrid detector
    measurement_engine = MeasurementEngine()
    
    # Use hybrid shoulder detector
    hybrid_result = measurement_engine.calculate_shoulder_width_hybrid(
        image, mask, landmarks, scale_factor, debug=True
    )
    
    print(f"\n✓ HYBRID SHOULDER DETECTION RESULTS:")
    print(f"  Shoulder width (pixels): {hybrid_result['shoulder_width_px']:.1f}")
    print(f"  Shoulder width (cm): {hybrid_result['shoulder_width_cm']:.2f}")
    print(f"  Confidence: {hybrid_result['confidence']:.2f}")
    print(f"  Source: {hybrid_result['source']}")
    print(f"  Shoulder Y-level: {hybrid_result['shoulder_y']}")
    print(f"  Left edge: {hybrid_result['left_shoulder']}")
    print(f"  Right edge: {hybrid_result['right_shoulder']}")
    
    print(f"\n{'─'*70}")
    print("STEP 5: COMPARISON - MEDIAPIPE vs HYBRID")
    print(f"{'─'*70}")
    
    # Compare MediaPipe direct measurement vs hybrid
    mediapipe_width_px = abs(right_shoulder[0] - left_shoulder[0])
    mediapipe_width_cm = mediapipe_width_px * scale_factor
    
    print(f"MediaPipe direct measurement:")
    print(f"  Width (pixels): {mediapipe_width_px:.1f}")
    print(f"  Width (cm): {mediapipe_width_cm:.2f}")
    
    print(f"\nHybrid edge-based measurement:")
    print(f"  Width (pixels): {hybrid_result['shoulder_width_px']:.1f}")
    print(f"  Width (cm): {hybrid_result['shoulder_width_cm']:.2f}")
    
    if hybrid_result['shoulder_width_px'] is not None:
        diff = abs(hybrid_result['shoulder_width_px'] - mediapipe_width_px)
        pct_diff = 100 * diff / mediapipe_width_px if mediapipe_width_px > 0 else 0
        print(f"\nDifference:")
        print(f"  Pixels: {diff:.1f} ({pct_diff:.1f}%)")
        print(f"  cm: {diff * scale_factor:.2f}")
    
    # Save visualizations
    output_dir = Path("hybrid_shoulder_results")
    output_dir.mkdir(exist_ok=True)
    
    # Save original with landmarks
    vis_image = image.copy()
    for i, lm in enumerate(landmarks):
        cv2.circle(vis_image, (int(lm[0]), int(lm[1])), 5, (0, 0, 255), -1)
    
    # Draw MediaPipe shoulders
    cv2.circle(vis_image, (int(left_shoulder[0]), int(left_shoulder[1])), 8, (255, 0, 0), 2)
    cv2.circle(vis_image, (int(right_shoulder[0]), int(right_shoulder[1])), 8, (255, 0, 0), 2)
    cv2.line(vis_image, 
             (int(left_shoulder[0]), int(left_shoulder[1])),
             (int(right_shoulder[0]), int(right_shoulder[1])),
             (255, 0, 0), 2)
    
    # Draw hybrid shoulders if available
    if hybrid_result['left_shoulder'] and hybrid_result['right_shoulder']:
        left = hybrid_result['left_shoulder']
        right = hybrid_result['right_shoulder']
        cv2.circle(vis_image, (int(left[0]), int(left[1])), 8, (0, 255, 0), 2)
        cv2.circle(vis_image, (int(right[0]), int(right[1])), 8, (0, 255, 0), 2)
        cv2.line(vis_image, (int(left[0]), int(left[1])), (int(right[0]), int(right[1])), (0, 255, 0), 2)
        
        # Add text annotations
        cv2.putText(vis_image, f"MediaPipe: {mediapipe_width_cm:.1f}cm", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(vis_image, f"Hybrid: {hybrid_result['shoulder_width_cm']:.1f}cm", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imwrite(str(output_dir / "comparison.jpg"), vis_image)
    print(f"\n✓ Saved comparison image to {output_dir / 'comparison.jpg'}")
    
    # Save mask visualization
    cv2.imwrite(str(output_dir / "mask.jpg"), mask)
    print(f"✓ Saved mask to {output_dir / 'mask.jpg'}")
    
    # Save debug image if available
    if hybrid_result['debug_image'] is not None:
        cv2.imwrite(str(output_dir / "debug.jpg"), hybrid_result['debug_image'])
        print(f"✓ Saved debug visualization to {output_dir / 'debug.jpg'}")
    
    landmark_detector.cleanup()
    
    return {
        'hybrid_result': hybrid_result,
        'mediapipe_width_cm': mediapipe_width_cm,
        'scale_factor': scale_factor,
        'edge_keypoints': edge_keypoints,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Shoulder Detection Demo")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("--height", type=float, default=None, 
                       help="User height in cm for calibration (default: 170)")
    
    args = parser.parse_args()
    
    result = run_hybrid_shoulder_detection(args.image, args.height)
    
    if result:
        print(f"\n{'='*70}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*70}\n")
