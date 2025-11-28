"""
Reference Object Detection Module
Detects and measures reference objects for scale calibration
"""
import cv2
import numpy as np
from typing import Optional, Tuple


class ReferenceDetector:
    """Detect reference objects in images"""
    
    def __init__(self):
        """Initialize reference detector"""
        self.min_area = 1000  # Minimum contour area
        self.max_area = 500000  # Maximum contour area
    
    def detect_reference(self, image: np.ndarray, axis: str = 'height') -> Optional[float]:
        """
        Detect reference object and return pixel measurement
        
        Args:
            image: Input image
            axis: 'width' or 'height' - which dimension to measure
            
        Returns:
            Pixel measurement of reference object, or None if not found
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest contour within size range
        valid_contours = [
            c for c in contours 
            if self.min_area < cv2.contourArea(c) < self.max_area
        ]
        
        if not valid_contours:
            return None
        
        # Get largest valid contour
        largest_contour = max(valid_contours, key=cv2.contourArea)
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Return requested dimension
        if axis == 'width':
            return float(w)
        else:
            return float(h)
    
    def detect_with_visualization(self, image: np.ndarray, axis: str = 'height') -> Tuple[Optional[float], np.ndarray]:
        """
        Detect reference and return visualization
        
        Returns:
            (pixel_measurement, annotated_image)
        """
        result_img = image.copy()
        
        # Detect reference
        measurement = self.detect_reference(image, axis)
        
        if measurement:
            # Find and draw the contour
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            valid_contours = [
                c for c in contours 
                if self.min_area < cv2.contourArea(c) < self.max_area
            ]
            
            if valid_contours:
                largest_contour = max(valid_contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Draw bounding box
                cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 3)
                
                # Draw measurement
                text = f"{axis}: {measurement:.1f}px"
                cv2.putText(result_img, text, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return measurement, result_img
