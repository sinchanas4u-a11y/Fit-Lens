"""
Measurement Engine
Calculates body measurements from landmarks with confidence scores
Uses ellipse geometry for chest and waist circumference calculations
"""
import numpy as np
from typing import Dict, Tuple, Optional
import math


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
        # Measurement definitions
        self.measurements = {
            'front': {
                # Width measurements
                'shoulder_width': ('left_shoulder', 'right_shoulder'),
                'hip_width': ('left_hip', 'right_hip'),
                'chest_width': ('left_shoulder', 'right_shoulder'),
                'waist_width': ('left_hip', 'right_hip'),
                'arm_span': ('left_wrist', 'right_wrist'),
                'knee_width': ('left_knee', 'right_knee'),
                'ankle_width': ('left_ankle', 'right_ankle'),
                
                # Length measurements (left side)
                'left_arm_length': ('left_shoulder', 'left_wrist'),
                'left_upper_arm': ('left_shoulder', 'left_elbow'),
                'left_forearm': ('left_elbow', 'left_wrist'),
                'left_leg_length': ('left_hip', 'left_ankle'),
                'left_thigh': ('left_hip', 'left_knee'),
                'left_calf': ('left_knee', 'left_ankle'),
                
                # Length measurements (right side)
                'right_arm_length': ('right_shoulder', 'right_wrist'),
                'right_upper_arm': ('right_shoulder', 'right_elbow'),
                'right_forearm': ('right_elbow', 'right_wrist'),
                'right_leg_length': ('right_hip', 'right_ankle'),
                'right_thigh': ('right_hip', 'right_knee'),
                'right_calf': ('right_knee', 'right_ankle'),
                
                # Torso measurements
                'torso_length': ('left_shoulder', 'left_hip'),
                'shoulder_to_knee': ('left_shoulder', 'left_knee'),
                'neck_to_waist': ('nose', 'left_hip'),
            },
            'side': {
                'torso_length': ('left_shoulder', 'left_hip'),
                'shoulder_to_hip': ('left_shoulder', 'left_hip'),
                'hip_to_ankle': ('left_hip', 'left_ankle'),
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
        print(f"\n🔧 MeasurementEngine.calculate_measurements_with_confidence called")
        print(f"   Landmarks: {landmarks.shape if hasattr(landmarks, 'shape') else 'None'}")
        print(f"   Scale factor: {scale_factor}")
        print(f"   View: {view}")
        
        if landmarks is None:
            print("   ⚠️ Landmarks is None, returning empty dict")
            return {}
        
        measurements = {}
        landmark_dict = self._landmarks_to_dict(landmarks)
        
        print(f"   Landmark dict has {len(landmark_dict)} landmarks")
        print(f"   Available landmarks: {list(landmark_dict.keys())[:10]}...")
        
        measurement_defs = self.measurements.get(view, {})
        print(f"   Measurement definitions for '{view}': {len(measurement_defs)} measurements")
        print(f"   Measurements to calculate: {list(measurement_defs.keys())}")
        
        for name, points in measurement_defs.items():
            print(f"\n   Processing: {name}")
            print(f"     Points needed: {points}")
            
            if len(points) == 2:
                p1_name, p2_name = points
                
                if p1_name in landmark_dict and p2_name in landmark_dict:
                    p1 = landmark_dict[p1_name]
                    p2 = landmark_dict[p2_name]
                    
                    print(f"     ✓ Found both landmarks")
                    print(f"       {p1_name}: {p1[:2]} (conf: {p1[2]:.2f})")
                    print(f"       {p2_name}: {p2[:2]} (conf: {p2[2]:.2f})")
                    
                    # Calculate distance
                    pixel_dist = np.linalg.norm(p1[:2] - p2[:2])
                    cm_dist = pixel_dist * scale_factor
                    
                    # Calculate confidence (average of point confidences)
                    confidence = (p1[2] + p2[2]) / 2
                    
                    # Determine source
                    source = 'direct'
                    
                    measurements[name] = (cm_dist, confidence, source)
                    print(f"     ✓ Calculated: {cm_dist:.2f} cm (confidence: {confidence:.2f})")
                else:
                    missing = []
                    if p1_name not in landmark_dict:
                        missing.append(p1_name)
                    if p2_name not in landmark_dict:
                        missing.append(p2_name)
                    print(f"     ✗ Missing landmarks: {missing}")
        
        print(f"\n   ✓ Total measurements calculated: {len(measurements)}")
        print(f"   Measurement names: {list(measurements.keys())}")
        
        # Calculate chest, waist, and hip circumferences using improved ellipse method
        print(f"\n   🔄 Calculating circumferences using improved ellipse method...")
        
        # Get width measurements
        shoulder_width = measurements.get('shoulder_width', (None,))[0] if 'shoulder_width' in measurements else None
        waist_width = measurements.get('waist_width', (None,))[0] if 'waist_width' in measurements else None
        hip_width = measurements.get('hip_width', (None,))[0] if 'hip_width' in measurements else None
        
        if shoulder_width:
            print(f"     Shoulder width: {shoulder_width:.2f} cm")
        if waist_width:
            print(f"     Waist width: {waist_width:.2f} cm")
        if hip_width:
            print(f"     Hip width: {hip_width:.2f} cm")
        
        # Calculate chest width from shoulder width
        chest_width = shoulder_width * self.alpha_s if shoulder_width else None
        
        # Estimate depths using improved method
        chest_depth, waist_depth, hip_depth = self.estimate_torso_depth_improved(
            landmark_dict, scale_factor, chest_width, waist_width, hip_width
        )
        
        # Calculate chest circumference
        if chest_width:
            chest_circumference = self.calculate_circumference_from_width(chest_width, chest_depth)
            
            # Calculate confidence
            avg_confidence = (landmark_dict.get('left_shoulder', [0,0,0])[2] + 
                            landmark_dict.get('right_shoulder', [0,0,0])[2]) / 2
            
            measurements['chest_circumference'] = (chest_circumference, avg_confidence, 'ellipse_improved')
            print(f"     ✓ Chest circumference: {chest_circumference:.2f} cm (width: {chest_width:.2f}, depth: {chest_depth:.2f})")
        
        # Calculate waist circumference
        if waist_width:
            waist_circumference = self.calculate_circumference_from_width(waist_width, waist_depth)
            
            # Calculate confidence
            avg_confidence = (landmark_dict.get('left_hip', [0,0,0])[2] + 
                            landmark_dict.get('right_hip', [0,0,0])[2]) / 2
            
            measurements['waist_circumference'] = (waist_circumference, avg_confidence, 'ellipse_improved')
            print(f"     ✓ Waist circumference: {waist_circumference:.2f} cm (width: {waist_width:.2f}, depth: {waist_depth:.2f})")
        
        # Calculate hip circumference
        if hip_width:
            hip_circumference = self.calculate_circumference_from_width(hip_width, hip_depth)
            
            # Calculate confidence
            avg_confidence = (landmark_dict.get('left_hip', [0,0,0])[2] + 
                            landmark_dict.get('right_hip', [0,0,0])[2]) / 2
            
            measurements['hip_circumference'] = (hip_circumference, avg_confidence, 'ellipse_improved')
            print(f"     ✓ Hip circumference: {hip_circumference:.2f} cm (width: {hip_width:.2f}, depth: {hip_depth:.2f})")
        
        print(f"\n   ✓ Final total measurements: {len(measurements)}")
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
    
    def calculate_ellipse_circumference(self, a: float, b: float) -> float:
        """
        Calculate ellipse circumference using Ramanujan's approximation
        
        Args:
            a: Semi-major axis (width/2)
            b: Semi-minor axis (depth/2)
            
        Returns:
            Circumference of ellipse
        """
        # Ramanujan's approximation for ellipse circumference
        h = ((a - b) ** 2) / ((a + b) ** 2)
        circumference = math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
        
        return circumference
    
    def estimate_torso_depth_improved(self, landmark_dict: Dict[str, np.ndarray], 
                                     scale_factor: float, 
                                     chest_width: float = None,
                                     waist_width: float = None,
                                     hip_width: float = None) -> Tuple[float, float, float]:
        """
        Improved torso depth estimation using multiple methods
        
        Args:
            landmark_dict: Dictionary of landmarks
            scale_factor: Pixel to cm conversion
            chest_width: Measured chest width (optional)
            waist_width: Measured waist width (optional)
            hip_width: Measured hip width (optional)
            
        Returns:
            (chest_depth, waist_depth, hip_depth) in cm
        """
        print(f"\n   📐 Improved depth estimation:")
        
        # Method 1: Proportional model from arm and torso
        arm_lengths = []
        if 'left_shoulder' in landmark_dict and 'left_wrist' in landmark_dict:
            left_arm = np.linalg.norm(
                landmark_dict['left_shoulder'][:2] - landmark_dict['left_wrist'][:2]
            )
            arm_lengths.append(left_arm * scale_factor)
        
        if 'right_shoulder' in landmark_dict and 'right_wrist' in landmark_dict:
            right_arm = np.linalg.norm(
                landmark_dict['right_shoulder'][:2] - landmark_dict['right_wrist'][:2]
            )
            arm_lengths.append(right_arm * scale_factor)
        
        avg_arm_length = np.mean(arm_lengths) if arm_lengths else 0
        
        # Calculate torso length
        torso_length = 0
        if 'left_shoulder' in landmark_dict and 'left_hip' in landmark_dict:
            torso_px = np.linalg.norm(
                landmark_dict['left_shoulder'][:2] - landmark_dict['left_hip'][:2]
            )
            torso_length = torso_px * scale_factor
        
        # Base depth from proportional model
        base_depth = self.alpha_a * avg_arm_length + self.alpha_t * torso_length
        print(f"     Method 1 (proportional): {base_depth:.2f} cm")
        
        # Method 2: Width-based estimation (more accurate if widths available)
        chest_depth_width = chest_width * self.chest_depth_ratio if chest_width else None
        waist_depth_width = waist_width * self.waist_depth_ratio if waist_width else None
        hip_depth_width = hip_width * self.hip_depth_ratio if hip_width else None
        
        if chest_depth_width:
            print(f"     Method 2 (width-based chest): {chest_depth_width:.2f} cm")
        if waist_depth_width:
            print(f"     Method 2 (width-based waist): {waist_depth_width:.2f} cm")
        if hip_depth_width:
            print(f"     Method 2 (width-based hip): {hip_depth_width:.2f} cm")
        
        # Combine methods with weighting
        # Width-based is more accurate, so give it higher weight if available
        chest_depth = chest_depth_width if chest_depth_width else base_depth * 1.1
        waist_depth = waist_depth_width if waist_depth_width else base_depth * 0.9
        hip_depth = hip_depth_width if hip_depth_width else base_depth * 1.0
        
        # Apply anatomical constraints
        # Chest should be deeper than waist
        if chest_depth < waist_depth:
            chest_depth = waist_depth * 1.15
        
        # Hip depth should be between waist and chest
        if hip_depth < waist_depth * 0.95:
            hip_depth = waist_depth * 1.05
        if hip_depth > chest_depth * 1.05:
            hip_depth = chest_depth * 0.95
        
        print(f"     Final depths - Chest: {chest_depth:.2f}, Waist: {waist_depth:.2f}, Hip: {hip_depth:.2f} cm")
        
        return chest_depth, waist_depth, hip_depth
    
    def estimate_torso_depth(self, landmark_dict: Dict[str, np.ndarray], 
                            scale_factor: float) -> Tuple[float, float]:
        """
        Legacy method - kept for compatibility
        """
        chest_depth, waist_depth, _ = self.estimate_torso_depth_improved(
            landmark_dict, scale_factor
        )
        return chest_depth, waist_depth
    
    def calculate_circumference_from_width(self, width: float, depth: float) -> float:
        """
        Calculate circumference from width and depth using ellipse model
        
        Args:
            width: Width measurement (left to right)
            depth: Depth measurement (front to back)
            
        Returns:
            Circumference
        """
        # Semi-axes
        a = width / 2  # Semi-major axis (width)
        b = depth / 2  # Semi-minor axis (depth)
        
        # Calculate circumference using Ramanujan's approximation
        return self.calculate_ellipse_circumference(a, b)
    
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
