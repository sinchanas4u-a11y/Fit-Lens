"""
HYBRID SHOULDER DETECTION - QUICK REFERENCE GUIDE

This guide shows the fastest way to integrate hybrid shoulder detection
into your existing code.
"""

# ============================================================================
# QUICK START: 3-STEP INTEGRATION
# ============================================================================

# OPTION 1: Using MeasurementEngine (Recommended)
# ─────────────────────────────────────────────────────────────────────────

from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
import cv2

# Initialize
image = cv2.imread('photo.jpg')
seg_model = SegmentationModel(model_size='n')
detector = LandmarkDetector()
engine = MeasurementEngine()

# Get mask and landmarks
mask = seg_model.segment_person(image)
landmarks = detector.detect(image)

# Calculate shoulder width with hybrid detection
scale_factor = 0.1  # pixels to cm
result = engine.calculate_shoulder_width_hybrid(
    image=image,
    mask=mask,
    landmarks=landmarks,
    scale_factor=scale_factor,
    debug=True  # Shows 2x2 visualization grid
)

# Use result
shoulder_width_cm = result['shoulder_width_cm']
confidence = result['confidence']
print(f"Shoulder width: {shoulder_width_cm:.2f} cm (confidence: {confidence:.2f})")


# ============================================================================
# OPTION 2: Direct HybridShoulderDetector Use
# ─────────────────────────────────────────────────────────────────────────

from hybrid_shoulder_detector import HybridShoulderDetector

# Initialize
hybrid = HybridShoulderDetector()

# Detect (assuming mask and landmarks are already available)
result = hybrid.detect_shoulder_width(
    image=image,
    mask=mask,
    landmarks=landmarks,
    scale_factor=scale_factor,
    debug=True
)

# With scikit-image refinement (optional)
result_refined = hybrid.detect_shoulder_width_with_refinement(
    image=image,
    mask=mask,
    landmarks=landmarks,
    scale_factor=scale_factor,
    use_scikit_image=True,
    debug=True
)


# ============================================================================
# OPTION 3: Using Contour Extraction Directly
# ─────────────────────────────────────────────────────────────────────────

# Get body edge keypoints using pure contour method
edge_keypoints = detector.extract_body_edge_keypoints(mask, landmarks)

if edge_keypoints['is_valid']:
    shoulder_width_px = edge_keypoints['shoulder_width_px']
    shoulder_width_cm = shoulder_width_px * scale_factor
    
    left_shoulder = edge_keypoints['left_shoulder_edge']
    right_shoulder = edge_keypoints['right_shoulder_edge']
    
    print(f"Shoulder width: {shoulder_width_cm:.2f} cm")
    print(f"Left shoulder: {left_shoulder}")
    print(f"Right shoulder: {right_shoulder}")


# ============================================================================
# COMPARISON: MediaPipe vs Hybrid
# ─────────────────────────────────────────────────────────────────────────

# Get MediaPipe direct measurement
left_shoulder_mp = landmarks[11, :2]
right_shoulder_mp = landmarks[12, :2]
width_mp_px = abs(right_shoulder_mp[0] - left_shoulder_mp[0])
width_mp_cm = width_mp_px * scale_factor

# Get hybrid edge-based measurement
width_hybrid_cm = result['shoulder_width_cm']

# Compare
print(f"\nComparison:")
print(f"  MediaPipe direct:  {width_mp_cm:.2f} cm")
print(f"  Hybrid (edges):    {width_hybrid_cm:.2f} cm")
print(f"  Difference:        {abs(width_mp_cm - width_hybrid_cm):.2f} cm")


# ============================================================================
# CALIBRATION: Scale Factor Calculation
# ─────────────────────────────────────────────────────────────────────────

import numpy as np

def calculate_scale_factor(mask, known_height_cm):
    """Calculate pixels-to-cm conversion factor"""
    # Find body height in pixels
    body_y_coords = np.where(np.any(mask, axis=1))[0]
    if len(body_y_coords) == 0:
        return None
    
    body_height_px = body_y_coords[-1] - body_y_coords[0]
    scale_factor = known_height_cm / body_height_px
    return scale_factor

# Usage
user_height_cm = 170  # Known user height
scale_factor = calculate_scale_factor(mask, user_height_cm)


# ============================================================================
# INTEGRATION INTO EXISTING PIPELINE
# ─────────────────────────────────────────────────────────────────────────

def measure_body_with_hybrid(image, mask, landmarks, user_height_cm=170):
    """Complete measurement pipeline with hybrid shoulder detection"""
    
    # Calculate scale factor from body height
    body_y_coords = np.where(np.any(mask, axis=1))[0]
    body_height_px = body_y_coords[-1] - body_y_coords[0]
    scale_factor = user_height_cm / body_height_px
    
    # Initialize engine
    engine = MeasurementEngine()
    
    # Get hybrid shoulder width
    shoulder_result = engine.calculate_shoulder_width_hybrid(
        image, mask, landmarks, scale_factor, debug=False
    )
    
    # Get other measurements
    overall_measurements = engine.calculate_measurements_with_confidence(
        landmarks, scale_factor, view='front'
    )
    
    # Replace shoulder_width with hybrid measurement if available
    if shoulder_result['shoulder_width_cm'] is not None:
        overall_measurements['shoulder_width'] = (
            shoulder_result['shoulder_width_cm'],
            shoulder_result['confidence'],
            'hybrid'
        )
    
    return overall_measurements, shoulder_result


# ============================================================================
# VISUALIZATION: Drawing Results
# ─────────────────────────────────────────────────────────────────────────

import cv2

def visualize_shoulder_detection(image, result, scale_factor):
    """Visualize both MediaPipe and hybrid shoulder detection"""
    vis = image.copy()
    
    # Draw shoulder Y-level line
    if result['shoulder_y'] is not None:
        h, w = image.shape[:2]
        cv2.line(vis, (0, result['shoulder_y']), (w, result['shoulder_y']),
                 (0, 255, 255), 2)
    
    # Draw detected shoulder points
    if result['left_shoulder'] is not None:
        cv2.circle(vis, tuple(map(int, result['left_shoulder'])), 8, (0, 255, 0), -1)
    if result['right_shoulder'] is not None:
        cv2.circle(vis, tuple(map(int, result['right_shoulder'])), 8, (0, 255, 0), -1)
    
    # Draw connecting line
    if result['left_shoulder'] and result['right_shoulder']:
        cv2.line(vis,
                 tuple(map(int, result['left_shoulder'])),
                 tuple(map(int, result['right_shoulder'])),
                 (0, 255, 0), 2)
    
    # Add text
    text = f"Shoulder: {result['shoulder_width_cm']:.1f}cm (conf: {result['confidence']:.2f})"
    cv2.putText(vis, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return vis


# ============================================================================
# TROUBLESHOOTING CHECKLIST
# ─────────────────────────────────────────────────────────────────────────

troubleshooting = {
    "Poor shoulder point detection": [
        "✓ Check YOLOv8 mask quality (should be clean binary)",
        "✓ Verify Canny edge detection output",
        "✓ Validate MediaPipe shoulder visibility > 0.3"
    ],
    
    "Low confidence scores": [
        "✓ Check if landmarks are properly detected",
        "✓ Ensure shoulders are clearly visible",
        "✓ Verify image resolution is adequate (720p+)"
    ],
    
    "Inconsistent measurements": [
        "✓ Verify scale_factor is correct",
        "✓ Check for extreme poses or tilted shoulders",
        "✓ Ensure consistent image size for calibration"
    ]
}

for issue, solutions in troubleshooting.items():
    print(f"\n{issue}:")
    for solution in solutions:
        print(f"  {solution}")


# ============================================================================
# PERFORMANCE OPTIMIZATION
# ─────────────────────────────────────────────────────────────────────────

# For real-time processing:
class RealtimeShoulderDetector:
    def __init__(self):
        self.seg_model = SegmentationModel(model_size='n')  # Fast nano model
        self.detector = LandmarkDetector()
        self.engine = MeasurementEngine()
    
    def process_frame(self, frame, scale_factor):
        """Process single video frame"""
        # Fast segmentation
        mask = self.seg_model.segment_person(frame, conf_threshold=0.5)
        if mask is None:
            return None
        
        # Fast landmark detection
        landmarks = self.detector.detect(frame)
        if landmarks is None:
            return None
        
        # Hybrid shoulder detection (no debug for speed)
        result = self.engine.calculate_shoulder_width_hybrid(
            frame, mask, landmarks, scale_factor, debug=False
        )
        
        return result


# ============================================================================
# DEPENDENCIES CHECK
# ─────────────────────────────────────────────────────────────────────────

def check_dependencies():
    """Verify all required packages are installed"""
    required = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'mediapipe': 'mediapipe',
        'ultralytics': 'ultralytics',
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages:")
        print(f"pip install {' '.join(missing)}")
    
    return len(missing) == 0

# ============================================================================
# EXAMPLE: Complete Measurement Script
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Check dependencies
    if not check_dependencies():
        exit(1)
    
    # Load image
    image = cv2.imread('sample_image.jpg')
    if image is None:
        print("Error: Cannot load image")
        exit(1)
    
    # Get mask and landmarks
    seg_model = SegmentationModel(model_size='n')
    detector = LandmarkDetector()
    
    mask = seg_model.segment_person(image)
    landmarks = detector.detect(image)
    
    if mask is None or landmarks is None:
        print("Error: Could not detect person")
        exit(1)
    
    # Calculate scale factor (assuming user height = 170 cm)
    body_y_coords = np.where(np.any(mask, axis=1))[0]
    body_height_px = body_y_coords[-1] - body_y_coords[0]
    scale_factor = 170 / body_height_px
    
    # Get measurements
    engine = MeasurementEngine()
    result = engine.calculate_shoulder_width_hybrid(
        image, mask, landmarks, scale_factor, debug=False
    )
    
    # Display result
    print(f"\nResults:")
    print(f"  Shoulder width: {result['shoulder_width_cm']:.2f} cm")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Source: {result['source']}")
    
    # Clean up
    detector.cleanup()
