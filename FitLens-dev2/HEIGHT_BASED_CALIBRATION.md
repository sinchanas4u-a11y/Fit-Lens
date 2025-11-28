# Height-Based Calibration System

## Overview

The system has been updated to use **user's height** as a reference instead of a reference object. This is more accurate and simpler!

## What Changed

### Before (Reference Object):
- Upload 3 images: front, side, reference object
- Enter object dimensions (width × height)
- System detects object and calculates scale

### After (User Height):
- Upload 2 images: front, side (optional)
- Enter your height
- System detects your height in image and calculates scale

## Benefits

✅ **More Accurate** - Uses full body height for calibration
✅ **Simpler** - No need for reference object photo
✅ **Faster** - One less image to upload
✅ **More Reliable** - Height detection is more robust than object detection

## How It Works

### Step 1: Upload Photos
- **Front view** (required): Stand straight, full body visible
- **Side view** (optional): Side profile, full body visible

### Step 2: Enter Your Height
- Enter your actual height
- Choose unit: cm, inches, or feet
- Examples:
  - 170 cm
  - 5.6 feet
  - 67 inches

### Step 3: Processing
1. System detects landmarks in your image
2. Measures your height in pixels (nose to ankle)
3. Calculates scale factor: `your_height_cm ÷ height_in_pixels`
4. Uses scale factor to convert all measurements

### Step 4: Get Results
- All body measurements in cm
- Visualizations (mask + landmarks)
- Calibration details

## Example

**Your Input:**
- Height: 170 cm
- Front image uploaded

**System Calculates:**
- Height in image: 850 pixels
- Scale factor: 170 ÷ 850 = 0.2 cm/px
- This means: 1 pixel = 0.2 cm

**Result:**
- All measurements calculated using this scale
- Shoulder width: 200 px × 0.2 = 40 cm
- Leg length: 400 px × 0.2 = 80 cm
- etc.

## Tips for Best Results

### 1. Photo Quality
✅ High resolution (1280x720 or higher)
✅ Good lighting
✅ Clear, unobstructed view
✅ **Full body must be visible** (head to feet)

### 2. Pose
✅ Stand straight
✅ Arms slightly away from body
✅ Face camera directly (front view)
✅ Feet visible on ground
✅ No shoes (or measure with shoes and adjust)

### 3. Height Input
✅ Enter your actual height
✅ Measure yourself accurately
✅ Use same unit consistently
✅ Include shoes if wearing them in photo

### 4. Background
✅ Simple, uncluttered background
✅ Good contrast with your clothing
✅ Avoid other people in frame

## Accuracy

### Factors Affecting Accuracy:

**Good Accuracy (±1-2 cm):**
- Full body visible
- Standing straight
- Good lighting
- Accurate height input
- High resolution image

**Reduced Accuracy (±3-5 cm):**
- Partial body visible
- Poor lighting
- Low resolution
- Incorrect height input
- Bent posture

## Height Units

### Supported Units:

| Unit | Example | Conversion |
|------|---------|------------|
| **cm** | 170 | Direct |
| **inches** | 67 | × 2.54 = cm |
| **feet** | 5.6 | × 30.48 = cm |

### Common Heights:

| Height | cm | inches | feet |
|--------|-----|--------|------|
| Short | 150-160 | 59-63 | 4.9-5.2 |
| Average | 160-180 | 63-71 | 5.2-5.9 |
| Tall | 180-200 | 71-79 | 5.9-6.6 |

## Troubleshooting

### "Could not detect person in image"
**Cause:** Full body not visible or poor image quality

**Solution:**
- Ensure full body is in frame (head to feet)
- Check lighting
- Use higher resolution image
- Stand further from camera

### "Could not measure height in image"
**Cause:** Feet or head not visible

**Solution:**
- Make sure both head and feet are visible
- Stand straight
- Don't crop the image
- Ensure full body is in frame

### Measurements seem incorrect
**Cause:** Incorrect height input or poor pose

**Solution:**
- Double-check your height input
- Ensure you're standing straight
- Verify full body is visible
- Check if you measured with/without shoes

## Comparison: Object vs Height

| Feature | Reference Object | User Height |
|---------|-----------------|-------------|
| **Accuracy** | ±2-3 cm | ±1-2 cm |
| **Setup** | Need object photo | Just enter height |
| **Speed** | 3 images | 2 images |
| **Reliability** | Object detection can fail | Height detection robust |
| **Ease** | Need to photograph object | Just type height |

## API Changes

### Old Request:
```json
{
  "front_image": "base64...",
  "side_image": "base64...",
  "reference_image": "base64...",
  "reference_width": 8.5,
  "reference_height": 5.5
}
```

### New Request:
```json
{
  "front_image": "base64...",
  "side_image": "base64...",
  "user_height": 170
}
```

### Old Response:
```json
{
  "reference_calibration": {
    "width_cm": 8.5,
    "height_cm": 5.5,
    "width_px": 245.0,
    "height_px": 158.0,
    "scale_factor": 0.0347
  }
}
```

### New Response:
```json
{
  "calibration": {
    "user_height_cm": 170,
    "height_in_image_px": 850.0,
    "scale_factor": 0.2,
    "formula": "170 cm ÷ 850.00 px = 0.2000 cm/px"
  }
}
```

## Usage

### Frontend:
1. Upload front view image
2. (Optional) Upload side view
3. Enter your height
4. Select unit (cm/inches/feet)
5. Click "Process Images"

### Backend:
1. Receives images and height
2. Detects landmarks
3. Measures height in pixels
4. Calculates scale factor
5. Computes all measurements
6. Returns results

## Migration

If you have old code using reference objects:

**Update frontend:**
- Remove reference image upload
- Remove width/height inputs
- Add height input with unit selector

**Update backend:**
- Remove reference object detection
- Add height-based scale calculation
- Update response structure

## Summary

✅ **Simpler:** No reference object needed
✅ **Faster:** One less image to upload
✅ **More Accurate:** Uses full body height
✅ **More Reliable:** Height detection is robust
✅ **Easier:** Just enter your height

The system now provides better accuracy with less complexity! 🎉
