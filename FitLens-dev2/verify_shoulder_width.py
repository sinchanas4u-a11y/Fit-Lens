import cv2
import numpy as np
import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from segmentation_model import SegmentationModel
from backend.landmark_detector import LandmarkDetector
from backend.measurement_engine import MeasurementEngine

def verify_shoulder_pipeline(image_path, user_height_cm=170.0):
    print(f"--- Verifying Shoulder Width Pipeline for {image_path} ---")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return
    
    # Initialize components
    segmenter = SegmentationModel(model_size='n')
    detector = LandmarkDetector()
    measurer = MeasurementEngine()
    
    # STEP 1: Masking
    print("Step 1: Masking...")
    mask = segmenter.segment_person(image)
    if mask is None:
        print("Error: No person detected")
        return
        
    # STEP 2: Landmarks
    print("Step 2: Landmarks...")
    landmarks = detector.detect(image)
    if landmarks is None:
        print("Error: No landmarks detected")
        return
        
    left_shoulder_orig = landmarks[11]
    right_shoulder_orig = landmarks[12]
    print(f"MediaPipe Left Shoulder: {left_shoulder_orig[:2]} (conf: {left_shoulder_orig[2]:.2f})")
    print(f"MediaPipe Right Shoulder: {right_shoulder_orig[:2]} (conf: {right_shoulder_orig[2]:.2f})")
    
    # STEP 3: Edge Keypoints
    print("Step 3: Extracting edge keypoints...")
    edge_keypoints = detector.extract_body_edge_keypoints(mask, landmarks)
    
    if not edge_keypoints.get('is_valid'):
        print("Error: Edge keypoint extraction failed")
        return
        
    shoulder_height = edge_keypoints['shoulder_height']
    shoulder_left = edge_keypoints['shoulder_left']
    shoulder_right = edge_keypoints['shoulder_right']
    height_px = edge_keypoints['height_px']
    
    print(f"Calculated Shoulder Height (avg): {shoulder_height:.2f}")
    print(f"Contour Left Edge at Shoulder Height: {shoulder_left}")
    print(f"Contour Right Edge at Shoulder Height: {shoulder_right}")
    print(f"Total Height in Pixels: {height_px:.2f}")
    
    # STEP 4: Measurements
    print("Step 4: Calculating measurements...")
    scale_factor = user_height_cm / height_px
    measurements = measurer.calculate_measurements_with_confidence(
        landmarks, scale_factor, view='front', edge_reference_points=edge_keypoints, user_height_cm=user_height_cm
    )
    
    if 'shoulder_width' in measurements:
        val, conf, src = measurements['shoulder_width']
        print(f"\nRESULT: Shoulder Width = {val:.2f} cm")
        print(f"Source: {src}")
        print(f"Confidence: {conf:.2f}")
    else:
        print("Error: Shoulder width not calculated")
    
    # STEP 5: Visualization check (Optional manual check)
    print("\nVerification complete. Check printed values above.")

if __name__ == "__main__":
    # Use a dummy image if none provided or just for structure
    # In a real scenario, we'd need a sample image.
    print("This script requires a sample image to run fully.")
    # verify_shoulder_pipeline("sample.jpg")
