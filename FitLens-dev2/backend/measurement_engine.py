"""
Measurement Engine
Calculates body measurements from landmarks with confidence scores
"""
import numpy as np
from typing import Dict, Tuple, Optional


class MeasurementEngine:
    """Calculate body measurements from landmarks"""
    
    def __init__(self):
        """Initialize measurement engine"""
        # Measurement definitions
        self.measurements = {
            'front': {
                'shoulder_width': ('left_shoulder', 'right_shoulder'),
                'hip_width': ('left_hip', 'right_hip'),
                'chest_width': ('left_shoulder', 'right_shoulder'),
                'waist_width': ('left_hip', 'right_hip'),
                'arm_span': ('left_wrist', 'right_wrist'),
            },
            'side': {
                'torso_depth': ('chest', 'back'),
                'shoulder_to_hip': ('shoulder', 'hip'),
                'hip_to_ankle': ('hip', 'ankle'),
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
        
        for name, points in self.measurements.get(view, {}).items():
            if len(points) == 2:
                p1_name, p2_name = points
                if p1_name in landmark_dict and p2_name in landmark_dict:
                    p1 = landmark_dict[p1_name]
                    p2 = landmark_dict[p2_name]
                    
                    # Calculate distance
                    pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                    cm_dist = pixel_dist * scale_factor
                    
                    # Calculate confidence (average of point confidences)
                    confidence = (p1[2] + p2[2]) / 2
                    
                    # Determine source
                    source = 'MediaPipe' if confidence > 0.5 else 'Estimated'
                    
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
