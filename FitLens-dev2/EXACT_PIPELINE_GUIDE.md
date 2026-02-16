# Exact Pipeline Implementation - Complete Guide

## Overview

This implementation provides the **exact pipeline** you requested:

1. **YOLOv8-seg** for precise human body masking (removes background noise)
2. **MediaPipe Pose** for detecting all 33 body landmarks (shoulders=11/12, hips=23/24, etc.)
3. **OpenCV Canny edge detection + findContours** on the mask for body edge/contour keypoints
4. **Measurements** computed with OpenCV point distances + NumPy scaling using: **`measurement_cm = pixel_dist * (user_height_cm / height_px)`**

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT: RGB Image                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: YOLOv8-seg Masking                                     │
│  ► Apply YOLOv8-seg model (yolov8n-seg.pt)                     │
│  ► Generate binary mask: 255=person, 0=background               │
│  ► Remove background noise for cleaner processing               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: MediaPipe Pose Detection (All 33 Landmarks)            │
│  ► Feed masked image to MediaPipe Pose                          │
│  ► Detect all 33 body landmarks:                                │
│    • Shoulders: 11 (left), 12 (right)                           │
│    • Hips: 23 (left), 24 (right)                                │
│    • Elbows: 13 (left), 14 (right)                              │
│    • Wrists: 15 (left), 16 (right)                              │
│    • Knees: 25 (left), 26 (right)                               │
│    • Ankles: 27 (left), 28 (right)                              │
│    • Plus nose, eyes, ears, mouth, fingers, heels, toes         │
│  ► Output: (33, 3) array with [x_px, y_px, confidence]          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Canny Edge Detection + findContours                    │
│  ► Apply Canny edge detection on mask                           │
│    • Threshold: 50-150                                           │
│  ► Find contours using cv2.findContours()                       │
│  ► Extract body edge keypoints at key heights:                  │
│    • Shoulder level (left/right edges)                          │
│    • Chest level (left/right edges)                             │
│    • Waist level (left/right edges)                             │
│    • Hip level (left/right edges)                               │
│  ► Calculate head-to-toe height in pixels (height_px)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Measurement Computation                                │
│  ► Calculate scale factor:                                       │
│    scale_factor = user_height_cm / height_px                    │
│                                                                  │
│  ► For width measurements (shoulder, chest, waist, hip):        │
│    pixel_dist = OpenCV distance between left/right edge points  │
│    measurement_cm = pixel_dist * scale_factor                   │
│                                                                  │
│  ► For skeletal measurements (arm_span, leg_length, etc.):      │
│    pixel_dist = OpenCV distance between MediaPipe landmarks     │
│    measurement_cm = pixel_dist * scale_factor                   │
│                                                                  │
│  ► Output: Dictionary of measurements with confidence scores    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Basic Usage

```bash
# Process single image with your height
python process_images_yolo.py photo.jpg --user-height 170

# Process multiple images
python process_images_yolo.py front.jpg side.jpg back.jpg --user-height 175

# Use different YOLOv8 model size
python process_images_yolo.py photo.jpg --user-height 170 --model-size s

# Display results interactively
python process_images_yolo.py photo.jpg --user-height 170 --display
```

### Programmatic Usage

```python
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
from measurement_engine import MeasurementEngine
import cv2

# Load image
image = cv2.imread('photo.jpg')

# Initialize components
segmenter = SegmentationModel(model_size='n')
detector = LandmarkDetector()
measurer = MeasurementEngine()

# STEP 1: YOLOv8-seg masking
mask = segmenter.segment_person(image)
masked_image = segmenter.apply_mask(image, mask, background_mode='remove')

# STEP 2: MediaPipe Pose (all 33 landmarks)
landmarks = detector.detect(masked_image, mask=mask)

# STEP 3: Canny + findContours for body edges
edge_keypoints = detector.extract_body_edge_keypoints(mask, landmarks)

# STEP 4: Compute measurements with height-based scaling
user_height_cm = 170.0  # Your actual height
measurements = measurer.calculate_measurements_with_confidence(
    landmarks=landmarks,
    scale_factor=1.0,  # Will be auto-calculated
    edge_reference_points=edge_keypoints,
    user_height_cm=user_height_cm
)

# Print results
for name, (value_cm, confidence, source) in measurements.items():
    print(f"{name}: {value_cm:.1f} cm (confidence: {confidence:.1%}, source: {source})")
```

---

## API Reference

### 1. SegmentationModel

**File:** `segmentation_model.py`

```python
class SegmentationModel:
    def __init__(self, model_size: str = 'n')
        """Initialize YOLOv8-seg model.
        
        Args:
            model_size: 'n', 's', 'm', 'l', or 'x'
                n = nano (fastest, smallest)
                s = small
                m = medium
                l = large
                x = xlarge (slowest, most accurate)
        """
    
    def segment_person(self, image: np.ndarray, conf_threshold: float = 0.5) -> np.ndarray
        """Segment person from image using YOLOv8-seg.
        
        Returns:
            Binary mask (255=person, 0=background)
        """
```

### 2. LandmarkDetector

**File:** `backend/landmark_detector.py`

```python
class LandmarkDetector:
    def detect(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray
        """Detect all 33 MediaPipe Pose landmarks.
        
        Args:
            image: Input image (BGR)
            mask: Optional binary mask to focus detection
            
        Returns:
            (33, 3) array with [x_px, y_px, confidence]
            
        Landmark indices:
            0: nose
            11: left_shoulder, 12: right_shoulder
            13: left_elbow, 14: right_elbow
            15: left_wrist, 16: right_wrist
            23: left_hip, 24: right_hip
            25: left_knee, 26: right_knee
            27: left_ankle, 28: right_ankle
            ... (see MediaPipe Pose documentation for all 33)
        """
    
    def extract_body_edge_keypoints(self, mask: np.ndarray, landmarks: Optional[np.ndarray]) -> Dict
        """Extract body edge keypoints using Canny + findContours.
        
        Returns:
            {
                'is_valid': bool,
                'shoulder_left': (x, y),
                'shoulder_right': (x, y),
                'chest_left': (x, y),
                'chest_right': (x, y),
                'waist_left': (x, y),
                'waist_right': (x, y),
                'hip_left': (x, y),
                'hip_right': (x, y),
                'contours': list,
                'height_px': float (head-to-toe height)
            }
        """
```

### 3. MeasurementEngine

**File:** `backend/measurement_engine.py`

```python
class MeasurementEngine:
    def calculate_scale_factor_from_height(self, height_px: float, user_height_cm: float) -> float
        """Calculate scale factor using formula: user_height_cm / height_px"""
    
    def calculate_measurements_with_confidence(
        self,
        landmarks: np.ndarray,
        scale_factor: float,
        edge_reference_points: Optional[Dict] = None,
        user_height_cm: Optional[float] = None
    ) -> Dict[str, Tuple[float, float, str]]
        """Calculate measurements using the exact pipeline.
        
        Returns:
            {
                'shoulder_width': (value_cm, confidence, source),
                'chest_width': (value_cm, confidence, source),
                'waist_width': (value_cm, confidence, source),
                'hip_width': (value_cm, confidence, source),
                'arm_span': (value_cm, confidence, source),
                ...
            }
            
        Sources:
            - "Canny+findContours Edge" for width measurements
            - "MediaPipe Landmarks (33 points)" for skeletal measurements
        """
```

---

## Key Implementation Details

### Height-Based Scaling Formula

```python
# Calculate scale factor
scale_factor = user_height_cm / height_px

# Example:
# User height: 170 cm
# Detected height in image: 850 pixels
# scale_factor = 170 / 850 = 0.2 cm/pixel

# Shoulder width measurement:
# Pixel distance between shoulder edges: 200 pixels
# shoulder_width_cm = 200 * 0.2 = 40 cm
```

### Edge-Based Width Measurements

Width measurements (shoulder, chest, waist, hip) use **Canny edge detection + findContours**:

1. Apply Canny edge detection on mask (thresholds: 50-150)
2. Find contours using `cv2.findContours()`
3. Extract leftmost and rightmost points at specific body heights
4. Calculate distance using `np.linalg.norm(left - right)`
5. Apply scaling: `width_cm = pixel_distance * scale_factor`

### Skeletal Measurements

Other measurements use **MediaPipe landmarks** (all 33 points):

```python
# Example: Arm span
left_wrist = landmarks[15]   # Index 15
right_wrist = landmarks[16]  # Index 16
pixel_distance = np.linalg.norm(left_wrist[:2] - right_wrist[:2])
arm_span_cm = pixel_distance * scale_factor
```

---

## Output Format

### Measurements Dictionary

```python
{
    'shoulder_width': (42.5, 0.95, 'Canny+findContours Edge'),
    'chest_width': (38.2, 0.95, 'Canny+findContours Edge'),
    'waist_width': (32.1, 0.95, 'Canny+findContours Edge'),
    'hip_width': (40.8, 0.95, 'Canny+findContours Edge'),
    'arm_span': (165.3, 0.87, 'MediaPipe Landmarks (33 points)')
}
```

Each measurement is a tuple: `(value_cm, confidence, source)`

- `value_cm`: Measurement in centimeters
- `confidence`: Confidence score (0-1)
- `source`: Detection method used

### Saved Files

When processing images, the following files are saved to `output/`:

- `{name}_mask.png` - Binary segmentation mask
- `{name}_masked.png` - Image with background removed
- `{name}_landmarks.png` - All 33 landmarks visualized
- `{name}_comparison.png` - Side-by-side comparison
- `{name}_measurements.png` - Measurements annotated

---

## Example Pipeline Demonstration

Run the example script to see the complete pipeline:

```bash
python example_pipeline.py photo.jpg 170
```

This will:
1. Show detailed step-by-step processing
2. Display detected landmarks and edge keypoints
3. Calculate and show scale factor
4. Print all measurements with sources
5. Save visualization with annotations

---

## Configuration

### YOLOv8 Model Size

Choose based on speed vs. accuracy trade-off:

| Size | Speed | Accuracy | Model File Size |
|------|-------|----------|-----------------|
| n    | Fastest | Good | ~6 MB |
| s    | Fast | Better | ~22 MB |
| m    | Medium | Better | ~50 MB |
| l    | Slow | Best | ~88 MB |
| x    | Slowest | Best | ~136 MB |

### Edge Detection Parameters

In `backend/landmark_detector.py`:

```python
# Canny thresholds
edges = cv2.Canny(mask, 50, 150)

# Contour area threshold
self.min_valid_contour_area = 500  # pixels

# Height tolerance for finding edge points
self.body_edge_tolerance = 15  # pixels
```

### Measurement Validation

Realistic measurement ranges (in cm):

```python
realistic_ranges = {
    'shoulder_width': (25, 65),
    'chest_width': (20, 55),
    'waist_width': (18, 45),
    'hip_width': (25, 55)
}
```

---

## Troubleshooting

### Issue: No person detected
**Solution:** Ensure person is clearly visible, good lighting, and facing camera.

### Issue: Low landmark confidence
**Solution:** 
- Use masked image (background removal helps)
- Ensure person is in T-pose or A-pose
- Check lighting conditions

### Issue: Inaccurate measurements
**Solution:**
- Provide accurate `user_height_cm`
- Stand at appropriate distance from camera
- Ensure full body is visible (head to toes)
- Use better quality image

### Issue: Edge keypoints not detected
**Solution:**
- Check mask quality (YOLOv8-seg should produce clean mask)
- Adjust `min_valid_contour_area` if needed
- Ensure contrast between person and background

---

## Technical Details

### Dependencies

```
ultralytics>=8.0.0       # YOLOv8
mediapipe>=0.10.0        # Pose detection
opencv-python>=4.8.0     # Image processing
numpy>=1.24.0            # Numerical operations
```

### Performance

On typical hardware (CPU):
- YOLOv8n-seg: ~100-200ms per image
- MediaPipe Pose: ~30-50ms per image
- Canny + findContours: ~5-10ms per image
- **Total: ~150-300ms per image**

---

## Files Modified

1. **`backend/landmark_detector.py`**
   - Added `extract_body_edge_keypoints()` - Canny + findContours implementation
   - Updated `detect()` to accept optional mask parameter
   - Added `_find_edge_points_at_height()` helper

2. **`backend/measurement_engine.py`**
   - Added `calculate_scale_factor_from_height()` - Height-based scaling
   - Updated `calculate_measurements()` and `calculate_measurements_with_confidence()`
   - Enhanced to support automatic scale calculation

3. **`process_images_yolo.py`**
   - Updated `process_single_image()` to implement exact pipeline
   - Renamed `reference_size_cm` to `user_height_cm`
   - Added detailed step logging
   - Updated visualization to show edge keypoints

4. **`example_pipeline.py`** (new)
   - Complete demonstration of the exact pipeline
   - Step-by-step processing with detailed output

---

## Summary

This implementation provides the **exact pipeline** you requested:

✅ **YOLOv8-seg** for precise masking (removes background noise)  
✅ **MediaPipe Pose** for all 33 landmarks (shoulders=11/12, hips=23/24)  
✅ **Canny edge detection + findContours** for body edge keypoints  
✅ **Height-based scaling**: `measurement_cm = pixel_dist * (user_height_cm / height_px)`  

All measurements are computed using OpenCV point distances and NumPy operations with the exact formula specified.
