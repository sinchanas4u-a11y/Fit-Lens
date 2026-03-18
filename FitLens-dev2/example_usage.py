"""
Example Usage: YOLOv8 + MediaPipe Body Measurement
Demonstrates how to use the system programmatically
"""
import cv2
import numpy as np
from process_images_yolo import ImageProcessor

def example_1_basic():
    """Example 1: Basic image processing"""
    print("\n" + "="*60)
    print("Example 1: Basic Image Processing")
    print("="*60)
    
    # Initialize processor
    processor = ImageProcessor(yolo_model_size='n')
    
    # Process image
    result = processor.process_single_image(
        'your_image.jpg',  # Replace with your image path
        save_output=True
    )
    
    if result['success']:
        print("\n✓ Processing successful!")
        print(f"  Detected {len(result['landmarks'])} landmarks")
        print(f"  Calculated {len(result['measurements'])} measurements")
        print(f"  Outputs saved to output/ folder")
    else:
        print(f"\n✗ Processing failed: {result.get('error', 'Unknown error')}")


def example_2_with_calibration():
    """Example 2: With height calibration"""
    print("\n" + "="*60)
    print("Example 2: With Height Calibration")
    print("="*60)
    
    processor = ImageProcessor(yolo_model_size='n')
    
    # Process with reference height
    result = processor.process_single_image(
        'your_image.jpg',
        reference_size_cm=170,  # Your height in cm
        save_output=True
    )
    
    if result['success']:
        print("\n✓ Processing successful!")
        print("\nMeasurements (calibrated):")
        
        # Print first 5 measurements
        for i, (name, data) in enumerate(result['measurements'].items()):
            if i >= 5:
                break
            if isinstance(data, dict):
                print(f"  {name}: {data['value_cm']:.1f} cm (confidence: {data['confidence']:.2f})")
            else:
                print(f"  {name}: {data:.1f} cm")


def example_3_multiple_images():
    """Example 3: Process multiple images"""
    print("\n" + "="*60)
    print("Example 3: Multiple Images")
    print("="*60)
    
    processor = ImageProcessor(yolo_model_size='n')
    
    # Process multiple images
    image_paths = [
        'front.jpg',
        'side.jpg',
        'back.jpg'
    ]
    
    results = processor.process_multiple_images(
        image_paths,
        reference_size_cm=170
    )
    
    # Print summary
    successful = sum(1 for r in results if r.get('success', False))
    print(f"\n✓ Processed {successful}/{len(image_paths)} images successfully")


def example_4_custom_segmentation():
    """Example 4: Custom segmentation and masking"""
    print("\n" + "="*60)
    print("Example 4: Custom Segmentation")
    print("="*60)
    
    from segmentation_model import SegmentationModel
    from landmark_detector import LandmarkDetector
    
    # Load image
    image = cv2.imread('your_image.jpg')
    if image is None:
        print("✗ Failed to load image")
        return
    
    # Initialize models
    seg_model = SegmentationModel(model_size='n')
    landmark_detector = LandmarkDetector()
    
    # Segment person
    print("\nSegmenting person...")
    mask = seg_model.segment_person(image, conf_threshold=0.5)
    
    if mask is None:
        print("✗ No person detected")
        return
    
    print("✓ Person segmented")
    
    # Try different background modes
    print("\nApplying different background modes...")
    
    # Mode 1: Remove background
    masked_remove = seg_model.apply_mask(image, mask, background_mode='remove')
    cv2.imwrite('output/example_remove_bg.png', masked_remove)
    print("  ✓ Saved: output/example_remove_bg.png")
    
    # Mode 2: Dim background
    masked_dim = seg_model.apply_mask(image, mask, background_mode='dim')
    cv2.imwrite('output/example_dim_bg.png', masked_dim)
    print("  ✓ Saved: output/example_dim_bg.png")
    
    # Mode 3: Blur background
    masked_blur = seg_model.apply_mask(image, mask, background_mode='blur')
    cv2.imwrite('output/example_blur_bg.png', masked_blur)
    print("  ✓ Saved: output/example_blur_bg.png")
    
    # Extract masked region
    masked_region, bbox = seg_model.get_masked_region(image, mask)
    x, y, w, h = bbox
    print(f"\n✓ Masked region: {w}x{h} at ({x}, {y})")
    cv2.imwrite('output/example_region.png', masked_region)
    print("  ✓ Saved: output/example_region.png")
    
    # Detect landmarks
    print("\nDetecting landmarks...")
    landmarks = landmark_detector.detect(image)
    
    if landmarks is not None:
        print(f"✓ Detected {len(landmarks)} landmarks")
        
        # Draw landmarks
        vis = landmark_detector.draw_landmarks(masked_dim.copy(), landmarks)
        cv2.imwrite('output/example_landmarks.png', vis)
        print("  ✓ Saved: output/example_landmarks.png")


def example_5_measurements_only():
    """Example 5: Get measurements without saving images"""
    print("\n" + "="*60)
    print("Example 5: Measurements Only")
    print("="*60)
    
    processor = ImageProcessor(yolo_model_size='n')
    
    # Process without saving
    result = processor.process_single_image(
        'your_image.jpg',
        reference_size_cm=170,
        save_output=False  # Don't save images
    )
    
    if result['success']:
        print("\n✓ Measurements calculated:")
        
        measurements = result['measurements']
        
        # Print all measurements
        for name, data in measurements.items():
            if isinstance(data, dict):
                value_cm = data['value_cm']
                confidence = data['confidence']
                print(f"  {name:.<30} {value_cm:>6.1f} cm (conf: {confidence:.2f})")
            else:
                print(f"  {name:.<30} {data:>6.1f} cm")


def example_6_batch_processing():
    """Example 6: Batch process multiple images"""
    print("\n" + "="*60)
    print("Example 6: Batch Processing")
    print("="*60)
    
    import os
    import glob
    
    processor = ImageProcessor(yolo_model_size='n')
    
    # Find all jpg images in a folder
    image_folder = 'images'  # Replace with your folder
    if not os.path.exists(image_folder):
        print(f"✗ Folder not found: {image_folder}")
        print("  Create a folder named 'images' and add your photos")
        return
    
    image_paths = glob.glob(os.path.join(image_folder, '*.jpg'))
    image_paths.extend(glob.glob(os.path.join(image_folder, '*.png')))
    
    if not image_paths:
        print(f"✗ No images found in {image_folder}")
        return
    
    print(f"\nFound {len(image_paths)} images")
    
    # Process all images
    results = processor.process_multiple_images(
        image_paths,
        reference_size_cm=170
    )
    
    # Save summary
    print("\n" + "="*60)
    print("Batch Processing Complete")
    print("="*60)
    
    successful = [r for r in results if r.get('success', False)]
    print(f"\nSuccessfully processed: {len(successful)}/{len(image_paths)} images")
    
    if successful:
        print("\nAverage measurements across all images:")
        
        # Calculate averages
        all_measurements = {}
        for result in successful:
            for name, data in result['measurements'].items():
                if isinstance(data, dict):
                    value = data['value_cm']
                else:
                    value = data
                
                if name not in all_measurements:
                    all_measurements[name] = []
                all_measurements[name].append(value)
        
        # Print averages
        for name, values in all_measurements.items():
            avg = np.mean(values)
            std = np.std(values)
            print(f"  {name:.<30} {avg:>6.1f} cm (±{std:.1f})")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("YOLOv8 + MediaPipe - Example Usage")
    print("="*60)
    print("\nThis script demonstrates various ways to use the system.")
    print("Make sure you have images ready before running!")
    print("\nNote: Replace 'your_image.jpg' with your actual image path")
    print("="*60)
    
    # Uncomment the examples you want to run:
    
    # example_1_basic()
    # example_2_with_calibration()
    # example_3_multiple_images()
    # example_4_custom_segmentation()
    # example_5_measurements_only()
    # example_6_batch_processing()
    
    print("\n" + "="*60)
    print("To run examples:")
    print("  1. Uncomment the example you want to run")
    print("  2. Replace 'your_image.jpg' with your image path")
    print("  3. Run: python example_usage.py")
    print("="*60)


if __name__ == "__main__":
    main()
