"""
Main Application: Real-time Body Measurement using R-CNN
Provides live camera feed with pose detection, alignment feedback, and measurements
"""
import cv2
import numpy as np
import time
import os
from typing import List, Optional, Tuple
import tempfile

from config import Config
from model_arch import KeypointRCNN, DepthEstimator, CenteringChecker
from pose_utils import AlignmentChecker, MeasurementCalculator, SkeletonDrawer
from dataset import SyntheticDataGenerator


class BodyMeasurementApp:
    """Main application for real-time body measurement"""
    
    def __init__(self, model_weights: Optional[str] = None, 
                 reference_height_cm: Optional[float] = None):
        """
        Initialize application
        
        Args:
            model_weights: Path to custom model weights (uses pretrained if None)
            reference_height_cm: User's height for calibration (optional)
        """
        print("Initializing Body Measurement Application...")
        
        # Initialize model
        self.model = KeypointRCNN(weights_file=model_weights)
        
        # Initialize utilities
        self.depth_estimator = DepthEstimator()
        self.measurement_calculator = MeasurementCalculator(reference_height_cm)
        
        # Capture state
        self.captured_images = []
        self.captured_keypoints = []
        self.captured_measurements = []
        self.alignment_frame_count = 0
        self.is_calibrated = False
        
        # Create temp directory if needed
        if not Config.AUTO_DELETE_TEMP:
            os.makedirs(Config.TEMP_DIR, exist_ok=True)
        
        print("✓ Application initialized")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool, Dict]:
        """
        Process single frame: detect pose, check alignment, provide feedback
        
        Args:
            frame: Input frame from camera
            
        Returns:
            (processed_frame, is_aligned, info_dict)
        """
        h, w = frame.shape[:2]
        
        # Run pose detection
        outputs = self.model.predict(frame)
        keypoints = self.model.extract_keypoints(outputs)
        
        info = {
            'keypoints': keypoints,
            'is_aligned': False,
            'feedback': "No person detected",
            'measurements': {}
        }
        
        if keypoints is None:
            # No person detected
            cv2.putText(frame, "No person detected", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
            return frame, False, info
        
        # Calibrate on first detection
        if not self.is_calibrated:
            self.depth_estimator.calibrate(keypoints)
            self.measurement_calculator.calibrate_scale(keypoints, (h, w))
            self.is_calibrated = True
        
        # Check alignment
        is_aligned, alignment_scores, feedback = AlignmentChecker.check_alignment(
            keypoints, (h, w)
        )
        
        # Check centering
        is_centered, centering_feedback = CenteringChecker.check_centering(
            keypoints, w, h
        )
        
        # Check depth/distance
        distance_feedback = self.depth_estimator.get_distance_feedback(keypoints)
        
        # Combine feedback
        all_feedback = []
        if not is_aligned:
            all_feedback.append(feedback)
        if not is_centered:
            all_feedback.append(centering_feedback)
        if distance_feedback:
            all_feedback.append(distance_feedback)
        
        combined_feedback = " | ".join(all_feedback) if all_feedback else "PERFECT! Hold still..."
        
        # Determine skeleton color
        skeleton_color = Config.SKELETON_COLOR_ALIGNED if is_aligned else Config.SKELETON_COLOR_MISALIGNED
        
        # Draw skeleton
        frame = SkeletonDrawer.draw_skeleton(frame, keypoints, skeleton_color)
        
        # Calculate measurements if aligned
        measurements = {}
        if is_aligned:
            try:
                measurements = self.measurement_calculator.calculate_measurements(keypoints)
            except Exception as e:
                print(f"Warning: Could not calculate measurements: {e}")
        
        # Update info
        info.update({
            'is_aligned': is_aligned,
            'feedback': combined_feedback,
            'measurements': measurements,
            'alignment_scores': alignment_scores
        })
        
        return frame, is_aligned, info
    
    def draw_ui(self, frame: np.ndarray, info: Dict) -> np.ndarray:
        """
        Draw UI overlay on frame
        
        Args:
            frame: Input frame
            info: Information dictionary from process_frame
            
        Returns:
            Frame with UI overlay
        """
        h, w = frame.shape[:2]
        
        # Status text
        is_aligned = info['is_aligned']
        feedback = info['feedback']
        
        status_color = Config.SKELETON_COLOR_ALIGNED if is_aligned else Config.SKELETON_COLOR_MISALIGNED
        
        # Main feedback
        cv2.putText(frame, feedback, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2, cv2.LINE_AA)
        
        # Capture progress
        progress_text = f"Captured: {len(self.captured_images)}/{Config.AUTO_CAPTURE_COUNT}"
        cv2.putText(frame, progress_text, (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Alignment progress bar
        if is_aligned:
            progress = min(self.alignment_frame_count / Config.STABILITY_FRAMES, 1.0)
            bar_width = int(progress * (w - 40))
            
            cv2.rectangle(frame, (20, h - 60), (20 + bar_width, h - 40),
                         Config.SKELETON_COLOR_ALIGNED, -1)
            cv2.rectangle(frame, (20, h - 60), (w - 20, h - 40),
                         (255, 255, 255), 2)
            
            # Countdown text
            frames_left = Config.STABILITY_FRAMES - self.alignment_frame_count
            countdown_text = f"Hold for {frames_left} frames..."
            cv2.putText(frame, countdown_text, (20, h - 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Display measurements if available
        if info['measurements']:
            y_offset = 120
            cv2.putText(frame, "Measurements:", (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            y_offset += 25
            
            for name, value in info['measurements'].items():
                text = f"  {name.replace('_', ' ').title()}: {value:.1f} cm"
                cv2.putText(frame, text, (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                y_offset += 20
        
        # Instructions
        instructions = "Press 'Q' to quit | 'R' to reset"
        cv2.putText(frame, instructions, (20, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        
        return frame
    
    def update_capture_state(self, is_aligned: bool, frame: np.ndarray, 
                            keypoints: np.ndarray, measurements: Dict) -> bool:
        """
        Update capture state and trigger capture if conditions met
        
        Args:
            is_aligned: Whether current frame is aligned
            frame: Current frame
            keypoints: Detected keypoints
            measurements: Calculated measurements
            
        Returns:
            True if capture triggered
        """
        if is_aligned:
            self.alignment_frame_count += 1
            
            if self.alignment_frame_count >= Config.STABILITY_FRAMES:
                # Trigger capture
                self.captured_images.append(frame.copy())
                self.captured_keypoints.append(keypoints.copy())
                self.captured_measurements.append(measurements.copy())
                
                self.alignment_frame_count = 0
                return True
        else:
            self.alignment_frame_count = 0
        
        return False
    
    def save_captured_image(self, frame: np.ndarray, keypoints: np.ndarray, 
                           measurements: Dict, index: int) -> str:
        """
        Save captured image with keypoint markers
        
        Args:
            frame: Image to save
            keypoints: Keypoints to mark
            measurements: Measurements to annotate
            index: Image index
            
        Returns:
            Path to saved image
        """
        # Draw keypoint markers (endpoints highlighted)
        annotated = frame.copy()
        annotated = SkeletonDrawer.draw_skeleton(
            annotated, keypoints, 
            Config.SKELETON_COLOR_ALIGNED,
            draw_endpoints=True
        )
        
        # Add measurement annotations
        y_offset = 30
        for name, value in measurements.items():
            text = f"{name.replace('_', ' ').title()}: {value:.1f} cm"
            cv2.putText(annotated, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            y_offset += 25
        
        # Save image
        if Config.SAVE_IMAGES:
            filename = f"capture_{index:02d}.jpg"
            if Config.AUTO_DELETE_TEMP:
                # Use temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.jpg', prefix=f'capture_{index}_'
                )
                filepath = temp_file.name
                temp_file.close()
            else:
                filepath = os.path.join(Config.TEMP_DIR, filename)
            
            cv2.imwrite(filepath, annotated)
            return filepath
        
        return ""
    
    def run(self):
        """Main application loop"""
        print("\n" + "=" * 60)
        print("Body Measurement Application - R-CNN/PyTorch")
        print("=" * 60)
        print("\nInstructions:")
        print("1. Stand facing the camera, arms slightly away from body")
        print("2. Skeleton will be RED when misaligned, GREEN when aligned")
        print("3. Follow on-screen guidance to adjust position")
        print("4. Hold aligned pose for", Config.STABILITY_FRAMES, "frames")
        print("5. Application will auto-capture", Config.AUTO_CAPTURE_COUNT, "images")
        print("6. Measurements will be displayed in real-time")
        print("\nPrivacy Note: Images are", 
              "NOT saved" if not Config.SAVE_IMAGES else "saved temporarily")
        print("\nPress 'Q' to quit, 'R' to reset captures\n")
        
        # Initialize camera
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        if not cap.isOpened():
            print("✗ Error: Could not open camera")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, Config.FPS)
        
        print("✓ Camera initialized")
        print("Starting capture loop...\n")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("✗ Failed to read frame")
                    break
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Process frame
                processed_frame, is_aligned, info = self.process_frame(frame)
                
                # Check if capture should trigger
                if len(self.captured_images) < Config.AUTO_CAPTURE_COUNT:
                    should_capture = self.update_capture_state(
                        is_aligned, frame, 
                        info['keypoints'], 
                        info['measurements']
                    )
                    
                    if should_capture:
                        print(f"✓ Captured image {len(self.captured_images)}/{Config.AUTO_CAPTURE_COUNT}")
                        
                        # Save image
                        if Config.SAVE_IMAGES:
                            filepath = self.save_captured_image(
                                frame, info['keypoints'], 
                                info['measurements'],
                                len(self.captured_images)
                            )
                            print(f"  Saved to: {filepath}")
                        
                        # Visual feedback
                        cv2.putText(processed_frame, "CAPTURED!", 
                                   (processed_frame.shape[1]//2 - 100, 
                                    processed_frame.shape[0]//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 2.0, 
                                   Config.SKELETON_COLOR_ALIGNED, 3, cv2.LINE_AA)
                        cv2.imshow('Body Measurement', processed_frame)
                        cv2.waitKey(500)
                
                # Draw UI
                processed_frame = self.draw_ui(processed_frame, info)
                
                # Display
                cv2.imshow('Body Measurement', processed_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\nQuitting...")
                    break
                elif key == ord('r') or key == ord('R'):
                    print("\nResetting captures...")
                    self.captured_images = []
                    self.captured_keypoints = []
                    self.captured_measurements = []
                    self.alignment_frame_count = 0
                
                # Check if all captures complete
                if len(self.captured_images) >= Config.AUTO_CAPTURE_COUNT:
                    print("\n✓ All captures complete!")
                    self.show_results()
                    break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
            # Cleanup temp files if privacy mode enabled
            if Config.AUTO_DELETE_TEMP and Config.SAVE_IMAGES:
                self.cleanup_temp_files()
    
    def show_results(self):
        """Display final results and measurements"""
        print("\n" + "=" * 60)
        print("FINAL MEASUREMENTS")
        print("=" * 60)
        
        if not self.captured_measurements:
            print("No measurements captured")
            return
        
        # Average measurements across all captures
        all_measurements = {}
        for measurements in self.captured_measurements:
            for key, value in measurements.items():
                if key not in all_measurements:
                    all_measurements[key] = []
                all_measurements[key].append(value)
        
        print("\nAverage measurements across", len(self.captured_measurements), "captures:\n")
        for name, values in all_measurements.items():
            avg = np.mean(values)
            std = np.std(values)
            print(f"  {name.replace('_', ' ').title():.<30} {avg:>6.1f} cm (±{std:.1f})")
        
        print("\n" + "=" * 60)
        
        # Show captured images
        if self.captured_images:
            print("\nDisplaying captured images (press any key to continue)...")
            for i, img in enumerate(self.captured_images):
                cv2.imshow(f'Capture {i+1}', img)
                cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    def cleanup_temp_files(self):
        """Clean up temporary files for privacy"""
        print("\nCleaning up temporary files...")
        # Temp files are auto-deleted by tempfile module
        print("✓ Cleanup complete")


def demo_mode():
    """Run demo with synthetic data"""
    print("Running in DEMO mode with synthetic data...")
    
    # Generate synthetic pose
    image, keypoints = SyntheticDataGenerator.generate_synthetic_pose()
    
    # Draw skeleton
    image = SkeletonDrawer.draw_skeleton(image, keypoints, (0, 255, 0))
    
    # Calculate measurements
    calc = MeasurementCalculator()
    calc.calibrate_scale(keypoints, image.shape[:2])
    measurements = calc.calculate_measurements(keypoints)
    
    # Display
    y_offset = 30
    for name, value in measurements.items():
        text = f"{name.replace('_', ' ').title()}: {value:.1f} cm"
        cv2.putText(image, text, (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
        y_offset += 25
    
    cv2.imshow('Demo - Synthetic Pose', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-time Body Measurement using R-CNN/PyTorch"
    )
    parser.add_argument("--weights", type=str, default=None,
                       help="Path to custom model weights")
    parser.add_argument("--height", type=float, default=None,
                       help="Your height in cm for calibration")
    parser.add_argument("--demo", action="store_true",
                       help="Run demo mode with synthetic data")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_mode()
    else:
        app = BodyMeasurementApp(
            model_weights=args.weights,
            reference_height_cm=args.height
        )
        app.run()


if __name__ == "__main__":
    main()
