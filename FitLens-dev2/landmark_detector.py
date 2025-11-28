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
        Draw landmarks on image
        
        Args:
            image: Input image
            landmarks: Landmarks array
            
        Returns:
            Image with landmarks drawn
        """
        if landmarks is None:
            return image
        
        result = image.copy()
        
        # Draw connections
        connections = self.mp_pose.POSE_CONNECTIONS
        
        for connection in connections:
            start_idx, end_idx = connection
            
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start_point = landmarks[start_idx]
                end_point = landmarks[end_idx]
                
                if start_point[2] > 0.5 and end_point[2] > 0.5:
                    start_pos = (int(start_point[0]), int(start_point[1]))
                    end_pos = (int(end_point[0]), int(end_point[1]))
                    
                    cv2.line(result, start_pos, end_pos, (0, 255, 0), 2)
        
        # Draw keypoints
        for landmark in landmarks:
            if landmark[2] > 0.5:
                pos = (int(landmark[0]), int(landmark[1]))
                cv2.circle(result, pos, 5, (0, 0, 255), -1)
        
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
