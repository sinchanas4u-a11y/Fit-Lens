"""
QUICKSTART: Hybrid Vision Approach
===================================

This guide helps you get started with FitLens' new hybrid vision system.
"""

# QUICK OVERVIEW

FitLens now uses **Hybrid Vision**:
- 🎯 **YOLOv8 Segmentation** for body width measurements (shoulder, waist, hip)
- 🦴 **MediaPipe Pose** for skeletal joint measurements (elbows, wrists, knees, ankles)  
- 😊 **MediaPipe Face Mesh** for facial landmarks (NEW!)

**What does this mean?**
- More accurate width measurements using body contour edges
- Better consistency across different body types and clothing
- All existing joint-based measurements unchanged
- Fully backward compatible

---

## SETUP

1. **Update your environment** (if needed):
   ```bash
   pip install mediapipe opencv-python ultralytics numpy
   ```

2. **Your existing code still works!**
   ```python
   # Old style still works:
   measurements = engine.calculate_measurements_with_confidence(landmarks, scale_factor)
   ```

---

## USAGE EXAMPLES

### Example 1: Basic Hybrid Measurement (Recommended)

```python
from backend.landmark_detector import LandmarkDetector
from backend.measurement_engine import MeasurementEngine
from backend.segmentation_model import SegmentationModel
import cv2

# Initialize
detector = LandmarkDetector()
engine = MeasurementEngine()
segmenter = SegmentationModel()

# Load image
image = cv2.imread('person.jpg')
h, w = image.shape[:2]

# Step 1: Get segmentation mask for edges
print("Step 1: Generating segmentation mask...")
mask = segmenter.segment_person(image)

# Step 2: Extract body contour from mask
print("Step 2: Extracting body contour...")
contour = detector.extract_body_contour(mask)

# Step 3: Get edge reference points (shoulders, waist, hips)
print("Step 3: Finding edge reference points...")
edge_points = detector.extract_edge_reference_points(contour, h, w, None)
print(f"   ✓ Edge points found: {edge_points.get('is_valid')}")

# Step 4: Get MediaPipe landmarks (for joints)
print("Step 4: Detecting MediaPipe landmarks...")
landmarks = detector.detect(image)
print(f"   ✓ {len(landmarks)} landmarks detected")

# Step 5: Calculate measurements using hybrid approach
print("Step 5: Calculating measurements...")
scale_factor = 0.1  # Adjust based on your reference object
measurements = engine.calculate_measurements_with_confidence(
    landmarks, 
    scale_factor, 
    view='front',
    edge_reference_points=edge_points  # KEY: Pass edge points!
)

# Step 6: Display results
print("\n" + "="*50)
print("MEASUREMENT RESULTS")
print("="*50)

for name, (value_cm, confidence, source) in measurements.items():
    source_badge = "📐" if source == "Segmentation Edge" else "🦴"
    print(f"{source_badge} {name:20s}: {value_cm:6.1f} cm (conf: {confidence:.2f})")

print("\nSource Summary:")
edge_count = len([m for m in measurements.values() if m[2] == "Segmentation Edge"])
joint_count = len([m for m in measurements.values() if m[2] == "MediaPipe Joints"])
print(f"  📐 Segmentation-based: {edge_count} measurements")
print(f"  🦴 MediaPipe-based: {joint_count} measurements")
```

**Output Example**:
```
==================================================
MEASUREMENT RESULTS
==================================================
📐 shoulder_width      :   40.5 cm (conf: 0.95)
📐 chest_width        :   38.2 cm (conf: 0.95)
📐 waist_width        :   32.5 cm (conf: 0.95)
📐 hip_width          :   42.0 cm (conf: 0.95)
🦴 arm_span           :  160.0 cm (conf: 0.92)
🦴 shoulder_to_hip    :   55.5 cm (conf: 0.88)
🦴 hip_to_ankle       :   75.0 cm (conf: 0.90)

Source Summary:
  📐 Segmentation-based: 4 measurements
  🦴 MediaPipe-based: 3 measurements
```

---

### Example 2: Using the API

```python
import requests
import base64

# Load images
with open('front.jpg', 'rb') as f:
    front_b64 = base64.b64encode(f.read()).decode()
with open('reference.jpg', 'rb') as f:
    ref_b64 = base64.b64encode(f.read()).decode()

# Call API with hybrid processing
response = requests.post('http://localhost:5000/api/upload/process', json={
    'front_image': front_b64,
    'reference_image': ref_b64,
    'reference_size': 15.0,  # cm
    'reference_axis': 'horizontal'
})

result = response.json()

# Display measurements with sources
print("API Response:")
for name, data in result['measurements'].items():
    source = "Edge" if data['source'] == "Segmentation Edge" else "MediaPipe"
    print(f"  {name:20s}: {data['value_cm']:6.1f}cm ({source})")

# Check hybrid metadata
hybrid = result.get('hybrid_approach', {})
print(f"\nHybrid Status: {'✓ Enabled' if hybrid.get('enabled') else '✗ Disabled'}")
print(f"Edge points available: {'✓ Yes' if hybrid.get('edge_points_available') else '✗ No'}")
print(f"Source breakdown: {hybrid.get('source_summary')}")
```

---

### Example 3: With Error Handling

```python
def safe_measure_person(image_path, segmenter, detector, engine, scale_factor):
    """Safely measure person with graceful fallback"""
    
    image = cv2.imread(image_path)
    if image is None:
        print("❌ Cannot load image")
        return None
    
    h, w = image.shape[:2]
    
    try:
        # Try hybrid approach first
        print("📐 Attempting hybrid measurement...")
        
        mask = segmenter.segment_person(image)
        if mask is None:
            raise Exception("Segmentation failed")
        
        contour = detector.extract_body_contour(mask)
        if contour is None:
            raise Exception("Contour extraction failed")
        
        landmarks = detector.detect(image)
        if landmarks is None:
            raise Exception("Landmark detection failed")
        
        edge_points = detector.extract_edge_reference_points(
            contour, h, w, landmarks
        )
        
        measurements = engine.calculate_measurements_with_confidence(
            landmarks, scale_factor, 'front',
            edge_reference_points=edge_points
        )
        
        print(f"✓ Hybrid measurement successful ({len(measurements)} measurements)")
        return measurements
        
    except Exception as e:
        print(f"⚠ Hybrid approach failed: {e}")
        print("🦴 Falling back to MediaPipe-only approach...")
        
        try:
            landmarks = detector.detect(image)
            measurements = engine.calculate_measurements_with_confidence(
                landmarks, scale_factor, 'front'
            )
            print(f"✓ Fallback successful ({len(measurements)} measurements)")
            return measurements
            
        except Exception as e:
            print(f"❌ Measurement failed: {e}")
            return None

# Usage
measurements = safe_measure_person('person.jpg', segmenter, detector, engine, 0.1)
if measurements:
    for name, (value, conf, source) in measurements.items():
        print(f"{name}: {value:.1f}cm from {source}")
```

---

### Example 4: Facial Measurements (NEW!)

```python
# Detect face landmarks
print("Detecting facial landmarks...")
face_landmarks = detector.detect_face_landmarks(image)

if face_landmarks:
    print(f"✓ Found {len(face_landmarks)} facial landmarks")
    
    # Access specific landmarks
    # Format: [x, y, z, presence] for each of 468 landmarks
    # Key indices:
    # - 0: Nose tip
    # - 33: Left eye outer
    # - 263: Right eye outer  
    # - 10: Chin
    # - etc.
    
    for i in [0, 10, 33, 263]:  # Nose, Chin, Left eye, Right eye
        if i < len(face_landmarks):
            x, y, z, presence = face_landmarks[i]
            print(f"  Landmark {i}: ({x:.2f}, {y:.2f}), confidence: {presence:.2f}")
else:
    print("❌ No face detected")
```

---

### Example 5: Validation

```python
# Validate measurements are realistic
def validate_measurements(measurements, engine):
    """Check measurements fall within realistic ranges"""
    
    print("Validation Results:")
    for name, (value_cm, conf, source) in measurements.items():
        if name in engine.edge_based_measurements:
            is_valid, reason = engine.validate_edge_measurement(name, value_cm)
            status = "✓" if is_valid else "❌"
            print(f"{status} {name:20s}: {reason}")

# Usage
validate_measurements(measurements, engine)
```

---

## CONFIGURATION

### Adjust Edge Detection Parameters

```python
detector = LandmarkDetector()

# Tuning parameters (in __init__):
detector.use_segmentation_for_widths = True      # Enable hybrid (default: True)
detector.body_edge_tolerance = 15                # Pixels above/below target (default: 15)
detector.contour_smoothing_kernel = 5            # Smoothing strength (default: 5)
detector.min_valid_contour_area = 500            # Min contour size (default: 500)

# Example: Stricter edge detection
detector.body_edge_tolerance = 10     # Narrower tolerance band
detector.min_valid_contour_area = 800 # Require larger contour
```

### Measurement Selection

```python
# View available measurements
measurements_set = engine.measurements['front']
print("Available measurements:", list(measurements_set.keys()))

# Check categorization
print("\nEdge-based (segmentation):")
print(engine.edge_based_measurements)

print("\nJoint-based (MediaPipe):")
print(engine.joint_based_measurements)
```

---

## TROUBLESHOOTING

### Problem: "Edge points not detected"

**Check segmentation quality**:
```python
mask = segmenter.segment_person(image, conf_threshold=0.7)
if mask is None:
    print("Segmentation confidence too low - try lower threshold")
    mask = segmenter.segment_person(image, conf_threshold=0.5)

# Verify contour
contour = detector.extract_body_contour(mask)
if contour is None:
    print("Failed to extract contour - person may be too small or partially cut off")
```

**Solution**: 
- Ensure person is fully visible and takes up >20% of frame
- Check lighting and background contrast
- Adjust `min_valid_contour_area` if needed

### Problem: "Width measurements seem too large/small"

**Verify scale factor**:
```python
# Problem
scale_factor = 0.1  # This means 1 px = 0.1 cm (10cm per 100px)
# Result: 200 pixels × 0.1 = 20cm

# Correct?
# Reference object: 15cm
# Measured in pixels: 150 pixels
# Scale factor: 15 / 150 = 0.1 cm/pixel ✓

# If wrong, recalculate:
reference_cm = 15.0
reference_pixels = 150.0
correct_scale_factor = reference_cm / reference_pixels
print(f"Correct scale factor: {correct_scale_factor}")
```

**Validate measurements**:
```python
is_valid, reason = engine.validate_edge_measurement('shoulder_width', 45.0)
if not is_valid:
    print(f"⚠ Warning: {reason}")
```

### Problem: "Measurements inconsistent between frames"

**Use temporal smoothing** (coming soon):
```python
# For now, use simple averaging:
from temporal_stabilizer import TemporalStabilizer

stabilizer = TemporalStabilizer()
smoothed_measurements = stabilizer.smooth_measurements(measurements)
```

---

## API MIGRATION GUIDE

### Old Code (Still Works!)
```python
measurements = engine.calculate_measurements_with_confidence(landmarks, scale_factor)
```

### New Code (Recommended)
```python
measurements = engine.calculate_measurements_with_confidence(
    landmarks, scale_factor,
    edge_reference_points=edge_points
)
```

### Migration Path:
1. ✅ Your old code continues to work (backward compatible)
2. ⭐ Update step-by-step to use new hybrid parameters
3. 📐 Gradually migrate to edge-based measurements

---

## TESTING

### Run Test Suite
```bash
python test_hybrid_vision.py
```

### Expected Output
```
test_measurement_categorization ... ok
test_edge_reference_points_structure ... ok
test_calculate_edge_distance ... ok
test_edge_measurement_validation ... ok
test_apply_edge_points_to_measurement ... ok
test_measurement_routing_with_edge_points ... ok
test_scale_conversion_preserved ... ok
test_backward_compatibility_without_edge_points ... ok
test_extract_body_contour ... ok
test_detect_face_landmarks ... ok
test_hybrid_approach_metadata ... ok
test_get_extreme_points_at_height ... ok

Ran 12 tests in 0.050s
OK
```

---

## PERFORMANCE TIPS

### Speed Optimization
```python
# Option 1: Skip edge extraction for fast processing
measurements = engine.calculate_measurements_with_confidence(
    landmarks, scale_factor
    # No edge_reference_points = faster, fallback to MediaPipe
)

# Option 2: Process only front view
measurements = engine.calculate_measurements_with_confidence(
    landmarks, scale_factor, view='front',
    edge_reference_points=edge_points
)
```

### Memory Optimization
```python
# Process images at reduced resolution
image_small = cv2.resize(image, (640, 480))
mask = segmenter.segment_person(image_small)

# Then scale back if needed
scale = original_size / reduced_size
```

---

## NEXT STEPS

1. ✅ **Review examples above** - Start with Example 1
2. ✅ **Run test suite** - `python test_hybrid_vision.py`
3. ✅ **Try the API** - POST to `/api/upload/process`
4. ✅ **Check measurements** - Verify sources match expectations
5. ✅ **Tune parameters** - Adjust if needed for your use case
6. ✅ **Read full docs** - HYBRID_VISION_APPROACH.md

---

## SUPPORT

For issues:
1. Check console logs for error messages
2. Verify segmentation quality with `segmenter.segment_person()`
3. Test MediaPipe fallback (works without edge_points)
4. Check face visibility for facial landmarks
5. Review TROUBLESHOOTING section above or HYBRID_VISION_APPROACH.md

---

**Hybrid Vision Status**: 🚀 Ready to Use!

For detailed technical info, see: **HYBRID_VISION_APPROACH.md**
