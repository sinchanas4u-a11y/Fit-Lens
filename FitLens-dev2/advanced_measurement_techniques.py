"""
Advanced Measurement Techniques
Additional methods to improve circumference accuracy
"""
import numpy as np
from typing import Dict, List, Tuple
import cv2


class AdvancedMeasurementTechniques:
    """Advanced techniques for more accurate measurements"""
    
    @staticmethod
    def multi_photo_averaging(measurements_list: List[Dict[str, float]]) -> Dict[str, Tuple[float, float]]:
        """
        Average measurements from multiple photos
        
        Args:
            measurements_list: List of measurement dictionaries from different photos
            
        Returns:
            Dictionary with (mean, std_dev) for each measurement
        """
        if not measurements_list:
            return {}
        
        # Collect all measurements by key
        by_key = {}
        for measurements in measurements_list:
            for key, value in measurements.items():
                if key not in by_key:
                    by_key[key] = []
                by_key[key].append(value)
        
        # Calculate mean and std dev
        result = {}
        for key, values in by_key.items():
            result[key] = (np.mean(values), np.std(values))
        
        return result
    
    @staticmethod
    def contour_based_width(mask: np.ndarray, y_position: int, scale_factor: float) -> float:
        """
        Measure width at specific height using contour analysis
        More accurate than landmark-based width
        
        Args:
            mask: Binary segmentation mask
            y_position: Y coordinate (height) to measure at
            scale_factor: Pixels to cm conversion
            
        Returns:
            Width in cm
        """
        # Get the row at y_position
        row = mask[y_position, :]
        
        # Find left and right edges
        nonzero = np.where(row > 0)[0]
        
        if len(nonzero) == 0:
            return 0.0
        
        left_edge = nonzero[0]
        right_edge = nonzero[-1]
        
        width_pixels = right_edge - left_edge
        width_cm = width_pixels * scale_factor
        
        return width_cm
    
    @staticmethod
    def measure_circumference_at_height(mask: np.ndarray, 
                                       y_position: int, 
                                       scale_factor: float,
                                       depth_ratio: float = 0.5) -> float:
        """
        Measure circumference at specific height using contour
        
        Args:
            mask: Binary segmentation mask
            y_position: Y coordinate to measure at
            scale_factor: Pixels to cm conversion
            depth_ratio: Depth to width ratio
            
        Returns:
            Circumference in cm
        """
        width = AdvancedMeasurementTechniques.contour_based_width(
            mask, y_position, scale_factor
        )
        
        if width == 0:
            return 0.0
        
        depth = width * depth_ratio
        
        # Ramanujan's ellipse approximation
        a = width / 2
        b = depth / 2
        h = ((a - b) ** 2) / ((a + b) ** 2)
        circumference = np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(4 - 3 * h)))
        
        return circumference
    
    @staticmethod
    def adaptive_depth_ratio(width: float, 
                            shoulder_width: float,
                            hip_width: float,
                            measurement_type: str) -> float:
        """
        Calculate adaptive depth ratio based on body proportions
        
        Args:
            width: Width at measurement point
            shoulder_width: Shoulder width
            hip_width: Hip width
            measurement_type: 'chest', 'waist', or 'hip'
            
        Returns:
            Adaptive depth ratio
        """
        # Calculate body shape indicator
        if shoulder_width > 0 and hip_width > 0:
            shape_ratio = shoulder_width / hip_width
        else:
            shape_ratio = 1.0
        
        # Base ratios
        base_ratios = {
            'chest': 0.55,
            'waist': 0.45,
            'hip': 0.50
        }
        
        base_ratio = base_ratios.get(measurement_type, 0.5)
        
        # Adjust based on body shape
        if shape_ratio > 1.1:  # Inverted triangle (broad shoulders)
            if measurement_type == 'chest':
                return base_ratio + 0.03
            elif measurement_type == 'waist':
                return base_ratio - 0.02
        elif shape_ratio < 0.9:  # Pear shape (wider hips)
            if measurement_type == 'hip':
                return base_ratio + 0.03
            elif measurement_type == 'waist':
                return base_ratio - 0.02
        
        return base_ratio
    
    @staticmethod
    def posture_correction(landmarks: np.ndarray) -> float:
        """
        Detect and correct for posture issues
        
        Args:
            landmarks: MediaPipe landmarks
            
        Returns:
            Correction factor (1.0 = perfect posture)
        """
        # Check shoulder alignment
        left_shoulder = landmarks[11]  # MediaPipe index
        right_shoulder = landmarks[12]
        
        # Calculate shoulder angle
        dy = right_shoulder[1] - left_shoulder[1]
        dx = right_shoulder[0] - left_shoulder[0]
        angle = np.abs(np.arctan2(dy, dx))
        
        # Ideal is 0 (horizontal)
        # Apply correction if shoulders are tilted
        if angle > 0.1:  # More than ~6 degrees
            correction = 1.0 + (angle * 0.5)  # Increase measurements slightly
            return min(correction, 1.1)  # Cap at 10% correction
        
        return 1.0
    
    @staticmethod
    def confidence_weighted_average(measurements: List[Tuple[float, float]]) -> float:
        """
        Calculate confidence-weighted average
        
        Args:
            measurements: List of (value, confidence) tuples
            
        Returns:
            Weighted average
        """
        if not measurements:
            return 0.0
        
        total_weight = sum(conf for _, conf in measurements)
        if total_weight == 0:
            return np.mean([val for val, _ in measurements])
        
        weighted_sum = sum(val * conf for val, conf in measurements)
        return weighted_sum / total_weight
    
    @staticmethod
    def outlier_removal(values: List[float], threshold: float = 2.0) -> List[float]:
        """
        Remove outliers using z-score method
        
        Args:
            values: List of measurements
            threshold: Z-score threshold (default 2.0 = 95% confidence)
            
        Returns:
            Filtered list without outliers
        """
        if len(values) < 3:
            return values
        
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return values
        
        filtered = []
        for val in values:
            z_score = abs((val - mean) / std)
            if z_score < threshold:
                filtered.append(val)
        
        return filtered if filtered else values
    
    @staticmethod
    def temporal_smoothing(current: float, 
                          previous: List[float], 
                          alpha: float = 0.3) -> float:
        """
        Smooth measurements over time (for video/live mode)
        
        Args:
            current: Current measurement
            previous: List of previous measurements
            alpha: Smoothing factor (0-1, higher = more responsive)
            
        Returns:
            Smoothed measurement
        """
        if not previous:
            return current
        
        # Exponential moving average
        prev_avg = np.mean(previous[-5:])  # Use last 5 measurements
        smoothed = alpha * current + (1 - alpha) * prev_avg
        
        return smoothed


class CircumferenceMeasurementV2:
    """Enhanced circumference measurement with multiple techniques"""
    
    def __init__(self):
        self.techniques = AdvancedMeasurementTechniques()
    
    def measure_with_multiple_methods(self,
                                      landmarks: np.ndarray,
                                      mask: np.ndarray,
                                      scale_factor: float,
                                      landmark_dict: Dict) -> Dict[str, Dict]:
        """
        Measure circumferences using multiple methods and combine
        
        Returns:
            Dictionary with measurements and confidence scores
        """
        results = {}
        
        # Method 1: Landmark-based (existing method)
        landmark_measurements = self._landmark_based_measurement(
            landmarks, landmark_dict, scale_factor
        )
        
        # Method 2: Contour-based (more accurate for width)
        if mask is not None:
            contour_measurements = self._contour_based_measurement(
                mask, landmarks, landmark_dict, scale_factor
            )
        else:
            contour_measurements = {}
        
        # Combine methods with weighting
        for measurement_type in ['chest', 'waist', 'hip']:
            methods = []
            
            # Add landmark method
            if f'{measurement_type}_circumference' in landmark_measurements:
                val, conf = landmark_measurements[f'{measurement_type}_circumference']
                methods.append((val, conf * 0.6))  # 60% weight
            
            # Add contour method
            if f'{measurement_type}_circumference' in contour_measurements:
                val, conf = contour_measurements[f'{measurement_type}_circumference']
                methods.append((val, conf * 0.8))  # 80% weight (more accurate)
            
            if methods:
                # Confidence-weighted average
                final_value = self.techniques.confidence_weighted_average(methods)
                final_confidence = np.mean([conf for _, conf in methods])
                
                results[f'{measurement_type}_circumference'] = {
                    'value': final_value,
                    'confidence': final_confidence,
                    'methods_used': len(methods)
                }
        
        return results
    
    def _landmark_based_measurement(self, landmarks, landmark_dict, scale_factor):
        """Existing landmark-based method"""
        # Implementation from existing measurement_engine.py
        return {}
    
    def _contour_based_measurement(self, mask, landmarks, landmark_dict, scale_factor):
        """New contour-based method"""
        measurements = {}
        
        # Find chest position (between shoulders and hips)
        if 'left_shoulder' in landmark_dict and 'left_hip' in landmark_dict:
            shoulder_y = int(landmark_dict['left_shoulder'][1])
            hip_y = int(landmark_dict['left_hip'][1])
            
            # Chest is ~30% down from shoulder to hip
            chest_y = int(shoulder_y + (hip_y - shoulder_y) * 0.3)
            
            # Measure chest
            chest_circ = self.techniques.measure_circumference_at_height(
                mask, chest_y, scale_factor, depth_ratio=0.55
            )
            
            if chest_circ > 0:
                measurements['chest_circumference'] = (chest_circ, 0.8)
            
            # Waist is ~70% down
            waist_y = int(shoulder_y + (hip_y - shoulder_y) * 0.7)
            waist_circ = self.techniques.measure_circumference_at_height(
                mask, waist_y, scale_factor, depth_ratio=0.45
            )
            
            if waist_circ > 0:
                measurements['waist_circumference'] = (waist_circ, 0.8)
            
            # Hip is at hip landmark
            hip_circ = self.techniques.measure_circumference_at_height(
                mask, hip_y, scale_factor, depth_ratio=0.50
            )
            
            if hip_circ > 0:
                measurements['hip_circumference'] = (hip_circ, 0.8)
        
        return measurements


# Example usage
if __name__ == "__main__":
    print("Advanced Measurement Techniques")
    print("\nKey improvements:")
    print("1. Multi-photo averaging - reduces random errors")
    print("2. Contour-based width - more accurate than landmarks")
    print("3. Adaptive depth ratios - adjusts for body shape")
    print("4. Posture correction - compensates for tilted pose")
    print("5. Confidence weighting - prioritizes reliable measurements")
    print("6. Outlier removal - filters bad measurements")
    print("7. Temporal smoothing - for video/live mode")
