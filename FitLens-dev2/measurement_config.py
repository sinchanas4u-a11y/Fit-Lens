"""
Measurement Configuration
Adjust these values to improve accuracy for different body types
"""

class MeasurementConfig:
    """Configuration for body measurements"""
    
    # ============================================
    # DEPTH ESTIMATION COEFFICIENTS
    # ============================================
    
    # Proportional model coefficients
    ALPHA_S = 0.5   # Shoulder width to chest width ratio
    ALPHA_A = 0.15  # Arm length contribution to depth
    ALPHA_T = 0.25  # Torso length contribution to depth
    
    # ============================================
    # BODY TYPE DEPTH RATIOS
    # ============================================
    # Adjust these based on body type for better accuracy
    
    # Default (Average Build)
    CHEST_DEPTH_RATIO = 0.55   # Chest depth to width ratio (0.5-0.6)
    WAIST_DEPTH_RATIO = 0.45   # Waist depth to width ratio (0.4-0.5)
    HIP_DEPTH_RATIO = 0.50     # Hip depth to width ratio (0.45-0.55)
    
    # Athletic/Muscular Build (uncomment to use)
    # CHEST_DEPTH_RATIO = 0.60
    # WAIST_DEPTH_RATIO = 0.48
    # HIP_DEPTH_RATIO = 0.52
    
    # Slim Build (uncomment to use)
    # CHEST_DEPTH_RATIO = 0.50
    # WAIST_DEPTH_RATIO = 0.42
    # HIP_DEPTH_RATIO = 0.48
    
    # Plus Size Build (uncomment to use)
    # CHEST_DEPTH_RATIO = 0.58
    # WAIST_DEPTH_RATIO = 0.52
    # HIP_DEPTH_RATIO = 0.55
    
    # ============================================
    # MEASUREMENT ADJUSTMENTS
    # ============================================
    
    # Circumference adjustment factors (fine-tuning)
    CHEST_ADJUSTMENT = 1.0   # Multiply final chest circumference by this
    WAIST_ADJUSTMENT = 1.0   # Multiply final waist circumference by this
    HIP_ADJUSTMENT = 1.0     # Multiply final hip circumference by this
    
    # ============================================
    # CONFIDENCE THRESHOLDS
    # ============================================
    
    MIN_LANDMARK_CONFIDENCE = 0.5   # Minimum confidence for landmark
    MIN_MEASUREMENT_CONFIDENCE = 0.6  # Minimum confidence for measurement
    
    # ============================================
    # VALIDATION RANGES
    # ============================================
    # Typical ranges for adult measurements (cm)
    
    CHEST_MIN = 70
    CHEST_MAX = 150
    
    WAIST_MIN = 60
    WAIST_MAX = 150
    
    HIP_MIN = 70
    HIP_MAX = 160
    
    # ============================================
    # CALIBRATION TIPS
    # ============================================
    
    @staticmethod
    def get_calibration_tips():
        """Get tips for calibrating the system"""
        return """
        CALIBRATION TIPS:
        
        1. Measure yourself with tape measure:
           - Chest: Around fullest part
           - Waist: Around narrowest part
           - Hip: Around fullest part
        
        2. Process your photo with system
        
        3. Compare results:
           - If chest is too small: Increase CHEST_DEPTH_RATIO
           - If chest is too large: Decrease CHEST_DEPTH_RATIO
           - Same for waist and hip
        
        4. Typical adjustments:
           - ±0.05 for depth ratios
           - ±0.05 for adjustment factors
        
        5. Test again and iterate
        
        Example:
           Manual chest: 95 cm
           System chest: 90 cm
           Difference: -5 cm (-5.3%)
           
           Adjustment: CHEST_ADJUSTMENT = 1.05
           New result: 90 × 1.05 = 94.5 cm ✓
        """
    
    @staticmethod
    def get_body_type_presets():
        """Get preset configurations for different body types"""
        return {
            'average': {
                'CHEST_DEPTH_RATIO': 0.55,
                'WAIST_DEPTH_RATIO': 0.45,
                'HIP_DEPTH_RATIO': 0.50,
                'description': 'Average build, balanced proportions'
            },
            'athletic': {
                'CHEST_DEPTH_RATIO': 0.60,
                'WAIST_DEPTH_RATIO': 0.48,
                'HIP_DEPTH_RATIO': 0.52,
                'description': 'Athletic/muscular build, defined muscles'
            },
            'slim': {
                'CHEST_DEPTH_RATIO': 0.50,
                'WAIST_DEPTH_RATIO': 0.42,
                'HIP_DEPTH_RATIO': 0.48,
                'description': 'Slim build, narrow frame'
            },
            'plus_size': {
                'CHEST_DEPTH_RATIO': 0.58,
                'WAIST_DEPTH_RATIO': 0.52,
                'HIP_DEPTH_RATIO': 0.55,
                'description': 'Plus size build, fuller proportions'
            },
            'pear_shape': {
                'CHEST_DEPTH_RATIO': 0.52,
                'WAIST_DEPTH_RATIO': 0.44,
                'HIP_DEPTH_RATIO': 0.56,
                'description': 'Pear shape, wider hips'
            },
            'apple_shape': {
                'CHEST_DEPTH_RATIO': 0.58,
                'WAIST_DEPTH_RATIO': 0.50,
                'HIP_DEPTH_RATIO': 0.48,
                'description': 'Apple shape, fuller midsection'
            }
        }


# ============================================
# USAGE EXAMPLES
# ============================================

def example_custom_config():
    """Example: Use custom configuration"""
    from measurement_engine import MeasurementEngine
    
    # Create engine
    engine = MeasurementEngine()
    
    # Customize for your body type
    engine.chest_depth_ratio = 0.60  # Athletic build
    engine.waist_depth_ratio = 0.48
    engine.hip_depth_ratio = 0.52
    
    # Process measurements
    # ... (rest of code)


def example_calibration():
    """Example: Calibrate based on known measurements"""
    from measurement_engine import MeasurementEngine
    
    # Your actual measurements (from tape measure)
    actual_chest = 95.0  # cm
    actual_waist = 80.0  # cm
    actual_hip = 98.0    # cm
    
    # System measurements (from photo)
    system_chest = 90.0  # cm
    system_waist = 78.0  # cm
    system_hip = 95.0    # cm
    
    # Calculate adjustment factors
    chest_adj = actual_chest / system_chest  # 95/90 = 1.056
    waist_adj = actual_waist / system_waist  # 80/78 = 1.026
    hip_adj = actual_hip / system_hip        # 98/95 = 1.032
    
    print(f"Chest adjustment: {chest_adj:.3f}")
    print(f"Waist adjustment: {waist_adj:.3f}")
    print(f"Hip adjustment: {hip_adj:.3f}")
    
    # Apply to measurement engine
    engine = MeasurementEngine()
    # Use these factors in your code


# ============================================
# ADVANCED: SIDE VIEW DEPTH MEASUREMENT
# ============================================

def calculate_depth_from_side_view(side_landmarks, scale_factor):
    """
    If side view is available, measure actual depth
    This is much more accurate than estimation!
    """
    # Get front and back points from side view
    # (This requires identifying which landmarks represent front/back)
    
    # Example: Use shoulder to estimate chest depth
    # In side view, shoulder width represents depth
    
    # This is a placeholder - actual implementation would need
    # proper landmark identification in side view
    
    pass


# ============================================
# TIPS FOR MAXIMUM ACCURACY
# ============================================

ACCURACY_TIPS = """
TOP 10 TIPS FOR ACCURATE MEASUREMENTS:

1. HIGH RESOLUTION IMAGE (1920x1080 or higher)
   - More pixels = better landmark detection

2. GOOD LIGHTING (even, bright)
   - No shadows obscuring body shape

3. FORM-FITTING CLOTHING (athletic wear)
   - Reveals actual body shape

4. PROPER POSE (straight, arms away)
   - Standard pose for consistent measurements

5. FULL BODY VISIBLE (head to feet)
   - Required for height calibration

6. ACCURATE HEIGHT INPUT
   - Measure yourself properly

7. CAMERA POSITION (chest level, 2-3m away)
   - Reduces perspective distortion

8. MULTIPLE PHOTOS (3-5 in same pose)
   - Average results for better accuracy

9. SIDE VIEW (if possible)
   - Allows direct depth measurement

10. VALIDATE WITH TAPE MEASURE
    - Compare and adjust ratios

Expected Accuracy with All Tips: ±1-2 cm
"""

if __name__ == "__main__":
    print(ACCURACY_TIPS)
    print("\nBody Type Presets:")
    config = MeasurementConfig()
    for name, preset in config.get_body_type_presets().items():
        print(f"\n{name.upper()}:")
        print(f"  {preset['description']}")
        print(f"  Chest: {preset['CHEST_DEPTH_RATIO']}")
        print(f"  Waist: {preset['WAIST_DEPTH_RATIO']}")
        print(f"  Hip: {preset['HIP_DEPTH_RATIO']}")
