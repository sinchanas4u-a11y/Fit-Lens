# Hybrid Vision Approach - Complete Documentation

## Overview

FitLens now uses a **Hybrid Vision Approach** that combines:
- **YOLOv8 Segmentation** for precise body edge detection (shoulder, chest, waist, hip widths)
- **MediaPipe Pose** for skeletal joint tracking (elbows, wrists, knees, ankles)
- **MediaPipe Face Mesh** for facial landmark detection

This approach achieves higher accuracy for width measurements while maintaining backward compatibility with existing joint-based measurements.

## Architecture

### Component 1: YOLOv8 Body Segmentation
**Purpose**: Generate binary masks of the person for width-based measurements

```
Input Image → YOLOv8 Segmentation → Binary Mask (255=person, 0=background)
    ↓
Extract Body Contour → Smooth with approxPolyDP
    ↓
Find Edge Points at Shoulder/Waist/Hip levels
```

**Advantages**:
- Precise body boundaries unaffected by clothing texture
- Consistent edge detection across different body types
- Naturally handles occlusions within the body contour

**Usage**:
```python
from landmark_detector import LandmarkDetector

detector = LandmarkDetector()

# Extract body contour from segmentation mask
contour = detector.extract_body_contour(mask)

# Get edge reference points (shoulder, waist, hip edges)
edge_points = detector.extract_edge_reference_points(contour, h, w, landmarks)
```

### Component 2: MediaPipe Pose (33 Landmarks)
**Purpose**: Track skeletal joints for movement and span-based measurements

**Selected Landmarks for Measurements**:
- Index 11: Left shoulder
- Index 12: Right shoulder
- Index 13: Left elbow
- Index 14: Right elbow
- Index 15: Left wrist
- Index 16: Right wrist
- Index 23: Left hip
- Index 24: Right hip
- Index 25: Left knee
- Index 26: Right knee
- Index 27: Left ankle
- Index 28: Right ankle

**NOT Used for Measurements** (replaced by segmentation edges):
- Shoulder width (replaced by edge-based measurement)
- Waist/hip width (replaced by edge-based measurements)

### Component 3: MediaPipe Face Mesh (468 Landmarks)
**Purpose**: Detect facial features for facial measurements

```python
face_landmarks = detector.detect_face_landmarks(image)
```

Returns array of 468 landmarks with (x, y, z, presence) for each point.

## Measurement Categorization

### Edge-Based Measurements (from YOLOv8 Contour)
These measurements use the body contour edges:

| Measurement | Calculation | Typical Range |
|---|---|---|
| `shoulder_width` | Distance between left and right shoulder edges | 25-65 cm |
| `chest_width` | Distance between left and right chest edges | 20-55 cm |
| `waist_width` | Distance between left and right waist edges | 18-45 cm |
| `hip_width` | Distance between left and right hip edges | 25-55 cm |

**Example**:
```python
edge_points = {
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

# shoulder_width = distance((100,200), (300,200)) × scale_factor
# = 200 pixels × 0.1 cm/pixel = 20 cm
```

### Joint-Based Measurements (from MediaPipe)
These measurements use skeletal joints:

| Measurement | Points Used | Purpose |
|---|---|---|
| `arm_span` | left_wrist to right_wrist | Arm reach measurement |
| `shoulder_to_hip` | shoulder median to hip median | Torso length |
| `hip_to_ankle` | hip to ankle | Leg length |
| `torso_depth` | chest to back (side view) | Anterior-posterior dimension |

## Data Flow

### Processing Pipeline

```
Input Image (BGR)
    ↓
┌─────────────────────────────────┐
│   1. YOLOv8 Segmentation        │
└─────────────────────────────────┘
    ↓
│ Binary Mask (person=255, bg=0)  │
    ↓
┌─────────────────────────────────┐
│   2. Extract Body Contour       │
│   • Find all contours in mask   │
│   • Select largest contour      │
│   • Validate area > threshold   │
│   • Smooth with approxPolyDP    │
└─────────────────────────────────┘
    ↓
│ Smoothed Contour Points         │
    ↓
┌─────────────────────────────────┐
│   3. Extract Edge Points        │
│   • Get shoulder edges at top   │
│   • Get waist edges at middle   │
│   • Get hip edges at bottom     │
│   • Store all 6 points + heights│
└─────────────────────────────────┘
    ↓
│ edge_reference_points dict      │
    ↓
┌─────────────────────────────────┐
│   4. MediaPipe Pose Detection   │
│   (in parallel)                 │
│   • Detect 33 landmarks         │
│   • Each landmark: x,y,conf     │
└─────────────────────────────────┘
    ↓
│ landmarks array (33×3)          │
    ↓
┌─────────────────────────────────┐
│   5. Calculate Measurements     │
│   • Route by type:              │
│     - Width → use edge_points   │
│     - Joint → use landmarks     │
│   • Apply scale_factor          │
│   • Calculate confidence        │
└─────────────────────────────────┘
    ↓
measurements_with_source dict
    ↓
Return API Response with measurements + sources
```

## Integration with Measurement Engine

### Method Signature

```python
measurements = measurement_engine.calculate_measurements_with_confidence(
    landmarks=landmarks,                    # MediaPipe landmarks (33×3)
    scale_factor=0.1,                       # pixels to cm conversion
    view='front',                           # 'front' or 'side'
    edge_reference_points=edge_points,      # Optional: from segmentation
    refined_shoulders=None                  # Deprecated (ignored)
)
```

### Return Format

```python
{
    'shoulder_width': (40.0, 0.95, 'Segmentation Edge'),
    'arm_span': (160.0, 0.92, 'MediaPipe Joints'),
    'waist_width': (32.5, 0.95, 'Segmentation Edge'),
    'hip_width': (42.0, 0.95, 'Segmentation Edge'),
    # ... more measurements
}
# (value_cm, confidence, source)
```

### Internal Routing Logic

```python
for measurement_name in measurements:
    if measurement_name in edge_based_measurements and edge_points_valid:
        # Use segmentation edges
        pixel_distance = calculate_from_edge_points(measurement_name, edge_points)
        source = 'Segmentation Edge'
        confidence = 0.95  # High confidence for contour
    else:
        # Fall back to MediaPipe
        pixel_distance = calculate_from_landmarks(measurement_name, landmarks)
        source = 'MediaPipe Joints'
        confidence = average_landmark_confidences
    
    # Scale conversion (UNCHANGED)
    cm_measurement = pixel_distance * scale_factor
```

## Scale Conversion (Critical: Unchanged)

**The pixel-to-scale conversion formula is COMPLETELY UNCHANGED**:

```
Measurement (cm) = Pixel Distance × Scale Factor

cm = pixels × scale_factor
```

This formula applies regardless of measurement source:
- Edge-based widths: `edge_pixels × scale_factor = cm`
- Joint-based measurements: `joint_pixels × scale_factor = cm`

**Example calculation**:
```
shoulder_width measurement:
- Edge points: (100, 200) to (300, 200)
- Pixel distance: 200 pixels
- Scale factor: 0.1 cm/pixel
- Result: 200 × 0.1 = 20.0 cm
```

## API Integration

### Updated `/api/upload/process` Endpoint

The endpoint now performs hybrid processing:

```python
# 1. Generate segmentation mask
mask = segmentation_model.segment_person(image)

# 2. Extract body contour and edge points
contour = landmark_detector.extract_body_contour(mask)
edge_points = landmark_detector.extract_edge_reference_points(
    contour, h, w, landmarks
)

# 3. Calculate measurements with hybrid routing
measurements = measurement_engine.calculate_measurements_with_confidence(
    landmarks, scale_factor, view,
    edge_reference_points=edge_points
)
```

### API Response Structure

```json
{
    "success": true,
    "measurements": {
        "shoulder_width": {
            "value_cm": 40.5,
            "value_pixels": 405,
            "confidence": 0.95,
            "source": "Segmentation Edge",
            "calculation": "405 px × 0.1 cm/px = 40.5 cm"
        },
        "arm_span": {
            "value_cm": 160.0,
            "value_pixels": 1600,
            "confidence": 0.92,
            "source": "MediaPipe Joints",
            "calculation": "1600 px × 0.1 cm/px = 160.0 cm"
        }
    },
    "hybrid_approach": {
        "enabled": true,
        "edge_points_available": true,
        "source_summary": {
            "segmentation_edge": 4,
            "mediapipe_joints": 3
        }
    }
}
```

## Code Examples

### Example 1: Basic Hybrid Measurement

```python
from landmark_detector import LandmarkDetector
from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
import cv2

# Initialize
detector = LandmarkDetector()
engine = MeasurementEngine()
segmenter = SegmentationModel()

# Load image
image = cv2.imread('person.jpg')
h, w = image.shape[:2]

# Get segmentation mask
mask = segmenter.segment_person(image)

# Extract edge points from contour
contour = detector.extract_body_contour(mask)
edge_points = detector.extract_edge_reference_points(contour, h, w, None)

# Get MediaPipe landmarks
landmarks = detector.detect(image)

# Calculate measurements with hybrid approach
scale_factor = 0.1  # 0.1 cm per pixel
measurements = engine.calculate_measurements_with_confidence(
    landmarks, scale_factor, view='front',
    edge_reference_points=edge_points
)

# Print results with sources
for name, (value_cm, confidence, source) in measurements.items():
    print(f"{name}: {value_cm:.1f}cm (from {source})")
```

### Example 2: Selective Edge Point Application

```python
# Apply edge points only to specific measurements
measurement_name = 'shoulder_width'
value_cm = engine.apply_edge_points_to_measurement(
    measurement_name, edge_points, scale_factor
)

# Validate the measurement
is_valid, reason = engine.validate_edge_measurement(
    measurement_name, value_cm
)

if is_valid:
    print(f"✓ {measurement_name}: {value_cm:.1f}cm")
else:
    print(f"✗ {reason}")
```

### Example 3: Face Landmark Detection

```python
# Detect facial landmarks
face_landmarks = detector.detect_face_landmarks(image)

if face_landmarks:
    print(f"Detected {len(face_landmarks)} facial landmarks")
    
    for i, landmark in enumerate(face_landmarks):
        x, y, z, presence = landmark
        print(f"Landmark {i}: ({x:.2f}, {y:.2f}), confidence: {presence:.2f}")
```

## Configuration Parameters

All parameters are defined in `LandmarkDetector.__init__()`:

```python
# Body segmentation and edge extraction
self.use_segmentation_for_widths = True           # Enable hybrid approach
self.contour_smoothing_kernel = 5                 # Smoothing strength (2-9)
self.body_edge_tolerance = 15                     # Pixels above/below target height
self.min_valid_contour_area = 500                 # Minimum contour size in pixels

# MediaPipe settings (same as joint detection)
self.confidence_threshold = 0.5                   # Minimum landmark confidence
self.min_tracking_confidence = 0.5                # Minimum tracking consistency

# Face mesh settings
self.face_mesh_confidence = 0.5                   # Face detection confidence
self.face_mesh_tracking = 0.5                     # Face tracking confidence
```

## Key Differences from Previous Versions

### Phase 3 (Previous)
- Used refinement to improve shoulder landmarks within MediaPipe
- All measurements sourced from MediaPipe
- Refinement applied post-detection

### Hybrid Approach (Current)
- Uses segmentation edges EXCLUSIVELY for width measurements
- Uses MediaPipe j EXCLUSIVELY for joint-based measurements
- Measurement source depends on measurement type, not on quality
- Cleaner separation of concerns (edges vs. joints)

## Backward Compatibility

The hybrid approach is **fully backward compatible**:

1. **Optional parameters**: `edge_reference_points` is optional (default=None)
2. **Fallback logic**: If edge points unavailable, falls back to MediaPipe
3. **Existing code unaffected**: Old code calling without edge_points still works
4. **Scale conversion unchanged**: Pixel-to-cm formula identical

```python
# Old code (still works):
measurements = engine.calculate_measurements_with_confidence(landmarks, scale_factor)

# New code (hybrid):
measurements = engine.calculate_measurements_with_confidence(
    landmarks, scale_factor, edge_reference_points=edge_points
)

# Both produce identical output structure
```

## Accuracy Improvements

### Width Measurements (Edge-Based)

| Metric | Before (MediaPipe) | After (Edge-Based) |
|---|---|---|
| Source consistency | Medium | Very High |
| Clothing interference | Medium | Very Low |
| Occlusion handling | Medium | High |
| Multi-body detection | Not handled | Handles best match |

### Joint Measurements (MediaPipe)

Unchanged from previous version - MediaPipe is the gold standard for joint detection.

## Troubleshooting

### Issue: Edge points not detected

**Causes**:
- Segmentation mask quality too low
- Person partially outside frame
- Background too similar to clothing

**Solutions**:
```python
# Check segmentation quality
mask = segmenter.segment_person(image, conf_threshold=0.7)

# Verify contour extraction
contour = detector.extract_body_contour(mask)
if contour is None:
    print("Failed to extract contour - insufficient segmentation quality")

# Check edge point validity
if not edge_points.get('is_valid'):
    print("Edge points marked invalid - using MediaPipe fallback")
```

### Issue: Width measurements unrealistic

**Check validation**:
```python
is_valid, reason = engine.validate_edge_measurement('shoulder_width', 45.0)
if not is_valid:
    print(f"Warning: {reason}")
```

**Adjust tolerance** if needed:
```python
detector.body_edge_tolerance = 20  # Increase from 15
```

## Testing

Run the comprehensive test suite:

```bash
python test_hybrid_vision.py
```

Tests cover:
- Measurement categorization (edge vs. joint)
- Edge point extraction
- Scale conversion integrity
- Backward compatibility
- Source routing
- Validation ranges

## Performance Notes

### Processing Time
- Segmentation: ~50ms (YOLOv8)
- Contour extraction: ~5ms
- Edge point extraction: ~3ms
- MediaPipe detection: ~30ms
- Measurement calculation: ~2ms
- **Total**: ~90ms per image

### Memory Usage
- Segmentation model: ~50MB
- MediaPipe Pose: ~28MB
- MediaPipe Face Mesh: ~20MB
- **Total**: ~100MB

## Future Enhancements

1. **Temporal Smoothing**: Smooth edge points across video frames
2. **Multi-body Support**: Handle group photos
3. **Depth Estimation**: Add 3D body measurements
4. **Clothing Compensation**: Estimate clothing thickness
5. **Gender-Specific Ranges**: Adjust validation ranges by gender

## References

- YOLOv8: https://docs.ultralytics.com/
- MediaPipe Pose: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- MediaPipe Face Mesh: https://developers.google.com/mediapipe/solutions/vision/face_landmarker

## Support

For issues with hybrid vision approach:
1. Check segmentation quality: `segmenter.segment_person()` produces valid mask
2. Verify edge point extraction: Check `edge_points.get('is_valid')`
3. Test MediaPipe fallback: Measurements work without edge_points
4. Review logs: Check console output for detection failures

---

**Last Updated**: 2024
**Version**: Hybrid Vision v1.0
**Status**: Production Ready
