"""
Landmark Detection using MediaPipe
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Optional


class LandmarkDetector:
    """Detect body landmarks using MediaPipe"""
    
    def __init__(self):
        """Initialize MediaPipe Pose"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
    
    def detect(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect landmarks in image
        
        Args:
            image: Input image (BGR)
            
        Returns:
            Landmarks array of shape (33, 3) with (x, y, confidence)
            or None if no person detected
        """
        # Convert to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process
        results = self.pose.process(image_rgb)
        
        if results.pose_landmarks:
            # Extract landmarks
            landmarks = []
            h, w = image.shape[:2]
            
            for landmark in results.pose_landmarks.landmark:
                # Convert normalized coordinates to pixels
                x = landmark.x * w
                y = landmark.y * h
                confidence = landmark.visibility
                
                landmarks.append([x, y, confidence])
            
            return np.array(landmarks)
        
        return None
    
    def draw_landmarks(self, image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        """
        Draw landmarks on image with side distinction
        Right side: Cyan (255, 255, 0) - BGR format
        Left side: Magenta (255, 0, 255) - BGR format
        Center/Cross: Green (0, 255, 0)
        """
        if landmarks is None:
            return image
        
        result = image.copy()
        
        # Define side indices
        # Right: 12, 14, 16, 18, 20, 22 (Arm), 24, 26, 28, 30, 32 (Leg), 2, 5, 8 (Face right)
        # Left: 11, 13, 15, 17, 19, 21 (Arm), 23, 25, 27, 29, 31 (Leg), 1, 4, 7 (Face left)
        
        right_indices = {2, 5, 8, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32}
        left_indices = {1, 4, 7, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31}
        
        # Colors (BGR)
        COLOR_RIGHT = (255, 255, 0)   # Cyan
        COLOR_LEFT = (255, 0, 255)    # Magenta
        COLOR_CENTER = (0, 255, 0)    # Green
        
        # Draw connections
        connections = self.mp_pose.POSE_CONNECTIONS
        
        for connection in connections:
            start_idx, end_idx = connection
            
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start_point = landmarks[start_idx]
                end_point = landmarks[end_idx]
                
                # Lower threshold to 0.3 to ensure visibility
                if start_point[2] > 0.3 and end_point[2] > 0.3:
                    start_pos = (int(start_point[0]), int(start_point[1]))
                    end_pos = (int(end_point[0]), int(end_point[1]))
                    
                    # Determine color
                    if start_idx in right_indices and end_idx in right_indices:
                        color = COLOR_RIGHT
                    elif start_idx in left_indices and end_idx in left_indices:
                        color = COLOR_LEFT
                    else:
                        color = COLOR_CENTER
                    
                    cv2.line(result, start_pos, end_pos, color, 2)
        
        # Draw keypoints
        for idx, landmark in enumerate(landmarks):
            if landmark[2] > 0.3:
                pos = (int(landmark[0]), int(landmark[1]))
                
                if idx in right_indices:
                    color = COLOR_RIGHT
                elif idx in left_indices:
                    color = COLOR_LEFT
                else:
                    color = COLOR_CENTER
                    
                cv2.circle(result, pos, 4, color, -1)
                # Optional: Draw white border for better visibility
                cv2.circle(result, pos, 5, (255, 255, 255), 1)
        
        return result
    
    def get_landmark_by_name(self, landmarks: np.ndarray, name: str) -> Optional[np.ndarray]:
        """Get specific landmark by name"""
        landmark_names = {
            'nose': 0,
            'left_eye_inner': 1,
            'left_eye': 2,
            'left_eye_outer': 3,
            'right_eye_inner': 4,
            'right_eye': 5,
            'right_eye_outer': 6,
            'left_ear': 7,
            'right_ear': 8,
            'mouth_left': 9,
            'mouth_right': 10,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_pinky': 17,
            'right_pinky': 18,
            'left_index': 19,
            'right_index': 20,
            'left_thumb': 21,
            'right_thumb': 22,
            'left_hip': 23,
            'right_hip': 24,
            'left_knee': 25,
            'right_knee': 26,
            'left_ankle': 27,
            'right_ankle': 28,
            'left_heel': 29,
            'right_heel': 30,
            'left_foot_index': 31,
            'right_foot_index': 32
        }
        
        if name in landmark_names:
            idx = landmark_names[name]
            if idx < len(landmarks):
                return landmarks[idx]
        
        return None
    
    def cleanup(self):
        """Release resources"""
        self.pose.close()
