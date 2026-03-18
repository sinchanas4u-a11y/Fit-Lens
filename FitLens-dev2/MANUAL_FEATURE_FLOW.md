# Manual Landmark Feature - Visual Flow

## 📊 User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER UPLOADS PHOTOS                       │
│                    (Front View + Height Entry)                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Click "Process│
         │    Images"    │
         └───────┬───────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │   MODE SELECTION MODAL     │
    │  ┌──────────┬──────────┐   │
    │  │  Manual  │Automatic │   │
    │  │  Marking │Detection │   │
    │  └─────┬────┴────┬─────┘   │
    └────────┼─────────┼─────────┘
             │         │
        ┌────┘         └────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ MANUAL MODE   │   │ AUTOMATIC     │
│               │   │ MODE          │
└───────┬───────┘   └───────┬───────┘
        │                   │
        ▼                   ▼
┌───────────────────┐  ┌─────────────────┐
│ Interactive Canvas│  │ AI Processing   │
│ - Select Type     │  │ - MediaPipe     │
│ - Click Points    │  │ - YOLOv8        │
│ - Draw Lines      │  │ - 33 Landmarks  │
│ - View Distance   │  │ - Segmentation  │
│ - Delete/Edit     │  └────────┬────────┘
└────────┬──────────┘           │
         │                      │
         ▼                      │
┌────────────────────┐          │
│ Complete Marking   │          │
│ (Send to Backend)  │          │
└─────────┬──────────┘          │
          │                     │
          └─────────┬───────────┘
                    │
                    ▼
          ┌─────────────────┐
          │ Backend API     │
          │ /api/process-*  │
          └────────┬────────┘
                   │
                   ▼
          ┌────────────────────┐
          │ Pixel-to-Scale     │
          │ Conversion         │
          │ Formula:           │
          │ cm = px × (H/h)    │
          └─────────┬──────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │   RESULTS DISPLAY   │
          │                     │
          │ Manual: Marked Only │
          │ Auto: All 8+ Meas.  │
          └─────────────────────┘
```

## 🔄 State Flow in UploadMode.jsx

```
Initial State:
├── frontImage: null
├── sideImage: null
├── userHeight: ''
├── showModeSelection: false
├── selectedMode: null
├── showManualMarker: false
├── currentMarkingView: null
├── manualLandmarks: { front: null, side: null }
├── processing: false
└── results: null

After Upload:
├── frontImage: File
├── frontPreview: 'data:image/jpeg;base64,...'
└── userHeight: '175'

User Clicks "Process Images":
└── showModeSelection: true

User Selects "Manual":
├── showModeSelection: false
├── selectedMode: 'manual'
├── showManualMarker: true
└── currentMarkingView: 'front'

User Completes Front Marking:
├── showManualMarker: false
├── manualLandmarks.front: {...landmarks}
├── currentMarkingView: 'side' (if sideImage exists)
└── showManualMarker: true (again for side)

User Completes Side Marking:
├── showManualMarker: false
├── manualLandmarks.side: {...landmarks}
└── processing: true

Backend Response:
├── processing: false
└── results: {...measurements}

User Clicks "Process New Images":
└── All state reset to initial
```

## 🎨 Component Hierarchy

```
App
└── UploadMode
    ├── ImageUpload (front view)
    ├── ImageUpload (side view)
    ├── HeightInput
    ├── ProcessButton
    │
    ├── ModeSelection (conditional: showModeSelection)
    │   ├── ManualCard
    │   └── AutomaticCard
    │
    ├── ManualLandmarkMarker (conditional: showManualMarker)
    │   ├── Canvas
    │   ├── LandmarkTypeSelector
    │   ├── InstructionsPanel
    │   └── MeasurementsList
    │
    ├── ProcessingSteps (conditional: processing)
    │   └── ProgressBar
    │
    └── ResultsDisplay (conditional: results)
        ├── ModeBadge
        ├── CalibrationInfo
        ├── FrontViewResults
        │   ├── Visualizations
        │   └── MeasurementsTable
        └── SideViewResults (if available)
            ├── Visualizations
            └── MeasurementsTable
```

## 📡 API Flow

### Manual Mode Request

```
Frontend                          Backend
   │                                │
   │  POST /api/process-manual      │
   ├──────────────────────────────►│
   │  {                             │
   │    user_height: 175,           │
   │    front_landmarks: {          │
   │      measurements: [           │
   │        {                       │
   │          name: "shoulder",     │
   │          points: [...],        │
   │          distance_px: 200      │
   │        }                       │
   │      ]                         │
   │    }                           │
   │  }                             │
   │                                │
   │                           ┌────▼────┐
   │                           │Estimate │
   │                           │Height   │
   │                           └────┬────┘
   │                                │
   │                           ┌────▼────┐
   │                           │Calculate│
   │                           │Scale    │
   │                           └────┬────┘
   │                                │
   │                           ┌────▼────┐
   │                           │Convert  │
   │                           │to cm    │
   │                           └────┬────┘
   │                                │
   │  Response                      │
   │◄───────────────────────────────┤
   │  {                             │
   │    mode: "manual",             │
   │    calibration: {...},         │
   │    results: {                  │
   │      front: {                  │
   │        measurements: {         │
   │          shoulder: {           │
   │            value_cm: 60,       │
   │            value_px: 200       │
   │          }                     │
   │        }                       │
   │      }                         │
   │    }                           │
   │  }                             │
   │                                │
```

### Automatic Mode Request

```
Frontend                          Backend
   │                                │
   │  POST /api/process             │
   ├──────────────────────────────►│
   │  {                             │
   │    front_image: "base64...",   │
   │    side_image: "base64...",    │
   │    user_height: 175            │
   │  }                             │
   │                                │
   │                           ┌────▼────┐
   │                           │Decode   │
   │                           │Images   │
   │                           └────┬────┘
   │                                │
   │                           ┌────▼────┐
   │                           │MediaPipe│
   │                           │Landmarks│
   │                           └────┬────┘
   │                                │
   │                           ┌────▼────┐
   │                           │YOLOv8   │
   │                           │Segment  │
   │                           └────┬────┘
   │                                │
   │                           ┌────▼────┐
   │                           │Calculate│
   │                           │Measure. │
   │                           └────┬────┘
   │                                │
   │  Response                      │
   │◄───────────────────────────────┤
   │  {                             │
   │    mode: "automatic",          │
   │    calibration: {...},         │
   │    results: {                  │
   │      front: {                  │
   │        measurements: {         │
   │          shoulder: {...},      │
   │          chest: {...},         │
   │          waist: {...},         │
   │          ... (8+ total)        │
   │        },                      │
   │        visualization: "...",   │
   │        mask: "..."             │
   │      }                         │
   │    }                           │
   │  }                             │
   │                                │
```

## 🧮 Calculation Flow

### Pixel to CM Conversion

```
┌──────────────────────────────────────────┐
│         USER INPUT                        │
│  ┌────────────┐    ┌─────────────┐       │
│  │ User Height│    │   Image     │       │
│  │  175 cm    │    │  (pixels)   │       │
│  └──────┬─────┘    └──────┬──────┘       │
└─────────┼──────────────────┼──────────────┘
          │                  │
          │                  ▼
          │         ┌────────────────┐
          │         │ Height         │
          │         │ Estimation     │
          │         │                │
          │         │ Manual: Sum    │
          │         │ vertical       │
          │         │ segments       │
          │         │                │
          │         │ Auto: MediaPipe│
          │         │ landmarks      │
          │         └────────┬───────┘
          │                  │
          │         height_px = 583
          │                  │
          └─────────┬────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  SCALE FACTOR   │
          │                 │
          │  175 / 583      │
          │  = 0.3000       │
          └────────┬────────┘
                   │
                   ▼
          ┌────────────────────┐
          │  MEASUREMENT       │
          │                    │
          │  shoulder_px = 200 │
          │  shoulder_cm =     │
          │  200 × 0.3 = 60 cm │
          └────────────────────┘
```

## 🎯 Manual Marking Workflow

```
┌─────────────────────────────────────┐
│     Canvas Loads with Image         │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────┐
    │ Select Landmark│
    │ Type from      │
    │ Dropdown       │
    └────────┬───────┘
             │
             ▼
    ┌──────────────────┐
    │ User Clicks      │
    │ Point 1          │
    │ (e.g., Left      │
    │  Shoulder)       │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐   ┌────────────────┐
    │ Blue Circle      │   │ Instructions:  │
    │ Appears at       │   │ "Click second  │
    │ Click Location   │   │  point..."     │
    └────────┬─────────┘   └────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ User Clicks      │
    │ Point 2          │
    │ (e.g., Right     │
    │  Shoulder)       │
    └────────┬─────────┘
             │
             ▼
    ┌───────────────────────┐
    │ Blue Line Drawn       │
    │ Between Points        │
    │                       │
    │ Distance Calculated:  │
    │ √[(x2-x1)²+(y2-y1)²] │
    └─────────┬─────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Measurement Added  │
    │ to Sidebar List    │
    │                    │
    │ "Shoulder: 200 px" │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ User Can:          │
    │ - Mark another     │
    │ - Delete existing  │
    │ - Complete marking │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Click "Complete    │
    │ Marking"           │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Send to Backend    │
    │ for Processing     │
    └────────────────────┘
```

## 🔐 Data Structure

### Manual Landmarks Format

```javascript
{
  measurements: [
    {
      name: "shoulder",
      points: [
        {
          x: 150,              // Canvas pixel X
          y: 200,              // Canvas pixel Y
          normalized_x: 0.25,  // 0-1 range
          normalized_y: 0.33   // 0-1 range
        },
        {
          x: 350,
          y: 200,
          normalized_x: 0.75,
          normalized_y: 0.33
        }
      ],
      distance_px: 200.0       // Euclidean distance
    },
    {
      name: "waist",
      points: [...],
      distance_px: 180.0
    }
  ]
}
```

### Backend Response Format

```javascript
{
  success: true,
  mode: "manual",  // or "automatic"
  calibration: {
    user_height_cm: 175.0,
    height_in_image_px: 583.33,
    scale_factor: 0.3000,
    formula: "measurement_cm = pixel_distance × 0.3000",
    description: "Height-based calibration using user's height"
  },
  results: {
    front: {
      success: true,
      measurements: {
        shoulder: {
          value_cm: 60.0,
          value_px: 200.0,
          confidence: 1.0
        },
        waist: {
          value_cm: 54.0,
          value_px: 180.0,
          confidence: 1.0
        }
      },
      // Only in automatic mode:
      visualization: "data:image/jpeg;base64,...",
      mask: "data:image/jpeg;base64,..."
    },
    side: {
      // Similar structure if side view exists
    }
  }
}
```

---

## 💡 Key Insights

1. **Same Calibration**: Both modes use identical `scale_factor = user_height_cm / height_px` formula
2. **Mode Detection**: `results.mode` field distinguishes processing type
3. **Height Estimation**: Manual mode estimates height from marked measurements
4. **Confidence Scores**: Manual = 1.0 (user-verified), Automatic = 0-1 (AI confidence)
5. **Visualization**: Only automatic mode has landmark/mask images

---

*This visual guide complements [MANUAL_LANDMARK_FEATURE.md](MANUAL_LANDMARK_FEATURE.md)*
