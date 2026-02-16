"""
Landmark Detection using MediaPipe with Hybrid Vision Approach
- MediaPipe Pose for skeletal joints (elbow, wrist, knee, ankle)
- YOLOv8 Segmentation for body edge reference points (shoulder, waist, hip widths)
- MediaPipe Face Mesh for facial landmarks
"""
import cv2
import numpy as np
from typing import Optional, List, Dict, Tuple
import json

# Import MediaPipe with error handling
try:
    import mediapipe as mp
    if not hasattr(mp, 'solutions'):
        raise ImportError("MediaPipe 'solutions' module not found")
except ImportError as e:
    print(f"Error importing MediaPipe: {e}")
    print("Please install: pip install mediapipe==0.10.14")
    raise


class LandmarkDetector:
    """Detect body landmarks using hybrid MediaPipe + segmentation approach"""
    
    def __init__(self):
        """Initialize MediaPipe Pose, Face Mesh, and hybrid parameters"""
        # MediaPipe 0.10.14 - Access solutions module
        try:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_face_mesh = mp.solutions.face_mesh
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
        
        # Initialize Face Mesh for facial landmarks
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Shoulder edge detection parameters
        self.shoulder_region_radius = 60  # pixels
        self.edge_detection_threshold = 50
        self.min_edge_confidence = 0.75
        self.frame_counter = 0
        
        # Hybrid approach parameters
        self.use_segmentation_for_widths = True  # Use mask for width measurements
        self.contour_smoothing_kernel = 5  # For smoothing extracted contours
        self.body_edge_tolerance = 15  # pixels - tolerance for finding edges at specific heights
        self.min_valid_contour_area = 500  # minimum pixels for valid contour
        self.shoulder_height_tolerance = 20  # pixels - tolerance for finding shoulder points at height
        self.min_shoulder_width = 50  # minimum shoulder width in pixels
    
    def detect_shoulder_edge_points(self, image: np.ndarray, landmarks: np.ndarray, 
                                   shoulder_type: str = 'both') -> Dict:
        """
        Detect edge points of the shoulder using image analysis and landmark data
        
        Args:
            image: Input image (BGR)
            landmarks: Detected landmarks from MediaPipe
            shoulder_type: 'left', 'right', or 'both'
            
        Returns:
            Dictionary with shoulder_edge_points and confidence_score
        """
        # Always increment frame counter
        self.frame_counter += 1
        
        if landmarks is None:
            return {
                'frame_number': self.frame_counter,
                'shoulder_edge_points': [],
                'confidence_score': 0.0
            }
        
        h, w = image.shape[:2]
        
        # Shoulder indices: 11=left_shoulder, 12=right_shoulder
        left_shoulder_idx = 11
        right_shoulder_idx = 12
        
        edge_points = []
        confidence_scores = []
        
        # Process left shoulder
        if shoulder_type in ['left', 'both']:
            if left_shoulder_idx < len(landmarks):
                left_points, left_conf = self._extract_shoulder_edges(
                    image, landmarks[left_shoulder_idx], 'left'
                )
                edge_points.extend(left_points)
                if left_conf > 0:
                    confidence_scores.append(left_conf)
        
        # Process right shoulder
        if shoulder_type in ['right', 'both']:
            if right_shoulder_idx < len(landmarks):
                right_points, right_conf = self._extract_shoulder_edges(
                    image, landmarks[right_shoulder_idx], 'right'
                )
                edge_points.extend(right_points)
                if right_conf > 0:
                    confidence_scores.append(right_conf)
        
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        return {
            'frame_number': self.frame_counter,
            'shoulder_edge_points': edge_points,
            'confidence_score': float(avg_confidence)
        }
    
    def _extract_shoulder_edges(self, image: np.ndarray, shoulder_landmark: np.ndarray,
                               side: str) -> Tuple[List[Dict], float]:
        """
        Extract edge points from a single shoulder
        
        Args:
            image: Input image
            shoulder_landmark: [x, y, confidence] of shoulder joint
            side: 'left' or 'right'
            
        Returns:
            Tuple of (edge_points_list, confidence_score)
        """
        h, w = image.shape[:2]
        center_x = int(shoulder_landmark[0])
        center_y = int(shoulder_landmark[1])
        punct_conf = shoulder_landmark[2]
        
        # Clamp coordinates to image bounds
        x_min = max(0, center_x - self.shoulder_region_radius)
        x_max = min(w, center_x + self.shoulder_region_radius)
        y_min = max(0, center_y - self.shoulder_region_radius)
        y_max = min(h, center_y + self.shoulder_region_radius)
        
        # Extract region of interest around shoulder
        roi = image[y_min:y_max, x_min:x_max]
        
        if roi.size == 0:
            return [], 0.0
        
        # Convert to grayscale and apply edge detection
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 1)
        
        # Apply Canny edge detection
        edges = cv2.Canny(blurred, self.edge_detection_threshold - 20, 
                         self.edge_detection_threshold)
        
        # Find contours in the edge image
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        edge_points = []
        confidence_values = []
        
        if contours:
            # Find the largest contour (likely the shoulder edge)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get the convex hull of the contour
            hull = cv2.convexHull(largest_contour)
            
            # Extract key edge points from the hull
            if len(hull) > 0:
                # Get extreme points
                extreme_points = self._get_extreme_points(hull, side)
                
                for point in extreme_points:
                    # Convert from ROI coordinates back to image coordinates
                    img_x = point[0] + x_min
                    img_y = point[1] + y_min
                    
                    # Normalize coordinates to 0-1 range
                    norm_x = img_x / w
                    norm_y = img_y / h
                    
                    edge_points.append({
                        'x': float(norm_x),
                        'y': float(norm_y),
                        'pixel_x': int(img_x),
                        'pixel_y': int(img_y)
                    })
                    
                    # Confidence higher for points with stronger edges
                    confidence_values.append(min(1.0, punct_conf))
        
        avg_confidence = np.mean(confidence_values) if confidence_values else 0.0
        
        return edge_points, avg_confidence
    
    def _get_extreme_points(self, hull: np.ndarray, side: str) -> List[Tuple[int, int]]:
        """
        Get extreme points from the shoulder contour hull based on side
        
        Args:
            hull: Convex hull of shoulder contour
            side: 'left' or 'right'
            
        Returns:
            List of extreme points
        """
        points = []
        
        if len(hull) == 0:
            return points
        
        # Extract coordinates
        hull_points = hull.reshape(-1, 2)
        
        # Get extreme points in different directions
        top_point = hull_points[hull_points[:, 1].argmin()]  # Topmost
        bottom_point = hull_points[hull_points[:, 1].argmax()]  # Bottommost
        
        # For shoulder edge, we want the lateral (outer) point
        if side == 'right':
            # Rightmost point for right shoulder
            lateral_point = hull_points[hull_points[:, 0].argmax()]
        else:  # left
            # Leftmost point for left shoulder
            lateral_point = hull_points[hull_points[:, 0].argmin()]
        
        # Get medial points (toward center of body)
        center_x = np.mean(hull_points[:, 0])
        if side == 'right':
            medial_point = hull_points[hull_points[:, 0].argmin()]
        else:
            medial_point = hull_points[hull_points[:, 0].argmax()]
        
        # Sample additional points along the edge for better coverage
        sampled_points = self._sample_contour_points(hull_points, 4)
        
        # Combine and return unique points
        candidate_points = [
            tuple(top_point),
            tuple(bottom_point),
            tuple(lateral_point),
            tuple(medial_point)
        ] + sampled_points
        
        # Remove duplicates
        unique_points = list(set(candidate_points))
        
        return unique_points[:8]  # Return up to 8 points
    
    def _sample_contour_points(self, hull_points: np.ndarray, num_samples: int) -> List[Tuple[int, int]]:
        """Sample evenly distributed points from contour"""
        if len(hull_points) == 0:
            return []
        
        sampled = []
        step = max(1, len(hull_points) // num_samples)
        
        for i in range(0, len(hull_points), step)[:num_samples]:
            sampled.append(tuple(hull_points[i]))
        
        return sampled
        
        # Shoulder edge detection parameters
        self.shoulder_region_radius = 60  # pixels
        self.edge_detection_threshold = 50
        self.min_edge_confidence = 0.75
        self.frame_counter = 0
    
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
    
    def draw_shoulder_edges(self, image: np.ndarray, shoulder_data: Dict,
                           show_labels: bool = True) -> np.ndarray:
        """
        Draw detected shoulder edge points on image
        
        Args:
            image: Input image
            shoulder_data: Output from detect_shoulder_edge_points()
            show_labels: Whether to show frame number and confidence
            
        Returns:
            Image with drawn shoulder edges
        """
        result = image.copy()
        h, w = image.shape[:2]
        
        if not shoulder_data.get('shoulder_edge_points'):
            return result
        
        # Colors for shoulder edges
        COLOR_EDGE = (0, 165, 255)  # Orange for edges
        COLOR_CONFIDENCE_HIGH = (0, 255, 0)  # Green for high confidence
        COLOR_CONFIDENCE_LOW = (0, 0, 255)  # Red for low confidence
        
        confidence = shoulder_data['confidence_score']
        
        # Choose color based on confidence
        color = COLOR_CONFIDENCE_HIGH if confidence > 0.8 else COLOR_CONFIDENCE_LOW
        
        # Draw edge points
        for point in shoulder_data['shoulder_edge_points']:
            pixel_x = point['pixel_x']
            pixel_y = point['pixel_y']
            
            # Draw point
            cv2.circle(result, (pixel_x, pixel_y), 6, color, -1)
            cv2.circle(result, (pixel_x, pixel_y), 7, (255, 255, 255), 1)
        
        # Connect related edge points to form shoulder edge contour
        if len(shoulder_data['shoulder_edge_points']) > 1:
            points_list = [(p['pixel_x'], p['pixel_y']) 
                          for p in shoulder_data['shoulder_edge_points']]
            # Sort points to draw a connected outline
            points_array = np.array(sorted(points_list, key=lambda p: (p[0], p[1])))
            cv2.polylines(result, [points_array], False, COLOR_EDGE, 2)
        
        # Add information text if requested
        if show_labels:
            frame_num = shoulder_data['frame_number']
            conf_text = f"Frame: {frame_num} | Confidence: {confidence:.2%}"
            cv2.putText(result, conf_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (255, 255, 255), 2)
        
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
    
    def export_shoulder_data_json(self, shoulder_data: Dict, 
                                 include_raw_points: bool = True) -> str:
        """
        Export shoulder edge detection data as JSON string
        
        Args:
            shoulder_data: Output from detect_shoulder_edge_points()
            include_raw_points: Whether to include raw pixel coordinates
            
        Returns:
            JSON string with formatted output
        """
        output = {
            'frame_number': shoulder_data['frame_number'],
            'shoulder_edge_points': [],
            'confidence_score': shoulder_data['confidence_score'],
            'timestamp': None,
            'detection_quality': self._assess_detection_quality(shoulder_data)
        }
        
        for point in shoulder_data['shoulder_edge_points']:
            point_data = {
                'x': point['x'],  # Normalized 0-1
                'y': point['y']   # Normalized 0-1
            }
            if include_raw_points:
                point_data['pixel_x'] = point['pixel_x']
                point_data['pixel_y'] = point['pixel_y']
            
            output['shoulder_edge_points'].append(point_data)
        
        return json.dumps(output, indent=2)
    
    def _assess_detection_quality(self, shoulder_data: Dict) -> Dict[str, str]:
        """
        Assess the quality of shoulder edge detection
        
        Returns:
            Dictionary with quality metrics
        """
        confidence = shoulder_data['confidence_score']
        num_points = len(shoulder_data['shoulder_edge_points'])
        
        quality_score = 'good' if confidence > 0.85 else ('fair' if confidence > 0.70 else 'poor')
        point_coverage = 'optimal' if num_points >= 6 else ('adequate' if num_points >= 4 else 'limited')
        
        return {
            'overall': quality_score,
            'confidence_level': 'high' if confidence > 0.8 else 'medium' if confidence > 0.6 else 'low',
            'point_coverage': point_coverage,
            'recommended_action': 'proceed' if quality_score == 'good' else 'review' if quality_score == 'fair' else 'retake'
        }
    
    def batch_detect_shoulder_edges(self, video_frames: List[np.ndarray]) -> List[Dict]:
        """
        Process multiple frames and return shoulder edge data for all
        
        Args:
            video_frames: List of frames to process
            
        Returns:
            List of detection results with JSON-compatible format
        """
        results = []
        
        for frame in video_frames:
            landmarks = self.detect(frame)
            shoulder_data = self.detect_shoulder_edge_points(frame, landmarks)
            results.append(shoulder_data)
        
        return results
    
    def get_detection_statistics(self, detection_results: List[Dict]) -> Dict:
        """
        Calculate statistics from multiple detection results
        
        Args:
            detection_results: List of results from detect_shoulder_edge_points()
            
        Returns:
            Dictionary with statistics
        """
        if not detection_results:
            return {}
        
        confidences = [r['confidence_score'] for r in detection_results]
        point_counts = [len(r['shoulder_edge_points']) for r in detection_results]
        
        return {
            'total_frames': len(detection_results),
            'average_confidence': float(np.mean(confidences)),
            'max_confidence': float(np.max(confidences)),
            'min_confidence': float(np.min(confidences)),
            'std_confidence': float(np.std(confidences)),
            'average_edge_points': float(np.mean(point_counts)),
            'frames_with_detections': sum(1 for c in confidences if c > 0),
            'detection_success_rate': float(sum(1 for c in confidences if c > 0) / len(confidences))
        }
    
    # ====== SHOULDER LANDMARK REFINEMENT USING SEGMENTATION ======
    
    def refine_shoulder_landmarks(self, image: np.ndarray, landmarks: np.ndarray,
                                   segmentation_mask: np.ndarray) -> Dict[str, Dict]:
        """
        Refine shoulder landmarks using segmentation mask boundary
        
        Extracts the shoulder region from the segmentation mask, computes its contour,
        and selects extreme left and right points at shoulder height as refined shoulder reference points.
        
        Args:
            image: Input image (BGR)
            landmarks: MediaPipe landmarks (33, 3) with (x, y, confidence)
            segmentation_mask: Binary segmentation mask (255 for person, 0 for background)
            
        Returns:
            Dictionary with refined shoulder data:
            {
                'left_shoulder': {'x': float, 'y': float, 'confidence': float, 'source': 'segmentation'},
                'right_shoulder': {'x': float, 'y': float, 'confidence': float, 'source': 'segmentation'},
                'original_left_shoulder': {...},  # Original MediaPipe landmark
                'original_right_shoulder': {...},
                'refinement_quality': float (0-1),  # How much refinement was applied
                'is_refined': bool
            }
        """
        if landmarks is None or segmentation_mask is None:
            return self._get_unrefined_shoulders(landmarks)
        
        h, w = image.shape[:2]
        
        # Get original shoulder landmarks
        left_shoulder_orig = landmarks[11]  # MediaPipe index for left shoulder
        right_shoulder_orig = landmarks[12]  # MediaPipe index for right shoulder
        
        # Extract shoulder region from segmentation mask
        left_region, left_bbox = self._extract_shoulder_region(
            segmentation_mask, left_shoulder_orig, 'left', h, w
        )
        right_region, right_bbox = self._extract_shoulder_region(
            segmentation_mask, right_shoulder_orig, 'right', h, w
        )
        
        # Compute contours and get refined points
        left_refined = self._compute_refined_shoulder_point(
            left_region, left_bbox, 'left', left_shoulder_orig
        )
        right_refined = self._compute_refined_shoulder_point(
            right_region, right_bbox, 'right', right_shoulder_orig
        )
        
        # Calculate overall refinement quality
        refinement_quality = self._calculate_refinement_quality(
            left_shoulder_orig, left_refined,
            right_shoulder_orig, right_refined
        )
        
        return {
            'left_shoulder': left_refined,
            'right_shoulder': right_refined,
            'original_left_shoulder': {
                'x': float(left_shoulder_orig[0]),
                'y': float(left_shoulder_orig[1]),
                'confidence': float(left_shoulder_orig[2]),
                'source': 'mediapipe'
            },
            'original_right_shoulder': {
                'x': float(right_shoulder_orig[0]),
                'y': float(right_shoulder_orig[1]),
                'confidence': float(right_shoulder_orig[2]),
                'source': 'mediapipe'
            },
            'refinement_quality': refinement_quality,
            'is_refined': True
        }
    
    def _extract_shoulder_region(self, mask: np.ndarray, shoulder_landmark: np.ndarray,
                                side: str, img_h: int, img_w: int) -> Tuple[np.ndarray, tuple]:
        """
        Extract shoulder region from segmentation mask
        
        Args:
            mask: Binary segmentation mask
            shoulder_landmark: [x, y, confidence] of shoulder from MediaPipe
            side: 'left' or 'right'
            img_h, img_w: Image dimensions
            
        Returns:
            (roi_mask, bbox) - extracted region and its bounding box
        """
        shoulder_x = int(shoulder_landmark[0])
        shoulder_y = int(shoulder_landmark[1])
        
        # Define shoulder extraction region (larger area above and around shoulder)
        # Heights: 40px above shoulder, 80px below
        # Width: 100px on each side for bilateral context
        x_margin = 100
        y_above = 40
        y_below = 80
        
        x_min = max(0, shoulder_x - x_margin)
        x_max = min(img_w, shoulder_x + x_margin)
        y_min = max(0, shoulder_y - y_above)
        y_max = min(img_h, shoulder_y + y_below)
        
        # Extract region
        roi_mask = mask[y_min:y_max, x_min:x_max].copy()
        bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
        
        return roi_mask, bbox
    
    def _compute_refined_shoulder_point(self, roi_mask: np.ndarray, bbox: tuple,
                                       side: str, original_landmark: np.ndarray) -> Dict:
        """
        Compute refined shoulder point from segmentation mask region
        
        Args:
            roi_mask: Extracted shoulder region from mask
            bbox: (x_min, y_min, width, height) of extracted region
            side: 'left' or 'right'
            original_landmark: Original MediaPipe landmark for fallback
            
        Returns:
            Dictionary with refined shoulder point
        """
        if roi_mask is None or roi_mask.size == 0:
            return self._landmark_to_dict(original_landmark, 'fallback')
        
        # Ensure mask is binary
        roi_mask = (roi_mask > 127).astype(np.uint8) * 255
        
        # Find contours in the mask
        contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return self._landmark_to_dict(original_landmark, 'fallback')
        
        # Get the largest contour (assuming it's the shoulder)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Compute convex hull for smoother outline
        hull = cv2.convexHull(largest_contour)
        
        if len(hull) < 3:
            return self._landmark_to_dict(original_landmark, 'fallback')
        
        # Get shoulder height range (median y-coordinate of hull points)
        hull_points = hull.reshape(-1, 2)
        shoulder_heights = hull_points[:, 1]
        median_shoulder_height = np.median(shoulder_heights)
        
        # Select extreme left/right points at shoulder height (with tolerance)
        height_tolerance = self.shoulder_height_tolerance
        points_at_height = hull_points[
            np.abs(hull_points[:, 1] - median_shoulder_height) <= height_tolerance
        ]
        
        if len(points_at_height) == 0:
            # Fallback: use hull center at shoulder height
            points_at_height = hull_points[
                np.abs(hull_points[:, 1] - median_shoulder_height) <= height_tolerance * 2
            ]
        
        if len(points_at_height) == 0:
            # Final fallback
            return self._landmark_to_dict(original_landmark, 'fallback')
        
        # Select extreme left or right point
        if side == 'right':
            # Select rightmost point at shoulder height
            refined_roi = points_at_height[np.argmax(points_at_height[:, 0])]
        else:  # left
            # Select leftmost point at shoulder height
            refined_roi = points_at_height[np.argmin(points_at_height[:, 0])]
        
        # Convert back to image coordinates
        x_min, y_min, roi_w, roi_h = bbox
        refined_x = refined_roi[0] + x_min
        refined_y = refined_roi[1] + y_min
        
        # Calculate confidence based on contour area and regularity
        contour_area = cv2.contourArea(largest_contour)
        hull_area = cv2.contourArea(hull)
        
        # Confidence is higher when hull is more regular (hull_area ≈ contour_area)
        area_ratio = contour_area / max(hull_area, 1)
        base_confidence = min(1.0, area_ratio * 0.9 + 0.1)  # Range: 0.1 to 1.0
        
        # Combine with original MediaPipe confidence
        combined_confidence = (base_confidence + original_landmark[2]) / 2
        
        return {
            'x': float(refined_x),
            'y': float(refined_y),
            'confidence': float(combined_confidence),
            'source': 'segmentation',
            'refinement_applied': True
        }
    
    def _calculate_refinement_quality(self, left_orig: np.ndarray, left_refined: Dict,
                                      right_orig: np.ndarray, right_refined: Dict) -> float:
        """
        Calculate overall quality of the shoulder refinement
        
        Returns:
            Float 0-1 indicating refinement quality
        """
        # Check if both shoulders were successfully refined
        if left_refined.get('source') == 'fallback' or right_refined.get('source') == 'fallback':
            quality = 0.5  # Reduced quality if fallback was needed
        else:
            quality = 0.9  # Good quality if both refined from segmentation
        
        # Boost quality if refined points have high confidence
        avg_confidence = (left_refined['confidence'] + right_refined['confidence']) / 2
        quality *= (0.5 + 0.5 * avg_confidence)  # Scale by confidence
        
        # Check if shoulder width is reasonable
        shoulder_width = abs(right_refined['x'] - left_refined['x'])
        if shoulder_width < self.min_shoulder_width:
            quality *= 0.7  # Penalize unrealistic shoulder width
        
        return float(min(1.0, max(0.0, quality)))
    
    def _landmark_to_dict(self, landmark: np.ndarray, source: str) -> Dict:
        """Convert landmark array to dictionary format"""
        return {
            'x': float(landmark[0]),
            'y': float(landmark[1]),
            'confidence': float(landmark[2]),
            'source': source,
            'refinement_applied': False
        }
    
    def _get_unrefined_shoulders(self, landmarks: Optional[np.ndarray]) -> Dict:
        """Return original shoulders when refinement is not possible"""
        if landmarks is None:
            return {
                'left_shoulder': {'x': 0, 'y': 0, 'confidence': 0, 'source': 'none'},
                'right_shoulder': {'x': 0, 'y': 0, 'confidence': 0, 'source': 'none'},
                'refinement_quality': 0.0,
                'is_refined': False
            }
        
        left_orig = landmarks[11]
        right_orig = landmarks[12]
        
        return {
            'left_shoulder': {
                'x': float(left_orig[0]),
                'y': float(left_orig[1]),
                'confidence': float(left_orig[2]),
                'source': 'mediapipe'
            },
            'right_shoulder': {
                'x': float(right_orig[0]),
                'y': float(right_orig[1]),
                'confidence': float(right_orig[2]),
                'source': 'mediapipe'
            },
            'refinement_quality': 0.0,
            'is_refined': False
        }
    
    def apply_refined_shoulders_to_landmarks(self, landmarks: np.ndarray,
                                            refined_shoulders: Dict) -> np.ndarray:
        """
        Apply refined shoulder landmarks back to the full landmark array
        
        Args:
            landmarks: Original MediaPipe landmarks
            refined_shoulders: Output from refine_shoulder_landmarks()
            
        Returns:
            Updated landmarks with refined shoulder points
        """
        if landmarks is None or not refined_shoulders.get('is_refined'):
            return landmarks
        
        landmarks_copy = landmarks.copy()
        
        # Update left shoulder (index 11)
        left = refined_shoulders['left_shoulder']
        landmarks_copy[11] = [left['x'], left['y'], left['confidence']]
        
        # Update right shoulder (index 12)
        right = refined_shoulders['right_shoulder']
        landmarks_copy[12] = [right['x'], right['y'], right['confidence']]
        
        return landmarks_copy
    
    def get_shoulder_width(self, refined_shoulders: Dict) -> float:
        """
        Get shoulder width from refined shoulder points
        
        Args:
            refined_shoulders: Output from refine_shoulder_landmarks()
            
        Returns:
            Shoulder width in pixels
        """
        left_x = refined_shoulders['left_shoulder']['x']
        right_x = refined_shoulders['right_shoulder']['x']
        
        return abs(right_x - left_x)
    
    def get_shoulder_midpoint(self, refined_shoulders: Dict) -> Tuple[float, float]:
        """
        Get the midpoint between refined shoulder points
        
        Args:
            refined_shoulders: Output from refine_shoulder_landmarks()
            
        Returns:
            (x, y) tuple of shoulder midpoint
        """
        left_x = refined_shoulders['left_shoulder']['x']
        left_y = refined_shoulders['left_shoulder']['y']
        right_x = refined_shoulders['right_shoulder']['x']
        right_y = refined_shoulders['right_shoulder']['y']
        
        mid_x = (left_x + right_x) / 2
        mid_y = (left_y + right_y) / 2
        
        return (mid_x, mid_y)
    
    # ====== HYBRID VISION APPROACH: BODY EDGE EXTRACTION FROM SEGMENTATION ======
    
    def extract_body_contour(self, segmentation_mask: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract the main body contour from YOLOv8 segmentation mask.
        
        Args:
            segmentation_mask: Binary mask from YOLOv8 (255=person, 0=background)
            
        Returns:
            Contour points array or None if no valid contour found
        """
        if segmentation_mask is None or segmentation_mask.size == 0:
            return None
        
        try:
            # Find contours in the mask
            contours, _ = cv2.findContours(
                segmentation_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                return None
            
            # Get the largest contour (main body)
            largest_contour = max(contours, key=cv2.contourArea)
            contour_area = cv2.contourArea(largest_contour)
            
            if contour_area < self.min_valid_contour_area:
                return None
            
            # Smooth the contour
            epsilon = 0.02 * cv2.arcLength(largest_contour, True)
            smoothed_contour = cv2.approxPolyDP(largest_contour, epsilon, True)
            
            return smoothed_contour
        
        except Exception as e:
            print(f"Error extracting body contour: {e}")
            return None
    
    def extract_body_edge_keypoints(
        self,
        mask: np.ndarray,
        mediapipe_landmarks: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Extract body edge keypoints (shoulder, waist, hip) from body mask.
        
        Args:
            mask: Binary mask from YOLOv8 (255=person, 0=background)
            mediapipe_landmarks: Optional MediaPipe landmarks for height reference
            
        Returns:
            Dictionary with edge points and height info
        """
        if mask is None or mask.size == 0:
            return self._create_empty_edge_points()
            
        # Extract contour first
        contour = self.extract_body_contour(mask)
        if contour is None or len(contour) < 4:
            return self._create_empty_edge_points()
            
        image_height, image_width = mask.shape[:2]
        
        try:
            # Flatten contour for easier processing
            contour_points = contour.reshape(-1, 2)
            
            # Additional height info: head-to-toe height for scaling
            # Use top-most (min y) and bottom-most (max y) points from contour
            contour_y_min = contour_points[:, 1].min()
            contour_y_max = contour_points[:, 1].max()
            height_px = contour_y_max - contour_y_min
            
            # Determine reference heights
            if mediapipe_landmarks is not None and len(mediapipe_landmarks) > 24:
                # Use MediaPipe landmarks for height guidance
                # Use average of left (11) and right (12) shoulder height
                left_shoulder_y = mediapipe_landmarks[11][1]
                right_shoulder_y = mediapipe_landmarks[12][1]
                shoulder_height = (left_shoulder_y + right_shoulder_y) / 2
                
                right_hip_y = mediapipe_landmarks[24][1]      # Right hip
                hip_height = right_hip_y
                waist_height = shoulder_height + (hip_height - shoulder_height) * 0.5
            else:
                # Divide body into thirds
                contour_y_min = contour_points[:, 1].min()
                contour_y_max = contour_points[:, 1].max()
                
                shoulder_height = contour_y_min + (contour_y_max - contour_y_min) * 0.2
                waist_height = contour_y_min + (contour_y_max - contour_y_min) * 0.5
                hip_height = contour_y_min + (contour_y_max - contour_y_min) * 0.8
            
            # Extract left-most and right-most points at each height level
            shoulder_left, shoulder_right = self._get_extreme_points_at_height(
                contour_points, shoulder_height, self.body_edge_tolerance
            )
            waist_left, waist_right = self._get_extreme_points_at_height(
                contour_points, waist_height, self.body_edge_tolerance
            )
            hip_left, hip_right = self._get_extreme_points_at_height(
                contour_points, hip_height, self.body_edge_tolerance
            )
            
            return {
                'shoulder_left': shoulder_left,
                'shoulder_right': shoulder_right,
                'waist_left': waist_left,
                'waist_right': waist_right,
                'hip_left': hip_left,
                'hip_right': hip_right,
                'shoulder_height': shoulder_height,
                'waist_height': waist_height,
                'hip_height': hip_height,
                'height_px': height_px,
                'contours': [contour],
                'is_valid': True
            }
        
        except Exception as e:
            print(f"Error extracting edge reference points: {e}")
            return self._create_empty_edge_points()
    
    def _get_extreme_points_at_height(
        self,
        contour_points: np.ndarray,
        target_height: float,
        tolerance: float
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get left-most and right-most points at a specific height (y-coordinate).
        
        Args:
            contour_points: Flattened contour points
            target_height: Target y-coordinate
            tolerance: Tolerance range for finding points
            
        Returns:
            Tuple of (left_point, right_point) or ((0,0), (0,0)) if not found
        """
        # Find points within tolerance of target height
        height_mask = np.abs(contour_points[:, 1] - target_height) <= tolerance
        points_at_height = contour_points[height_mask]
        
        if len(points_at_height) < 2:
            # If no points within tolerance, find closest
            height_distances = np.abs(contour_points[:, 1] - target_height)
            closest_idx = np.argsort(height_distances)[:2]
            if len(closest_idx) >= 2:
                points_at_height = contour_points[closest_idx]
            else:
                return (0.0, 0.0), (0.0, 0.0)
        
        # Get left-most (minimum x) and right-most (maximum x)
        left_point = tuple(points_at_height[np.argmin(points_at_height[:, 0])])
        right_point = tuple(points_at_height[np.argmax(points_at_height[:, 0])])
        
        return (float(left_point[0]), float(left_point[1])), (float(right_point[0]), float(right_point[1]))
    
    def _create_empty_edge_points(self) -> Dict:
        """Create an empty edge points dictionary"""
        return {
            'shoulder_left': (0.0, 0.0),
            'shoulder_right': (0.0, 0.0),
            'waist_left': (0.0, 0.0),
            'waist_right': (0.0, 0.0),
            'hip_left': (0.0, 0.0),
            'hip_right': (0.0, 0.0),
            'shoulder_height': 0.0,
            'waist_height': 0.0,
            'hip_height': 0.0,
            'is_valid': False
        }
    
    def detect_face_landmarks(self, image: np.ndarray) -> Optional[List]:
        """
        Detect facial landmarks using MediaPipe Face Mesh.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            List of facial landmarks or None if no face detected
        """
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)
            
            if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
                face_landmarks = results.multi_face_landmarks[0]
                landmarks_list = []
                
                for landmark in face_landmarks.landmark:
                    landmarks_list.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'presence': landmark.presence if hasattr(landmark, 'presence') else 1.0
                    })
                
                return landmarks_list
            
            return None
        
        except Exception as e:
            print(f"Error detecting face landmarks: {e}")
            return None
    
    
    def cleanup(self):
        """Release resources"""
        self.pose.close()
        self.face_mesh.close()

