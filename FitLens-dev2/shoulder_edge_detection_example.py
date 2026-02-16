"""
Example: Shoulder Edge Point Detection using Modified MediaPipe

This script demonstrates:
1. Real-time shoulder edge detection from video or webcam
2. JSON output generation with frame data
3. Performance metrics tracking
4. Visual output with edge point highlighting
"""

import cv2
import numpy as np
import json
from pathlib import Path
from backend.landmark_detector import LandmarkDetector
import time


class ShoulderEdgeDetectionDemo:
    """Demonstrates shoulder edge detection capabilities"""
    
    def __init__(self):
        self.detector = LandmarkDetector()
        self.results_history = []
        self.frame_times = []
        
    def process_video_file(self, video_path: str, output_json_path: str = None,
                          output_video_path: str = None) -> Dict:
        """
        Process a video file and detect shoulder edges in all frames
        
        Args:
            video_path: Path to input video file
            output_json_path: Optional path to save JSON results
            output_video_path: Optional path to save annotated video
            
        Returns:
            Dictionary with statistics and results
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return {}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup output video writer if needed
        out_video = None
        if output_video_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        frame_count = 0
        start_time = time.time()
        
        print(f"Processing video: {video_path}")
        print(f"Resolution: {width}x{height}, FPS: {fps}")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_start = time.time()
                
                # Detect landmarks
                landmarks = self.detector.detect(frame)
                
                # Detect shoulder edges
                shoulder_data = self.detector.detect_shoulder_edge_points(
                    frame, landmarks, shoulder_type='both'
                )
                
                # Draw shoulder edges on frame
                annotated_frame = self.detector.draw_shoulder_edges(frame, shoulder_data)
                
                # Draw skeleton for reference
                if landmarks is not None:
                    annotated_frame = self.detector.draw_landmarks(annotated_frame, landmarks)
                
                # Store results
                self.results_history.append(shoulder_data)
                
                # Track frame processing time
                frame_time = time.time() - frame_start
                self.frame_times.append(frame_time)
                
                # Write annotated frame to output video
                if out_video:
                    out_video.write(annotated_frame)
                
                # Display progress
                frame_count += 1
                if frame_count % 30 == 0:
                    avg_fps = frame_count / (time.time() - start_time)
                    conf = shoulder_data['confidence_score']
                    print(f"Frame {frame_count}: FPS={avg_fps:.1f}, Confidence={conf:.2%}")
                
                # Display frame (optional)
                cv2.imshow('Shoulder Edge Detection', annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            if out_video:
                out_video.release()
            cv2.destroyAllWindows()
        
        total_time = time.time() - start_time
        
        # Save JSON results
        if output_json_path:
            self._save_results_json(output_json_path)
        
        # Calculate and return statistics
        stats = self.detector.get_detection_statistics(self.results_history)
        stats.update({
            'total_processing_time': total_time,
            'average_fps': frame_count / total_time,
            'total_frames_processed': frame_count
        })
        
        return stats
    
    def process_webcam(self, duration_seconds: int = 30,
                       output_json_path: str = None) -> Dict:
        """
        Process webcam stream in real-time
        
        Args:
            duration_seconds: How long to capture (0 for unlimited)
            output_json_path: Optional path to save JSON results
            
        Returns:
            Dictionary with statistics
        """
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not access webcam")
            return {}
        
        # Set resolution for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        frame_count = 0
        start_time = time.time()
        
        print(f"Starting webcam capture for {duration_seconds} seconds...")
        print("Press 'q' to quit early")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detect landmarks
                landmarks = self.detector.detect(frame)
                
                # Detect shoulder edges
                shoulder_data = self.detector.detect_shoulder_edge_points(
                    frame, landmarks, shoulder_type='both'
                )
                
                # Draw shoulder edges
                annotated_frame = self.detector.draw_shoulder_edges(frame, shoulder_data)
                
                # Draw skeleton
                if landmarks is not None:
                    annotated_frame = self.detector.draw_landmarks(annotated_frame, landmarks)
                
                # Store results
                self.results_history.append(shoulder_data)
                
                # Display
                cv2.imshow('Shoulder Edge Detection - Webcam', annotated_frame)
                
                frame_count += 1
                elapsed = time.time() - start_time
                
                # Check time limit
                if duration_seconds > 0 and elapsed > duration_seconds:
                    break
                
                # Display every 30 frames
                if frame_count % 30 == 0:
                    fps = frame_count / elapsed
                    conf = shoulder_data['confidence_score']
                    print(f"Frame {frame_count}: FPS={fps:.1f}, Confidence={conf:.2%}")
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        total_time = time.time() - start_time
        
        # Save JSON results
        if output_json_path:
            self._save_results_json(output_json_path)
        
        # Calculate statistics
        stats = self.detector.get_detection_statistics(self.results_history)
        stats.update({
            'total_processing_time': total_time,
            'average_fps': frame_count / total_time if total_time > 0 else 0,
            'total_frames_processed': frame_count
        })
        
        return stats
    
    def _save_results_json(self, output_path: str):
        """Save detection results to JSON file"""
        output = {
            'metadata': {
                'total_frames': len(self.results_history),
                'timestamp': str(time.time())
            },
            'frames': self.results_history
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results saved to: {output_path}")
    
    def print_summary(self, stats: Dict):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("SHOULDER EDGE DETECTION SUMMARY")
        print("="*60)
        print(f"Total Frames Processed: {stats.get('total_frames_processed', 0)}")
        print(f"Total Processing Time: {stats.get('total_processing_time', 0):.2f}s")
        print(f"Average FPS: {stats.get('average_fps', 0):.1f}")
        print(f"Detection Success Rate: {stats.get('detection_success_rate', 0):.1%}")
        print(f"\nConfidence Metrics:")
        print(f"  Average: {stats.get('average_confidence', 0):.2%}")
        print(f"  Max: {stats.get('max_confidence', 0):.2%}")
        print(f"  Min: {stats.get('min_confidence', 0):.2%}")
        print(f"  Std Dev: {stats.get('std_confidence', 0):.3f}")
        print(f"\nEdge Points:")
        print(f"  Average per frame: {stats.get('average_edge_points', 0):.1f}")
        print(f"  Frames with detections: {stats.get('frames_with_detections', 0)}")
        print("="*60 + "\n")


def main():
    """Main execution"""
    import sys
    
    demo = ShoulderEdgeDetectionDemo()
    
    if len(sys.argv) > 1:
        # Process video file
        video_path = sys.argv[1]
        output_json = sys.argv[2] if len(sys.argv) > 2 else None
        output_video = sys.argv[3] if len(sys.argv) > 3 else None
        
        stats = demo.process_video_file(video_path, output_json, output_video)
        demo.print_summary(stats)
    else:
        # Use webcam
        print("No video file provided. Using webcam...")
        stats = demo.process_webcam(duration_seconds=30)
        demo.print_summary(stats)
    
    # Cleanup
    demo.detector.cleanup()


if __name__ == '__main__':
    main()
