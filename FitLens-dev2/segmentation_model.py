"""
Person Segmentation using YOLOv8
"""
import cv2
import numpy as np
from typing import Optional, Tuple

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Install with: pip install ultralytics")


class SegmentationModel:
    """Person segmentation using YOLOv8-seg"""
    
    def __init__(self, model_size: str = 'n'):
        """
        Initialize YOLOv8 segmentation model
        
        Args:
            model_size: Model size ('n', 's', 'm', 'l', 'x') - 'n' is fastest
        """
        self.model = None
        
        if YOLO_AVAILABLE:
            self._init_yolo(model_size)
        else:
            print("Warning: YOLOv8 not available, using fallback segmentation")
    
    def _init_yolo(self, model_size: str):
        """Initialize YOLOv8 segmentation model"""
        try:
            # Load pretrained YOLOv8-seg model
            model_name = f'yolov8{model_size}-seg.pt'
            print(f"Loading YOLOv8 segmentation model: {model_name}")
            self.model = YOLO(model_name)
            print("✓ YOLOv8 segmentation model loaded successfully")
        except Exception as e:
            print(f"Failed to initialize YOLOv8: {e}")
            self.model = None
    
    def segment_person(self, image: np.ndarray, conf_threshold: float = 0.5) -> Optional[np.ndarray]:
        """
        Segment person from image using YOLOv8
        
        Args:
            image: Input image (BGR)
            conf_threshold: Confidence threshold for detection
            
        Returns:
            Binary mask of person (255 for person, 0 for background), or None if not found
        """
        if self.model is not None:
            return self._segment_with_yolo(image, conf_threshold)
        else:
            return self._segment_fallback(image)
    
    def _segment_with_yolo(self, image: np.ndarray, conf_threshold: float) -> Optional[np.ndarray]:
        """Segment using YOLOv8"""
        try:
            # Run inference
            results = self.model(image, conf=conf_threshold, verbose=False)
            
            if len(results) == 0:
                return None
            
            result = results[0]
            
            # Check if masks are available
            if result.masks is None or len(result.masks) == 0:
                return None
            
            # Get class IDs (0 = person in COCO dataset)
            boxes = result.boxes
            class_ids = boxes.cls.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()
            
            # Filter for person class (class_id = 0)
            person_indices = np.where(class_ids == 0)[0]
            
            if len(person_indices) == 0:
                return None
            
            # Get the person with highest confidence
            person_confidences = confidences[person_indices]
            best_person_idx = person_indices[np.argmax(person_confidences)]
            
            # Get the mask for the best person
            mask_data = result.masks.data[best_person_idx].cpu().numpy()
            
            # Resize mask to original image size
            h, w = image.shape[:2]
            mask = cv2.resize(mask_data, (w, h), interpolation=cv2.INTER_LINEAR)
            
            # Convert to binary mask (0-255)
            mask = (mask > 0.5).astype(np.uint8) * 255
            
            return mask
            
        except Exception as e:
            print(f"YOLOv8 segmentation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _segment_fallback(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Fallback segmentation using simple background subtraction"""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define skin color range (simplified)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        # Create mask
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Morphological operations to clean up
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find largest contour
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            mask = np.zeros_like(mask)
            cv2.drawContours(mask, [largest_contour], -1, 255, -1)
            return mask
        
        return None
    
    def apply_mask(self, image: np.ndarray, mask: np.ndarray, 
                   background_mode: str = 'dim') -> np.ndarray:
        """
        Apply mask to image to isolate person
        
        Args:
            image: Input image (BGR)
            mask: Binary mask (255 for person, 0 for background)
            background_mode: 'dim', 'remove', or 'blur'
            
        Returns:
            Processed image with background modified
        """
        if mask is None:
            return image
        
        result = image.copy()
        
        # Ensure mask is single channel
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        # Create 3-channel mask
        mask_3ch = cv2.merge([mask, mask, mask])
        
        if background_mode == 'remove':
            # Set background to black
            result = cv2.bitwise_and(result, mask_3ch)
            
        elif background_mode == 'dim':
            # Dim the background
            background = cv2.bitwise_and(result, cv2.bitwise_not(mask_3ch))
            background = (background * 0.3).astype(np.uint8)
            foreground = cv2.bitwise_and(result, mask_3ch)
            result = cv2.add(foreground, background)
            
        elif background_mode == 'blur':
            # Blur the background
            blurred = cv2.GaussianBlur(result, (21, 21), 0)
            background = cv2.bitwise_and(blurred, cv2.bitwise_not(mask_3ch))
            foreground = cv2.bitwise_and(result, mask_3ch)
            result = cv2.add(foreground, background)
        
        return result
    
    def get_masked_region(self, image: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, tuple]:
        """
        Extract only the masked region from image
        
        Args:
            image: Input image (BGR)
            mask: Binary mask
            
        Returns:
            (cropped_image, bbox) where bbox is (x, y, w, h)
        """
        if mask is None:
            return image, (0, 0, image.shape[1], image.shape[0])
        
        # Find bounding box
        bbox = self.get_person_bbox(mask)
        if bbox is None:
            return image, (0, 0, image.shape[1], image.shape[0])
        
        x, y, w, h = bbox
        
        # Crop image and mask
        cropped_image = image[y:y+h, x:x+w].copy()
        cropped_mask = mask[y:y+h, x:x+w]
        
        # Apply mask to cropped region
        if len(cropped_mask.shape) == 2:
            cropped_mask = cv2.merge([cropped_mask, cropped_mask, cropped_mask])
        
        masked_region = cv2.bitwise_and(cropped_image, cropped_mask)
        
        return masked_region, bbox
    
    def get_person_bbox(self, mask: np.ndarray) -> Optional[tuple]:
        """Get bounding box of person from mask"""
        if mask is None:
            return None
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            return (x, y, w, h)
        
        return None
