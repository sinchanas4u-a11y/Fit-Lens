# Pose-Aligned Automatic Image Capture

A Python application that uses computer vision to automatically capture photos when you align with a reference pose outline.

## Features

- **Live Camera Preview** with transparent human outline overlay
- **Real-time Pose Detection** using MediaPipe
- **Smart Alignment Detection** - outline turns GREEN when aligned, RED when not
- **3-Second Stability Timer** - must hold pose before capture
- **Automatic Capture** of 5 images
- **Interactive Gallery** - select your favorite image
- **Privacy-Focused** - only saves the image you select

## Requirements

- Python 3.10+
- Webcam
- Windows/Linux/macOS

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python pose_capture.py
```

### How It Works

1. **Position yourself** in front of the camera
2. **Align your body** with the outline (standing pose, arms slightly away from body)
3. **Watch the outline color**:
   - 🔴 RED = Not aligned
   - 🟢 GREEN = Aligned correctly
4. **Hold the pose** for 3 seconds when aligned
5. **Auto-capture** happens automatically
6. **Repeat** until 5 images are captured
7. **Select** your favorite from the gallery
8. **Done!** Only your selected image is saved

### Controls

- **Mouse Click** - Select image in gallery
- **Q Key** - Quit at any time

## Technical Details

### Pose Detection
- Uses **MediaPipe Pose** for fast, accurate keypoint detection
- Tracks 13 key body landmarks
- Requires 80% of keypoints to be aligned within tolerance

### Alignment Algorithm
- Position tolerance: 8% of frame size (normalized)
- Checks visibility and position of each keypoint
- Compares detected pose with reference template

### Modular Design
The code is structured to easily swap pose detection models:
- `PoseAlignmentCapture` class encapsulates all logic
- `process_frame()` method handles pose detection
- Replace MediaPipe with PyTorch/OpenPose by modifying this method

## Configuration

Edit these parameters in `pose_capture.py`:

```python
app = PoseAlignmentCapture(
    target_images=5,        # Number of images to capture
    stability_duration=2.0  # Seconds to hold pose
)

# Alignment tolerances
self.position_tolerance = 0.08  # Position tolerance (0-1)
self.angle_tolerance = 15       # Angle tolerance (degrees)
```

## Output

- Selected image saved as `selected_pose.jpg` in the current directory
- All other captured images are discarded (not saved)

## Troubleshooting

**Camera not opening:**
- Check if another application is using the camera
- Try changing camera index: `cv2.VideoCapture(1)` instead of `0`

**Pose not detected:**
- Ensure good lighting
- Stand 1-2 meters from camera
- Make sure full body is visible

**Alignment too sensitive:**
- Increase `position_tolerance` value
- Lower alignment ratio threshold in `check_alignment()`

## License

MIT License - Feel free to modify and use as needed.
