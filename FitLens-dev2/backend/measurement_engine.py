"""
Measurement Engine - Hybrid Vision Approach
- Uses YOLOv8 segmentation edge points for width measurements
- Uses MediaPipe Pose for skeletal joint measurements
- Keeps all existing pixel-to-scale conversion logic unchanged
"""
import numpy as np
import json
import os
from typing import Dict, Tuple, Optional

class RegressionCorrector:
    """
    Self-updating regression corrector.
    Stores data points and recomputes
    regression for any n datasets.

    Formula: actual = slope × measured
                      + intercept
    Minimum R² to apply correction
    Below this threshold use raw value
    """
    MIN_R2 = 0.85
    MIN_POINTS = 3
    
    _data = {}
    _models = {}
    _DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regression_data.json")
    _loaded = False

    @classmethod
    def load_data(cls):
        if cls._loaded:
            return
        if os.path.exists(cls._DATA_FILE):
            try:
                with open(cls._DATA_FILE, 'r') as f:
                    cls._data = json.load(f)
                cls._recompute_all()
            except Exception as e:
                print(f"Error loading regression data: {e}")
        cls._loaded = True

    @classmethod
    def save_data(cls):
        try:
            with open(cls._DATA_FILE, 'w') as f:
                json.dump(cls._data, f, indent=4)
        except Exception as e:
            print(f"Error saving regression data: {e}")

    @classmethod
    def add_data_point(cls, measurement_name: str, measured_cm: float, actual_cm: float):
        cls.load_data()
        if measurement_name not in cls._data:
            cls._data[measurement_name] = []
        cls._data[measurement_name].append((measured_cm, actual_cm))
        cls.save_data()
        cls._recompute(measurement_name)

    @classmethod
    def _recompute_all(cls):
        for name in cls._data:
            cls._recompute(name)

    @classmethod
    def _recompute(cls, measurement_name: str):
        points = cls._data.get(measurement_name, [])
        if len(points) < cls.MIN_POINTS:
            cls._models[measurement_name] = {
                'slope':     1.0,
                'intercept': 0.0,
                'r2':        0.0,
                'n':         len(points),
                'valid':     False
            }
            return cls._models[measurement_name]

        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        n = len(points)

        # OLS formula
        sum_x   = np.sum(x)
        sum_y   = np.sum(y)
        sum_xy  = np.sum(x * y)
        sum_x2  = np.sum(x ** 2)

        denom = n * sum_x2 - sum_x ** 2

        if abs(denom) < 1e-10:
            # Vertical line — cannot fit
            cls._models[measurement_name] = {
                'slope':     1.0,
                'intercept': 0.0,
                'r2':        0.0,
                'n':         n,
                'valid':     False,
                'reason':    'x values too similar'
            }
            return cls._models[measurement_name]

        slope     = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        # R² calculation
        y_pred  = slope * x + intercept
        ss_res  = np.sum((y - y_pred) ** 2)
        ss_tot  = np.sum((y - np.mean(y)) ** 2)

        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        cls._models[measurement_name] = {
            'slope': slope,
            'intercept': intercept,
            'r2': r2,
            'n': n,
            'valid': r2 >= cls.MIN_R2
        }
        return cls._models[measurement_name]

    @classmethod
    def apply(cls, measurement_name: str, raw_px: float, scale_factor: float) -> float:
        cls.load_data()
        raw_cm = raw_px * scale_factor
        model = cls._models.get(measurement_name)
        if model and model.get('valid'):
            corrected = (model['slope'] * raw_cm) + model['intercept']
            return max(0.1, corrected)
        return raw_cm


class MeasurementEngine:
    """Calculate body measurements from landmarks and segmentation edge points"""
    
    def __init__(self):
        """Initialize measurement engine"""
        # Measurement definitions - only requested measurements
        self.measurements = {
            'front': {
                'shoulder_width': ('left_shoulder', 'right_shoulder'),
                'arm_length': ('left_shoulder', 'left_wrist'),
                'chest_circumference': ('left_shoulder', 'right_shoulder'),
                'waist_circumference': ('left_hip', 'right_hip'),
                'hip_width': ('left_hip', 'right_hip'),
                'torso_length': ('left_shoulder', 'left_hip'),
                'leg_length': ('left_hip', 'left_ankle'),
                'full_height': ('nose', 'left_ankle'),
            },
            'side': {
                'torso_length': ('shoulder', 'hip'),
                'leg_length': ('hip', 'ankle'),
            }
        }
        
        # Measurements that use segmentation edges instead of MediaPipe
        self.edge_based_measurements = {
            'shoulder_width',
            'chest_circumference',
            'waist_circumference',
            'hip_width',
            'chest_width',
            'waist_width',
        }
        
        # Measurements that use MediaPipe joints
        self.joint_based_measurements = {
            'arm_length',
            'torso_length',
            'leg_length',
            'full_height',
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
            
            # Convert to cm using scale factor with regression correction
            cm_dist = RegressionCorrector.apply(name, pixel_dist, scale_factor)
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
                    measurement_value = RegressionCorrector.apply(name, pixel_dist, scale_factor)
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
                    # Apply height-based scaling with regression correction
                    measurement_value = RegressionCorrector.apply(name, pixel_dist, scale_factor)
                    confidence = (p1[2] + p2[2]) / 2
                    source = "MediaPipe Landmarks (33 points)"
            
            if measurement_value is not None:
                measurements[name] = (measurement_value, confidence, source)
        
        # Override full_height with user_height_cm if provided to avoid 2-3cm bias
        if user_height_cm and float(user_height_cm) > 0:
            measurements['full_height'] = (float(user_height_cm), 1.0, 'User Input')
                
        return measurements
    
    def _calculate_edge_distance(self, measurement_name: str, edge_reference_points: Dict) -> float:
        """
        Calculate distance between edge points for a specific measurement.
        
        Args:
            measurement_name: Name of measurement (shoulder_width, chest_circumference, etc.)
            edge_reference_points: Dictionary with edge coordinates
            
        Returns:
            Distance in pixels
        """
        left_point = right_point = None
        
        if measurement_name in ('shoulder_width', 'chest_circumference', 'chest_width'):
            left_point = edge_reference_points.get('shoulder_left') if measurement_name == 'shoulder_width' else edge_reference_points.get('chest_left')
            right_point = edge_reference_points.get('shoulder_right') if measurement_name == 'shoulder_width' else edge_reference_points.get('chest_right')
            
            # Special case for chest_circumference: width * 3.0
            if measurement_name == 'chest_circumference' and left_point and right_point:
                left_array = np.array(left_point, dtype=np.float32)
                right_array = np.array(right_point, dtype=np.float32)
                width_px = float(np.linalg.norm(right_array - left_array))
                return width_px * 3.0

        elif measurement_name in ('waist_circumference', 'waist_width'):
            left_point = edge_reference_points.get('waist_left')
            right_point = edge_reference_points.get('waist_right')
            
            # Special case for waist_circumference: width * 2.8
            if measurement_name == 'waist_circumference' and left_point and right_point:
                left_array = np.array(left_point, dtype=np.float32)
                right_array = np.array(right_point, dtype=np.float32)
                width_px = float(np.linalg.norm(right_array - left_array))
                return width_px * 2.8

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
            'shoulder_width': (25, 65),         # Shoulder widths typical 30-60cm
            'chest_circumference': (60, 140),   # Chest circumference typical 70-130cm
            'waist_circumference': (50, 120),   # Waist circumference typical 60-110cm
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
        
        measurement_cm = RegressionCorrector.apply(measurement_name, pixel_dist, scale_factor)
        
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
                cm_dist = RegressionCorrector.apply(name, pixel_dist, scale_factor)
                
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
        
        # Define reasonable ranges (cm) for requested measurements
        ranges = {
            'shoulder_width': (25, 65),
            'arm_length': (40, 90),
            'chest_circumference': (60, 140),
            'waist_circumference': (50, 120),
            'torso_length': (40, 80),
            'leg_length': (60, 120),
            'full_height': (100, 220),
        }
        
        for name, value in measurements.items():
            if name in ranges:
                min_val, max_val = ranges[name]
                validation[name] = min_val <= value <= max_val
            else:
                validation[name] = True
        
        return validation

