"""
R-CNN Model Architecture and Inference using Detectron2
"""
import torch
import numpy as np
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2 import model_zoo
from typing import Optional, Dict, Tuple
from config import Config


class KeypointRCNN:
    """Wrapper for Detectron2 Keypoint R-CNN model"""
    
    def __init__(self, config_file: Optional[str] = None, 
                 weights_file: Optional[str] = None,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initialize Keypoint R-CNN model
        
        Args:
            config_file: Path to model config (uses default if None)
            weights_file: Path to model weights (uses pretrained if None)
            device: Device to run model on
        """
        self.device = device
        self.cfg = self._setup_config(config_file, weights_file)
        self.predictor = DefaultPredictor(self.cfg)
        
        print(f"Keypoint R-CNN initialized on device: {self.device}")
        print(f"Model: {config_file or Config.MODEL_CONFIG}")
    
    def _setup_config(self, config_file: Optional[str], 
                     weights_file: Optional[str]) -> object:
        """
        Setup Detectron2 configuration
        
        Args:
            config_file: Model config file
            weights_file: Model weights file
            
        Returns:
            Detectron2 config object
        """
        cfg = get_cfg()
        
        # Load model config
        config_path = config_file or Config.MODEL_CONFIG
        cfg.merge_from_file(model_zoo.get_config_file(config_path))
        
        # Set model weights
        if weights_file:
            cfg.MODEL.WEIGHTS = weights_file
        else:
            cfg.MODEL.WEIGHTS = Config.MODEL_WEIGHTS
        
        # Set inference parameters
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = Config.DETECTION_THRESHOLD
        cfg.MODEL.DEVICE = self.device
        
        return cfg
    
    def predict(self, frame: np.ndarray) -> Dict:
        """
        Run inference on a single frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Dictionary containing predictions
        """
        outputs = self.predictor(frame)
        return outputs
    
    def extract_keypoints(self, outputs: Dict) -> Optional[np.ndarray]:
        """
        Extract keypoints from model outputs
        
        Args:
            outputs: Model prediction outputs
            
        Returns:
            Keypoints array of shape (17, 3) or None if no person detected
        """
        if "instances" not in outputs:
            return None
        
        instances = outputs["instances"]
        
        # Filter for person class (class_id = 0 in COCO)
        if len(instances) == 0:
            return None
        
        # Get highest confidence detection
        scores = instances.scores.cpu().numpy()
        best_idx = np.argmax(scores)
        
        # Extract keypoints (x, y, confidence)
        if hasattr(instances, 'pred_keypoints'):
            keypoints = instances.pred_keypoints[best_idx].cpu().numpy()
            return keypoints
        
        return None
    
    def get_bounding_box(self, outputs: Dict) -> Optional[Tuple[int, int, int, int]]:
        """
        Extract bounding box from outputs
        
        Args:
            outputs: Model prediction outputs
            
        Returns:
            (x1, y1, x2, y2) or None
        """
        if "instances" not in outputs or len(outputs["instances"]) == 0:
            return None
        
        instances = outputs["instances"]
        scores = instances.scores.cpu().numpy()
        best_idx = np.argmax(scores)
        
        bbox = instances.pred_boxes[best_idx].tensor.cpu().numpy()[0]
        return tuple(map(int, bbox))


class ModelTrainer:
    """Training wrapper for Keypoint R-CNN"""
    
    def __init__(self, output_dir: str = Config.CHECKPOINT_DIR):
        """
        Initialize trainer
        
        Args:
            output_dir: Directory to save checkpoints
        """
        self.output_dir = output_dir
        self.cfg = None
    
    def setup_training_config(self, dataset_name: str, num_classes: int = 1) -> object:
        """
        Setup configuration for training
        
        Args:
            dataset_name: Name of registered dataset
            num_classes: Number of classes (1 for person)
            
        Returns:
            Detectron2 config object
        """
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file(Config.MODEL_CONFIG))
        
        # Training dataset
        cfg.DATASETS.TRAIN = (dataset_name,)
        cfg.DATASETS.TEST = ()
        
        # Training parameters
        cfg.DATALOADER.NUM_WORKERS = Config.NUM_WORKERS
        cfg.SOLVER.IMS_PER_BATCH = Config.TRAIN_BATCH_SIZE
        cfg.SOLVER.BASE_LR = Config.LEARNING_RATE
        cfg.SOLVER.MAX_ITER = Config.MAX_ITER
        cfg.SOLVER.CHECKPOINT_PERIOD = Config.CHECKPOINT_PERIOD
        
        # Model parameters
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = num_classes
        cfg.MODEL.WEIGHTS = Config.MODEL_WEIGHTS  # Start from pretrained
        
        # Output directory
        cfg.OUTPUT_DIR = self.output_dir
        
        # Device
        cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.cfg = cfg
        return cfg
    
    def train(self):
        """
        Train the model
        Note: This requires dataset to be registered first
        """
        if self.cfg is None:
            raise ValueError("Config not setup. Call setup_training_config() first.")
        
        from detectron2.engine import DefaultTrainer
        
        trainer = DefaultTrainer(self.cfg)
        trainer.resume_or_load(resume=False)
        trainer.train()
        
        return trainer
    
    @staticmethod
    def evaluate_model(cfg: object, dataset_name: str):
        """
        Evaluate trained model
        
        Args:
            cfg: Detectron2 config
            dataset_name: Name of dataset to evaluate on
        """
        from detectron2.evaluation import COCOEvaluator, inference_on_dataset
        from detectron2.data import build_detection_test_loader
        
        predictor = DefaultPredictor(cfg)
        evaluator = COCOEvaluator(dataset_name, cfg, False, output_dir=cfg.OUTPUT_DIR)
        val_loader = build_detection_test_loader(cfg, dataset_name)
        
        results = inference_on_dataset(predictor.model, val_loader, evaluator)
        return results


class DepthEstimator:
    """Estimate depth (Z-axis) from keypoint data for distance guidance"""
    
    def __init__(self, reference_shoulder_width_cm: float = 40.0):
        """
        Initialize depth estimator
        
        Args:
            reference_shoulder_width_cm: Average shoulder width for reference
        """
        self.reference_shoulder_width_cm = reference_shoulder_width_cm
        self.baseline_pixel_width = None
        self.baseline_distance_cm = Config.REFERENCE_DISTANCE_CM
    
    def calibrate(self, keypoints: np.ndarray):
        """
        Calibrate depth estimation using current frame
        
        Args:
            keypoints: Keypoint array
        """
        # Get shoulder keypoints
        left_shoulder = keypoints[5][:2]
        right_shoulder = keypoints[6][:2]
        
        # Calculate pixel width
        self.baseline_pixel_width = np.linalg.norm(right_shoulder - left_shoulder)
    
    def estimate_distance(self, keypoints: np.ndarray) -> Optional[float]:
        """
        Estimate distance from camera in cm
        
        Args:
            keypoints: Keypoint array
            
        Returns:
            Estimated distance in cm or None
        """
        if self.baseline_pixel_width is None:
            return None
        
        # Get current shoulder width in pixels
        left_shoulder = keypoints[5][:2]
        right_shoulder = keypoints[6][:2]
        current_pixel_width = np.linalg.norm(right_shoulder - left_shoulder)
        
        # Using similar triangles: distance is inversely proportional to pixel size
        # distance = (reference_width * focal_length) / pixel_width
        estimated_distance = (self.reference_shoulder_width_cm * self.baseline_pixel_width) / (current_pixel_width + 1e-6)
        
        return estimated_distance
    
    def get_distance_feedback(self, keypoints: np.ndarray) -> str:
        """
        Get feedback message for distance adjustment
        
        Args:
            keypoints: Keypoint array
            
        Returns:
            Feedback message
        """
        distance = self.estimate_distance(keypoints)
        
        if distance is None:
            return ""
        
        # Compare to baseline
        diff = distance - self.baseline_distance_cm
        
        if abs(diff) < 20:  # Within 20cm tolerance
            return ""
        elif diff > 0:
            return "Move closer to camera"
        else:
            return "Move back from camera"


class CenteringChecker:
    """Check if person is centered in frame"""
    
    @staticmethod
    def check_centering(keypoints: np.ndarray, frame_width: int, 
                       frame_height: int) -> Tuple[bool, str]:
        """
        Check if person is centered in frame
        
        Args:
            keypoints: Keypoint array
            frame_width: Frame width
            frame_height: Frame height
            
        Returns:
            (is_centered, feedback_message)
        """
        # Calculate center of mass of keypoints
        valid_kps = keypoints[keypoints[:, 2] > Config.KEYPOINT_THRESHOLD]
        
        if len(valid_kps) == 0:
            return False, "No person detected"
        
        center_x = np.mean(valid_kps[:, 0])
        center_y = np.mean(valid_kps[:, 1])
        
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        # Calculate offset
        offset_x = center_x - frame_center_x
        offset_y = center_y - frame_center_y
        
        # Normalize by frame size
        norm_offset_x = offset_x / frame_width
        norm_offset_y = offset_y / frame_height
        
        # Check if within tolerance
        is_centered = abs(norm_offset_x) < 0.1 and abs(norm_offset_y) < 0.1
        
        # Generate feedback
        feedback_parts = []
        if norm_offset_x > 0.1:
            feedback_parts.append("Move left")
        elif norm_offset_x < -0.1:
            feedback_parts.append("Move right")
        
        if norm_offset_y > 0.1:
            feedback_parts.append("Move up")
        elif norm_offset_y < -0.1:
            feedback_parts.append("Move down")
        
        feedback = " | ".join(feedback_parts) if feedback_parts else ""
        
        return is_centered, feedback
