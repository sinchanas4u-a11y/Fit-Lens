"""
Measurement Engine
Calculates body measurements from landmarks with confidence scores
Uses ellipse geometry for chest and waist circumference calculations
Includes hybrid shoulder detection using MediaPipe + YOLOv8 + OpenCV
"""
import numpy as np
from typing import Dict, Tuple, Optional
import math
try:
    from hybrid_shoulder_detector import HybridShoulderDetector
    HYBRID_SHOULDER_AVAILABLE = True
except ImportError:
    HYBRID_SHOULDER_AVAILABLE = False


class MeasurementEngine:
    """Calculate body measurements from landmarks"""
    
    def __init__(self):
        """Initialize measurement engine"""
        # Proportional coefficients for ellipse estimation
        self.alpha_s = 0.5  # Shoulder width to torso width ratio
        self.alpha_a = 0.15  # Arm length contribution to depth
        self.alpha_t = 0.25  # Torso length contribution to depth
        
        # Body type adjustment factors
        self.chest_depth_ratio = 0.55  # Chest depth to width ratio (typical: 0.5-0.6)
        self.waist_depth_ratio = 0.45  # Waist depth to width ratio (typical: 0.4-0.5)
        self.hip_depth_ratio = 0.50   # Hip depth to width ratio (typical: 0.45-0.55)
        
        # Initialize hybrid shoulder detector if available
        self.hybrid_shoulder_detector = None
        if HYBRID_SHOULDER_AVAILABLE:
            try:
                self.hybrid_shoulder_detector = HybridShoulderDetector()
                print("✓ Hybrid shoulder detector initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize hybrid shoulder detector: {e}")
        
        # Measurement definitions - only requested measurements
        self.measurements = {
            'front': {
                'shoulder_width': ('left_shoulder', 'right_shoulder'),
                'arm_length': ('left_shoulder', 'left_wrist'),
                'chest_circumference': ('left_shoulder', 'right_shoulder'),
                'waist_circumference': ('left_hip', 'right_hip'),
                'torso_length': ('left_shoulder', 'left_hip'),
                'leg_length': ('left_hip', 'left_ankle'),
                'full_height': ('nose', 'left_ankle'),
            },
            'side': {
                'torso_length': ('left_shoulder', 'left_hip'),
                'leg_length': ('left_hip', 'left_ankle'),
                'full_height': ('nose', 'left_ankle'),
            }
        }
    
    def calculate_measurements(
        self, 
        landmarks: np.ndarray, 
        scale_factor: float,
        view: str = 'front'
    ) -> Dict[str, float]:
        """
        Calculate measurements from landmarks
        
        Args:
            landmarks: Detected landmarks (N, 3) with (x, y, confidence)
            scale_factor: Pixels to cm conversion factor
            view: 'front' or 'side'
            
        Returns:
            Dictionary of measurements in cm
        """
        if landmarks is None:
            return {}
        
        measurements = {}
        
        # Get landmark dictionary
        landmark_dict = self._landmarks_to_dict(landmarks)
        
        # Calculate each measurement
        for name, points in self.measurements.get(view, {}).items():
            if len(points) == 2:
                # Direct distance measurement
                p1_name, p2_name = points
                if p1_name in landmark_dict and p2_name in landmark_dict:
                    p1 = landmark_dict[p1_name]
                    p2 = landmark_dict[p2_name]
                    
                    # Calculate pixel distance
                    pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                    
                    # Convert to cm
                    cm_dist = pixel_dist * scale_factor
                    
                    measurements[name] = cm_dist
        
        return measurements
    
    def calculate_measurements_with_confidence(
        self,
        landmarks: np.ndarray,
        scale_factor: float,
        view: str = 'front'
    ) -> Dict[str, Tuple[float, float, str]]:
        """
        Calculate measurements with confidence scores
        
        Returns:
            Dictionary with (value_cm, confidence, source)
        """
        if landmarks is None:
            return {}
        
        measurements = {}
        landmark_dict = self._landmarks_to_dict(landmarks)
        
        measurement_defs = self.measurements.get(view, {})
        
        for name, points in measurement_defs.items():
            if len(points) == 2:
                p1_name, p2_name = points
                
                if p1_name in landmark_dict and p2_name in landmark_dict:
                    p1 = landmark_dict[p1_name]
                    p2 = landmark_dict[p2_name]
                    
                    # Pixel distance between landmarks
                    pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                    # Pure pixel-to-scale conversion
                    cm_dist = pixel_dist * scale_factor
                    
                    # Calculate confidence (average of point confidences)
                    confidence = (p1[2] + p2[2]) / 2
                    
                    # Determine source
                    source = 'pixel_to_scale'
                    
                    measurements[name] = (cm_dist, confidence, source)

        return measurements
    
    def _landmarks_to_dict(self, landmarks: np.ndarray) -> Dict[str, np.ndarray]:
        """Convert landmark array to dictionary"""
        # MediaPipe landmark names
        landmark_names = [
            'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
            'right_eye_inner', 'right_eye', 'right_eye_outer',
            'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
            'left_shoulder', 'right_shoulder',
            'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist',
            'left_pinky', 'right_pinky',
            'left_index', 'right_index',
            'left_thumb', 'right_thumb',
            'left_hip', 'right_hip',
            'left_knee', 'right_knee',
            'left_ankle', 'right_ankle',
            'left_heel', 'right_heel',
            'left_foot_index', 'right_foot_index'
        ]
        
        landmark_dict = {}
        for i, name in enumerate(landmark_names):
            if i < len(landmarks):
                landmark_dict[name] = landmarks[i]
        
        return landmark_dict
    
    def calculate_shoulder_width_hybrid(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        landmarks: np.ndarray,
        scale_factor: float,
        debug: bool = False
    ) -> Dict[str, any]:
        """
        Calculate shoulder width using hybrid approach
        
        Uses:
        - MediaPipe for shoulder Y-level
        - YOLOv8 mask for body silhouette
        - OpenCV Canny edge detection
        - OpenCV contour extraction
        - NumPy for point filtering
        
        Args:
            image: Original image (BGR)
            mask: YOLOv8 segmentation mask
            landmarks: MediaPipe landmarks
            scale_factor: Pixel to cm conversion
            debug: Whether to include debug info
            
        Returns:
            Dictionary with shoulder_width_cm, confidence, and debug info
        """
        result = {
            'shoulder_width_cm': None,
            'shoulder_width_px': None,
            'confidence': 0.0,
            'source': 'hybrid',
            'left_shoulder': None,
            'right_shoulder': None,
            'shoulder_y': None,
            'debug_image': None,
        }
        
        if not HYBRID_SHOULDER_AVAILABLE:
            print("⚠️ Hybrid shoulder detector not available")
            return result
        
        if self.hybrid_shoulder_detector is None:
            print("⚠️ Hybrid shoulder detector not initialized")
            return result
        
        try:
            # Use the hybrid detector with optional scikit-image refinement
            hybrid_result = self.hybrid_shoulder_detector.detect_shoulder_width_with_refinement(
                image, mask, landmarks, scale_factor, use_scikit_image=True, debug=debug
            )
            
            # Copy relevant fields
            result.update({
                'shoulder_width_cm': hybrid_result.get('shoulder_width_cm'),
                'shoulder_width_px': hybrid_result.get('shoulder_width_px'),
                'confidence': hybrid_result.get('confidence', 0.0),
                'left_shoulder': hybrid_result.get('left_shoulder'),
                'right_shoulder': hybrid_result.get('right_shoulder'),
                'shoulder_y': hybrid_result.get('shoulder_y'),
                'debug_image': hybrid_result.get('debug_image') if debug else None,
            })
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error in hybrid shoulder detection: {e}")
            return result
    
    def calculate_body_proportions(self, measurements: Dict[str, float]) -> Dict[str, float]:
        """Calculate body proportions and ratios"""
        proportions = {}
        
        if 'shoulder_width' in measurements and 'hip_width' in measurements:
            proportions['shoulder_to_hip_ratio'] = (
                measurements['shoulder_width'] / measurements['hip_width']
            )
        
        return proportions
    
    def validate_measurements(self, measurements: Dict[str, float]) -> Dict[str, bool]:
        """Validate measurements are within reasonable ranges"""
        validation = {}
        
        # Define reasonable ranges (cm)
        ranges = {
            'shoulder_width': (30, 60),
            'hip_width': (25, 50),
            'arm_span': (120, 220),
            'torso_depth': (15, 35),
        }
        
        for name, value in measurements.items():
            if name in ranges:
                min_val, max_val = ranges[name]
                validation[name] = min_val <= value <= max_val
            else:
                validation[name] = True
        
        return validation
