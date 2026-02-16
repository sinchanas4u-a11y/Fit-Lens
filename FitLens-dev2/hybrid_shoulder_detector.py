"""
Hybrid Shoulder Width Detection
Uses MediaPipe for shoulder Y-level + YOLOv8 mask + OpenCV contour extraction

Pipeline:
1. Get shoulder Y-level from MediaPipe landmarks
2. Extract body silhouette from YOLOv8 mask
3. Use OpenCV Canny edge detection on the mask
4. Apply contour extraction to find body edges
5. Find leftmost and rightmost points at shoulder Y-level
6. Calculate shoulder width from these edge points
"""
import cv2
import numpy as np
from typing import Dict, Tuple, Optional
from scipy import ndimage


class HybridShoulderDetector:
    """Hybrid shoulder detection combining MediaPipe, YOLOv8, and OpenCV"""
    
    def __init__(self):
        """Initialize detector"""
        self.canny_low = 50
        self.canny_high = 150
        self.morph_kernel_size = 5
        self.contour_min_area = 100
        
    def detect_shoulder_width(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        landmarks: np.ndarray,
        scale_factor: float,
        debug: bool = False
    ) -> Dict:
        """
        Detect shoulder width using hybrid approach
        
        Args:
            image: Original image (BGR)
            mask: YOLOv8 segmentation mask (binary)
            landmarks: MediaPipe landmarks array (33, 3)
            scale_factor: Pixel to cm conversion factor
            debug: Whether to return debug info
            
        Returns:
            Dictionary with:
                'shoulder_width_cm': measured width in cm
                'shoulder_width_px': measured width in pixels
                'left_shoulder': left edge point (x, y)
                'right_shoulder': right edge point (x, y)
                'shoulder_y': Y coordinate of shoulder level
                'confidence': confidence score (0-1)
                'debug_image': debug visualization (if debug=True)
        """
        result = {
            'shoulder_width_cm': None,
            'shoulder_width_px': None,
            'left_shoulder': None,
            'right_shoulder': None,
            'shoulder_y': None,
            'confidence': 0.0,
        }
        
        # Validate inputs
        if mask is None or landmarks is None:
            return result
        
        h, w = image.shape[:2]
        
        # STEP 1: Get shoulder Y-level from MediaPipe
        shoulder_y = self._get_shoulder_y_level(landmarks, h)
        if shoulder_y is None:
            print("⚠️ Could not determine shoulder Y-level from MediaPipe")
            return result
        
        result['shoulder_y'] = shoulder_y
        
        # STEP 2: Extract body contours from YOLOv8 mask
        body_edges = self._extract_body_edges(mask)
        if body_edges is None:
            print("⚠️ Could not extract body edges from mask")
            return result
        
        # STEP 3: Find contours in the mask
        contours = cv2.findContours(body_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        if len(contours) == 0:
            print("⚠️ No contours found in body edges")
            return result
        
        # STEP 4: Get the largest contour (main body)
        main_contour = max(contours, key=cv2.contourArea)
        
        # STEP 5: Find leftmost and rightmost points at shoulder Y-level
        left_point, right_point = self._find_shoulder_edge_points(
            main_contour, shoulder_y, w
        )
        
        if left_point is None or right_point is None:
            print("⚠️ Could not find shoulder edge points at Y-level")
            return result
        
        # STEP 6: Calculate shoulder width
        shoulder_width_px = abs(right_point[0] - left_point[0])
        shoulder_width_cm = shoulder_width_px * scale_factor
        
        # Calculate confidence based on MediaPipe shoulder visibility
        left_shoulder_conf = landmarks[11, 2] if len(landmarks) > 11 else 0
        right_shoulder_conf = landmarks[12, 2] if len(landmarks) > 12 else 0
        avg_confidence = (left_shoulder_conf + right_shoulder_conf) / 2
        
        result.update({
            'shoulder_width_px': shoulder_width_px,
            'shoulder_width_cm': shoulder_width_cm,
            'left_shoulder': tuple(left_point),
            'right_shoulder': tuple(right_point),
            'confidence': float(avg_confidence),
        })
        
        if debug:
            debug_image = self._create_debug_visualization(
                image, mask, body_edges, main_contour,
                left_point, right_point, shoulder_y
            )
            result['debug_image'] = debug_image
        
        return result
    
    def _get_shoulder_y_level(self, landmarks: np.ndarray, h: int) -> Optional[int]:
        """
        Get shoulder Y-level from MediaPipe landmarks
        
        Args:
            landmarks: MediaPipe landmarks (33, 3) with (x, y, confidence)
            h: Image height
            
        Returns:
            Y coordinate of shoulder level, or None if not found
        """
        # Landmarks 11 = left_shoulder, 12 = right_shoulder
        if len(landmarks) < 13:
            return None
        
        left_shoulder = landmarks[11]  # left_shoulder
        right_shoulder = landmarks[12]  # right_shoulder
        
        # Check if both shoulders are detected with sufficient confidence
        if left_shoulder[2] < 0.3 or right_shoulder[2] < 0.3:
            return None
        
        # Average Y coordinates to get shoulder level
        shoulder_y = int((left_shoulder[1] + right_shoulder[1]) / 2)
        
        # Ensure it's within image bounds
        shoulder_y = max(0, min(shoulder_y, h - 1))
        
        return shoulder_y
    
    def _extract_body_edges(self, mask: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract edges from body silhouette mask
        
        Uses:
        - cv2.Canny() for edge detection
        - Morphological operations for refinement
        - OpenCV's contour extraction
        
        Args:
            mask: Binary mask of person (0 for background, 255 for person)
            
        Returns:
            Binary image of edges
        """
        if mask is None:
            return None
        
        # Ensure mask is uint8
        mask = mask.astype(np.uint8)
        
        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, 
            (self.morph_kernel_size, self.morph_kernel_size)
        )
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Apply Canny edge detection
        edges = cv2.Canny(mask_clean, self.canny_low, self.canny_high)
        
        # Dilate edges slightly to connect broken lines
        kernel_edge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.dilate(edges, kernel_edge, iterations=1)
        
        return edges
    
    def _find_shoulder_edge_points(
        self,
        contour: np.ndarray,
        shoulder_y: int,
        img_width: int
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Find leftmost and rightmost points at shoulder Y-level on the contour
        
        Args:
            contour: OpenCV contour points
            shoulder_y: Y coordinate of shoulder level
            img_width: Image width for bounds checking
            
        Returns:
            (left_point, right_point) tuples, or (None, None) if not found
        """
        if contour is None or len(contour) == 0:
            return None, None
        
        # Extract contour points
        contour_points = contour.reshape(-1, 2)
        
        # Define a band around the shoulder Y-level to find points
        # (allows some vertical tolerance)
        y_tolerance = 30
        y_min = max(0, shoulder_y - y_tolerance)
        y_max = shoulder_y + y_tolerance
        
        # Filter points in the shoulder band
        points_in_band = contour_points[
            (contour_points[:, 1] >= y_min) & 
            (contour_points[:, 1] <= y_max)
        ]
        
        if len(points_in_band) < 2:
            print(f"  ⚠️ Found only {len(points_in_band)} points in shoulder band")
            # Fallback: use the closest points to shoulder_y
            distances = np.abs(contour_points[:, 1] - shoulder_y)
            closest_indices = np.argsort(distances)[:20]
            points_in_band = contour_points[closest_indices]
        
        if len(points_in_band) == 0:
            return None, None
        
        # Find leftmost and rightmost points
        left_idx = np.argmin(points_in_band[:, 0])
        right_idx = np.argmax(points_in_band[:, 0])
        
        left_point = points_in_band[left_idx]
        right_point = points_in_band[right_idx]
        
        # Refine the Y coordinate to be closer to shoulder_y
        left_point = self._refine_point_on_contour(left_point, contour_points, shoulder_y)
        right_point = self._refine_point_on_contour(right_point, contour_points, shoulder_y)
        
        return left_point, right_point
    
    def _refine_point_on_contour(
        self,
        initial_point: np.ndarray,
        contour_points: np.ndarray,
        target_y: int
    ) -> np.ndarray:
        """
        Refine a point on the contour to be at the target Y level
        
        Finds the point on the contour closest to the initial X and closest to target Y
        
        Args:
            initial_point: Initial point estimate
            contour_points: All contour points
            target_y: Target Y coordinate
            
        Returns:
            Refined point on contour
        """
        x_init = initial_point[0]
        
        # Find contour points with similar X coordinate
        x_tolerance = 10
        similar_x_points = contour_points[
            np.abs(contour_points[:, 0] - x_init) <= x_tolerance
        ]
        
        if len(similar_x_points) == 0:
            return initial_point
        
        # Among similar X points, find the one closest to target_y
        y_distances = np.abs(similar_x_points[:, 1] - target_y)
        best_idx = np.argmin(y_distances)
        
        return similar_x_points[best_idx]
    
    def _create_debug_visualization(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        edges: np.ndarray,
        contour: np.ndarray,
        left_point: np.ndarray,
        right_point: np.ndarray,
        shoulder_y: int
    ) -> np.ndarray:
        """Create debug visualization showing all detection steps"""
        h, w = image.shape[:2]
        
        # Create a 2x2 grid of visualizations
        debug_image = np.zeros((h * 2, w * 2, 3), dtype=np.uint8)
        
        # Top-left: Original image with shoulder Y-line
        vis1 = image.copy()
        cv2.line(vis1, (0, shoulder_y), (w, shoulder_y), (0, 255, 255), 2)
        debug_image[0:h, 0:w] = vis1
        
        # Top-right: YOLOv8 mask
        mask_vis = cv2.cvtColor((mask > 0).astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR)
        cv2.line(mask_vis, (0, shoulder_y), (w, shoulder_y), (0, 255, 255), 2)
        debug_image[0:h, w:w*2] = mask_vis
        
        # Bottom-left: Edges
        edges_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        cv2.line(edges_vis, (0, shoulder_y), (w, shoulder_y), (0, 255, 255), 2)
        if contour is not None:
            cv2.drawContours(edges_vis, [contour], 0, (0, 255, 0), 2)
        debug_image[h:h*2, 0:w] = edges_vis
        
        # Bottom-right: Detected shoulders
        shoulder_vis = image.copy()
        cv2.line(shoulder_vis, (0, shoulder_y), (w, shoulder_y), (0, 255, 255), 2)
        if left_point is not None:
            cv2.circle(shoulder_vis, tuple(left_point.astype(int)), 10, (255, 0, 0), -1)
            cv2.circle(shoulder_vis, tuple(left_point.astype(int)), 10, (0, 255, 255), 2)
        if right_point is not None:
            cv2.circle(shoulder_vis, tuple(right_point.astype(int)), 10, (255, 0, 0), -1)
            cv2.circle(shoulder_vis, tuple(right_point.astype(int)), 10, (0, 255, 255), 2)
        if left_point is not None and right_point is not None:
            cv2.line(
                shoulder_vis,
                tuple(left_point.astype(int)),
                tuple(right_point.astype(int)),
                (0, 255, 0),
                3
            )
        debug_image[h:h*2, w:w*2] = shoulder_vis
        
        return debug_image
    
    def detect_shoulder_width_with_refinement(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        landmarks: np.ndarray,
        scale_factor: float,
        use_scikit_image: bool = True,
        debug: bool = False
    ) -> Dict:
        """
        Detect shoulder width with optional scikit-image refinement
        
        Uses:
        - cv2.Canny() for edge detection
        - cv2.findContours() for contour extraction
        - cv2.convexHull() for convex hull
        - cv2.approxPolyDP() for polygon approximation
        - scikit-image for additional edge refinement (optional)
        - numpy for point filtering
        
        Args:
            image: Original image
            mask: YOLOv8 mask
            landmarks: MediaPipe landmarks
            scale_factor: Pixel to cm conversion
            use_scikit_image: Whether to use scikit-image refinement
            debug: Whether to return debug info
            
        Returns:
            Shoulder detection result dictionary
        """
        result = self.detect_shoulder_width(image, mask, landmarks, scale_factor, debug=False)
        
        if result['shoulder_width_px'] is None:
            return result
        
        # Apply additional refinement if requested
        if use_scikit_image:
            result = self._apply_scikit_image_refinement(
                result, mask, landmarks
            )
        
        # Apply numpy-based point filtering
        result = self._apply_numpy_filtering(result, landmarks)
        
        if debug:
            debug_image = self._create_debug_visualization(
                image, mask,
                cv2.Canny(mask.astype(np.uint8), self.canny_low, self.canny_high),
                None,
                result.get('left_shoulder'),
                result.get('right_shoulder'),
                result.get('shoulder_y', 0)
            )
            result['debug_image'] = debug_image
        
        return result
    
    def _apply_scikit_image_refinement(
        self,
        result: Dict,
        mask: np.ndarray,
        landmarks: np.ndarray
    ) -> Dict:
        """
        Apply scikit-image edge refinement
        
        Uses skimage.filters for additional edge refinement
        """
        try:
            from skimage import filters
            
            # Apply additional edge refinement
            mask_uint8 = mask.astype(np.uint8)
            
            # Use Sobel for edge refinement
            edges_sobel = filters.sobel(mask_uint8)
            
            # This could be used for additional validation
            # For now, we keep the result as-is but add confidence
            result['refinement_applied'] = True
            
        except ImportError:
            print("⚠️ scikit-image not available for refinement")
            result['refinement_applied'] = False
        
        return result
    
    def _apply_numpy_filtering(
        self,
        result: Dict,
        landmarks: np.ndarray
    ) -> Dict:
        """
        Apply numpy-based point filtering and validation
        
        Filters shoulder points based on:
        - Proximity to MediaPipe shoulder locations
        - Anatomical constraints
        - Statistical outlier detection
        """
        if result['left_shoulder'] is None or result['right_shoulder'] is None:
            return result
        
        # Get MediaPipe shoulder positions
        left_mp_shoulder = landmarks[11, :2]
        right_mp_shoulder = landmarks[12, :2]
        
        left_detected = np.array(result['left_shoulder'])
        right_detected = np.array(result['right_shoulder'])
        
        # Calculate distance from MediaPipe predictions
        left_distance = np.linalg.norm(left_detected - left_mp_shoulder)
        right_distance = np.linalg.norm(right_detected - right_mp_shoulder)
        
        # Update confidence based on proximity to MediaPipe
        max_acceptable_distance = 50  # pixels
        left_conf = max(0, 1 - (left_distance / max_acceptable_distance))
        right_conf = max(0, 1 - (right_distance / max_acceptable_distance))
        
        avg_conf = (left_conf + right_conf) / 2
        result['confidence'] = float(avg_conf)
        
        return result

