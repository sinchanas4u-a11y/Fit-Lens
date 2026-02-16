# 🚀 Getting Started with Shoulder Edge Detection

## Quick Start Guide

### Step 1: Verify Installation ✅
```bash
cd c:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2
python test_shoulder_edge_detection.py
```
**Expected Output:** `🎉 All tests passed! Implementation is ready for use.`

### Step 2: Choose Your Use Case

#### 📸 Single Photo
```python
from backend.landmark_detector import LandmarkDetector
import cv2

detector = LandmarkDetector()
image = cv2.imread('photo.jpg')
landmarks = detector.detect(image)
result = detector.detect_shoulder_edge_points(image, landmarks)

print(f"✅ Found {len(result['shoulder_edge_points'])} edge points")
print(f"📊 Confidence: {result['confidence_score']:.0%}")
print(f"🎯 Quality: {result['detection_quality']['overall']}")

detector.cleanup()
```

#### 🎥 Video File
```bash
python shoulder_edge_detection_example.py input.mp4 results.json output_video.mp4
```

#### 📹 Webcam (Live)
```python
from shoulder_edge_detection_example import ShoulderEdgeDetectionDemo

demo = ShoulderEdgeDetectionDemo()
stats = demo.process_webcam(duration_seconds=30)
demo.print_summary(stats)
```

#### 🌐 REST API
```bash
curl -X POST http://localhost:5000/api/shoulder/detect \
  -H "Content-Type: application/json" \
  -d '{
    "image": "BASE64_ENCODED_IMAGE",
    "shoulder_type": "both"
  }'
```

### Step 3: Interpret Results

```python
# Response structure:
{
    'frame_number': 1,                    # Frame index
    'shoulder_edge_points': [             # Array of detected points
        {'x': 0.45, 'y': 0.32, ...},     # Normalized coordinates (0-1)
        {'x': 0.48, 'y': 0.28, ...}      # (pixel_x, pixel_y) also included
    ],
    'confidence_score': 0.87,             # Overall confidence (0-1)
    'detection_quality': {
        'overall': 'good',                # good|fair|poor
        'confidence_level': 'high',       # high|medium|low
        'point_coverage': 'optimal',      # optimal|adequate|limited
        'recommended_action': 'proceed'   # proceed|review|retake
    }
}

# Quality Guidelines:
# ✅ 'good' + 'high' confidence: Proceed with analysis
# ⚠️  'fair' + 'medium' confidence: Review results
# ❌ 'poor' + 'low' confidence: Retake measurement
```

---

## 📚 Documentation Guide

| Document | Purpose | Read If... |
|----------|---------|-----------|
| **SHOULDER_EDGE_QUICK_REFERENCE.md** | Quick cheat sheet | You know what you're doing |
| **SHOULDER_EDGE_DETECTION_GUIDE.md** | Complete guide | You want detailed info |
| **IMPLEMENTATION_INDEX.md** | Project overview | You need the big picture |
| **CHANGES_SUMMARY.md** | What changed | You need technical details |
| **This file** | Getting started | This is your first time |

---

## 🔧 Common Tasks

### Task 1: Process a Photo
```python
from backend.landmark_detector import LandmarkDetector
import cv2

detector = LandmarkDetector()
img = cv2.imread('shoulder.jpg')
landmarks = detector.detect(img)
edges = detector.detect_shoulder_edge_points(img, landmarks, shoulder_type='both')

# Visualize
result = detector.draw_shoulder_edges(img, edges)
cv2.imshow('Shoulder Edges', result)
cv2.waitKey(0)

detector.cleanup()
```

### Task 2: Batch Process Multiple Photos
```python
from backend.landmark_detector import LandmarkDetector
import cv2
import glob

detector = LandmarkDetector()
results = []

for photo_path in glob.glob('photos/*.jpg'):
    img = cv2.imread(photo_path)
    landmarks = detector.detect(img)
    edges = detector.detect_shoulder_edge_points(img, landmarks)
    results.append(edges)

stats = detector.get_detection_statistics(results)
print(f"Average confidence: {stats['average_confidence']:.0%}")

detector.cleanup()
```

### Task 3: Export Results to JSON
```python
import json
from backend.landmark_detector import LandmarkDetector
import cv2

detector = LandmarkDetector()
img = cv2.imread('shoulder.jpg')
landmarks = detector.detect(img)
edges = detector.detect_shoulder_edge_points(img, landmarks)

# Export as JSON string
json_string = detector.export_shoulder_data_json(edges)

# Save to file
with open('results.json', 'w') as f:
    f.write(json_string)

detector.cleanup()
```

### Task 4: Process Video
```bash
# Process pre-recorded video
python shoulder_edge_detection_example.py my_video.mp4 results.json output_video.mp4

# Options:
# - Input: my_video.mp4 (required)
# - Output JSON: results.json (creates new file)
# - Output video: output_video.mp4 (annotated with detections)
```

### Task 5: Live Webcam
```python
from shoulder_edge_detection_example import ShoulderEdgeDetectionDemo

demo = ShoulderEdgeDetectionDemo()

# Capture for 60 seconds
stats = demo.process_webcam(duration_seconds=60)
demo.print_summary(stats)

# Saves results to JSON if specified
```

### Task 6: Call API from JavaScript
```javascript
async function detectShoulders(imageBase64) {
    const response = await fetch('/api/shoulder/detect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image: imageBase64,
            shoulder_type: 'both'
        })
    });
    
    const result = await response.json();
    
    console.log(`Found ${result.shoulder_edge_points.length} edge points`);
    console.log(`Confidence: ${(result.confidence_score * 100).toFixed(0)}%`);
    console.log(`Quality: ${result.detection_quality.overall}`);
    
    return result;
}

// Usage
const img = document.getElementById('image');
const base64 = canvas.toDataURL().split(',')[1];
const result = await detectShoulders(base64);
```

---

## ⚙️ Configuration

### Adjust Detection Sensitivity
```python
from backend.landmark_detector import LandmarkDetector

detector = LandmarkDetector()

# For larger shoulders
detector.shoulder_region_radius = 80  # Default: 60

# For lighter clothing (easier edge detection)
detector.edge_detection_threshold = 30  # Default: 50

# For higher confidence requirement
detector.min_edge_confidence = 0.85  # Default: 0.75
```

### For Different Scenarios
```python
# Portrait orientation (default)
detector.shoulder_region_radius = 60

# Landscape orientation
detector.shoulder_region_radius = 100

# Close-up shots
detector.shoulder_region_radius = 40

# Dark clothing
detector.edge_detection_threshold = 60

# Light clothing
detector.edge_detection_threshold = 30
```

---

## 🎯 Expected Results

### Good Detection ✅
- Confidence: > 0.85
- Edge points: 6-8
- Quality: "good"
- All extreme points detected
- Smooth contour outline

### Fair Detection ⚠️
- Confidence: 0.70-0.85
- Edge points: 4-5
- Quality: "fair"
- Some points missing
- Need review before use

### Poor Detection ❌
- Confidence: < 0.70
- Edge points: < 4
- Quality: "poor"
- Most points missing
- Should retake measurement

---

## 🐛 Troubleshooting

### "Low Confidence Score"
**Problem:** confidence_score < 0.70
**Solutions:**
1. Improve lighting (use natural light or soft lighting)
2. Clear away obstacles behind shoulder
3. Position shoulder more clearly in frame
4. Try different angles

### "Missing Edge Points"
**Problem:** shoulder_edge_points is empty or has < 4 points
**Solutions:**
1. Increase `shoulder_region_radius` (for larger shoulders)
2. Decrease `edge_detection_threshold` (for lighter clothing)
3. Ensure complete shoulder visibility
4. Use higher resolution image

### "Slow Performance"
**Problem:** FPS < 20
**Solutions:**
1. Reduce image resolution (resize input)
2. Use batch processing (process multiple frames at once)
3. Close other applications
4. Consider GPU acceleration

### "No Landmarks Detected"
**Problem:** `landmarks is None`
**Solutions:**
1. Ensure person is fully visible in frame
2. Check image quality and resolution
3. Improve lighting
4. Verify MediaPipe installation
5. Check image format (should be valid image)

### "API Not Responding"
**Problem:** Connection refused
**Solutions:**
1. Start Flask backend: `python backend/app.py`
2. Check port 5000 is not in use
3. Verify base64 image format
4. Check network connection

---

## 📊 Monitoring Performance

### Get Real-time Metrics
```python
from backend.landmark_detector import LandmarkDetector
import cv2
import time

detector = LandmarkDetector()
frames_processed = 0
total_confidence = 0

cap = cv2.VideoCapture(0)  # Webcam
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    landmarks = detector.detect(frame)
    edges = detector.detect_shoulder_edge_points(frame, landmarks)
    
    frames_processed += 1
    total_confidence += edges['confidence_score']
    
    # Every 30 frames, print stats
    if frames_processed % 30 == 0:
        elapsed = time.time() - start_time
        fps = frames_processed / elapsed
        avg_conf = total_confidence / frames_processed
        print(f"FPS: {fps:.1f} | Avg Confidence: {avg_conf:.0%}")

cap.release()
detector.cleanup()
```

---

## 🚦 Quality Checklist

Before using results in production:

- ✅ **Confidence Score**: > 0.80
- ✅ **Edge Points**: ≥ 6
- ✅ **Quality Level**: "good"
- ✅ **Point Coverage**: "optimal"
- ✅ **Recommended Action**: "proceed"
- ✅ **Visual Inspection**: Points make sense

---

## 🎓 Learning Paths

### Beginner (5 minutes)
1. Read this file
2. Run tests: `python test_shoulder_edge_detection.py`
3. Try single photo example

### Intermediate (30 minutes)
1. Process a video file
2. Review JSON output
3. Read QUICK_REFERENCE_GUIDE.md

### Advanced (1-2 hours)
1. Read SHOULDER_EDGE_DETECTION_GUIDE.md
2. Study shoulder_edge_detection_example.py
3. Customize configuration parameters
4. Integrate with your pipeline

---

## 📖 Next Steps

1. **Verify**: Run the test suite
2. **Explore**: Try the example scripts
3. **Learn**: Read the documentation
4. **Integrate**: Add to your application
5. **Optimize**: Tune parameters for your use case

---

## 📞 Quick Help

| Need | Where to Look |
|------|---------------|
| Quick command | SHOULDER_EDGE_QUICK_REFERENCE.md |
| API endpoint docs | SHOULDER_EDGE_DETECTION_GUIDE.md |
| Code examples | shoulder_edge_detection_example.py |
| Technical details | CHANGES_SUMMARY.md |
| Full overview | IMPLEMENTATION_INDEX.md |

---

## ✅ You're Ready!

You now have everything needed to:
- ✅ Detect shoulder edge points
- ✅ Process images and videos
- ✅ Integrate with APIs
- ✅ Export results
- ✅ Monitor quality
- ✅ Optimize performance

**Start with:** `python test_shoulder_edge_detection.py`

Good luck! 🚀
