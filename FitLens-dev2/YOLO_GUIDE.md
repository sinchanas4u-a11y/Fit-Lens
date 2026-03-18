# YOLOv8 + MediaPipe Body Measurement Guide

## Overview

This system uses **YOLOv8 segmentation** to create clean human body masks and **MediaPipe** for landmark detection and measurements.

## Features

✅ **YOLOv8 Segmentation**: State-of-the-art person segmentation
✅ **Clean Masking**: Automatically isolates human body from background
✅ **MediaPipe Landmarks**: 33 body keypoints for accurate measurements
✅ **Multiple Images**: Process 1-3 images simultaneously
✅ **Automatic Measurements**: Calculate body dimensions automatically
✅ **Visual Outputs**: Multiple visualization modes

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `ultralytics` (YOLOv8)
- `mediapipe` (Landmark detection)
- `opencv-python` (Image processing)
- `numpy` (Numerical operations)

### 2. First Run

On first run, YOLOv8 will automatically download the pretrained model (~6MB for nano model).

## Usage

### Method 1: Command Line (Recommended)

#### Process Single Image
```bash
python process_images_yolo.py image1.jpg
```

#### Process Multiple Images (3 images)
```bash
python process_images_yolo.py front.jpg side.jpg back.jpg
```

#### With Reference Size Calibration
```bash
python process_images_yolo.py image1.jpg --reference-size 170
```
(170 = your height in cm for accurate measurements)

#### Display Results
```bash
python process_images_yolo.py image1.jpg --display
```

#### Choose Model Size
```bash
python process_images_yolo.py image1.jpg --model-size m
```

Model sizes:
- `n` (nano) - Fastest, ~6MB (default)
- `s` (small) - Fast, ~22MB
- `m` (medium) - Balanced, ~50MB
- `l` (large) - Accurate, ~100MB
- `x` (xlarge) - Most accurate, ~140MB

### Method 2: Batch Script (Windows)

```bash
RUN_YOLO_PROCESSOR.bat image1.jpg image2.jpg image3.jpg
```

### Method 3: Python Script

```python
from process_images_yolo import ImageProcessor

# Initialize processor
processor = ImageProcessor(yolo_model_size='n')

# Process single image
result = processor.process_single_image(
    'image.jpg',
    reference_size_cm=170,  # Your height in cm
    save_output=True
)

# Process multiple images
results = processor.process_multiple_images(
    ['image1.jpg', 'image2.jpg', 'image3.jpg'],
    reference_size_cm=170
)

# Access results
if result['success']:
    mask = result['mask']
    landmarks = result['landmarks']
    measurements = result['measurements']
    visualizations = result['visualizations']
```

## Output Files

All outputs are saved to the `output/` folder:

1. **`*_mask.png`** - Binary segmentation mask (white = person, black = background)
2. **`*_masked.png`** - Image with dimmed background
3. **`*_landmarks.png`** - Masked image with MediaPipe landmarks
4. **`*_comparison.png`** - 4-panel comparison view
5. **`*_measurements.png`** - Image with measurement annotations

## How It Works

### Step 1: YOLOv8 Segmentation
- Loads pretrained YOLOv8-seg model
- Detects person in image
- Generates pixel-perfect segmentation mask
- Isolates human body from background

### Step 2: Mask Application
- Applies mask to original image
- Options: dim background, remove background, or blur background
- Extracts clean human outline

### Step 3: MediaPipe Landmark Detection
- Detects 33 body landmarks on masked region
- Includes: shoulders, elbows, wrists, hips, knees, ankles, etc.
- High accuracy even with complex poses

### Step 4: Measurement Calculation
- Calculates distances between landmarks
- Converts pixel distances to real-world measurements (cm)
- Provides confidence scores for each measurement

### Step 5: Visualization
- Draws landmarks on image
- Annotates measurements
- Creates comparison views

## Measurements Calculated

The system calculates:

- **Height**: Full body height
- **Shoulder Width**: Distance between shoulders
- **Arm Length**: Shoulder to wrist
- **Torso Length**: Shoulder to hip
- **Leg Length**: Hip to ankle
- **Chest Width**: Across chest
- **Waist Width**: Across waist
- **Hip Width**: Across hips
- And more...

## Tips for Best Results

### 1. Image Quality
- Use high-resolution images (1280x720 or higher)
- Good lighting conditions
- Clear, unobstructed view of person

### 2. Pose
- Stand straight, arms slightly away from body
- Face camera directly (for front view)
- Full body visible in frame
- Avoid baggy clothing for accurate measurements

### 3. Background
- Simple, uncluttered background works best
- YOLOv8 handles complex backgrounds well
- Avoid other people in frame

### 4. Reference Calibration
- Provide your actual height with `--reference-size` for accurate measurements
- Without calibration, measurements are in relative units

### 5. Multiple Images
- Process front, side, and back views for comprehensive measurements
- System averages measurements across images for better accuracy

## Integration with Existing System

The new YOLOv8 segmentation is integrated into the existing backend:

### Backend API
The Flask backend (`backend/app.py`) automatically uses YOLOv8 when available:

```python
from segmentation_model import SegmentationModel

# Initialize (automatically uses YOLOv8 if installed)
segmentation_model = SegmentationModel()

# Segment person
mask = segmentation_model.segment_person(image)

# Apply mask
masked_image = segmentation_model.apply_mask(image, mask, background_mode='dim')
```

### Frontend Upload
The frontend upload mode automatically benefits from YOLOv8 segmentation:
1. User uploads images
2. Backend segments with YOLOv8
3. Detects landmarks with MediaPipe
4. Returns measurements and visualizations

## Troubleshooting

### YOLOv8 Not Loading
```
Warning: ultralytics not installed
```
**Solution**: Install ultralytics
```bash
pip install ultralytics
```

### Model Download Fails
**Solution**: Check internet connection. Model downloads automatically on first run.

### No Person Detected
**Solution**: 
- Ensure person is clearly visible
- Try lowering confidence threshold: `conf_threshold=0.3`
- Check image quality

### Landmarks Not Detected
**Solution**:
- Ensure full body is visible
- Check lighting conditions
- Try different pose (arms away from body)

### Memory Issues
**Solution**: Use smaller model size
```bash
python process_images_yolo.py image.jpg --model-size n
```

## Performance

### Speed (on CPU)
- Nano (n): ~0.5-1 second per image
- Small (s): ~1-2 seconds per image
- Medium (m): ~2-4 seconds per image

### Speed (on GPU)
- Nano (n): ~0.1-0.2 seconds per image
- Small (s): ~0.2-0.4 seconds per image
- Medium (m): ~0.4-0.8 seconds per image

### Accuracy
- YOLOv8 achieves 95%+ person detection accuracy
- MediaPipe provides sub-pixel landmark accuracy
- Combined system: highly accurate body measurements

## Advanced Usage

### Custom Background Modes

```python
# Remove background completely
masked = segmentation_model.apply_mask(image, mask, background_mode='remove')

# Dim background (default)
masked = segmentation_model.apply_mask(image, mask, background_mode='dim')

# Blur background
masked = segmentation_model.apply_mask(image, mask, background_mode='blur')
```

### Extract Masked Region Only

```python
# Get only the person region
masked_region, bbox = segmentation_model.get_masked_region(image, mask)
x, y, w, h = bbox
```

### Adjust Confidence Threshold

```python
# Lower threshold for difficult images
mask = segmentation_model.segment_person(image, conf_threshold=0.3)

# Higher threshold for cleaner results
mask = segmentation_model.segment_person(image, conf_threshold=0.7)
```

## Comparison: YOLOv8 vs Mask R-CNN

| Feature | YOLOv8 | Mask R-CNN |
|---------|--------|------------|
| Speed | ⚡ Very Fast | 🐢 Slower |
| Accuracy | ✅ Excellent | ✅ Excellent |
| Model Size | 📦 Small (6MB) | 📦 Large (170MB) |
| Setup | ✅ Easy | ⚠️ Complex |
| Dependencies | Minimal | Heavy (detectron2) |
| GPU Required | ❌ No | ⚠️ Recommended |

## Next Steps

1. **Test the system**: Process your first image
2. **Calibrate**: Use `--reference-size` with your height
3. **Process multiple views**: Front, side, back
4. **Integrate**: Use in your application via API

## Support

For issues or questions:
1. Check this guide
2. Review error messages
3. Check `output/` folder for results
4. Verify dependencies are installed

## License

This system uses:
- YOLOv8 (AGPL-3.0)
- MediaPipe (Apache 2.0)
- OpenCV (Apache 2.0)
