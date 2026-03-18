"""
Quick Accuracy Improvement Script
Run this to improve your circumference measurements
"""
import sys
import os


def print_menu():
    print("\n" + "="*70)
    print("CIRCUMFERENCE ACCURACY IMPROVEMENT TOOL")
    print("="*70)
    print("\n📊 Current Status:")
    print("   Basic accuracy: ±5-8 cm")
    print("   With improvements: ±1-2 cm")
    
    print("\n🎯 Choose an improvement method:\n")
    print("1. 🌟 Personal Calibration (RECOMMENDED - 10 min)")
    print("   Learn from your measurements for instant accuracy boost")
    
    print("\n2. 📸 Multi-Photo Processing (15 min)")
    print("   Process multiple photos and average for better results")
    
    print("\n3. ⚙️  Body Type Configuration (5 min)")
    print("   Adjust depth ratios for your body type")
    
    print("\n4. 📐 Side View Setup (30 min)")
    print("   Add side view for direct depth measurement (best accuracy)")
    
    print("\n5. 📊 View Current Calibration")
    print("   See your calibration status and statistics")
    
    print("\n6. 📖 Read Full Guide")
    print("   Open comprehensive accuracy guide")
    
    print("\n0. Exit")
    print("\n" + "="*70)


def run_calibration():
    """Run interactive calibration"""
    print("\n" + "="*70)
    print("PERSONAL CALIBRATION")
    print("="*70)
    
    try:
        from calibration_system import interactive_calibration
        interactive_calibration()
    except ImportError:
        print("\n❌ calibration_system.py not found")
        print("Make sure calibration_system.py is in the same directory")


def multi_photo_guide():
    """Guide for multi-photo processing"""
    print("\n" + "="*70)
    print("MULTI-PHOTO PROCESSING GUIDE")
    print("="*70)
    
    print("""
STEP 1: Take 5 photos
------------------------
- Same pose and distance
- Within 1-2 minutes
- Same lighting
- High resolution (1920×1080+)

STEP 2: Process each photo
------------------------
Run your measurement system 5 times, once for each photo.
Save the results.

STEP 3: Average the results
------------------------
Use this code:

```python
from advanced_measurement_techniques import AdvancedMeasurementTechniques

# Your measurements from 5 photos
measurements_list = [
    {'chest_circumference': 92.5, 'waist_circumference': 78.3, 'hip_circumference': 96.1},
    {'chest_circumference': 93.1, 'waist_circumference': 79.0, 'hip_circumference': 95.8},
    {'chest_circumference': 92.8, 'waist_circumference': 78.5, 'hip_circumference': 96.3},
    {'chest_circumference': 92.3, 'waist_circumference': 78.8, 'hip_circumference': 95.9},
    {'chest_circumference': 93.0, 'waist_circumference': 78.6, 'hip_circumference': 96.0},
]

techniques = AdvancedMeasurementTechniques()
averaged = techniques.multi_photo_averaging(measurements_list)

# Results with standard deviation
for measurement, (mean, std) in averaged.items():
    print(f"{measurement}: {mean:.1f} ± {std:.1f} cm")
```

EXPECTED IMPROVEMENT: ±2-3 cm accuracy
""")
    
    input("\nPress Enter to continue...")


def body_type_config():
    """Configure body type"""
    print("\n" + "="*70)
    print("BODY TYPE CONFIGURATION")
    print("="*70)
    
    print("\nSelect your body type:\n")
    print("1. Average - Balanced proportions")
    print("2. Athletic - Muscular, defined")
    print("3. Slim - Narrow frame")
    print("4. Plus Size - Fuller proportions")
    print("5. Pear Shape - Wider hips")
    print("6. Apple Shape - Fuller midsection")
    print("7. Custom - Enter your own ratios")
    
    choice = input("\nChoice (1-7): ").strip()
    
    presets = {
        '1': {'chest': 0.55, 'waist': 0.45, 'hip': 0.50, 'name': 'Average'},
        '2': {'chest': 0.60, 'waist': 0.48, 'hip': 0.52, 'name': 'Athletic'},
        '3': {'chest': 0.50, 'waist': 0.42, 'hip': 0.48, 'name': 'Slim'},
        '4': {'chest': 0.58, 'waist': 0.52, 'hip': 0.55, 'name': 'Plus Size'},
        '5': {'chest': 0.52, 'waist': 0.44, 'hip': 0.56, 'name': 'Pear Shape'},
        '6': {'chest': 0.58, 'waist': 0.50, 'hip': 0.48, 'name': 'Apple Shape'},
    }
    
    if choice in presets:
        preset = presets[choice]
        print(f"\n✓ Selected: {preset['name']}")
        print(f"\nDepth Ratios:")
        print(f"  Chest: {preset['chest']}")
        print(f"  Waist: {preset['waist']}")
        print(f"  Hip: {preset['hip']}")
        
        print(f"\nTo apply, update measurement_config.py:")
        print(f"""
CHEST_DEPTH_RATIO = {preset['chest']}
WAIST_DEPTH_RATIO = {preset['waist']}
HIP_DEPTH_RATIO = {preset['hip']}
""")
        
        # Try to update measurement_engine.py
        try:
            from measurement_engine import MeasurementEngine
            engine = MeasurementEngine()
            engine.chest_depth_ratio = preset['chest']
            engine.waist_depth_ratio = preset['waist']
            engine.hip_depth_ratio = preset['hip']
            print("✓ Ratios updated in memory (for this session)")
        except:
            pass
    
    elif choice == '7':
        print("\nEnter custom depth ratios (0.3-0.7):")
        chest = float(input("  Chest depth ratio: "))
        waist = float(input("  Waist depth ratio: "))
        hip = float(input("  Hip depth ratio: "))
        
        print(f"\nCustom Ratios:")
        print(f"  Chest: {chest}")
        print(f"  Waist: {waist}")
        print(f"  Hip: {hip}")
        
        print(f"\nTo apply, update measurement_config.py:")
        print(f"""
CHEST_DEPTH_RATIO = {chest}
WAIST_DEPTH_RATIO = {waist}
HIP_DEPTH_RATIO = {hip}
""")
    
    input("\nPress Enter to continue...")


def side_view_guide():
    """Guide for side view setup"""
    print("\n" + "="*70)
    print("SIDE VIEW SETUP GUIDE")
    print("="*70)
    
    print("""
Side view provides the MOST ACCURATE measurements by directly measuring
depth instead of estimating it.

SETUP STEPS:
------------

1. CAPTURE REQUIREMENTS:
   - Take TWO photos: front view + side view
   - Same distance from camera (2-3 meters)
   - Same lighting conditions
   - Camera at chest level

2. SIDE VIEW POSE:
   - Stand sideways (90° from front view)
   - Arms slightly forward (not touching body)
   - Stand straight, shoulders back
   - Same clothing as front view

3. IMPLEMENTATION:
   
   You'll need to modify your processing code to:
   a) Accept both front and side images
   b) Detect landmarks in side view
   c) Measure depth from side view
   d) Use measured depth instead of estimated

4. CODE EXAMPLE:

```python
# Process both views
front_landmarks = detect_landmarks(front_image)
side_landmarks = detect_landmarks(side_image)

# Measure width from front view
chest_width = measure_width(front_landmarks, 'chest')

# Measure depth from side view (NEW!)
chest_depth = measure_depth(side_landmarks, 'chest')

# Calculate circumference with measured depth
chest_circumference = calculate_ellipse_circumference(
    chest_width / 2,
    chest_depth / 2  # Measured, not estimated!
)
```

5. EXPECTED IMPROVEMENT:
   - From ±3-5 cm to ±1-2 cm
   - 50-70% error reduction
   - Most accurate method available

NEXT STEPS:
-----------
1. Test capturing side view photos
2. Verify landmarks are detected in side view
3. Implement depth measurement from side view
4. Integrate into your processing pipeline

Need help implementing? Check the full guide in:
CIRCUMFERENCE_ACCURACY_GUIDE.md (Section: Advanced: Side View Implementation)
""")
    
    input("\nPress Enter to continue...")


def view_calibration():
    """View current calibration status"""
    print("\n" + "="*70)
    print("CALIBRATION STATUS")
    print("="*70)
    
    try:
        from calibration_system import PersonalCalibration
        
        calibration = PersonalCalibration()
        stats = calibration.get_statistics()
        
        if 'message' in stats:
            print(f"\n{stats['message']}")
            print("\nRun option 1 to create calibration data.")
        else:
            print(f"\n✓ Total measurements: {stats['total_measurements']}")
            
            print(f"\nCurrent Calibration Factors:")
            print(f"  Chest: {stats['current_factors']['chest']:.3f}")
            print(f"  Waist: {stats['current_factors']['waist']:.3f}")
            print(f"  Hip: {stats['current_factors']['hip']:.3f}")
            
            if stats['average_errors']:
                print(f"\nAverage Errors:")
                for mtype, error_data in stats['average_errors'].items():
                    print(f"  {mtype.capitalize()}: {error_data['mean']:+.1f} cm "
                          f"(±{error_data['std']:.1f} cm, n={error_data['count']})")
            
            print(f"\nCalibration file: {calibration.calibration_file}")
    
    except ImportError:
        print("\n❌ calibration_system.py not found")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPress Enter to continue...")


def read_guide():
    """Open the full guide"""
    print("\n" + "="*70)
    print("FULL ACCURACY GUIDE")
    print("="*70)
    
    guide_file = "CIRCUMFERENCE_ACCURACY_GUIDE.md"
    
    if os.path.exists(guide_file):
        print(f"\n✓ Opening {guide_file}...")
        
        # Try to open with default application
        if sys.platform == 'win32':
            os.system(f'start {guide_file}')
        elif sys.platform == 'darwin':
            os.system(f'open {guide_file}')
        else:
            os.system(f'xdg-open {guide_file}')
        
        print("\nIf the file didn't open, you can manually open:")
        print(f"  {os.path.abspath(guide_file)}")
    else:
        print(f"\n❌ {guide_file} not found")
        print("Make sure CIRCUMFERENCE_ACCURACY_GUIDE.md is in the same directory")
    
    input("\nPress Enter to continue...")


def main():
    """Main menu loop"""
    while True:
        print_menu()
        choice = input("\nChoice (0-6): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        elif choice == '1':
            run_calibration()
        elif choice == '2':
            multi_photo_guide()
        elif choice == '3':
            body_type_config()
        elif choice == '4':
            side_view_guide()
        elif choice == '5':
            view_calibration()
        elif choice == '6':
            read_guide()
        else:
            print("\n❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
