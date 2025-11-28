# System Architecture Documentation

Complete technical documentation for the R-CNN Body Measurement System.

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  (Camera Feed, Visual Feedback, Measurements Display)        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Application Layer (main.py)                 │
│  • Frame Processing Loop                                     │
│  • Capture State Management                                  │
│  • UI Rendering                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼──────┐ ┌──▼────────────┐
│ Model Layer  │ │ Pose    │ │ Measurement   │
│ (R-CNN)      │ │ Utils   │ │ Calculator    │
│              │ │         │ │               │
│ • Detection  │ │ • Align │ │ • Calibration │
│ • Keypoints  │ │ • Check │ │ • Conversion  │
└──────────────┘ └─────────┘ └───────────────┘
```

## 📦 Module Architecture

### 1. Configuration Layer (`config.py`)

**Purpose:** Centralized configuration management

**Key Components:**
- Model parameters
- Camera settings
- Alignment thresholds
- Privacy settings
- Dataset paths

**Design Pattern:** Singleton configuration class

```python
class Config:
    # All configuration parameters
    # Class methods for directory creation
```

### 2. Model Layer (`model_arch.py`)

**Purpose:** Deep learning model management and inference

**Components:**

#### KeypointRCNN
```python
class KeypointRCNN:
    - __init__(): Initialize Detectron2 model
    - predict(): Run inference on frame
    - extract_keypoints(): Parse model outputs
    - get_bounding_box(): Extract person bbox
```

**Architecture:**
- Backbone: ResNet-50 + FPN
- Detection: Faster R-CNN
- Keypoints: Heatmap-based prediction

#### ModelTrainer
```python
class ModelTrainer:
    - setup_training_config(): Configure training
    - train(): Execute training loop
    - evaluate_model(): Run evaluation
```

**Training Pipeline:**
1. Load COCO dataset
2. Initialize model with pretrained weights
3. Fine-tune on person keypoints
4. Save checkpoints periodically
5. Evaluate on validation set

#### DepthEstimator
```python
class DepthEstimator:
    - calibrate(): Set baseline measurements
    - estimate_distance(): Calculate Z-axis distance
    - get_distance_feedback(): Generate guidance
```

**Algorithm:**
```
distance = (reference_width × baseline_pixel_width) / current_pixel_width
```

#### CenteringChecker
```python
class CenteringChecker:
    - check_centering(): Validate frame position
```

**Algorithm:**
- Calculate center of mass of keypoints
- Compare to frame center
- Generate directional feedback

### 3. Pose Utilities Layer (`pose_utils.py`)

**Purpose:** Geometric calculations and pose analysis

**Components:**

#### PoseUtils
```python
class PoseUtils:
    - calculate_angle(): 3-point angle calculation
    - calculate_distance(): Euclidean distance
    - get_keypoint_dict(): Convert array to dict
    - check_arms_away_from_body(): Arm position validation
    - check_elbow_angles(): Elbow straightness
    - check_facing_camera(): Frontal orientation
    - check_standing_straight(): Vertical alignment
```

**Geometric Algorithms:**

**Angle Calculation:**
```python
v1 = p1 - p2
v2 = p3 - p2
angle = arccos(dot(v1, v2) / (||v1|| × ||v2||))
```

**Distance Calculation:**
```python
distance = sqrt((x2-x1)² + (y2-y1)²)
```

#### AlignmentChecker
```python
class AlignmentChecker:
    - check_alignment(): Comprehensive pose validation
    - _generate_feedback(): User guidance messages
```

**Alignment Score:**
```python
score = mean([
    arms_away_score,
    elbow_angle_score,
    facing_camera_score,
    standing_straight_score
])
is_aligned = score >= ALIGNMENT_THRESHOLD
```

#### MeasurementCalculator
```python
class MeasurementCalculator:
    - calibrate_scale(): Pixel-to-cm conversion setup
    - calculate_measurements(): Compute body measurements
    - draw_measurements(): Visualize on frame
```

**Calibration Methods:**

**Method 1: Reference Height**
```python
scale_factor = reference_height_cm / pixel_height
```

**Method 2: Pinhole Camera Model**
```python
pixel_size_mm = sensor_width_mm / image_width
real_size_per_pixel = (pixel_size × distance) / focal_length
scale_factor = real_size_per_pixel / 10  # Convert to cm
```

#### SkeletonDrawer
```python
class SkeletonDrawer:
    - draw_skeleton(): Render keypoints and connections
```

**Visualization:**
- Draw lines between connected keypoints
- Render circles at keypoint locations
- Highlight endpoints (shoulders, elbows, wrists, hips)
- Color-code based on alignment status

### 4. Dataset Layer (`dataset.py`)

**Purpose:** Data loading and preprocessing for training

**Components:**

#### COCOKeypointDataset
```python
class COCOKeypointDataset:
    - __init__(): Load COCO annotations
    - get_detectron2_dicts(): Convert to Detectron2 format
```

**Data Format Conversion:**
```
COCO Format → Detectron2 Format
{
    'file_name': path,
    'image_id': id,
    'height': h,
    'width': w,
    'annotations': [
        {
            'bbox': [x, y, w, h],
            'keypoints': [x1, y1, v1, ...],
            'category_id': 0
        }
    ]
}
```

#### DataAugmentation
```python
class DataAugmentation:
    - get_training_augmentation(): Training pipeline
    - get_validation_augmentation(): Validation pipeline
```

**Augmentation Pipeline:**
1. Horizontal flip (50%)
2. Brightness/contrast adjustment
3. Hue/saturation variation
4. Gaussian noise
5. Blur
6. Random scaling

#### SyntheticDataGenerator
```python
class SyntheticDataGenerator:
    - generate_synthetic_pose(): Create test data
```

**Use Cases:**
- Testing without camera
- Demo mode
- Unit testing
- Debugging

### 5. Training Layer (`train.py`)

**Purpose:** Model training and evaluation

**Components:**

#### CustomTrainer
```python
class CustomTrainer(DefaultTrainer):
    - build_evaluator(): Setup COCO evaluator
    - build_train_loader(): Data loader with augmentation
```

**Training Loop:**
```
for iteration in range(MAX_ITER):
    1. Load batch
    2. Forward pass
    3. Calculate loss
    4. Backward pass
    5. Update weights
    6. Log metrics
    7. Save checkpoint (periodic)
```

**Functions:**
- `train_model()`: Main training entry point
- `evaluate_model()`: Run evaluation
- `visualize_training_data()`: Data inspection

### 6. Application Layer (`main.py`)

**Purpose:** Main application orchestration

**Components:**

#### BodyMeasurementApp
```python
class BodyMeasurementApp:
    - __init__(): Initialize all components
    - process_frame(): Main processing pipeline
    - draw_ui(): Render user interface
    - update_capture_state(): Manage captures
    - save_captured_image(): Store results
    - run(): Main application loop
    - show_results(): Display final measurements
```

**Application Flow:**

```
┌─────────────────┐
│  Initialize     │
│  • Model        │
│  • Camera       │
│  • Utilities    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Main Loop      │
│  while True:    │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Capture │
    │ Frame   │
    └────┬────┘
         │
    ┌────▼────────┐
    │ Detect Pose │
    │ (R-CNN)     │
    └────┬────────┘
         │
    ┌────▼──────────┐
    │ Check         │
    │ Alignment     │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │ Calculate     │
    │ Measurements  │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │ Update UI     │
    │ & Display     │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │ Check Capture │
    │ Trigger       │
    └────┬──────────┘
         │
         ▼
    [Repeat or Exit]
```

## 🔄 Data Flow

### Frame Processing Pipeline

```
Camera Frame (BGR)
    │
    ▼
┌───────────────────┐
│ Flip Horizontal   │ (Mirror effect)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ R-CNN Inference   │
│ • Person detect   │
│ • Keypoint detect │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Keypoint Extract  │
│ (17, 3) array     │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│Alignment│ │Centering │
│Check    │ │Check     │
└────┬───┘ └────┬─────┘
     │          │
     └────┬─────┘
          │
          ▼
    ┌──────────┐
    │ Depth    │
    │ Check    │
    └────┬─────┘
         │
         ▼
    ┌──────────────┐
    │ Measurements │
    │ (if aligned) │
    └────┬─────────┘
         │
         ▼
    ┌──────────────┐
    │ Draw Skeleton│
    │ & UI         │
    └────┬─────────┘
         │
         ▼
    Display Frame
```

### Measurement Calculation Flow

```
Keypoints (17, 3)
    │
    ▼
┌─────────────────┐
│ Calibrate Scale │
│ (first frame)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ For each        │
│ body segment:   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get keypoint    │
│ coordinates     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Calculate       │
│ pixel distance  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Convert to cm   │
│ using scale     │
└────────┬────────┘
         │
         ▼
Measurements Dict
```

## 🎯 Design Patterns

### 1. Singleton Pattern
**Used in:** `Config` class
**Purpose:** Single source of configuration

### 2. Strategy Pattern
**Used in:** Calibration methods
**Purpose:** Multiple calibration strategies

### 3. Observer Pattern
**Used in:** Capture state management
**Purpose:** React to alignment changes

### 4. Factory Pattern
**Used in:** Dataset creation
**Purpose:** Create different dataset types

### 5. Template Method Pattern
**Used in:** Training pipeline
**Purpose:** Standardized training flow

## 🔐 Privacy Architecture

### Privacy-First Design Principles

1. **No Persistent Storage**
   - Frames processed in memory
   - No video recording
   - Temporary files auto-deleted

2. **Minimal Data Retention**
   - Only user-selected images saved
   - Keypoint data not logged
   - Measurements not stored

3. **User Control**
   - `SAVE_IMAGES = False` by default
   - Clear privacy settings
   - Explicit user consent

4. **Secure Processing**
   - Local processing only
   - No network transmission
   - No cloud storage

### Data Lifecycle

```
Frame Capture
    │
    ▼
In-Memory Processing
    │
    ▼
Display (Temporary)
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
```

## 🚀 Performance Optimization

### 1. Model Optimization
- Use FP16 inference (if supported)
- Batch processing (training)
- Model pruning (optional)

### 2. Frame Processing
- Skip frames if needed
- Reduce resolution for speed
- Async processing (future)

### 3. Memory Management
- Release frames after processing
- Clear capture buffer
- Garbage collection

### 4. GPU Utilization
- CUDA acceleration
- Tensor operations on GPU
- Minimize CPU-GPU transfers

## 🧪 Testing Strategy

### Unit Tests
- Geometric calculations
- Alignment checking
- Measurement conversion
- Data loading

### Integration Tests
- Model inference
- End-to-end pipeline
- Camera integration
- UI rendering

### Performance Tests
- FPS benchmarking
- Memory profiling
- Latency measurement

## 📊 Metrics & Monitoring

### Model Metrics
- Detection AP (Average Precision)
- Keypoint AP
- Inference time
- Memory usage

### Application Metrics
- FPS (frames per second)
- Alignment success rate
- Capture success rate
- Measurement accuracy

### User Experience Metrics
- Time to first capture
- Number of alignment attempts
- User feedback quality

## 🔮 Extensibility

### Adding New Measurements
1. Define keypoint pairs in `Config.BODY_SEGMENTS`
2. Measurement automatically calculated
3. Display in UI

### Adding New Alignment Checks
1. Implement check function in `PoseUtils`
2. Add to `AlignmentChecker.check_alignment()`
3. Update feedback generation

### Custom Model Training
1. Prepare custom dataset
2. Register with Detectron2
3. Run training script
4. Use custom weights in main app

### Multi-Person Support
1. Modify `extract_keypoints()` to return list
2. Update alignment checking for multiple people
3. Add person selection UI

---

**This architecture provides a solid foundation for accurate, privacy-focused body measurement applications.**
