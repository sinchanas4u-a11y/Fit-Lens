"""
Automatic Pose-Aligned Image Capture Application
Uses OpenCV + MediaPipe for real-time pose detection and alignment verification
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import tempfile
import os
from typing import List, Tuple, Optional


class PoseAlignmentCapture:
    """Main application class for pose-aligned automatic image capture"""
    
    def __init__(self, target_images: int = 5, stability_duration: float = 3.0):
        """
        Initialize the pose capture application
        
        Args:
            target_images: Number of images to capture before showing selection
            stability_duration: Seconds user must hold pose before capture (default: 3.0 seconds)
        """
        self.target_images = target_images
        self.stability_duration = stability_duration
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Capture state
        self.captured_images = []
        self.alignment_start_time = None
        self.is_aligned = False
        
        # Alignment tolerance (normalized coordinates 0-1)
        self.position_tolerance = 0.08
        self.angle_tolerance = 15  # degrees
        
    def get_reference_pose(self, frame_width: int, frame_height: int) -> dict:
        """
        Define the reference pose outline (standing, arms slightly away)
        Returns normalized keypoint positions for a front-facing pose
        """
        # Normalized coordinates (0-1) for ideal pose
        # Format: {landmark_name: (x, y)}
        return {
            'nose': (0.5, 0.15),
            'left_shoulder': (0.42, 0.28),
            'right_shoulder': (0.58, 0.28),
            'left_elbow': (0.35, 0.45),
            'right_elbow': (0.65, 0.45),
            'left_wrist': (0.30, 0.60),
            'right_wrist': (0.70, 0.60),
            'left_hip': (0.45, 0.55),
            'right_hip': (0.55, 0.55),
            'left_knee': (0.45, 0.75),
            'right_knee': (0.55, 0.75),
            'left_ankle': (0.45, 0.95),
            'right_ankle': (0.55, 0.95),
        }
    
    def draw_reference_outline(self, frame: np.ndarray, color: Tuple[int, int, int]) -> np.ndarray:
        """
        Draw the reference pose outline on the frame
        
        Args:
            frame: Input frame to draw on
            color: BGR color tuple (changes based on alignment)
        
        Returns:
            Frame with outline drawn
        """
        h, w = frame.shape[:2]
        ref_pose = self.get_reference_pose(w, h)
        
        # Convert normalized coordinates to pixel coordinates
        points = {name: (int(x * w), int(y * h)) for name, (x, y) in ref_pose.items()}
        
        # Define skeleton connections
        connections = [
            ('nose', 'left_shoulder'), ('nose', 'right_shoulder'),
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist'),
            ('left_shoulder', 'left_hip'), ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('left_hip', 'left_knee'), ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'), ('right_knee', 'right_ankle'),
        ]
        
        # Draw connections
        for start, end in connections:
            if start in points and end in points:
                cv2.line(frame, points[start], points[end], color, 3, cv2.LINE_AA)
        
        # Draw keypoints
        for point in points.values():
            cv2.circle(frame, point, 6, color, -1, cv2.LINE_AA)
            cv2.circle(frame, point, 8, (255, 255, 255), 2, cv2.LINE_AA)
        
        return frame
    
    def check_alignment(self, landmarks, frame_width: int, frame_height: int) -> bool:
        """
        Check if detected pose aligns with reference outline
        
        Args:
            landmarks: MediaPipe pose landmarks
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        
        Returns:
            True if pose is aligned within tolerance
        """
        if not landmarks:
            return False
        
        ref_pose = self.get_reference_pose(frame_width, frame_height)
        
        # MediaPipe landmark indices
        landmark_map = {
            'nose': self.mp_pose.PoseLandmark.NOSE,
            'left_shoulder': self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            'right_shoulder': self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            'left_elbow': self.mp_pose.PoseLandmark.LEFT_ELBOW,
            'right_elbow': self.mp_pose.PoseLandmark.RIGHT_ELBOW,
            'left_wrist': self.mp_pose.PoseLandmark.LEFT_WRIST,
            'right_wrist': self.mp_pose.PoseLandmark.RIGHT_WRIST,
            'left_hip': self.mp_pose.PoseLandmark.LEFT_HIP,
            'right_hip': self.mp_pose.PoseLandmark.RIGHT_HIP,
            'left_knee': self.mp_pose.PoseLandmark.LEFT_KNEE,
            'right_knee': self.mp_pose.PoseLandmark.RIGHT_KNEE,
            'left_ankle': self.mp_pose.PoseLandmark.LEFT_ANKLE,
            'right_ankle': self.mp_pose.PoseLandmark.RIGHT_ANKLE,
        }
        
        # Check each keypoint alignment
        misaligned_count = 0
        total_points = len(landmark_map)
        
        for name, landmark_idx in landmark_map.items():
            detected = landmarks.landmark[landmark_idx.value]
            ref_x, ref_y = ref_pose[name]
            
            # Calculate distance (normalized)
            distance = np.sqrt((detected.x - ref_x)**2 + (detected.y - ref_y)**2)
            
            # Check visibility and distance
            if detected.visibility < 0.5 or distance > self.position_tolerance:
                misaligned_count += 1
        
        # Allow some tolerance: 80% of points must be aligned
        alignment_ratio = 1 - (misaligned_count / total_points)
        return alignment_ratio >= 0.8
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Process a single frame: detect pose and check alignment
        
        Args:
            frame: Input frame from camera
        
        Returns:
            Tuple of (processed_frame, is_aligned)
        """
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        # Check alignment
        h, w = frame.shape[:2]
        is_aligned = False
        
        if results.pose_landmarks:
            is_aligned = self.check_alignment(results.pose_landmarks, w, h)
        
        # Determine outline color
        outline_color = (0, 255, 0) if is_aligned else (0, 0, 255)  # Green or Red
        
        # Draw reference outline
        frame = self.draw_reference_outline(frame, outline_color)
        
        return frame, is_aligned
    
    def update_capture_state(self, is_aligned: bool) -> bool:
        """
        Update capture state based on alignment and timing
        
        Args:
            is_aligned: Whether current frame shows alignment
        
        Returns:
            True if image should be captured
        """
        current_time = time.time()
        
        if is_aligned:
            if self.alignment_start_time is None:
                self.alignment_start_time = current_time
            elif current_time - self.alignment_start_time >= self.stability_duration:
                # Capture triggered
                self.alignment_start_time = None
                return True
        else:
            self.alignment_start_time = None
        
        return False
    
    def draw_ui_overlay(self, frame: np.ndarray, is_aligned: bool) -> np.ndarray:
        """
        Draw UI elements: status, timer, progress
        
        Args:
            frame: Input frame
            is_aligned: Current alignment status
        
        Returns:
            Frame with UI overlay
        """
        h, w = frame.shape[:2]
        
        # Status text
        status_text = "ALIGNED - Hold still!" if is_aligned else "Align with outline"
        status_color = (0, 255, 0) if is_aligned else (0, 0, 255)
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, status_color, 2, cv2.LINE_AA)
        
        # Progress
        progress_text = f"Images: {len(self.captured_images)}/{self.target_images}"
        cv2.putText(frame, progress_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Timer bar
        if is_aligned and self.alignment_start_time:
            elapsed = time.time() - self.alignment_start_time
            progress = min(elapsed / self.stability_duration, 1.0)
            bar_width = int(progress * (w - 40))
            cv2.rectangle(frame, (20, h - 40), (20 + bar_width, h - 20), 
                         (0, 255, 0), -1)
            cv2.rectangle(frame, (20, h - 40), (w - 20, h - 20), 
                         (255, 255, 255), 2)
        
        return frame

    def capture_images(self, cap: cv2.VideoCapture) -> List[np.ndarray]:
        """
        Main capture loop: process frames until target images captured
        
        Args:
            cap: OpenCV VideoCapture object
        
        Returns:
            List of captured images
        """
        print(f"Starting capture session. Target: {self.target_images} images")
        
        while len(self.captured_images) < self.target_images:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera")
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame
            processed_frame, is_aligned = self.process_frame(frame)
            
            # Check if capture should trigger
            should_capture = self.update_capture_state(is_aligned)
            
            if should_capture:
                # Store original frame (without overlay)
                self.captured_images.append(frame.copy())
                print(f"Captured image {len(self.captured_images)}/{self.target_images}")
                
                # Visual feedback
                cv2.putText(processed_frame, "CAPTURED!", (processed_frame.shape[1]//2 - 100, 
                           processed_frame.shape[0]//2), cv2.FONT_HERSHEY_SIMPLEX,
                           2.0, (0, 255, 0), 3, cv2.LINE_AA)
                cv2.imshow('Pose Capture', processed_frame)
                cv2.waitKey(500)  # Show capture feedback
            
            # Draw UI overlay
            processed_frame = self.draw_ui_overlay(processed_frame, is_aligned)
            
            # Display
            cv2.imshow('Pose Capture', processed_frame)
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Capture cancelled by user")
                break
        
        return self.captured_images
    
    def show_selection_gallery(self, images: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        Display gallery of captured images for user selection
        
        Args:
            images: List of captured images
        
        Returns:
            Selected image or None if cancelled
        """
        if not images:
            print("No images to select from")
            return None
        
        print(f"\nShowing gallery of {len(images)} images")
        print("Click on an image to select it, or press 'q' to cancel")
        
        # Create gallery grid
        num_images = len(images)
        cols = min(3, num_images)
        rows = (num_images + cols - 1) // cols
        
        # Resize images for gallery
        thumb_height = 300
        thumbnails = []
        for img in images:
            h, w = img.shape[:2]
            thumb_width = int(w * thumb_height / h)
            thumb = cv2.resize(img, (thumb_width, thumb_height))
            thumbnails.append(thumb)
        
        # Find max width for uniform sizing
        max_width = max(t.shape[1] for t in thumbnails)
        
        # Pad thumbnails to same width
        padded_thumbs = []
        for thumb in thumbnails:
            if thumb.shape[1] < max_width:
                pad = max_width - thumb.shape[1]
                thumb = cv2.copyMakeBorder(thumb, 0, 0, 0, pad, 
                                          cv2.BORDER_CONSTANT, value=(0, 0, 0))
            padded_thumbs.append(thumb)
        
        # Create gallery grid
        gallery_rows = []
        for r in range(rows):
            row_images = []
            for c in range(cols):
                idx = r * cols + c
                if idx < len(padded_thumbs):
                    img = padded_thumbs[idx].copy()
                    # Add border and number
                    cv2.rectangle(img, (0, 0), (img.shape[1]-1, img.shape[0]-1), 
                                 (255, 255, 255), 3)
                    cv2.putText(img, f"#{idx+1}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                               1.2, (255, 255, 255), 2, cv2.LINE_AA)
                    row_images.append(img)
                else:
                    # Empty slot
                    row_images.append(np.zeros_like(padded_thumbs[0]))
            
            gallery_rows.append(np.hstack(row_images))
        
        gallery = np.vstack(gallery_rows)
        
        # Mouse callback for selection
        selected_idx = [None]
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Calculate which image was clicked
                col = x // max_width
                row = y // thumb_height
                idx = row * cols + col
                if idx < len(images):
                    selected_idx[0] = idx
        
        cv2.namedWindow('Select Your Favorite')
        cv2.setMouseCallback('Select Your Favorite', mouse_callback)
        
        # Display gallery
        while True:
            display = gallery.copy()
            
            # Add instructions
            cv2.putText(display, "Click on your favorite image", 
                       (20, display.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (255, 255, 255), 2, cv2.LINE_AA)
            
            cv2.imshow('Select Your Favorite', display)
            
            key = cv2.waitKey(100)
            if key == ord('q'):
                print("Selection cancelled")
                return None
            
            if selected_idx[0] is not None:
                print(f"Selected image #{selected_idx[0] + 1}")
                return images[selected_idx[0]]
        
    def cleanup(self):
        """Release resources"""
        self.pose.close()
        cv2.destroyAllWindows()


def main():
    """Main application entry point"""
    print("=" * 60)
    print("Pose-Aligned Automatic Image Capture")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Stand in front of the camera")
    print("2. Align your body with the outline on screen")
    print("3. When aligned, the outline turns GREEN")
    print("4. Hold the pose for 3 seconds to auto-capture")
    print("5. Repeat until 5 images are captured")
    print("6. Select your favorite from the gallery")
    print("\nPress 'q' at any time to quit\n")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open camera")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Initialize application (3 seconds stability duration)
    app = PoseAlignmentCapture(target_images=5, stability_duration=3.0)
    
    try:
        # Capture images
        captured_images = app.capture_images(cap)
        
        if captured_images:
            # Show selection gallery
            selected_image = app.show_selection_gallery(captured_images)
            
            if selected_image is not None:
                # Save selected image
                output_path = "selected_pose.jpg"
                cv2.imwrite(output_path, selected_image)
                print(f"\n✓ Selected image saved to: {output_path}")
                
                # Show final image
                print("Displaying final selection (press any key to close)")
                cv2.imshow('Final Selection', selected_image)
                cv2.waitKey(0)
            else:
                print("\nNo image selected. Session ended.")
        else:
            print("\nNo images captured. Session ended.")
    
    finally:
        # Cleanup
        cap.release()
        app.cleanup()
        print("\nSession complete. Goodbye!")


if __name__ == "__main__":
    main()
