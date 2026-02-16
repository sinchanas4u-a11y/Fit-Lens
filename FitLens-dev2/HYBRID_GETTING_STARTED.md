"""
GETTING STARTED WITH HYBRID SHOULDER DETECTION

This guide will help you quickly start using the hybrid shoulder detection system.
"""

## 1. INSTALLATION

Make sure all dependencies are installed:

```bash
pip install opencv-python>=4.8.0
pip install mediapipe==0.10.14
pip install ultralytics>=8.0.0
pip install numpy>=1.23.5
pip install scikit-image>=0.19.0  # Optional but recommended
pip install scipy>=1.9.0           # Optional
```

Or install everything at once:
```bash
pip install -r requirements.txt
```

## 2. RUN TESTS

First, verify that everything is working correctly:

```bash
python test_hybrid_shoulder_detection.py
```

This will run 8 tests covering:
- Module imports
- Component initialization
- Edge detection
- Contour extraction
- Point filtering
- Full pipeline

Expected output: "✓ ALL TESTS PASSED!"

## 3. RUN EXAMPLE

Run the complete example pipeline with your own image:

```bash
python example_hybrid_shoulder.py path/to/your/image.jpg --height 170
```

Arguments:
- `path/to/your/image.jpg` - Your input image (required)
- `--height` - Your height in cm (optional, default: 170)

Example:
```bash
python example_hybrid_shoulder.py photo.jpg --height 175
```

This will:
1. Segment the person using YOLOv8
2. Detect landmarks with MediaPipe
3. Extract body edges with OpenCV
4. Find shoulder points using contours
5. Calculate shoulder width
6. Compare with MediaPipe direct measurement
7. Save debug images to `hybrid_shoulder_results/` folder

Output files:
- `comparison.jpg` - Side-by-side comparison with annotations
- `mask.jpg` - YOLOv8 segmentation mask
- `debug.jpg` - 2x2 visualization grid showing all pipeline steps

## 4. USE IN YOUR CODE

### Option A: Simple Integration (Recommended)

```python
from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
import cv2

# Load image
image = cv2.imread('photo.jpg')

# Get segmentation mask
seg_model = SegmentationModel(model_size='n')
mask = seg_model.segment_person(image)

# Get landmarks
detector = LandmarkDetector()
landmarks = detector.detect(image)

# Calculate scale factor (assuming user height = 170 cm)
import numpy as np
body_y_coords = np.where(np.any(mask, axis=1))[0]
body_height_px = body_y_coords[-1] - body_y_coords[0]
scale_factor = 170 / body_height_px

# Get hybrid shoulder width
engine = MeasurementEngine()
result = engine.calculate_shoulder_width_hybrid(
    image, mask, landmarks, scale_factor, debug=False
)

print(f"Shoulder width: {result['shoulder_width_cm']:.2f} cm")
print(f"Confidence: {result['confidence']:.2f}")

# Cleanup
detector.cleanup()
```

### Option B: Direct Hybrid Detector

```python
from hybrid_shoulder_detector import HybridShoulderDetector

detector = HybridShoulderDetector()
result = detector.detect_shoulder_width_with_refinement(
    image, mask, landmarks, scale_factor,
    use_scikit_image=True,
    debug=False
)
```

### Option C: Using Edge Keypoints Only

```python
edge_keypoints = detector.extract_body_edge_keypoints(mask)

if edge_keypoints['is_valid']:
    shoulder_width_px = edge_keypoints['shoulder_width_px']
    shoulder_width_cm = shoulder_width_px * scale_factor
    print(f"Shoulder width: {shoulder_width_cm:.2f} cm")
```

## 5. KEY COMPONENTS

### HybridShoulderDetector
Located in: `hybrid_shoulder_detector.py`

Main class for hybrid detection. Key methods:
- `detect_shoulder_width()` - Basic detection
- `detect_shoulder_width_with_refinement()` - With optional scikit-image refinement

### MeasurementEngine
Updated with new method:
- `calculate_shoulder_width_hybrid()` - High-level interface

### LandmarkDetector
Updated with new method:
- `extract_body_edge_keypoints()` - Pure contour-based extraction

## 6. UNDERSTANDING THE OUTPUT

Result dictionary contains:

```python
{
    'shoulder_width_cm': 42.5,      # Width in centimeters
    'shoulder_width_px': 425.0,     # Width in pixels
    'confidence': 0.85,              # Confidence score (0-1)
    'left_shoulder': (150, 200),    # Left edge point (x, y)
    'right_shoulder': (575, 200),   # Right edge point (x, y)
    'shoulder_y': 200,              # Y-level of shoulders
    'source': 'hybrid',              # Detection method
    'debug_image': None,             # Optional debug visualization
}
```

## 7. TROUBLESHOOTING

### Q: Getting "No person detected"
A: Make sure your image clearly shows a full person. Try:
- Using a higher resolution image
- Ensuring good lighting
- Standing further from camera

### Q: Low confidence scores
A: Check that:
- Shoulders are clearly visible and not occluded
- Image has good contrast
- Person is centered in frame
- Using proper height for scale calibration

### Q: Different results from MediaPipe
A: This is normal! Hybrid detection:
- Uses actual body edges instead of joint positions
- Is typically more accurate for width measurements
- May differ by 5-15% depending on clothing and pose

### Q: Getting "No contours found"
A: Try:
- Using a higher resolution image
- Adjusting Canny thresholds in HybridShoulderDetector
- Checking that YOLOv8 mask has good quality

## 8. PERFORMANCE TIPS

For faster processing:
```python
# Use nano YOLOv8 model (faster)
seg_model = SegmentationModel(model_size='n')

# Disable debug mode in production
result = engine.calculate_shoulder_width_hybrid(
    image, mask, landmarks, scale_factor, debug=False
)

# Process lower resolution for video
image_small = cv2.resize(image, (640, 480))
```

For better accuracy:
```python
# Use small YOLOv8 model (more accurate)
seg_model = SegmentationModel(model_size='s')

# Enable debug mode to check quality
result = engine.calculate_shoulder_width_hybrid(
    image, mask, landmarks, scale_factor, debug=True
)

# Verify confidence > 0.7
if result['confidence'] > 0.7:
    use_measurement = True
```

## 9. NEXT STEPS

1. **Read the full documentation:**
   - `HYBRID_SHOULDER_DETECTION_GUIDE.md` - Technical details
   - `HYBRID_SHOULDER_QUICK_REFERENCE.md` - Code recipes

2. **Integrate into your app:**
   - Use Option A simple integration
   - Follow the measurement engine approach
   - Customize parameters as needed

3. **Customize for your use case:**
   - Adjust Canny thresholds for different lighting
   - Modify y_tolerance for different body types
   - Add temporal filtering for video

4. **Monitor performance:**
   - Track confidence scores
   - Compare with ground truth when possible
   - Adjust calibration if needed

## 10. EXAMPLE SCRIPT: BATCH PROCESSING

Process multiple images:

```python
from pathlib import Path
import cv2
from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
import numpy as np

# Initialize
seg_model = SegmentationModel(model_size='n')
detector = LandmarkDetector()
engine = MeasurementEngine()

# Process images
image_dir = Path('images/')
results = {}

for image_path in image_dir.glob('*.jpg'):
    image = cv2.imread(str(image_path))
    if image is None:
        continue
    
    mask = seg_model.segment_person(image)
    landmarks = detector.detect(image)
    
    if mask is None or landmarks is None:
        print(f"Skipped: {image_path.name}")
        continue
    
    # Calculate scale factor
    body_y_coords = np.where(np.any(mask, axis=1))[0]
    body_height_px = body_y_coords[-1] - body_y_coords[0]
    scale_factor = 170 / body_height_px
    
    # Get measurement
    result = engine.calculate_shoulder_width_hybrid(
        image, mask, landmarks, scale_factor, debug=False
    )
    
    results[image_path.name] = result
    print(f"{image_path.name}: {result['shoulder_width_cm']:.2f} cm")

# Print summary
print("\nSummary:")
for name, result in results.items():
    if result['shoulder_width_cm']:
        print(f"  {name}: {result['shoulder_width_cm']:.2f} cm")

detector.cleanup()
```

## 11. COMPARING WITH MEDIAPIPE

To see the difference:

```python
# MediaPipe direct measurement
left_shoulder = landmarks[11, :2]      # (x, y)
right_shoulder = landmarks[12, :2]     # (x, y)
width_mp = (right_shoulder[0] - left_shoulder[0]) * scale_factor

# Hybrid measurement
result = engine.calculate_shoulder_width_hybrid(...)
width_hybrid = result['shoulder_width_cm']

# Comparison
print(f"MediaPipe:  {width_mp:.2f} cm")
print(f"Hybrid:     {width_hybrid:.2f} cm")
print(f"Difference: {abs(width_mp - width_hybrid):.2f} cm")
```

Typical difference: 5-15% (hybrid is usually more accurate for clothing)

---

For more detailed information, see:
- HYBRID_SHOULDER_DETECTION_GUIDE.md
- HYBRID_SHOULDER_QUICK_REFERENCE.md
- example_hybrid_shoulder.py
- test_hybrid_shoulder_detection.py
"""
