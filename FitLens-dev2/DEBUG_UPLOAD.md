# Debug Upload Issue

## How to Debug

### Step 1: Check Backend Logs

When you upload images and click "Process & Measure", watch the backend terminal for these messages:

```
Processing front image with scale factor: 0.0660
Segmentation complete: True
Landmarks detected: True
Number of landmarks: 33
Measurements calculated: 5 measurements
Measurements with pixels: 5
Returning 5 measurements
```

### Step 2: Check Browser Console

Open browser console (F12) and look for:
- Any error messages
- Network tab → Check the POST request to `/api/upload/process`
- Response should contain measurements

### Step 3: Common Issues

#### Issue 1: No Measurements Returned

**Symptoms:**
- Results show but measurements table is empty
- Backend logs show: "Measurements calculated: 0 measurements"

**Cause:** Landmarks detected but measurements couldn't be calculated

**Fix:** Check if the person is fully visible in the image (head to feet)

#### Issue 2: "No person detected"

**Symptoms:**
- Error message: "No person detected"
- Backend logs show: "Landmarks detected: False"

**Cause:** MediaPipe couldn't detect a person in the image

**Fix:**
- Ensure person is clearly visible
- Good lighting
- Person facing camera
- Full body in frame

#### Issue 3: Reference Object Not Detected

**Symptoms:**
- Error: "Reference object not detected"
- Processing stops before measurements

**Cause:** Reference detector couldn't find the object

**Fix:**
- Use clear, well-lit reference object
- Plain background
- Object fully visible
- Try A4 paper (larger, easier to detect)

#### Issue 4: Frontend Shows Loading Forever

**Symptoms:**
- "Processing..." never completes
- No results displayed

**Cause:** Backend error or network issue

**Fix:**
- Check backend terminal for errors
- Check browser console for network errors
- Restart backend

### Step 4: Test with Sample Images

Create a test with known good images:

1. Take a clear photo of A4 paper
2. Take a clear full-body photo (front view)
3. Upload both
4. Enter 29.7 cm (A4 height)
5. Click Process

### Step 5: Check Measurements Definition

The measurements are defined in `backend/measurement_engine.py`:

```python
self.measurements = {
    'front': {
        'shoulder_width': ('left_shoulder', 'right_shoulder'),
        'hip_width': ('left_hip', 'right_hip'),
        'chest_width': ('left_shoulder', 'right_shoulder'),
        'waist_width': ('left_hip', 'right_hip'),
        'arm_span': ('left_wrist', 'right_wrist'),
    },
    ...
}
```

If these landmarks aren't visible, no measurements will be calculated.

## Quick Test

### Test Backend Directly

```bash
cd backend
python
```

```python
import cv2
from landmark_detector import LandmarkDetector
from measurement_engine import MeasurementEngine

# Load test image
img = cv2.imread('path/to/your/image.jpg')

# Detect landmarks
detector = LandmarkDetector()
landmarks = detector.detect(img)

print(f"Landmarks detected: {landmarks is not None}")
if landmarks:
    print(f"Number of landmarks: {len(landmarks)}")
    
    # Calculate measurements
    engine = MeasurementEngine()
    scale_factor = 0.066  # Example
    measurements = engine.calculate_measurements_with_confidence(
        landmarks, scale_factor, 'front'
    )
    
    print(f"Measurements: {len(measurements)}")
    for name, val in measurements.items():
        print(f"  {name}: {val[0]:.2f} cm")
```

## What to Check in Backend Logs

Look for these specific messages:

1. **"Processing front image..."** - Processing started
2. **"Landmarks detected: True"** - Person found
3. **"Number of landmarks: 33"** - All landmarks detected
4. **"Measurements calculated: X"** - Measurements computed
5. **"Returning X measurements"** - Success!

If you see:
- **"Landmarks detected: False"** → Person not detected in image
- **"Measurements calculated: 0"** → Landmarks found but measurements failed
- **"ERROR in process_single_image"** → Processing error

## Frontend Display

After successful processing, you should see:

1. **Blue Calibration Box** with:
   - Reference size
   - Detected pixels
   - Scale factor
   - Formula

2. **Measurements Table** with columns:
   - Measurement name
   - Pixels
   - Centimeters
   - Confidence
   - Calculation

3. **Visualization Image** with:
   - Skeleton overlay
   - Top 5 measurements annotated

## Still Not Working?

### Enable Debug Mode

Add this to the top of `backend/app.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Image Format

Ensure images are:
- JPG or PNG format
- Not too large (< 5MB)
- Good resolution (at least 640x480)
- Not corrupted

### Test with Different Images

Try with:
1. Different person
2. Different lighting
3. Different background
4. Different camera/phone

### Restart Everything

```bash
# Stop backend (Ctrl+C)
# Stop frontend (Ctrl+C)

# Restart backend
cd backend
python app.py

# Restart frontend (new terminal)
cd frontend
npm start
```

---

**Most Common Issue:** Person not fully visible in image or poor lighting. Ensure full body (head to feet) is clearly visible in the photo.
