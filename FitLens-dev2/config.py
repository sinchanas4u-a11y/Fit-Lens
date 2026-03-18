"""
Configuration file for R-CNN Body Measurement System
"""
import os

class Config:
    """Configuration parameters for the application"""
    
    # ==================== MODEL CONFIGURATION ====================
    # Detectron2 model configuration
    MODEL_CONFIG = "COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml"
    MODEL_WEIGHTS = "detectron2://COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x/137849621/model_final_a6e10b.pkl"
    
    # Training parameters
    TRAIN_BATCH_SIZE = 4
    LEARNING_RATE = 0.00025
    MAX_ITER = 5000
    CHECKPOINT_PERIOD = 500
    NUM_WORKERS = 4
    
    # Model thresholds
    DETECTION_THRESHOLD = 0.7
    KEYPOINT_THRESHOLD = 0.5
    
    # ==================== POSE ALIGNMENT CONFIGURATION ====================
    # Target pose requirements
    TARGET_POSE = {
        'arms_away_from_body': True,  # Arms should be away from torso
        'facing_camera': True,         # User should face camera directly
        'standing_straight': True,     # Upright posture
        'elbow_angle_min': 160,        # Minimum elbow angle (degrees)
        'arm_torso_distance_min': 0.1  # Minimum normalized distance
    }
    
    # Alignment tolerances
    POSITION_TOLERANCE = 0.08  # Normalized coordinate tolerance
    ANGLE_TOLERANCE = 15       # Degrees
    DEPTH_TOLERANCE = 0.15     # Z-axis tolerance
    
    # Stability requirements
    STABILITY_FRAMES = 90      # Frames to hold pose before capture (3 seconds at 30 FPS)
    ALIGNMENT_THRESHOLD = 0.85 # Minimum alignment score (0-1)
    
    # ==================== CAMERA & CALIBRATION ====================
    # Camera settings
    CAMERA_INDEX = 0
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720
    FPS = 30
    
    # Camera calibration (pinhole model)
    # These should be calibrated for your specific camera
    FOCAL_LENGTH_MM = 4.0      # Camera focal length in mm
    SENSOR_WIDTH_MM = 6.17     # Sensor width in mm
    REFERENCE_DISTANCE_CM = 200 # Reference distance for calibration (cm)
    
    # ==================== MEASUREMENT CONFIGURATION ====================
    # Body segments to measure
    BODY_SEGMENTS = {
        'shoulder_width': ('left_shoulder', 'right_shoulder'),
        'arm_length_left': ('left_shoulder', 'left_elbow', 'left_wrist'),
        'arm_length_right': ('right_shoulder', 'right_elbow', 'right_wrist'),
        'torso_length': ('neck', 'left_hip', 'right_hip'),
        'hip_width': ('left_hip', 'right_hip'),
        'leg_length_left': ('left_hip', 'left_knee', 'left_ankle'),
        'leg_length_right': ('right_hip', 'right_knee', 'right_ankle'),
        'chest_width': ('left_shoulder', 'right_shoulder'),  # At shoulder level
    }
    
    # Keypoint indices (COCO format)
    KEYPOINT_NAMES = [
        'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
        'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
    ]
    
    # ==================== OUTPUT CONFIGURATION ====================
    # Auto-capture settings
    AUTO_CAPTURE_COUNT = 3     # Number of images to auto-capture
    SAVE_IMAGES = False        # Privacy: disabled by default
    TEMP_DIR = "temp_captures" # Temporary directory for captures
    
    # Visualization settings
    SKELETON_COLOR_ALIGNED = (0, 255, 0)    # Green when aligned
    SKELETON_COLOR_MISALIGNED = (0, 0, 255) # Red when misaligned
    KEYPOINT_RADIUS = 5
    LINE_THICKNESS = 2
    
    # Keypoint markers for saved images
    ENDPOINT_COLOR = (0, 255, 255)  # Yellow for endpoints
    ENDPOINT_RADIUS = 8
    
    # ==================== DATASET CONFIGURATION ====================
    # Training dataset paths
    DATASET_ROOT = "datasets/coco"
    TRAIN_JSON = os.path.join(DATASET_ROOT, "annotations/person_keypoints_train2017.json")
    VAL_JSON = os.path.join(DATASET_ROOT, "annotations/person_keypoints_val2017.json")
    TRAIN_IMAGES = os.path.join(DATASET_ROOT, "train2017")
    VAL_IMAGES = os.path.join(DATASET_ROOT, "val2017")
    
    # Output directories
    OUTPUT_DIR = "output"
    CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, "checkpoints")
    RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")
    
    # ==================== PRIVACY SETTINGS ====================
    # IMPORTANT: Privacy-first configuration
    STORE_RAW_FRAMES = False   # Do not store raw video frames
    STORE_KEYPOINTS = False    # Do not store keypoint data
    AUTO_DELETE_TEMP = True    # Auto-delete temporary files
    SAVE_ONLY_SELECTED = True  # Only save user-selected images
    
    @classmethod
    def create_directories(cls):
        """Create necessary output directories"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.CHECKPOINT_DIR, exist_ok=True)
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
        if not cls.AUTO_DELETE_TEMP:
            os.makedirs(cls.TEMP_DIR, exist_ok=True)
