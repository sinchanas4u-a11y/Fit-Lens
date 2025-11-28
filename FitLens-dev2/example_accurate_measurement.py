"""
Example: Complete Accurate Measurement Pipeline
Demonstrates how to use all accuracy improvements together
"""
import numpy as np
from typing import Dict, List
import cv2


def accurate_measurement_pipeline(image_path: str, 
                                  user_height_cm: float,
                                  additional_photos: List[str] = None,
                                  use_calibration: bool = True) -> Dict:
    """
    Complete pipeline with all accuracy improvements
    
    Args:
        image_path: Path to main front view image
        user_height_cm: User's actual height in cm
        additional_photos: List of additional photo paths for averaging
        use_calibration: Whether to apply personal calibration
        
    Returns:
        Dictionary with accurate measurements
    """
    print("\n" + "="*70)
    print("ACCURATE MEASUREMENT PIPELINE")
    print("="*70)
    
    # Step 1: Load required modules
    print("\n[1/7] Loading modules...")
    try:
        from segmentation_model import SegmentationModel
        from landmark_detector import LandmarkDetector
        from measurement_engine import MeasurementEngine
        from calibration_system import PersonalCalibration
        from advanced_measurement_techniques import (
            AdvancedMeasurementTechniques,
            CircumferenceMeasurementV2
        )
        print("✓ All modules loaded")
    except ImportError as e:
        print(f"❌ Error loading modules: {e}")
        return {}
    
    # Step 2: Initialize components
    print("\n[2/7] Initializing components...")
    segmentation = SegmentationModel()
    landmark_detector = LandmarkDetector()
    measurement_engine = MeasurementEngine()
    techniques = AdvancedMeasurementTechniques()
    advanced_measurer = CircumferenceMeasurementV2()
    
    if use_calibration:
        calibration = PersonalCalibration()
        print(f"✓ Personal calibration loaded (factors: "
              f"chest={calibration.calibration_data['chest_factor']:.3f}, "
              f"waist={calibration.calibration_data['waist_factor']:.3f}, "
              f"hip={calibration.calibration_data['hip_factor']:.3f})")
    
    # Step 3: Process main image
    print("\n[3/7] Processing main image...")
    main_measurements = process_single_image(
        image_path, user_height_cm, segmentation, 
        landmark_detector, measurement_engine, advanced_measurer
    )
    
    if not main_measurements:
        print("❌ Failed to process main image")
        return {}
    
    print(f"✓ Main image processed: {len(main_measurements)} measurements")
    
    # Step 4: Process additional photos (if provided)
    all_measurements = [main_measurements]
    
    if additional_photos:
        print(f"\n[4/7] Processing {len(additional_photos)} additional photos...")
        for i, photo_path in enumerate(additional_photos, 1):
            print(f"  Processing photo {i}/{len(additional_photos)}...")
            measurements = process_single_image(
                photo_path, user_height_cm, segmentation,
                landmark_detector, measurement_engine, advanced_measurer
            )
            if measurements:
                all_measurements.append(measurements)
                print(f"  ✓ Photo {i} processed")
            else:
                print(f"  ⚠️ Photo {i} failed, skipping")
        
        print(f"✓ Processed {len(all_measurements)} photos total")
    else:
        print("\n[4/7] No additional photos provided (skipping averaging)")
    
    # Step 5: Average measurements (if multiple photos)
    print("\n[5/7] Calculating final measurements...")
    
    if len(all_measurements) > 1:
        # Multi-photo averaging with outlier removal
        averaged = techniques.multi_photo_averaging(all_measurements)
        
        final_measurements = {}
        for key, (mean, std) in averaged.items():
            final_measurements[key] = mean
            print(f"  {key}: {mean:.1f} ± {std:.1f} cm")
        
        print(f"✓ Averaged {len(all_measurements)} measurements")
    else:
        final_measurements = main_measurements
        print("✓ Using single measurement")
    
    # Step 6: Apply personal calibration
    if use_calibration:
        print("\n[6/7] Applying personal calibration...")
        
        original = final_measurements.copy()
        
        if 'chest_circumference' in final_measurements:
            final_measurements['chest_circumference'] *= calibration.calibration_data['chest_factor']
            print(f"  Chest: {original['chest_circumference']:.1f} → "
                  f"{final_measurements['chest_circumference']:.1f} cm")
        
        if 'waist_circumference' in final_measurements:
            final_measurements['waist_circumference'] *= calibration.calibration_data['waist_factor']
            print(f"  Waist: {original['waist_circumference']:.1f} → "
                  f"{final_measurements['waist_circumference']:.1f} cm")
        
        if 'hip_circumference' in final_measurements:
            final_measurements['hip_circumference'] *= calibration.calibration_data['hip_factor']
            print(f"  Hip: {original['hip_circumference']:.1f} → "
                  f"{final_measurements['hip_circumference']:.1f} cm")
        
        print("✓ Calibration applied")
    else:
        print("\n[6/7] Skipping calibration (use_calibration=False)")
    
    # Step 7: Validate and return
    print("\n[7/7] Validating measurements...")
    
    validation = validate_measurements(final_measurements)
    
    for key, is_valid in validation.items():
        status = "✓" if is_valid else "⚠️"
        value = final_measurements.get(key, 0)
        print(f"  {status} {key}: {value:.1f} cm")
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    if 'chest_circumference' in final_measurements:
        print(f"Chest: {final_measurements['chest_circumference']:.1f} cm")
    if 'waist_circumference' in final_measurements:
        print(f"Waist: {final_measurements['waist_circumference']:.1f} cm")
    if 'hip_circumference' in final_measurements:
        print(f"Hip: {final_measurements['hip_circumference']:.1f} cm")
    
    print("\n" + "="*70)
    
    return final_measurements


def process_single_image(image_path, user_height_cm, segmentation, 
                         landmark_detector, measurement_engine, advanced_measurer):
    """Process a single image and return measurements"""
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        # Segment person
        mask = segmentation.segment_person(image)
        if mask is None:
            return None
        
        # Detect landmarks
        landmarks = landmark_detector.detect_landmarks(image)
        if landmarks is None:
            return None
        
        # Calculate scale factor from height
        detected_height_px = calculate_detected_height(landmarks)
        scale_factor = user_height_cm / detected_height_px
        
        # Get landmark dictionary
        landmark_dict = landmarks_to_dict(landmarks)
        
        # Use advanced measurement with multiple methods
        results = advanced_measurer.measure_with_multiple_methods(
            landmarks, mask, scale_factor, landmark_dict
        )
        
        # Extract values
        measurements = {}
        for key, data in results.items():
            measurements[key] = data['value']
        
        return measurements
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def calculate_detected_height(landmarks):
    """Calculate detected height in pixels"""
    # Top of head (nose) to bottom (ankle)
    nose = landmarks[0]
    left_ankle = landmarks[27]
    right_ankle = landmarks[28]
    
    ankle = (left_ankle + right_ankle) / 2
    height_px = np.linalg.norm(nose[:2] - ankle[:2])
    
    return height_px


def landmarks_to_dict(landmarks):
    """Convert landmarks array to dictionary"""
    landmark_names = [
        'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
        'right_eye_inner', 'right_eye', 'right_eye_outer',
        'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_pinky', 'right_pinky',
        'left_index', 'right_index',
        'left_thumb', 'right_thumb',
        'left_hip', 'right_hip',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle',
        'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index'
    ]
    
    landmark_dict = {}
    for i, name in enumerate(landmark_names):
        if i < len(landmarks):
            landmark_dict[name] = landmarks[i]
    
    return landmark_dict


def validate_measurements(measurements):
    """Validate measurements are within reasonable ranges"""
    validation = {}
    
    ranges = {
        'chest_circumference': (70, 150),
        'waist_circumference': (60, 150),
        'hip_circumference': (70, 160),
    }
    
    for key, value in measurements.items():
        if key in ranges:
            min_val, max_val = ranges[key]
            validation[key] = min_val <= value <= max_val
        else:
            validation[key] = True
    
    return validation


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_basic():
    """Example 1: Basic usage with single photo"""
    print("\nEXAMPLE 1: Basic Usage")
    print("-" * 70)
    
    measurements = accurate_measurement_pipeline(
        image_path='front_view.jpg',
        user_height_cm=175.0,
        use_calibration=True
    )
    
    print(f"\nResults: {measurements}")


def example_multi_photo():
    """Example 2: Multi-photo averaging for best accuracy"""
    print("\nEXAMPLE 2: Multi-Photo Averaging")
    print("-" * 70)
    
    measurements = accurate_measurement_pipeline(
        image_path='photo1.jpg',
        user_height_cm=175.0,
        additional_photos=[
            'photo2.jpg',
            'photo3.jpg',
            'photo4.jpg',
            'photo5.jpg'
        ],
        use_calibration=True
    )
    
    print(f"\nResults: {measurements}")


def example_with_feedback():
    """Example 3: Add feedback to improve calibration"""
    print("\nEXAMPLE 3: Adding Feedback")
    print("-" * 70)
    
    from calibration_system import PersonalCalibration
    
    # Process image
    measurements = accurate_measurement_pipeline(
        image_path='front_view.jpg',
        user_height_cm=175.0,
        use_calibration=True
    )
    
    # User measures with tape
    print("\nNow measure yourself with a tape measure:")
    actual_chest = 95.0  # User's actual measurement
    actual_waist = 80.0
    actual_hip = 98.0
    
    # Add feedback
    calibration = PersonalCalibration()
    calibration.add_measurement_feedback(
        'chest', measurements['chest_circumference'], actual_chest
    )
    calibration.add_measurement_feedback(
        'waist', measurements['waist_circumference'], actual_waist
    )
    calibration.add_measurement_feedback(
        'hip', measurements['hip_circumference'], actual_hip
    )
    
    print("\n✓ Calibration updated! Next measurements will be more accurate.")


def example_custom_body_type():
    """Example 4: Custom body type configuration"""
    print("\nEXAMPLE 4: Custom Body Type")
    print("-" * 70)
    
    from measurement_engine import MeasurementEngine
    
    # Create custom engine with your body type
    engine = MeasurementEngine()
    
    # Athletic build
    engine.chest_depth_ratio = 0.60
    engine.waist_depth_ratio = 0.48
    engine.hip_depth_ratio = 0.52
    
    print("✓ Custom body type configured")
    
    # Then use in your processing...


if __name__ == "__main__":
    print("""
ACCURATE MEASUREMENT EXAMPLES

This file demonstrates how to use all accuracy improvements together.

Available examples:
1. example_basic() - Single photo with calibration
2. example_multi_photo() - Multiple photos for averaging
3. example_with_feedback() - Add feedback to improve calibration
4. example_custom_body_type() - Configure for your body type

To run:
    python example_accurate_measurement.py

Or import and use:
    from example_accurate_measurement import accurate_measurement_pipeline
    
    measurements = accurate_measurement_pipeline(
        image_path='your_photo.jpg',
        user_height_cm=175.0,
        additional_photos=['photo2.jpg', 'photo3.jpg'],
        use_calibration=True
    )
""")
