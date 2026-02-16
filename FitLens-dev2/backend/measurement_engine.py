"""
Measurement Engine - Hybrid Vision Approach
- Uses YOLOv8 segmentation edge points for width measurements
- Uses MediaPipe Pose for skeletal joint measurements
- Keeps all existing pixel-to-scale conversion logic unchanged
"""
import numpy as np
from typing import Dict, Tuple, Optional


class MeasurementEngine:
    """Calculate body measurements from landmarks and segmentation edge points"""
    
    def __init__(self):
        """Initialize measurement engine"""
        # Measurement definitions - tracks which use edges vs joints
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
        
        # Measurements that use segmentation edges instead of MediaPipe
        self.edge_based_measurements = {
            'shoulder_width',
            'chest_width',
            'waist_width',
            'hip_width'
        }
        
        # Measurements that use MediaPipe joints
        self.joint_based_measurements = {
            'arm_span',
            'shoulder_to_hip',
            'hip_to_ankle',
            'torso_depth'
        }
    
    def calculate_scale_factor_from_height(self, height_px: float, user_height_cm: float) -> float:
        """
        Calculate pixel-to-cm scale factor from detected height and user-provided height.
        Formula: scale_factor = user_height_cm / height_px
        
        Args:
            height_px: Detected head-to-toe height in pixels
            user_height_cm: User's actual height in centimeters
            
        Returns:
            Scale factor (cm per pixel)
        """
        if height_px <= 0:
            return 1.0  # Fallback
        
        return user_height_cm / height_px
    
    def calculate_measurements(
        self, 
        landmarks: np.ndarray, 
        scale_factor: float,
        view: str = 'front',
        refined_shoulders: Optional[Dict] = None,
        edge_reference_points: Optional[Dict] = None,
        user_height_cm: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate measurements from landmarks and/or edge reference points.
        
        Pipeline approach:
        - Uses edge_reference_points for width measurements (shoulder, chest, waist, hip)
        - Uses MediaPipe landmarks (all 33 points) for skeletal measurements
        - Uses height-based scaling: scale_factor = user_height_cm / height_px
        
        Args:
            landmarks: MediaPipe detected landmarks (33, 3) with (x, y, confidence)
            scale_factor: Pixels to cm conversion factor
            view: 'front' or 'side'
            refined_shoulders: Optional refined shoulder landmarks
            edge_reference_points: Edge points from Canny + findContours on mask
            user_height_cm: User's actual height for automatic scale calibration
            
        Returns:
            Dictionary of measurements in cm
        """
        if landmarks is None and edge_reference_points is None:
            return {}
        
        measurements = {}
        
        # Auto-calculate scale factor if user height provided
        if user_height_cm and edge_reference_points and 'height_px' in edge_reference_points:
            scale_factor = self.calculate_scale_factor_from_height(
                edge_reference_points['height_px'], user_height_cm
            )
        
        # Get landmark dictionary for joint-based measurements
        landmark_dict = self._landmarks_to_dict(landmarks) if landmarks is not None else {}
        
        # Calculate each measurement using appropriate source
        for name, points in self.measurements.get(view, {}).items():
            # Use segmentation edges if available for edge-based measurements
            if name in self.edge_based_measurements and edge_reference_points and edge_reference_points.get('is_valid'):
                pixel_dist = self._calculate_edge_distance(name, edge_reference_points)
            else:
                # Fall back to MediaPipe measurements
                if len(points) == 2:
                    p1_name, p2_name = points
                    if p1_name in landmark_dict and p2_name in landmark_dict:
                        p1 = landmark_dict[p1_name]
                        p2 = landmark_dict[p2_name]
                        pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                    else:
                        continue
                else:
                    continue
            
            # Convert to cm using scale factor: measurement_cm = pixel_dist * (user_height_cm / height_px)
            cm_dist = pixel_dist * scale_factor
            measurements[name] = cm_dist
        
        return measurements
    
    def calculate_measurements_with_confidence(
        self,
        landmarks: np.ndarray,
        scale_factor: float,
        view: str = 'front',
        refined_shoulders: Optional[Dict] = None,
        edge_reference_points: Optional[Dict] = None,
        user_height_cm: Optional[float] = None
    ) -> Dict[str, Tuple[float, float, str]]:
        """
        Calculate measurements with confidence scores using hybrid approach.
        
        Pipeline:
        1. YOLOv8-seg mask → Canny edge detection → findContours → edge keypoints
        2. Masked image → MediaPipe Pose → 33 landmarks (shoulders=11/12, hips=23/24)
        3. Measurements = OpenCV distances * (user_height_cm / height_px)
        
        Args:
            landmarks: MediaPipe detected landmarks (33 points)
            scale_factor: Pixels to cm conversion factor
            view: 'front' or 'side'
            refined_shoulders: Optional refined shoulders
            edge_reference_points: Edge points from Canny + findContours
            user_height_cm: User's actual height for auto-scaling
        
        Returns:
            Dictionary with (value_cm, confidence, source)
        """
        if landmarks is None and edge_reference_points is None:
            return {}
        
        measurements = {}
        
        # Auto-calculate scale factor if user height provided
        if user_height_cm and edge_reference_points and 'height_px' in edge_reference_points:
            scale_factor = self.calculate_scale_factor_from_height(
                edge_reference_points['height_px'], user_height_cm
            )
        
        landmark_dict = self._landmarks_to_dict(landmarks) if landmarks is not None else {}
        
        for name, points in self.measurements.get(view, {}).items():
            measurement_value = None
            confidence = 0.9
            source = "Unknown"
            
            # Use segmentation edges for width measurements (Canny + findContours)
            if name in self.edge_based_measurements and edge_reference_points and edge_reference_points.get('is_valid'):
                pixel_dist = self._calculate_edge_distance(name, edge_reference_points)
                if pixel_dist > 0:
                    measurement_value = pixel_dist * scale_factor
                    confidence = 0.95  # High confidence for contour-based
                    source = "Canny+findContours Edge"
            
            # Fall back to MediaPipe for skeletal measurements (all 33 landmarks)
            if measurement_value is None and len(points) == 2:
                p1_name, p2_name = points
                if p1_name in landmark_dict and p2_name in landmark_dict:
                    p1 = landmark_dict[p1_name]
                    p2 = landmark_dict[p2_name]
                    # OpenCV distance calculation
                    pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                    # Apply height-based scaling
                    measurement_value = pixel_dist * scale_factor
                    confidence = (p1[2] + p2[2]) / 2
                    source = "MediaPipe Landmarks (33 points)"
            
            if measurement_value is not None:
                measurements[name] = (measurement_value, confidence, source)
        
        return measurements
    
    def _calculate_edge_distance(self, measurement_name: str, edge_reference_points: Dict) -> float:
        """
        Calculate distance between edge points for a specific measurement.
        
        Args:
            measurement_name: Name of measurement (shoulder_width, hip_width, etc.)
            edge_reference_points: Dictionary with edge coordinates
            
        Returns:
            Distance in pixels
        """
        left_point = right_point = None
        
        if measurement_name in ('shoulder_width', 'chest_width'):
            left_point = edge_reference_points.get('shoulder_left')
            right_point = edge_reference_points.get('shoulder_right')
        elif measurement_name == 'waist_width':
            left_point = edge_reference_points.get('waist_left')
            right_point = edge_reference_points.get('waist_right')
        elif measurement_name == 'hip_width':
            left_point = edge_reference_points.get('hip_left')
            right_point = edge_reference_points.get('hip_right')
        
        if left_point and right_point and (left_point != (0, 0) or right_point != (0, 0)):
            left_array = np.array(left_point, dtype=np.float32)
            right_array = np.array(right_point, dtype=np.float32)
            return float(np.linalg.norm(right_array - left_array))
        
        return 0.0
    
    def validate_edge_measurement(self, measurement_name: str, measurement_cm: float) -> Tuple[bool, str]:
        """
        Validate that edge-based measurements fall within realistic ranges.
        
        Args:
            measurement_name: Name of the measurement
            measurement_cm: Value of measurement in cm
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Realistic measurement ranges (in cm) for front view
        realistic_ranges = {
            'shoulder_width': (25, 65),   # Shoulder widths typical 30-60cm
            'chest_width': (20, 55),      # Chest widths typical 25-50cm
            'waist_width': (18, 45),      # Waist widths typical 20-40cm
            'hip_width': (25, 55)         # Hip widths typical 30-50cm
        }
        
        if measurement_name not in realistic_ranges:
            return True, "Non-width measurement"
        
        min_cm, max_cm = realistic_ranges[measurement_name]
        
        if measurement_cm < min_cm:
            return False, f"{measurement_name} too narrow: {measurement_cm:.1f}cm (min {min_cm}cm)"
        elif measurement_cm > max_cm:
            return False, f"{measurement_name} too wide: {measurement_cm:.1f}cm (max {max_cm}cm)"
        
        return True, f"{measurement_name} valid: {measurement_cm:.1f}cm"
    
    def apply_edge_points_to_measurement(
        self,
        measurement_name: str,
        edge_reference_points: Dict,
        scale_factor: float
    ) -> Optional[float]:
        """
        Calculate a single measurement using edge reference points.
        
        Args:
            measurement_name: Name of measurement to calculate
            edge_reference_points: Edge points from segmentation
            scale_factor: Pixels to cm conversion factor
            
        Returns:
            Measurement value in cm or None if calculation fails
        """
        if not edge_reference_points or not edge_reference_points.get('is_valid'):
            return None
        
        pixel_dist = self._calculate_edge_distance(measurement_name, edge_reference_points)
        
        if pixel_dist <= 0:
            return None
        
        measurement_cm = pixel_dist * scale_factor
        
        # Validate the measurement
        is_valid, reason = self.validate_edge_measurement(measurement_name, measurement_cm)
        
        if not is_valid:
            # Log warning but return the value anyway (caller can decide)
            return measurement_cm
        
        return measurement_cm
    
    def _apply_refined_shoulders(self, landmark_dict: Dict, 
                                refined_shoulders: Dict) -> Dict:
        """
        Apply refined shoulder landmarks to measurement calculations
        
        Args:
            landmark_dict: Original landmark dictionary
            refined_shoulders: Refined shoulder data from segmentation
            
        Returns:
            Updated landmark dictionary with refined shoulders
        """
        updated_dict = landmark_dict.copy()
        
        # Replace shoulder landmarks with refined versions
        left_shoulder = refined_shoulders['left_shoulder']
        right_shoulder = refined_shoulders['right_shoulder']
        
        # Create refined shoulder arrays [x, y, confidence]
        updated_dict['left_shoulder'] = np.array([
            left_shoulder['x'],
            left_shoulder['y'],
            left_shoulder['confidence']
        ])
        
        updated_dict['right_shoulder'] = np.array([
            right_shoulder['x'],
            right_shoulder['y'],
            right_shoulder['confidence']
        ])
        
        return updated_dict
    
    def calculate_shoulder_measurements_only(
        self,
        landmarks: np.ndarray,
        scale_factor: float,
        refined_shoulders: Optional[Dict] = None
    ) -> Dict[str, Tuple[float, float, str]]:
        """
        Calculate only shoulder-related measurements using refined points
        
        Args:
            landmarks: Detected landmarks
            scale_factor: Pixels to cm conversion factor
            refined_shoulders: Refined shoulder landmarks from segmentation
            
        Returns:
            Dictionary with shoulder measurements and metadata
        """
        if landmarks is None:
            return {}
        
        measurements = {}
        landmark_dict = self._landmarks_to_dict(landmarks)
        
        # Always use refined shoulders if available for these measurements
        if refined_shoulders and refined_shoulders.get('is_refined'):
            landmark_dict = self._apply_refined_shoulders(landmark_dict, refined_shoulders)
            confidence_boost = refined_shoulders.get('refinement_quality', 0.8)
        else:
            confidence_boost = 1.0
        
        # Calculate shoulder-specific measurements
        shoulder_measurement_pairs = {
            'shoulder_width': ('left_shoulder', 'right_shoulder'),
            'chest_width': ('left_shoulder', 'right_shoulder'),
            'arm_span': ('left_wrist', 'right_wrist'),
        }
        
        for name, (p1_name, p2_name) in shoulder_measurement_pairs.items():
            if p1_name in landmark_dict and p2_name in landmark_dict:
                p1 = landmark_dict[p1_name]
                p2 = landmark_dict[p2_name]
                
                pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                cm_dist = pixel_dist * scale_factor
                
                # Use refined confidence if available
                if refined_shoulders and refined_shoulders.get('is_refined'):
                    confidence = (p1[2] + p2[2]) / 2 * confidence_boost
                    source = 'Refined Segmentation'
                else:
                    confidence = (p1[2] + p2[2]) / 2
                    source = 'MediaPipe'
                
                measurements[name] = (cm_dist, min(confidence, 1.0), source)
        
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

