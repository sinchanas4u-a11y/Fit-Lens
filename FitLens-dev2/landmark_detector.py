"""
Landmark Detection using MediaPipe
"""
import cv2
import numpy as np
from typing import Optional

# Import MediaPipe with error handling
try:
    import mediapipe as mp
    if not hasattr(mp, 'solutions'):
        print(f"DEBUG: MediaPipe loaded from: {mp.__file__}")
        print(f"DEBUG: MediaPipe dir: {dir(mp)}")
        raise ImportError("MediaPipe 'solutions' module not found")
except ImportError as e:
    print(f"Error importing MediaPipe: {e}")
    # Try to print debug info if mp exists
    try:
        import mediapipe as mp
        print(f"DEBUG: MediaPipe loaded from: {mp.__file__}")
    except:
        pass
    print("Please install: pip install mediapipe==0.10.14")
    raise


class LandmarkDetector:
    """Detect body landmarks using MediaPipe"""
    
    def __init__(self):
        """Initialize MediaPipe Pose"""
        # MediaPipe 0.10.14 - Access solutions module
        try:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
        except AttributeError as e:
            raise ImportError(
                f"Cannot access MediaPipe solutions: {e}\n"
                "Please ensure MediaPipe 0.10.14 is installed: pip install mediapipe==0.10.14"
            )
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
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
    
    def extract_body_edge_keypoints(
        self,
        mask: np.ndarray,
        landmarks: np.ndarray = None
    ) -> dict:
        """
        Extract body edge keypoints from YOLOv8 mask using OpenCV contour extraction
        
        Uses:
        - cv2.Canny() for edge detection
        - cv2.findContours() for contour extraction
        - cv2.convexHull() for convex hull
        - cv2.approxPolyDP() for polygon approximation
        - numpy for point filtering
        
        Args:
            mask: YOLOv8 binary mask
            landmarks: MediaPipe landmarks (optional, for validation)
            
        Returns:
            Dictionary with detected edge keypoints
        """
        if mask is None:
            return {'is_valid': False, 'error': 'Mask is None'}
        
        h, w = mask.shape[:2]
        
        # Convert mask to uint8 if needed
        mask_uint8 = mask.astype(np.uint8)
        
        # Apply morphological operations to clean mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_clean = cv2.morphologyEx(mask_uint8, cv2.MORPH_CLOSE, kernel)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Apply Canny edge detection
        edges = cv2.Canny(mask_clean, 50, 150)
        
        # Find contours
        contours = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        
        if len(contours) == 0:
            return {'is_valid': False, 'error': 'No contours found'}
        
        # Get the largest contour (main body)
        main_contour = max(contours, key=cv2.contourArea)
        
        # Get convex hull
        hull = cv2.convexHull(main_contour)
        
        # Approximate polygon
        epsilon = 0.02 * cv2.arcLength(main_contour, True)
        approx_contour = cv2.approxPolyDP(main_contour, epsilon, True)
        
        # Extract key points using numpy filtering
        hull_points = hull.reshape(-1, 2)
        
        # Find topmost, bottommost, leftmost, rightmost points
        topmost = hull_points[np.argmin(hull_points[:, 1])]
        bottommost = hull_points[np.argmax(hull_points[:, 1])]
        leftmost = hull_points[np.argmin(hull_points[:, 0])]
        rightmost = hull_points[np.argmax(hull_points[:, 0])]
        
        # Calculate body height from mask
        body_points_y = hull_points[:, 1]
        height_px = int(np.max(body_points_y) - np.min(body_points_y))
        
        # Find shoulder level (approximately 1/5 from top)
        shoulder_y = int(topmost[1] + height_px * 0.2)
        
        # Find points at shoulder level
        y_tolerance = 30
        shoulder_region_mask = (hull_points[:, 1] >= shoulder_y - y_tolerance) & \
                               (hull_points[:, 1] <= shoulder_y + y_tolerance)
        shoulder_points = hull_points[shoulder_region_mask]
        
        if len(shoulder_points) >= 2:
            left_shoulder_edge = shoulder_points[np.argmin(shoulder_points[:, 0])]
            right_shoulder_edge = shoulder_points[np.argmax(shoulder_points[:, 0])]
        else:
            left_shoulder_edge = leftmost
            right_shoulder_edge = rightmost
        
        return {
            'is_valid': True,
            'height_px': height_px,
            'topmost': tuple(topmost),
            'bottommost': tuple(bottommost),
            'leftmost': tuple(leftmost),
            'rightmost': tuple(rightmost),
            'shoulder_y': shoulder_y,
            'left_shoulder_edge': tuple(left_shoulder_edge),
            'right_shoulder_edge': tuple(right_shoulder_edge),
            'shoulder_width_px': int(right_shoulder_edge[0] - left_shoulder_edge[0]),
            'main_contour': main_contour,
            'hull': hull,
            'approx_contour': approx_contour,
        }
    
