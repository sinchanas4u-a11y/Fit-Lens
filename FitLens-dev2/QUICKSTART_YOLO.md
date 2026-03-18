# Quick Start: YOLOv8 Body Measurement

Get started with YOLOv8 segmentation + MediaPipe landmarks in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
pip install ultralytics opencv-python mediapipe numpy pillow
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

## Step 2: Test Setup (1 minute)

```bash
python test_yolo_setup.py
```

Or on Windows:
```bash
TEST_YOLO_SETUP.bat
```

You should see:
```
✓ OpenCV: 4.x.x
✓ NumPy: 1.x.x
✓ MediaPipe: 0.x.x
✓ Ultralytics (YOLOv8): 8.x.x
✓ All tests passed!
```

## Step 3: Process Your First Image (2 minutes)

### Option A: Single Image

```bash
python process_images_yolo.py your_image.jpg
```

### Option B: Three Images (Front, Side, Back)

```bash
python process_images_yolo.py front.jpg side.jpg back.jpg
```

### Option C: With Height Calibration

```bash
python process_images_yolo.py front.jpg --reference-size 170
```
(Replace 170 with your height in cm)

## Step 4: View Results

Check the `output/` folder for:
- `*_mask.png` - Segmentation mask
- `*_masked.png` - Image with background dimmed
- `*_landmarks.png` - Landmarks overlay
- `*_comparison.png` - Side-by-side comparison
- `*_measurements.png` - With measurement annotations

## Example Output

```
Processing: front.jpg
  Image size: 1920x1080
  Step 1: Segmenting person with YOLOv8...
  ✓ Person segmented
  Step 2: Applying mask...
  ✓ Masked region: 800x1600 at (560, 100)
  Step 3: Detecting landmarks with MediaPipe...
  ✓ Detected 33 landmarks
  Step 4: Calculating measurements...
  ✓ Calculated 15 measurements
  Step 5: Creating visualizations...
  ✓ Visualizations created
  Step 6: Saving outputs...
  ✓ Saved outputs to output/
```

## What You Get

### Measurements
- Height
- Shoulder width
- Arm length (left/right)
- Torso length
- Leg length (left/right)
- Chest width
- Waist width
- Hip width
- And more...

### Visualizations
1. **Original** - Your input image
2. **Masked** - Clean human outline with dimmed background
3. **Landmarks** - 33 body keypoints marked
4. **Mask** - Binary segmentation mask
5. **Comparison** - All views side-by-side
6. **Measurements** - Annotated with dimensions

## Tips for Best Results

### 1. Image Quality
✅ High resolution (1280x720 or better)
✅ Good lighting
✅ Clear view of full body
❌ Avoid blurry or dark images

### 2. Pose
✅ Stand straight
✅ Arms slightly away from body
✅ Face camera directly
❌ Avoid crossed arms or legs

### 3. Background
✅ Simple background (but not required)
✅ YOLOv8 handles complex backgrounds well
❌ Avoid other people in frame

## Common Issues

### "No person detected"
- Ensure person is clearly visible in image
- Try lowering confidence: `--conf-threshold 0.3`
- Check image quality

### "No landmarks detected"
- Ensure full body is visible
- Check lighting
- Try different pose

### "ultralytics not installed"
```bash
pip install ultralytics
```

## Next Steps

### Process Multiple Images
```bash
python process_images_yolo.py img1.jpg img2.jpg img3.jpg
```

### Display Results Interactively
```bash
python process_images_yolo.py image.jpg --display
```

### Use Larger Model for Better Accuracy
```bash
python process_images_yolo.py image.jpg --model-size m
```

Model sizes: `n` (fastest), `s`, `m`, `l`, `x` (most accurate)

### Integrate into Your Code
```python
from process_images_yolo import ImageProcessor

processor = ImageProcessor(yolo_model_size='n')
result = processor.process_single_image('image.jpg', reference_size_cm=170)

if result['success']:
    measurements = result['measurements']
    print(f"Height: {measurements['height']['value_cm']:.1f} cm")
```

## Full Documentation

See `YOLO_GUIDE.md` for complete documentation including:
- Advanced usage
- API integration
- Performance tuning
- Troubleshooting
- Custom configurations

## Support

1. Run `python test_yolo_setup.py` to verify installation
2. Check `output/` folder for results
3. Review `YOLO_GUIDE.md` for detailed help
4. Ensure all dependencies are installed

## That's It!

You're now ready to process body measurements with YOLOv8 + MediaPipe! 🎉

Start with:
```bash
python process_images_yolo.py your_image.jpg --display
```
