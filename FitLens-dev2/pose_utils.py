"""
Utility functions for pose estimation, alignment checking, and measurements
"""
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
from config import Config


class PoseUtils:
    """Utility class for pose-related calculations"""
    
    @staticmethod
    def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """
        Calculate angle at point p2 formed by p1-p2-p3
        
        Args:
            p1, p2, p3: Points as (x, y) arrays
            
        Returns:
            Angle in degrees
        """
        v1 = p1 - p2
        v2 = p3 - p2
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return np.degrees(angle)
    
    @staticmethod
    def calculate_distance(p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate Euclidean distance between two points"""
        return np.linalg.norm(p1 - p2)
    
    @staticmethod
    def get_keypoint_dict(keypoints: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Convert keypoint array to dictionary with named keypoints
        
        Args:
            keypoints: Array of shape (17, 3) with (x, y, confidence)
            
        Returns:
            Dictionary mapping keypoint names to (x, y, conf) arrays
        """
        kp_dict = {}
        for i, name in enumerate(Config.KEYPOINT_NAMES):
            if i < len(keypoints):
                kp_dict[name] = keypoints[i]
        return kp_dict
    
    @staticmethod
    def check_arms_away_from_body(kp_dict: Dict[str, np.ndarray]) -> Tuple[bool, float]:
        """
        Check if arms are away from body (not touching sides)
        
        Args:
            kp_dict: Dictionary of keypoints
            
        Returns:
            (is_away, distance_score)
        """
        required_kps = ['left_shoulder', 'right_shoulder', 'left_elbow', 
                       'right_elbow', 'left_hip', 'right_hip']
        
        if not all(kp in kp_dict for kp in required_kps):
            return False, 0.0
        
        # Calculate torso width
        torso_width = PoseUtils.calculate_distance(
            kp_dict['left_shoulder'][:2], 
            kp_dict['right_shoulder'][:2]
        )
        
        # Calculate distance from elbows to torso midline
        torso_center_x = (kp_dict['left_hip'][0] + kp_dict['right_hip'][0]) / 2
        
        left_elbow_dist = abs(kp_dict['left_elbow'][0] - torso_center_x)
        right_elbow_dist = abs(kp_dict['right_elbow'][0] - torso_center_x)
        
        # Normalize by torso width
        left_norm = left_elbow_dist / (torso_width / 2 + 1e-6)
        right_norm = right_elbow_dist / (torso_width / 2 + 1e-6)
        
        # Arms should be at least 10% away from body
        min_distance = Config.TARGET_POSE['arm_torso_distance_min']
        is_away = left_norm > min_distance and right_norm > min_distance
        
        distance_score = min(left_norm, right_norm)
        return is_away, distance_score
    
    @staticmethod
    def check_elbow_angles(kp_dict: Dict[str, np.ndarray]) -> Tuple[bool, float]:
        """
        Check if elbows are relatively straight (arms extended)
        
        Args:
            kp_dict: Dictionary of keypoints
            
        Returns:
            (is_straight, angle_score)
        """
        required_kps = ['left_shoulder', 'left_elbow', 'left_wrist',
                       'right_shoulder', 'right_elbow', 'right_wrist']
        
        if not all(kp in kp_dict for kp in required_kps):
            return False, 0.0
        
        # Calculate elbow angles
        left_angle = PoseUtils.calculate_angle(
            kp_dict['left_shoulder'][:2],
            kp_dict['left_elbow'][:2],
            kp_dict['left_wrist'][:2]
        )
        
        right_angle = PoseUtils.calculate_angle(
            kp_dict['right_shoulder'][:2],
            kp_dict['right_elbow'][:2],
            kp_dict['right_wrist'][:2]
        )
        
        min_angle = Config.TARGET_POSE['elbow_angle_min']
        is_straight = left_angle >= min_angle and right_angle >= min_angle
        
        # Score based on how close to 180 degrees
        angle_score = min(left_angle, right_angle) / 180.0
        
        return is_straight, angle_score
    
    @staticmethod
    def check_facing_camera(kp_dict: Dict[str, np.ndarray]) -> Tuple[bool, float]:
        """
        Check if person is facing the camera (shoulders roughly horizontal)
        
        Args:
            kp_dict: Dictionary of keypoints
            
        Returns:
            (is_facing, symmetry_score)
        """
        required_kps = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
        
        if not all(kp in kp_dict for kp in required_kps):
            return False, 0.0
        
        # Check shoulder symmetry
        shoulder_y_diff = abs(kp_dict['left_shoulder'][1] - kp_dict['right_shoulder'][1])
        shoulder_width = abs(kp_dict['left_shoulder'][0] - kp_dict['right_shoulder'][0])
        
        # Check hip symmetry
        hip_y_diff = abs(kp_dict['left_hip'][1] - kp_dict['right_hip'][1])
        hip_width = abs(kp_dict['left_hip'][0] - kp_dict['right_hip'][0])
        
        # Normalize differences
        shoulder_symmetry = 1.0 - min(shoulder_y_diff / (shoulder_width + 1e-6), 1.0)
        hip_symmetry = 1.0 - min(hip_y_diff / (hip_width + 1e-6), 1.0)
        
        symmetry_score = (shoulder_symmetry + hip_symmetry) / 2
        is_facing = symmetry_score > 0.85
        
        return is_facing, symmetry_score
    
    @staticmethod
    def check_standing_straight(kp_dict: Dict[str, np.ndarray]) -> Tuple[bool, float]:
        """
        Check if person is standing straight (vertical alignment)
        
        Args:
            kp_dict: Dictionary of keypoints
            
        Returns:
            (is_straight, alignment_score)
        """
        required_kps = ['nose', 'left_hip', 'right_hip', 'left_ankle', 'right_ankle']
        
        if not all(kp in kp_dict for kp in required_kps):
            return False, 0.0
        
        # Calculate center points
        hip_center_x = (kp_dict['left_hip'][0] + kp_dict['right_hip'][0]) / 2
        ankle_center_x = (kp_dict['left_ankle'][0] + kp_dict['right_ankle'][0]) / 2
        nose_x = kp_dict['nose'][0]
        
        # Check vertical alignment
        hip_ankle_diff = abs(hip_center_x - ankle_center_x)
        nose_hip_diff = abs(nose_x - hip_center_x)
        
        # Normalize by body height
        body_height = abs(kp_dict['nose'][1] - ankle_center_x)
        
        alignment_score = 1.0 - min((hip_ankle_diff + nose_hip_diff) / (body_height + 1e-6), 1.0)
        is_straight = alignment_score > 0.85
        
        return is_straight, alignment_score


class AlignmentChecker:
    """Check if detected pose matches target pose requirements"""
    
    @staticmethod
    def check_alignment(keypoints: np.ndarray, frame_shape: Tuple[int, int]) -> Tuple[bool, Dict[str, float], str]:
        """
        Comprehensive alignment check
        
        Args:
            keypoints: Array of shape (17, 3) with (x, y, confidence)
            frame_shape: (height, width) of frame
            
        Returns:
            (is_aligned, scores_dict, feedback_message)
        """
        kp_dict = PoseUtils.get_keypoint_dict(keypoints)
        
        # Check all alignment criteria
        arms_away, arms_score = PoseUtils.check_arms_away_from_body(kp_dict)
        elbows_straight, elbow_score = PoseUtils.check_elbow_angles(kp_dict)
        facing_camera, facing_score = PoseUtils.check_facing_camera(kp_dict)
        standing_straight, standing_score = PoseUtils.check_standing_straight(kp_dict)
        
        scores = {
            'arms_away': arms_score,
            'elbows_straight': elbow_score,
            'facing_camera': facing_score,
            'standing_straight': standing_score
        }
        
        # Overall alignment score
        overall_score = np.mean(list(scores.values()))
        is_aligned = overall_score >= Config.ALIGNMENT_THRESHOLD
        
        # Generate feedback message
        feedback = AlignmentChecker._generate_feedback(
            arms_away, elbows_straight, facing_camera, standing_straight, scores
        )
        
        return is_aligned, scores, feedback
    
    @staticmethod
    def _generate_feedback(arms_away: bool, elbows_straight: bool, 
                          facing_camera: bool, standing_straight: bool,
                          scores: Dict[str, float]) -> str:
        """Generate user feedback message based on alignment checks"""
        if all([arms_away, elbows_straight, facing_camera, standing_straight]):
            return "PERFECT! Hold still..."
        
        feedback_parts = []
        
        if not arms_away:
            feedback_parts.append("Move arms away from body")
        if not elbows_straight:
            feedback_parts.append("Straighten arms")
        if not facing_camera:
            feedback_parts.append("Face camera directly")
        if not standing_straight:
            feedback_parts.append("Stand up straight")
        
        return " | ".join(feedback_parts)


class MeasurementCalculator:
    """Calculate body measurements from keypoints with pixel-to-scale conversion"""
    
    def __init__(self, reference_height_cm: Optional[float] = None):
        """
        Initialize measurement calculator
        
        Args:
            reference_height_cm: Known height for calibration (optional)
        """
        self.reference_height_cm = reference_height_cm
        self.scale_factor = None
    
    def calibrate_scale(self, keypoints: np.ndarray, frame_shape: Tuple[int, int]):
        """
        Calibrate pixel-to-cm scale factor using reference height
        
        Args:
            keypoints: Array of shape (17, 3)
            frame_shape: (height, width)
        """
        if self.reference_height_cm is None:
            # Use default calibration based on camera parameters
            self._calibrate_from_camera_params(frame_shape)
            return
        
        kp_dict = PoseUtils.get_keypoint_dict(keypoints)
        
        # Calculate pixel height (nose to ankle)
        if 'nose' in kp_dict and 'left_ankle' in kp_dict and 'right_ankle' in kp_dict:
            ankle_center_y = (kp_dict['left_ankle'][1] + kp_dict['right_ankle'][1]) / 2
            pixel_height = abs(ankle_center_y - kp_dict['nose'][1])
            
            # Calculate scale factor (cm per pixel)
            self.scale_factor = self.reference_height_cm / (pixel_height + 1e-6)
        else:
            self._calibrate_from_camera_params(frame_shape)
    
    def _calibrate_from_camera_params(self, frame_shape: Tuple[int, int]):
        """
        Calibrate using pinhole camera model
        
        Args:
            frame_shape: (height, width)
        """
        height, width = frame_shape
        
        # Pinhole camera model: pixel_size = (sensor_width / image_width)
        pixel_size_mm = Config.SENSOR_WIDTH_MM / width
        
        # At reference distance, calculate real-world size per pixel
        # Using similar triangles: real_size / distance = sensor_size / focal_length
        real_size_per_pixel_mm = (pixel_size_mm * Config.REFERENCE_DISTANCE_CM * 10) / Config.FOCAL_LENGTH_MM
        
        # Convert to cm
        self.scale_factor = real_size_per_pixel_mm / 10
    
    def calculate_measurements(self, keypoints: np.ndarray) -> Dict[str, float]:
        """
        Calculate all body measurements in centimeters
        
        Args:
            keypoints: Array of shape (17, 3)
            
        Returns:
            Dictionary of measurements in cm
        """
        if self.scale_factor is None:
            raise ValueError("Scale not calibrated. Call calibrate_scale() first.")
        
        kp_dict = PoseUtils.get_keypoint_dict(keypoints)
        measurements = {}
        
        for segment_name, keypoint_names in Config.BODY_SEGMENTS.items():
            if len(keypoint_names) == 2:
                # Direct distance measurement
                if all(kp in kp_dict for kp in keypoint_names):
                    p1 = kp_dict[keypoint_names[0]][:2]
                    p2 = kp_dict[keypoint_names[1]][:2]
                    pixel_dist = PoseUtils.calculate_distance(p1, p2)
                    measurements[segment_name] = pixel_dist * self.scale_factor
            
            elif len(keypoint_names) == 3:
                # Sum of two segments (e.g., arm length)
                if all(kp in kp_dict for kp in keypoint_names):
                    p1 = kp_dict[keypoint_names[0]][:2]
                    p2 = kp_dict[keypoint_names[1]][:2]
                    p3 = kp_dict[keypoint_names[2]][:2]
                    
                    dist1 = PoseUtils.calculate_distance(p1, p2)
                    dist2 = PoseUtils.calculate_distance(p2, p3)
                    total_pixel_dist = dist1 + dist2
                    measurements[segment_name] = total_pixel_dist * self.scale_factor
        
        return measurements
    
    @staticmethod
    def draw_measurements(frame: np.ndarray, keypoints: np.ndarray, 
                         measurements: Dict[str, float]) -> np.ndarray:
        """
        Draw measurements on frame
        
        Args:
            frame: Input frame
            keypoints: Keypoint array
            measurements: Dictionary of measurements
            
        Returns:
            Frame with measurements drawn
        """
        kp_dict = PoseUtils.get_keypoint_dict(keypoints)
        
        # Draw measurement lines and text
        y_offset = 30
        for segment_name, value_cm in measurements.items():
            text = f"{segment_name.replace('_', ' ').title()}: {value_cm:.1f} cm"
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, (255, 255, 255), 2, cv2.LINE_AA)
            y_offset += 25
        
        return frame


class SkeletonDrawer:
    """Draw skeleton and keypoints on frames"""
    
    # COCO skeleton connections
    SKELETON_CONNECTIONS = [
        (0, 1), (0, 2), (1, 3), (2, 4),  # Head
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
        (5, 11), (6, 12), (11, 12),  # Torso
        (11, 13), (13, 15), (12, 14), (14, 16)  # Legs
    ]
    
    @staticmethod
    def draw_skeleton(frame: np.ndarray, keypoints: np.ndarray, 
                     color: Tuple[int, int, int], 
                     draw_endpoints: bool = False) -> np.ndarray:
        """
        Draw skeleton on frame
        
        Args:
            frame: Input frame
            keypoints: Array of shape (17, 3)
            color: BGR color tuple
            draw_endpoints: Whether to highlight endpoints
            
        Returns:
            Frame with skeleton drawn
        """
        # Draw connections
        for start_idx, end_idx in SkeletonDrawer.SKELETON_CONNECTIONS:
            if start_idx < len(keypoints) and end_idx < len(keypoints):
                start_kp = keypoints[start_idx]
                end_kp = keypoints[end_idx]
                
                if start_kp[2] > Config.KEYPOINT_THRESHOLD and end_kp[2] > Config.KEYPOINT_THRESHOLD:
                    start_pt = (int(start_kp[0]), int(start_kp[1]))
                    end_pt = (int(end_kp[0]), int(end_kp[1]))
                    cv2.line(frame, start_pt, end_pt, color, Config.LINE_THICKNESS, cv2.LINE_AA)
        
        # Draw keypoints
        for i, kp in enumerate(keypoints):
            if kp[2] > Config.KEYPOINT_THRESHOLD:
                pt = (int(kp[0]), int(kp[1]))
                
                if draw_endpoints and i in [5, 6, 7, 8, 9, 10, 11, 12]:
                    # Highlight endpoints (shoulders, elbows, wrists, hips)
                    cv2.circle(frame, pt, Config.ENDPOINT_RADIUS, 
                             Config.ENDPOINT_COLOR, -1, cv2.LINE_AA)
                    cv2.circle(frame, pt, Config.ENDPOINT_RADIUS + 2, 
                             (255, 255, 255), 2, cv2.LINE_AA)
                else:
                    cv2.circle(frame, pt, Config.KEYPOINT_RADIUS, 
                             color, -1, cv2.LINE_AA)
        
        return frame
