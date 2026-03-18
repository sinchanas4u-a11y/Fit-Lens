# Manual Landmark Marking Feature - Complete Implementation Guide

## 🎯 Feature Overview

The FitLens application now supports **two measurement modes**:

1. **Manual Landmark Marking** - Users manually click to place measurement points on their photos
2. **Automatic Detection** - AI-powered full body analysis using MediaPipe and YOLOv8

Both modes use the **same pixel-to-scale conversion formula** to ensure consistent measurements.

---

## 📋 User Workflow

### Step 1: Upload Photos
Users upload front view (required) and side view (optional) photos as before.

### Step 2: Enter Height
Users enter their height in cm, inches, or feet.

### Step 3: Click "Process Images"
Instead of immediately processing, a **mode selection modal** appears.

### Step 4: Choose Mode

#### Option A: Manual Landmark Marking
- **Description**: "Click to place measurement points yourself"
- **Use Case**: When user wants precise control over measurement points
- **Features**:
  - Mark specific body parts (shoulder, chest, waist, hip, arm, leg)
  - Click to place two points, lines automatically drawn
  - Edit or delete points
  - Visual feedback with hover effects
  - Canvas automatically scales to fit image

#### Option B: Automatic Detection (Recommended)
- **Description**: "AI-powered full body analysis"
- **Use Case**: Quick, comprehensive body measurements
- **Features**:
  - Detects 33 key landmarks automatically
  - Generates segmentation mask
  - Calculates 8+ body measurements
  - Includes confidence scores

### Step 5: Manual Marking Workflow (if Manual Mode selected)

1. **Select Landmark Type** from dropdown:
   - Shoulder Width
   - Chest Width
   - Waist Width
   - Hip Width
   - Arm Length
   - Leg Length
   - Custom Measurement

2. **Click on Image** to place first point
   - Blue circle appears at click location

3. **Click Again** to place second point
   - Blue line drawn between points
   - Distance calculated in pixels
   - Measurement automatically added to list

4. **Repeat** for additional measurements

5. **Review** marked points in the sidebar:
   - View all measurements
   - See pixel distances
   - Delete unwanted marks

6. **Click "Complete Marking"** to process

7. **If Side View Exists**: Repeat marking process for side view

8. **View Results** with calculated measurements in cm

---

## 🏗️ Technical Architecture

### Frontend Components

#### 1. **ModeSelection.jsx**
- **Location**: `frontend-vite/src/components/ModeSelection.jsx`
- **Purpose**: Modal overlay for choosing measurement mode
- **Props**:
  - `onSelectMode(mode)` - Callback when mode selected ('manual' or 'automatic')
  - `onCancel()` - Callback when user closes modal
- **Features**:
  - Two-card layout with visual distinction
  - "Recommended" badge on Automatic mode
  - Feature lists for each mode
  - Responsive design

#### 2. **ManualLandmarkMarker.jsx**
- **Location**: `frontend-vite/src/components/ManualLandmarkMarker.jsx`
- **Purpose**: Interactive canvas for manual point marking
- **Props**:
  - `imageUrl` - Image to display (base64 or URL)
  - `viewType` - Either 'front' or 'side'
  - `onComplete(data)` - Callback with landmark data
  - `onCancel()` - Callback when user cancels
- **Features**:
  - HTML5 canvas with mouse event handling
  - 7 predefined landmark types
  - Point placement validation
  - Distance calculation
  - Visual feedback (hover, active states)
  - Responsive canvas scaling

#### 3. **UploadMode.jsx** (Updated)
- **Location**: `frontend-vite/src/components/UploadMode.jsx`
- **New State Variables**:
  ```javascript
  const [showModeSelection, setShowModeSelection] = useState(false);
  const [selectedMode, setSelectedMode] = useState(null);
  const [showManualMarker, setShowManualMarker] = useState(false);
  const [currentMarkingView, setCurrentMarkingView] = useState(null);
  const [manualLandmarks, setManualLandmarks] = useState({ front: null, side: null });
  ```
- **New Functions**:
  - `handleInitialProcess()` - Shows mode selection
  - `handleModeSelection(mode)` - Handles mode choice
  - `handleManualLandmarkComplete(data)` - Saves manual landmarks
  - `handleManualMarkingCancel()` - Cancels marking
  - `processManualLandmarks(landmarks)` - Sends to backend
  - `handleAutomaticProcess()` - Original automatic flow

### Backend API

#### 1. **POST /api/process-manual**
- **Location**: `backend/app_updated.py`
- **Purpose**: Process manually marked landmarks
- **Request Body**:
  ```json
  {
    "user_height": 175.0,
    "front_landmarks": {
      "measurements": [
        {
          "name": "shoulder",
          "points": [
            {"x": 100, "y": 200, "normalized_x": 0.25, "normalized_y": 0.4},
            {"x": 300, "y": 200, "normalized_x": 0.75, "normalized_y": 0.4}
          ],
          "distance_px": 200.0
        }
      ]
    },
    "side_landmarks": null
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "mode": "manual",
    "calibration": {
      "user_height_cm": 175.0,
      "height_in_image_px": 583.33,
      "scale_factor": 0.3,
      "formula": "measurement_cm = pixel_distance × 0.3000"
    },
    "results": {
      "front": {
        "success": true,
        "measurements": {
          "shoulder": {
            "value_cm": 60.0,
            "value_px": 200.0,
            "confidence": 1.0
          }
        }
      }
    }
  }
  ```

#### 2. **Helper Functions** (backend/app_updated.py)

##### `estimate_height_from_landmarks(landmarks)`
- **Purpose**: Estimate body height from marked vertical measurements
- **Logic**:
  - Looks for shoulder, chest, waist, hip, leg landmarks
  - Calculates height as sum of vertical segments
  - Uses widths × 3 as rough height estimate if no vertical marks
- **Returns**: Estimated height in pixels

##### `process_manual_landmarks(landmarks, user_height_cm, height_px)`
- **Purpose**: Convert pixel distances to cm using scale factor
- **Formula**: `measurement_cm = pixel_distance × (user_height_cm / height_px)`
- **Returns**: Dictionary of measurements with cm values

##### `process_manual_view(view_data, user_height_cm, height_px)`
- **Purpose**: Process landmarks for one view (front or side)
- **Returns**: Results object with measurements

---

## 🔢 Measurement Calculation

### Common Scale Factor Formula

Both manual and automatic modes use the **same formula**:

```
scale_factor = user_height_cm / height_in_image_px
measurement_cm = pixel_distance × scale_factor
```

### Manual Mode Height Estimation

Since manual mode doesn't detect full body, height is estimated by:

1. **If vertical measurements exist** (arm, leg):
   - Sum all vertical segment lengths
   - Use as height_px

2. **If only horizontal measurements** (shoulder, chest, waist, hip):
   - Average the widths
   - Multiply by 3 (rough body proportion)
   - Use as height_px

3. **Default fallback**: 500 pixels if no measurements

### Example Calculation

Given:
- User height: 175 cm
- Shoulder mark: 200 pixels
- Estimated body height: 583 pixels

Calculate:
```
scale_factor = 175 / 583 = 0.3
shoulder_width_cm = 200 × 0.3 = 60 cm
```

---

## 🎨 UI/UX Design

### Mode Selection Modal
- **Visual**: Overlay with two large cards
- **Colors**:
  - Manual: Orange accent (#ff9800)
  - Automatic: Green accent (#4caf50)
- **Badge**: "Recommended" on Automatic mode
- **Hover**: Scale transform on hover

### Manual Landmark Marker
- **Layout**: Split screen
  - Left: Canvas (75% width)
  - Right: Sidebar (25% width)
- **Colors**:
  - Points: Blue (#2196f3)
  - Lines: Blue
  - Hover: Scale + shadow
  - Selected type: Orange background
- **Feedback**:
  - Instructions update based on state
  - Point count shown for each measurement
  - Delete button on hover

### Results Display
- **Mode Badge**: Colored pill showing mode
- **Manual Note**: Yellow info box for manual mode
- **Measurements**: Same table format as automatic mode
- **Differentiation**: Manual shows only marked measurements

---

## 📁 File Structure

```
FitLens-dev2/
├── backend/
│   ├── app_updated.py           # Flask API with /api/process-manual
│   ├── landmark_detector.py     # MediaPipe pose detection (automatic mode)
│   └── measurement_engine.py    # Shared measurement logic
│
├── frontend-vite/
│   └── src/
│       └── components/
│           ├── UploadMode.jsx              # Main upload workflow (updated)
│           ├── ModeSelection.jsx           # NEW: Mode selection modal
│           ├── ModeSelection.css           # NEW: Modal styling
│           ├── ManualLandmarkMarker.jsx    # NEW: Canvas marker component
│           └── ManualLandmarkMarker.css    # NEW: Marker styling
│
└── MANUAL_LANDMARK_FEATURE.md    # This documentation
```

---

## 🧪 Testing Checklist

### Manual Mode Testing

- [ ] Upload front image
- [ ] Enter height
- [ ] Click "Process Images"
- [ ] Mode selection modal appears
- [ ] Click "Manual Landmark Marking"
- [ ] Image loads on canvas
- [ ] Select "Shoulder Width" from dropdown
- [ ] Click left shoulder → blue point appears
- [ ] Click right shoulder → blue line drawn
- [ ] Measurement appears in sidebar
- [ ] Repeat for other landmarks
- [ ] Click "Complete Marking"
- [ ] Results show manual mode badge
- [ ] Results show only marked measurements
- [ ] Measurements in cm are reasonable

### Automatic Mode Testing

- [ ] Upload front image
- [ ] Enter height
- [ ] Click "Process Images"
- [ ] Mode selection modal appears
- [ ] Click "Automatic Detection"
- [ ] Processing steps show
- [ ] Results show automatic mode badge
- [ ] Results show all detected measurements
- [ ] Landmarks visualization displayed
- [ ] Segmentation mask displayed

### Edge Cases

- [ ] Cancel mode selection → returns to upload screen
- [ ] Cancel manual marking → shows mode selection again
- [ ] Upload only front view → works in both modes
- [ ] Upload front + side → manual mode marks both views
- [ ] No landmarks marked → error message
- [ ] Mark one point only → error message
- [ ] Different height units (cm/inches/feet) → correct conversion
- [ ] Reset button → clears all state

---

## 🚀 How to Run

### 1. Start Backend
```bash
cd backend
python app_updated.py
```
Backend runs on: http://localhost:5001

### 2. Start Frontend
```bash
cd frontend-vite
npm run dev
```
Frontend runs on: http://localhost:3001

### 3. Open Browser
Navigate to: http://localhost:3001

### 4. Test the Feature
1. Click "Upload Mode"
2. Upload a test image (recommend full body photo)
3. Enter height (e.g., 175 cm)
4. Click "Process Images"
5. Choose "Manual Landmark Marking"
6. Mark body measurements
7. View results

---

## 🔍 Debugging

### Check Browser Console
Press F12 to open DevTools, look for:
- `🎯 Processing manual landmarks...` - Manual mode triggered
- `📤 Sending manual landmarks to backend:` - Data being sent
- `📥 Received response from backend:` - Results received
- `🚀 Starting automatic image processing...` - Automatic mode triggered

### Check Backend Logs
Look for:
- `Received manual landmarks request` - Request received
- `Estimated height: X px` - Height estimation
- `Scale factor: X` - Calibration calculated
- `Measurements calculated: X` - Number of measurements

### Common Issues

**Issue**: Mode selection doesn't appear
- **Fix**: Check that `showModeSelection` state is set to `true` in `handleInitialProcess()`

**Issue**: Canvas doesn't show image
- **Fix**: Verify `imageUrl` prop contains valid base64 data or URL

**Issue**: Manual measurements incorrect
- **Fix**: Check that `user_height` is in cm (conversion happens in `handleProcess`)

**Issue**: Backend 500 error
- **Fix**: Check backend logs for stack trace, verify request data format

---

## 📊 Performance Notes

### Manual Mode
- **Pros**:
  - Fast (no AI processing)
  - User control over exact points
  - Works with partial body shots
- **Cons**:
  - Requires user effort
  - Fewer measurements than automatic
  - Accuracy depends on user precision

### Automatic Mode
- **Pros**:
  - Comprehensive measurements (8+)
  - No user effort after upload
  - Includes confidence scores
- **Cons**:
  - Requires full body in frame
  - Processing takes 3-5 seconds
  - Requires good lighting/pose

---

## 🔜 Future Enhancements

1. **Save Landmark Templates**: Allow users to save common measurement sets
2. **Zoom/Pan Canvas**: For precise point placement on large images
3. **Angle Measurements**: Add protractor tool for joint angles
4. **Comparison Mode**: Compare manual vs automatic results side-by-side
5. **Mobile Touch Support**: Optimize for touch screens
6. **Undo/Redo**: History stack for landmark edits
7. **Bulk Edit**: Select multiple landmarks and move together
8. **Export Landmark Data**: Save landmark coordinates as JSON

---

## 📝 API Reference

### Frontend → Backend: Manual Mode

**Endpoint**: `POST /api/process-manual`

**Request**:
```typescript
{
  user_height: number,           // Height in cm
  front_landmarks: {
    measurements: Array<{
      name: string,              // e.g., "shoulder", "waist"
      points: Array<{
        x: number,               // Pixel x coordinate
        y: number,               // Pixel y coordinate
        normalized_x: number,    // X as fraction of width (0-1)
        normalized_y: number     // Y as fraction of height (0-1)
      }>,
      distance_px: number        // Distance between points in pixels
    }>
  } | null,
  side_landmarks: {              // Same structure as front
    // ...
  } | null
}
```

**Response**:
```typescript
{
  success: boolean,
  mode: "manual",
  calibration: {
    user_height_cm: number,
    height_in_image_px: number,
    scale_factor: number,
    formula: string,
    description: string
  },
  results: {
    front?: {
      success: boolean,
      measurements: {
        [measurementName: string]: {
          value_cm: number,
          value_px: number,
          confidence: number     // Always 1.0 for manual
        }
      }
    },
    side?: {
      // Same structure as front
    }
  }
}
```

---

## 🎓 Development Notes

### State Management Flow

1. **Initial**: `showModeSelection=false, selectedMode=null`
2. **User clicks Process**: `showModeSelection=true`
3. **User selects Manual**: `selectedMode='manual', showModeSelection=false, showManualMarker=true`
4. **User completes marking**: `showManualMarker=false, processing=true`
5. **Results received**: `processing=false, results={...}`
6. **User clicks Reset**: All state cleared

### Component Communication

```
UploadMode (parent)
  ├─> ModeSelection (modal)
  │     └─> onSelectMode(mode) → handleModeSelection
  │
  └─> ManualLandmarkMarker (canvas)
        ├─> onComplete(data) → handleManualLandmarkComplete
        └─> onCancel() → handleManualMarkingCancel
```

### Pixel-to-Scale Consistency

Both modes must use identical calibration:
```javascript
// Automatic mode (backend/landmark_detector.py)
height_px = calculate_body_height_from_landmarks(landmarks)
scale_factor = user_height_cm / height_px

// Manual mode (backend/app_updated.py)
height_px = estimate_height_from_landmarks(manual_landmarks)
scale_factor = user_height_cm / height_px

// Both use same measurement formula
measurement_cm = pixel_distance * scale_factor
```

---

## 📞 Support

If you encounter issues:

1. **Check this documentation** for setup/usage instructions
2. **Check browser console** (F12) for frontend errors
3. **Check backend logs** in terminal for API errors
4. **Verify file structure** matches documentation
5. **Ensure all dependencies installed** (`npm install`, `pip install -r requirements.txt`)

---

## ✅ Implementation Complete

All components are implemented and integrated:
- ✅ ModeSelection modal component
- ✅ ManualLandmarkMarker canvas component
- ✅ UploadMode integration
- ✅ Backend /api/process-manual endpoint
- ✅ Height estimation logic
- ✅ Measurement calculation
- ✅ Results display differentiation
- ✅ State management
- ✅ Error handling

**The feature is ready for testing!**

---

*Last Updated: 2024*
*FitLens - Body Measurement Application*
