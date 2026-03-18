"""
Personal Calibration System
Learns from user measurements to improve accuracy over time
"""
import json
import os
from typing import Dict, Tuple
import numpy as np


class PersonalCalibration:
    """Stores and applies personal calibration data"""
    
    def __init__(self, calibration_file='user_calibration.json'):
        self.calibration_file = calibration_file
        self.calibration_data = self.load_calibration()
    
    def load_calibration(self) -> Dict:
        """Load calibration data from file"""
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file, 'r') as f:
                return json.load(f)
        return {
            'chest_factor': 1.0,
            'waist_factor': 1.0,
            'hip_factor': 1.0,
            'chest_depth_ratio': 0.55,
            'waist_depth_ratio': 0.45,
            'hip_depth_ratio': 0.50,
            'measurements_count': 0,
            'history': []
        }
    
    def save_calibration(self):
        """Save calibration data to file"""
        with open(self.calibration_file, 'w') as f:
            json.dump(self.calibration_data, f, indent=2)
    
    def add_measurement_feedback(self, 
                                 measurement_type: str,
                                 system_value: float,
                                 actual_value: float):
        """
        Add user feedback to improve calibration
        
        Args:
            measurement_type: 'chest', 'waist', or 'hip'
            system_value: What the system measured
            actual_value: What the user measured with tape
        """
        # Calculate error
        error_ratio = actual_value / system_value
        
        # Update factor with exponential moving average
        factor_key = f'{measurement_type}_factor'
        alpha = 0.3  # Learning rate
        
        current_factor = self.calibration_data.get(factor_key, 1.0)
        new_factor = alpha * error_ratio + (1 - alpha) * current_factor
        
        self.calibration_data[factor_key] = new_factor
        self.calibration_data['measurements_count'] += 1
        
        # Store in history
        self.calibration_data['history'].append({
            'type': measurement_type,
            'system': system_value,
            'actual': actual_value,
            'error': actual_value - system_value,
            'error_percent': ((actual_value - system_value) / actual_value) * 100,
            'factor': new_factor
        })
        
        # Keep only last 20 measurements
        if len(self.calibration_data['history']) > 20:
            self.calibration_data['history'] = self.calibration_data['history'][-20:]
        
        self.save_calibration()
        
        print(f"\n✓ Calibration updated for {measurement_type}")
        print(f"  System: {system_value:.1f} cm")
        print(f"  Actual: {actual_value:.1f} cm")
        print(f"  Error: {actual_value - system_value:+.1f} cm ({((actual_value - system_value) / actual_value) * 100:+.1f}%)")
        print(f"  New factor: {new_factor:.3f}")
    
    def apply_calibration(self, measurements: Dict[str, float]) -> Dict[str, float]:
        """Apply calibration factors to measurements"""
        calibrated = measurements.copy()
        
        if 'chest_circumference' in calibrated:
            calibrated['chest_circumference'] *= self.calibration_data['chest_factor']
        
        if 'waist_circumference' in calibrated:
            calibrated['waist_circumference'] *= self.calibration_data['waist_factor']
        
        if 'hip_circumference' in calibrated:
            calibrated['hip_circumference'] *= self.calibration_data['hip_factor']
        
        return calibrated
    
    def get_depth_ratios(self) -> Tuple[float, float, float]:
        """Get calibrated depth ratios"""
        return (
            self.calibration_data['chest_depth_ratio'],
            self.calibration_data['waist_depth_ratio'],
            self.calibration_data['hip_depth_ratio']
        )
    
    def update_depth_ratios(self, chest: float = None, waist: float = None, hip: float = None):
        """Manually update depth ratios"""
        if chest is not None:
            self.calibration_data['chest_depth_ratio'] = chest
        if waist is not None:
            self.calibration_data['waist_depth_ratio'] = waist
        if hip is not None:
            self.calibration_data['hip_depth_ratio'] = hip
        
        self.save_calibration()
    
    def get_statistics(self) -> Dict:
        """Get calibration statistics"""
        if not self.calibration_data['history']:
            return {'message': 'No calibration data yet'}
        
        history = self.calibration_data['history']
        
        # Calculate average errors by type
        errors_by_type = {}
        for entry in history:
            mtype = entry['type']
            if mtype not in errors_by_type:
                errors_by_type[mtype] = []
            errors_by_type[mtype].append(entry['error'])
        
        stats = {
            'total_measurements': len(history),
            'current_factors': {
                'chest': self.calibration_data['chest_factor'],
                'waist': self.calibration_data['waist_factor'],
                'hip': self.calibration_data['hip_factor']
            },
            'average_errors': {}
        }
        
        for mtype, errors in errors_by_type.items():
            stats['average_errors'][mtype] = {
                'mean': np.mean(errors),
                'std': np.std(errors),
                'count': len(errors)
            }
        
        return stats
    
    def reset_calibration(self):
        """Reset calibration to defaults"""
        self.calibration_data = {
            'chest_factor': 1.0,
            'waist_factor': 1.0,
            'hip_factor': 1.0,
            'chest_depth_ratio': 0.55,
            'waist_depth_ratio': 0.45,
            'hip_depth_ratio': 0.50,
            'measurements_count': 0,
            'history': []
        }
        self.save_calibration()
        print("✓ Calibration reset to defaults")


def interactive_calibration():
    """Interactive calibration tool"""
    print("\n" + "="*60)
    print("PERSONAL CALIBRATION SYSTEM")
    print("="*60)
    
    calibration = PersonalCalibration()
    
    print("\nThis tool helps improve accuracy by learning from your measurements.")
    print("\nYou'll need:")
    print("  1. A photo of yourself (front view)")
    print("  2. Actual measurements with a tape measure")
    
    print("\n" + "-"*60)
    print("STEP 1: Process your photo with the system")
    print("-"*60)
    print("Run the measurement system and note the results.")
    
    input("\nPress Enter when you have the system measurements...")
    
    print("\n" + "-"*60)
    print("STEP 2: Enter your actual measurements")
    print("-"*60)
    
    measurements = {}
    
    # Chest
    print("\nCHEST CIRCUMFERENCE:")
    system_chest = float(input("  System measured (cm): "))
    actual_chest = float(input("  Your tape measure (cm): "))
    calibration.add_measurement_feedback('chest', system_chest, actual_chest)
    
    # Waist
    print("\nWAIST CIRCUMFERENCE:")
    system_waist = float(input("  System measured (cm): "))
    actual_waist = float(input("  Your tape measure (cm): "))
    calibration.add_measurement_feedback('waist', system_waist, actual_waist)
    
    # Hip
    print("\nHIP CIRCUMFERENCE:")
    system_hip = float(input("  System measured (cm): "))
    actual_hip = float(input("  Your tape measure (cm): "))
    calibration.add_measurement_feedback('hip', system_hip, actual_hip)
    
    print("\n" + "="*60)
    print("CALIBRATION COMPLETE!")
    print("="*60)
    
    stats = calibration.get_statistics()
    print(f"\nCalibration factors:")
    print(f"  Chest: {stats['current_factors']['chest']:.3f}")
    print(f"  Waist: {stats['current_factors']['waist']:.3f}")
    print(f"  Hip: {stats['current_factors']['hip']:.3f}")
    
    print("\nThese factors will be automatically applied to future measurements.")
    print(f"Calibration saved to: {calibration.calibration_file}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_calibration()
    else:
        print("Personal Calibration System")
        print("\nUsage:")
        print("  python calibration_system.py interactive  - Run interactive calibration")
        print("\nOr import in your code:")
        print("  from calibration_system import PersonalCalibration")
        print("  calibration = PersonalCalibration()")
        print("  calibrated_measurements = calibration.apply_calibration(measurements)")
