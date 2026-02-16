# Exact Pipeline - Quick Reference

## 🚀 Quick Start

```bash
# Single image with your height
python process_images_yolo.py photo.jpg --user-height 170

# Multiple images
python process_images_yolo.py front.jpg side.jpg --user-height 175
```

## 📋 Pipeline Steps

```
1. YOLOv8-seg → Binary mask (255=person, 0=background)
2. Masked image → MediaPipe → 33 landmarks (shoulders=11/12, hips=23/24)
3. Canny(mask, 50, 150) + findContours → Edge keypoints
4. measurement_cm = pixel_dist * (user_height_cm / height_px)
```

## 🔧 Key Commands

```bash
# Basic usage
python process_images_yolo.py IMAGE.jpg --user-height YOUR_HEIGHT

# With display
python process_images_yolo.py IMAGE.jpg --user-height 170 --display

# Different model (n/s/m/l/x)
python process_images_yolo.py IMAGE.jpg --user-height 170 --model-size s

# Multiple images
python process_images_yolo.py img1.jpg img2.jpg img3.jpg --user-height 175

# Demo script
python example_pipeline.py photo.jpg 170
```

## 💻 Programmatic Usage

```python
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
from measurement_engine import MeasurementEngine
import cv2

# Load image
image = cv2.imread('photo.jpg')

# Initialize
segmenter = SegmentationModel(model_size='n')
detector = LandmarkDetector()
measurer = MeasurementEngine()

# Step 1: YOLOv8-seg masking
mask = segmenter.segment_person(image)

# Step 2: MediaPipe Pose (33 landmarks)
landmarks = detector.detect(image, mask=mask)

# Step 3: Canny + findContours
edge_keypoints = detector.extract_body_edge_keypoints(mask, landmarks)

# Step 4: Measurements
measurements = measurer.calculate_measurements_with_confidence(
    landmarks=landmarks,
    scale_factor=1.0,
    edge_reference_points=edge_keypoints,
    user_height_cm=170.0
)

# Results
for name, (value, conf, source) in measurements.items():
    print(f"{name}: {value:.1f} cm ({source})")
```

## 📊 MediaPipe Landmark Indices

```
0: nose
11: left_shoulder      12: right_shoulder
13: left_elbow         14: right_elbow
15: left_wrist         16: right_wrist
23: left_hip           24: right_hip
25: left_knee          26: right_knee
27: left_ankle         28: right_ankle
... (33 total landmarks)
```

## 🎯 Edge Keypoints

```python
edge_keypoints = {
    'shoulder_left': (x, y),
    'shoulder_right': (x, y),
    'chest_left': (x, y),
    'chest_right': (x, y),
    'waist_left': (x, y),
    'waist_right': (x, y),
    'hip_left': (x, y),
    'hip_right': (x, y),
    'height_px': float  # Head-to-toe height
}
```

## 📐 Scaling Formula

```python
# Auto-calculated when user_height_cm provided
scale_factor = user_height_cm / height_px

# Example:
# user_height_cm = 170
# height_px = 850
# scale_factor = 170 / 850 = 0.2 cm/pixel

# Measurement:
# pixel_distance = 200 pixels
# measurement_cm = 200 * 0.2 = 40 cm
```

## 📦 Output Files

```
output/
  ├── {name}_mask.png              # Binary mask
  ├── {name}_masked.png            # Background removed
  ├── {name}_landmarks.png         # 33 landmarks drawn
  ├── {name}_comparison.png        # Side-by-side views
  └── {name}_measurements.png      # With annotations
```

## 🔍 Measurement Sources

```
Width measurements (Canny+findContours):
  - shoulder_width
  - chest_width
  - waist_width
  - hip_width

Skeletal measurements (MediaPipe 33 landmarks):
  - arm_span
  - torso_length
  - leg_length
  - etc.
```

## ⚙️ Configuration

### YOLOv8 Model Sizes
```
n: 6 MB   - Fastest    (recommended)
s: 22 MB  - Fast
m: 50 MB  - Medium
l: 88 MB  - Slow
x: 136 MB - Slowest, most accurate
```

### Canny Parameters
```python
# In backend/landmark_detector.py
edges = cv2.Canny(mask, 50, 150)  # Lower=50, Upper=150
```

### Measurement Ranges (cm)
```python
shoulder_width: 25-65
chest_width:    20-55
waist_width:    18-45
hip_width:      25-55
```

## 🐛 Common Issues

**No person detected**
→ Better lighting, clear view of person

**Low landmark confidence**
→ Use masked image, T-pose/A-pose, good lighting

**Inaccurate measurements**
→ Provide accurate user_height_cm, full body visible

**Edge keypoints failed**
→ Check mask quality, adjust min_valid_contour_area

## 📚 Documentation

- **Complete Guide**: [EXACT_PIPELINE_GUIDE.md](EXACT_PIPELINE_GUIDE.md)
- **Example Script**: [example_pipeline.py](example_pipeline.py)
- **Main Script**: [process_images_yolo.py](process_images_yolo.py)

## 🎓 Example Output

```
Processing: photo.jpg
  [Step 1/4] YOLOv8-seg: Precise human body masking...
  ✓ Person segmented, background noise removed

  [Step 2/4] MediaPipe Pose: Detecting all 33 body landmarks...
  ✓ Detected 33 landmarks (all 33 body points)

  [Step 3/4] OpenCV Canny + findContours: Extracting body edges...
  ✓ Body contours extracted, height_px = 850.0

  [Step 4/4] Computing measurements...
     Scale: 0.2000 cm/pixel (user_height_cm=170 / height_px=850.0)
  ✓ Calculated 5 measurements

Measurement          Value      Confidence   Source
──────────────────────────────────────────────────────────────
shoulder_width        42.5 cm    95.0%       Canny+findContours Edge
chest_width           38.2 cm    95.0%       Canny+findContours Edge
waist_width           32.1 cm    95.0%       Canny+findContours Edge
hip_width             40.8 cm    95.0%       Canny+findContours Edge
arm_span             165.3 cm    87.0%       MediaPipe Landmarks (33 points)
```

---

**Need help?** See [EXACT_PIPELINE_GUIDE.md](EXACT_PIPELINE_GUIDE.md) for complete documentation.
