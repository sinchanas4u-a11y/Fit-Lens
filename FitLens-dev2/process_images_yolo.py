"""
YOLOv8 + MediaPipe Image Processing Script
Upload 3 images, segment person with YOLOv8, detect landmarks with MediaPipe
"""
import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
import argparse

from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
from measurement_engine import MeasurementEngine


class ImageProcessor:
    """Process images with YOLOv8 segmentation and MediaPipe landmarks"""
    
    def __init__(self, yolo_model_size: str = 'n'):
        """
        Initialize processor
        
        Args:
            yolo_model_size: YOLOv8 model size ('n', 's', 'm', 'l', 'x')
        """
        print("Initializing Image Processor...")
        print(f"  - YOLOv8 model size: {yolo_model_size}")
        
        self.segmentation_model = SegmentationModel(model_size=yolo_model_size)
        self.landmark_detector = LandmarkDetector()
        self.measurement_engine = MeasurementEngine()
        
        print("✓ Initialization complete\n")
    
    def process_single_image(self, image_path: str, reference_size_cm: Optional[float] = None,
                            save_output: bool = True) -> dict:
        """
        Process a single image
        
        Args:
            image_path: Path to input image
            reference_size_cm: Reference object size in cm for scale calibration
            save_output: Whether to save output images
            
        Returns:
            Dictionary with results
        """
        print(f"\nProcessing: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ✗ Failed to load image")
            return {'error': 'Failed to load image'}
        
        h, w = image.shape[:2]
        print(f"  Image size: {w}x{h}")
        
        # Step 1: Segment person with YOLOv8
        print("  Step 1: Segmenting person with YOLOv8...")
        mask = self.segmentation_model.segment_person(image, conf_threshold=0.5)
        
        if mask is None:
            print("  ✗ No person detected")
            return {'error': 'No person detected'}
        
        print("  ✓ Person segmented")
        
        # Step 2: Apply mask to get clean human outline
        print("  Step 2: Applying mask...")
        masked_image = self.segmentation_model.apply_mask(image, mask, background_mode='dim')
        
        # Get masked region only
        masked_region, bbox = self.segmentation_model.get_masked_region(image, mask)
        x, y, w_bbox, h_bbox = bbox
        print(f"  ✓ Masked region: {w_bbox}x{h_bbox} at ({x}, {y})")
        
        # Step 3: Detect landmarks with MediaPipe on masked region
        print("  Step 3: Detecting landmarks with MediaPipe...")
        
        # Use original image for landmark detection (MediaPipe works better on full image)
        landmarks = self.landmark_detector.detect(image)
        
        if landmarks is None:
            print("  ✗ No landmarks detected")
            return {
                'error': 'No landmarks detected',
                'mask': mask,
                'masked_image': masked_image
            }
        
        print(f"  ✓ Detected {len(landmarks)} landmarks")
        
        # Step 4: Calculate measurements
        print("  Step 4: Calculating measurements...")
        
        # Determine scale factor
        scale_factor = 1.0  # Default: 1 pixel = 1 cm
        if reference_size_cm:
            # Use reference size for calibration
            scale_factor = reference_size_cm / h  # Simple height-based calibration
            print(f"  Scale factor: {scale_factor:.4f} cm/pixel")
        
        measurements = self.measurement_engine.calculate_measurements_with_confidence(
            landmarks, scale_factor, view='front'
        )
        
        print(f"  ✓ Calculated {len(measurements)} measurements")
        
        # Step 5: Create visualizations
        print("  Step 5: Creating visualizations...")
        
        # Visualization 1: Masked image with landmarks
        vis_masked = masked_image.copy()
        vis_masked = self.landmark_detector.draw_landmarks(vis_masked, landmarks)
        
        # Visualization 2: Original with landmarks
        vis_original = image.copy()
        vis_original = self.landmark_detector.draw_landmarks(vis_original, landmarks)
        
        # Visualization 3: Mask overlay
        vis_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        
        # Visualization 4: Side-by-side comparison
        vis_comparison = self._create_comparison_view(
            image, masked_image, vis_masked, mask
        )
        
        # Add measurement annotations
        vis_with_measurements = self._add_measurement_annotations(
            vis_masked.copy(), measurements
        )
        
        print("  ✓ Visualizations created")
        
        # Step 6: Save outputs
        if save_output:
            print("  Step 6: Saving outputs...")
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            cv2.imwrite(f"{output_dir}/{base_name}_mask.png", mask)
            cv2.imwrite(f"{output_dir}/{base_name}_masked.png", masked_image)
            cv2.imwrite(f"{output_dir}/{base_name}_landmarks.png", vis_masked)
            cv2.imwrite(f"{output_dir}/{base_name}_comparison.png", vis_comparison)
            cv2.imwrite(f"{output_dir}/{base_name}_measurements.png", vis_with_measurements)
            
            print(f"  ✓ Saved outputs to {output_dir}/")
        
        return {
            'success': True,
            'image_path': image_path,
            'mask': mask,
            'masked_image': masked_image,
            'landmarks': landmarks,
            'measurements': measurements,
            'visualizations': {
                'masked_with_landmarks': vis_masked,
                'original_with_landmarks': vis_original,
                'mask_only': vis_mask,
                'comparison': vis_comparison,
                'with_measurements': vis_with_measurements
            },
            'bbox': bbox
        }
    
    def process_multiple_images(self, image_paths: List[str], 
                               reference_size_cm: Optional[float] = None) -> List[dict]:
        """
        Process multiple images
        
        Args:
            image_paths: List of image paths
            reference_size_cm: Reference size for calibration
            
        Returns:
            List of result dictionaries
        """
        print(f"\n{'='*60}")
        print(f"Processing {len(image_paths)} images")
        print(f"{'='*60}")
        
        results = []
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{len(image_paths)}]")
            result = self.process_single_image(image_path, reference_size_cm)
            results.append(result)
        
        # Summary
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        
        successful = sum(1 for r in results if r.get('success', False))
        print(f"  Successful: {successful}/{len(image_paths)}")
        
        if successful > 0:
            print("\n  Average Measurements:")
            self._print_average_measurements(results)
        
        return results
    
    def _create_comparison_view(self, original, masked, landmarks_vis, mask):
        """Create side-by-side comparison view"""
        h, w = original.shape[:2]
        
        # Resize for comparison
        scale = 0.5
        new_w, new_h = int(w * scale), int(h * scale)
        
        img1 = cv2.resize(original, (new_w, new_h))
        img2 = cv2.resize(masked, (new_w, new_h))
        img3 = cv2.resize(landmarks_vis, (new_w, new_h))
        mask_vis = cv2.resize(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), (new_w, new_h))
        
        # Add labels
        cv2.putText(img1, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img2, "Masked", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img3, "Landmarks", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(mask_vis, "Mask", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Combine
        top_row = np.hstack([img1, img2])
        bottom_row = np.hstack([img3, mask_vis])
        comparison = np.vstack([top_row, bottom_row])
        
        return comparison
    
    def _add_measurement_annotations(self, image, measurements):
        """Add measurement text annotations to image"""
        y_offset = 30
        
        for name, data in measurements.items():
            if isinstance(data, dict):
                value_cm = data.get('value_cm', 0)
                confidence = data.get('confidence', 0)
                text = f"{name}: {value_cm:.1f}cm (conf: {confidence:.2f})"
            else:
                text = f"{name}: {data:.1f}cm"
            
            cv2.putText(image, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
            y_offset += 25
            
            # Limit to first 15 measurements to avoid clutter
            if y_offset > 400:
                break
        
        return image
    
    def _print_average_measurements(self, results):
        """Print average measurements across all successful results"""
        all_measurements = {}
        
        for result in results:
            if not result.get('success', False):
                continue
            
            measurements = result.get('measurements', {})
            for name, data in measurements.items():
                if isinstance(data, dict):
                    value = data.get('value_cm', 0)
                else:
                    value = data
                
                if name not in all_measurements:
                    all_measurements[name] = []
                all_measurements[name].append(value)
        
        for name, values in all_measurements.items():
            if values:
                avg = np.mean(values)
                std = np.std(values)
                print(f"    {name:.<30} {avg:>6.1f} cm (±{std:.1f})")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Process images with YOLOv8 segmentation and MediaPipe landmarks"
    )
    parser.add_argument("images", nargs='+', help="Path(s) to input image(s)")
    parser.add_argument("--model-size", type=str, default='n', 
                       choices=['n', 's', 'm', 'l', 'x'],
                       help="YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=xlarge)")
    parser.add_argument("--reference-size", type=float, default=None,
                       help="Reference object size in cm for scale calibration")
    parser.add_argument("--no-save", action='store_true',
                       help="Don't save output images")
    parser.add_argument("--display", action='store_true',
                       help="Display results in windows")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = ImageProcessor(yolo_model_size=args.model_size)
    
    # Process images
    if len(args.images) == 1:
        result = processor.process_single_image(
            args.images[0], 
            reference_size_cm=args.reference_size,
            save_output=not args.no_save
        )
        results = [result]
    else:
        results = processor.process_multiple_images(
            args.images,
            reference_size_cm=args.reference_size
        )
    
    # Display results if requested
    if args.display:
        print("\nDisplaying results (press any key to continue)...")
        for i, result in enumerate(results):
            if result.get('success', False):
                vis = result['visualizations']['comparison']
                cv2.imshow(f"Result {i+1}", vis)
                cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    print("\n✓ Processing complete!")


if __name__ == "__main__":
    main()
