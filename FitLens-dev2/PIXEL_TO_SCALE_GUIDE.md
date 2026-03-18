# Pixel-to-Scale Calculation Guide

## 📏 Understanding the Calibration

### What is Pixel-to-Scale Conversion?

When you take a photo, measurements are initially in **pixels**. To convert them to real-world units (centimeters), we need a **scale factor**.

### The Calibration Process

1. **Reference Object**: You provide an object with a known size (e.g., A4 paper = 29.7 cm)
2. **Detection**: System detects the object and measures it in pixels
3. **Scale Factor**: Calculates how many centimeters each pixel represents
4. **Conversion**: Uses this factor to convert all measurements

## 🧮 The Math

### Step 1: Detect Reference Object

```
Reference Object (A4 paper height)
Known Size: 29.7 cm
Detected Size: 450 pixels
```

### Step 2: Calculate Scale Factor

```
Scale Factor = Known Size ÷ Detected Size
Scale Factor = 29.7 cm ÷ 450 px
Scale Factor = 0.0660 cm/pixel
```

This means: **1 pixel = 0.0660 cm**

### Step 3: Convert Measurements

For any body measurement:

```
Real Size (cm) = Pixel Distance × Scale Factor

Example - Shoulder Width:
Pixel Distance: 250 pixels
Real Size: 250 px × 0.0660 cm/px = 16.5 cm
```

## 📊 What You'll See

### Upload Mode

After processing, you'll see:

**Calibration Section:**
```
📏 Pixel-to-Scale Calibration
Reference Object: 29.7 cm = 450.00 pixels
Formula: 29.7 cm ÷ 450.00 px = 0.0660 cm/px
Scale Factor: 0.0660 cm/pixel
1 pixel = 0.0660 cm
```

**Measurements Table:**
```
Measurement      | Pixels  | Centimeters | Confidence | Calculation
----------------|---------|-------------|------------|---------------------------
Shoulder Width  | 250 px  | 16.50 cm    | 95%        | 250.00 px × 0.0660 = 16.50 cm
Arm Length      | 450 px  | 29.70 cm    | 92%        | 450.00 px × 0.0660 = 29.70 cm
Hip Width       | 220 px  | 14.52 cm    | 88%        | 220.00 px × 0.0660 = 14.52 cm
```

### Live Camera Mode

In the feedback log, you'll see:

```
=== CALIBRATION INFO ===
Reference: 29.7 cm
Detected: 450.00 pixels
Scale Factor: 0.0660 cm/px
Formula: 29.7 ÷ 450.00 = 0.0660

=== MEASUREMENTS ===
SHOULDER WIDTH:
  250 px → 16.50 cm
  Confidence: 95%

ARM LENGTH:
  450 px → 29.70 cm
  Confidence: 92%
```

## 🎯 Why This Matters

### Accuracy

The scale factor determines measurement accuracy:

- **Good calibration**: ±1-2 cm accuracy
- **Poor calibration**: ±5-10 cm accuracy

### Factors Affecting Accuracy

1. **Reference Object Size**
   - Larger objects = better accuracy
   - A4 paper (29.7 cm) is ideal
   - Credit card (8.56 cm) works but less accurate

2. **Distance from Camera**
   - Reference and body must be at same distance
   - Closer = larger pixels = different scale
   - Farther = smaller pixels = different scale

3. **Camera Angle**
   - Perpendicular to camera = accurate
   - Angled = distorted measurements

4. **Reference Detection**
   - Clear, well-lit object = accurate detection
   - Blurry or dark = inaccurate pixel count

## 📐 Example Calculations

### Example 1: A4 Paper (Height)

```
Known Size: 29.7 cm
Detected: 450 pixels
Scale Factor: 29.7 ÷ 450 = 0.0660 cm/px

Shoulder Width: 250 px
Real Size: 250 × 0.0660 = 16.5 cm

Arm Length: 450 px
Real Size: 450 × 0.0660 = 29.7 cm
```

### Example 2: Credit Card (Width)

```
Known Size: 8.56 cm
Detected: 130 pixels
Scale Factor: 8.56 ÷ 130 = 0.0658 cm/px

Shoulder Width: 250 px
Real Size: 250 × 0.0658 = 16.45 cm
```

### Example 3: Different Distance

**Close to Camera:**
```
A4 Paper: 29.7 cm = 600 pixels
Scale Factor: 29.7 ÷ 600 = 0.0495 cm/px
Shoulder: 250 px × 0.0495 = 12.38 cm (too small!)
```

**Far from Camera:**
```
A4 Paper: 29.7 cm = 300 pixels
Scale Factor: 29.7 ÷ 300 = 0.0990 cm/px
Shoulder: 250 px × 0.0990 = 24.75 cm (too large!)
```

**Correct Distance:**
```
A4 Paper: 29.7 cm = 450 pixels
Scale Factor: 29.7 ÷ 450 = 0.0660 cm/px
Shoulder: 250 px × 0.0660 = 16.50 cm (correct!)
```

## 🔍 Verifying Accuracy

### Method 1: Check Scale Factor

Typical scale factors at 2 meters distance:
- **0.05 - 0.08 cm/px**: Normal range
- **< 0.03 cm/px**: Too close to camera
- **> 0.15 cm/px**: Too far from camera

### Method 2: Cross-Check Measurements

If you know your actual measurements:
```
Actual Shoulder Width: 40 cm
Measured: 38-42 cm → Good (±5% error)
Measured: 30-50 cm → Poor (±25% error)
```

### Method 3: Multiple Captures

Take 3 measurements and compare:
```
Capture 1: 40.2 cm
Capture 2: 40.5 cm
Capture 3: 39.8 cm
Average: 40.17 cm
Variation: ±0.7 cm → Consistent!
```

## 💡 Tips for Best Results

### 1. Use Large Reference Objects
- ✅ A4 paper (29.7 cm)
- ✅ Ruler (30 cm)
- ⚠️ Credit card (8.56 cm) - less accurate
- ❌ Coin (2 cm) - too small

### 2. Maintain Same Distance
- Place reference at same distance as body
- Don't move between reference and body capture
- Use tape marks on floor for consistency

### 3. Good Lighting
- Even lighting on reference and body
- No shadows on reference object
- Avoid glare on shiny objects

### 4. Clear Detection
- Hold reference flat (not tilted)
- Ensure full object is visible
- Plain background helps detection

### 5. Multiple Measurements
- Take 3-5 captures
- Average the results
- Discard outliers

## 📊 Understanding the Display

### Calibration Box (Blue)
Shows how the scale factor was calculated:
- Input: Reference size in cm
- Detection: Size in pixels
- Output: Scale factor (cm/px)

### Measurements Table
For each measurement:
- **Pixels**: Raw pixel distance
- **Centimeters**: Converted real-world size
- **Confidence**: How reliable (0-100%)
- **Calculation**: Shows the math

### Visualization Image
Annotated image showing:
- Detected landmarks (dots)
- Skeleton connections (lines)
- Top 5 measurements (text overlay)

## 🎓 Advanced: Camera Calibration

For even better accuracy, you can use camera intrinsic parameters:

```python
# Pinhole camera model
focal_length = 4.0 mm
sensor_width = 6.17 mm
image_width = 1280 pixels
distance = 200 cm

pixel_size = sensor_width / image_width
real_size_per_pixel = (pixel_size × distance) / focal_length
scale_factor = real_size_per_pixel / 10  # Convert to cm
```

This accounts for:
- Camera focal length
- Sensor size
- Distance from camera
- Image resolution

## 🆘 Troubleshooting

### Measurements Too Small
**Cause**: Scale factor too small (< 0.03)
**Fix**: Move farther from camera or use larger reference

### Measurements Too Large
**Cause**: Scale factor too large (> 0.15)
**Fix**: Move closer to camera or check reference detection

### Inconsistent Results
**Cause**: Reference and body at different distances
**Fix**: Ensure both at same distance from camera

### Reference Not Detected
**Cause**: Poor lighting or unclear object
**Fix**: Improve lighting, use plain background, hold flat

---

**Now you understand exactly how your measurements are calculated!** 📏✨
