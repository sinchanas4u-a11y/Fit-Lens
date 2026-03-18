# Visual Guide: Body Measurement Application

Visual diagrams and flowcharts to understand the system.

## 🎨 User Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│                     Camera Feed Window                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  Status: "PERFECT! Hold still..."          [GREEN]     │  │
│  │  Captured: 1/3                                         │  │
│  │                                                         │  │
│  │              ┌─────────────┐                           │  │
│  │              │    👤       │  ← Skeleton Overlay       │  │
│  │              │   /│\      │     (GREEN when aligned)   │  │
│  │              │  / │ \     │     (RED when misaligned)  │  │
│  │              │    │       │                            │  │
│  │              │   / \      │                            │  │
│  │              │  /   \     │                            │  │
│  │              └─────────────┘                           │  │
│  │                                                         │  │
│  │  Measurements:                                         │  │
│  │    Shoulder Width: 42.3 cm                            │  │
│  │    Arm Length Left: 58.7 cm                           │  │
│  │    Torso Length: 65.2 cm                              │  │
│  │                                                         │  │
│  │  Progress Bar:                                         │  │
│  │  [████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    │  │
│  │  Hold for 15 frames...                                │  │
│  │                                                         │  │
│  │  Press 'Q' to quit | 'R' to reset                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Skeleton Overlay States

### ❌ Misaligned (RED)
```
     O nose
    /|\
   / | \
  O  O  O  ← shoulders, elbows, wrists
     |
    O O   ← hips
    | |
    O O  ← knees
    | |
    O O  ← ankles

Color: RED (0, 0, 255)
Message: "Move arms away from body"
```

### ✅ Aligned (GREEN)
```
     O nose
    /|\
   / | \
  O  O  O  ← shoulders, elbows, wrists
     |
    O O   ← hips
    | |
    O O  ← knees
    | |
    O O  ← ankles

Color: GREEN (0, 255, 0)
Message: "PERFECT! Hold still..."
```

### 📸 Captured (with endpoints marked)
```
     O nose
    /|\
   / | \
  ●  ●  ●  ← YELLOW endpoints
     |
    ● ●   ← YELLOW endpoints
    | |
    O O  ← knees
    | |
    O O  ← ankles

Yellow circles = Measurement endpoints
Saved with measurements annotated
```

## 🔄 Application Flow Diagram

```
START
  │
  ▼
Initialize
• Load Model
• Open Camera
• Setup Utils
  │
  ▼
Capture Frame
  │
  ▼
Flip Horizontal (Mirror)
  │
  ▼
R-CNN Inference
Detect Person
Extract 17 Keypoints
  │
  ▼
Person Found?
  │
  ├─NO──► Display "No person detected"
  │
  └─YES─► Calibrate (first time)
          │
          ▼
          Check Alignment
          • Arms away?
          • Elbows straight?
          • Facing camera?
          • Standing straight?
          • Centered?
          • Correct distance?
          │
          ▼
          Aligned?
          │
          ├─NO──► Reset counter
          │       Display feedback
          │
          └─YES─► Calculate Measurements
                  Increment counter
                  │
                  ▼
                  Counter >= 30?
                  │
                  ├─NO──► Continue
                  │
                  └─YES─► CAPTURE!
                          Save Image
                          │
                          ▼
                          Count >= 3?
                          │
                          ├─NO──► Continue
                          │
                          └─YES─► DONE!
                                  Show Results
  │
  ▼
Draw Skeleton & UI
Display Frame
  │
  ▼
Check Keys
Q=Quit | R=Reset
  │
  └──► Loop Back
```

## 📏 Measurement Calculation

```
Keypoints Detected
        │
        ▼
┌───────────────────┐
│ Shoulder Width    │
│ left_shoulder ──── right_shoulder
│      O                    O
│       └───────────────────┘
│ Distance = sqrt((x2-x1)² + (y2-y1)²)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Arm Length        │
│ shoulder ──── elbow ──── wrist
│    O            O          O
│     └───────────┴──────────┘
│ Length = dist(shoulder,elbow) + dist(elbow,wrist)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Pixel to CM       │
│ pixel_distance    │
│       ×           │
│ scale_factor      │
│       =           │
│ measurement_cm    │
└───────────────────┘
```

## 🎯 Alignment Checks

```
1. Arms Away from Body
   ┌─────────┐
   │    O    │  ← Torso center
   │   /|\   │
   │  O O O  │  ← Elbows must be > 10% away
   │    |    │
   └─────────┘

2. Elbow Angles
   shoulder O
            \
             \ angle > 160°
              O elbow
               \
                O wrist

3. Facing Camera (Symmetry)
   left_shoulder    right_shoulder
        O ─────────── O
        |              |  ← Y-coordinates similar
        O ─────────── O
   left_hip        right_hip

4. Standing Straight (Vertical)
        nose O
             |
             |  ← X-coordinates aligned
             |
        hip  O
             |
             |
      ankle  O
```

## 🎓 Training Pipeline

```
COCO Dataset
    │
    ▼
Load Images & Annotations
    │
    ▼
Data Augmentation
• Flip
• Brightness
• Scale
    │
    ▼
Batch Creation (4 images)
    │
    ▼
R-CNN Forward Pass
    │
    ▼
Calculate Loss
• RPN loss
• Box loss
• Keypoint loss
    │
    ▼
Backward Pass (Gradients)
    │
    ▼
Update Weights (Optimizer)
    │
    ▼
Save Checkpoint (every 500 iterations)
    │
    └──► Repeat for MAX_ITER
```

## 📊 Data Flow

```
Camera → Frame → R-CNN → Keypoints → Alignment → Measurements → Display
  │                                      │
  │                                      ▼
  │                                  Feedback
  │                                      │
  │                                      ▼
  └──────────────────────────────► UI Overlay
```

## 🔧 Calibration Methods

### Method 1: Reference Height
```
User provides height (e.g., 175 cm)
    │
    ▼
Measure pixel height (nose to ankle)
    │
    ▼
scale_factor = reference_height_cm / pixel_height
    │
    ▼
Use for all measurements
```

### Method 2: Pinhole Camera Model
```
Camera parameters:
• Focal length (mm)
• Sensor width (mm)
• Reference distance (cm)
    │
    ▼
pixel_size = sensor_width / image_width
    │
    ▼
real_size_per_pixel = (pixel_size × distance) / focal_length
    │
    ▼
scale_factor = real_size_per_pixel / 10
    │
    ▼
Use for all measurements
```

## 🎮 User Interaction Flow

```
1. Launch Application
   python main.py --height 175
        │
        ▼
2. Position Yourself
   • Stand 2m from camera
   • Face camera
   • Full body visible
        │
        ▼
3. Follow Guidance
   • RED skeleton = adjust
   • GREEN skeleton = hold
        │
        ▼
4. Hold Pose
   • Progress bar fills
   • 30 frames countdown
        │
        ▼
5. Auto-Capture
   • Flash feedback
   • Image saved
        │
        ▼
6. Repeat 3x
   • Total 3 captures
        │
        ▼
7. View Results
   • Average measurements
   • Captured images
        │
        ▼
8. Done!
```

## 🔒 Privacy Flow

```
Frame Captured
    │
    ▼
Processed in Memory
    │
    ▼
Displayed (Temporary)
    │
    ▼
[If capture triggered]
    │
    ▼
Temporary Storage
    │
    ▼
User Review
    │
    ▼
Auto-Delete (if enabled)
    │
    ▼
No Persistent Data
```

## 📈 Performance Optimization

```
Input Frame
    │
    ▼
Resize (if needed)
    │
    ▼
GPU Transfer
    │
    ▼
R-CNN Inference (GPU)
    │
    ▼
Extract Results
    │
    ▼
CPU Processing
• Alignment checks
• Measurements
• UI rendering
    │
    ▼
Display
```

---

**These diagrams provide a visual understanding of the system architecture and flow!**
