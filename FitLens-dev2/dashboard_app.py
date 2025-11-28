"""
Body Measurement Dashboard Application
Supports both Upload and Live Camera modes with reference object calibration
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import queue
from typing import Optional, Tuple, Dict, List
import pyttsx3

from reference_detector import ReferenceDetector
from temporal_stabilizer import TemporalStabilizer
from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector


class BodyMeasurementDashboard:
    """Main dashboard application"""
    
    def __init__(self):
        """Initialize dashboard"""
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Body Measurement System")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.reference_detector = ReferenceDetector()
        self.temporal_stabilizer = TemporalStabilizer()
        self.measurement_engine = MeasurementEngine()
        self.segmentation_model = SegmentationModel()
        self.landmark_detector = LandmarkDetector()
        
        # TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_enabled = True
        
        # State variables
        self.mode = None  # 'upload' or 'live'
        self.reference_size_cm = None
        self.reference_axis = 'width'  # 'width' or 'height'
        self.reference_captured = False
        self.reference_px_size = None
        
        # Camera variables
        self.camera = None
        self.camera_running = False
        self.frame_queue = queue.Queue(maxsize=2)
        
        # Alignment state
        self.alignment_status = 'red'  # 'red', 'amber', 'green'
        self.green_start_time = None
        self.countdown_active = False
        
        # Build UI
        self.build_dashboard()
        
    def build_dashboard(self):
        """Build main dashboard UI"""
        # Title
        title = ctk.CTkLabel(
            self.root,
            text="Body Measurement System",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=30)
        
        # Mode selection frame
        mode_frame = ctk.CTkFrame(self.root)
        mode_frame.pack(pady=20)
        
        # Upload button
        upload_btn = ctk.CTkButton(
            mode_frame,
            text="📤 Upload Images",
            font=ctk.CTkFont(size=20),
            width=300,
            height=100,
            command=self.start_upload_mode
        )
        upload_btn.grid(row=0, column=0, padx=20)
        
        # Live camera button
        live_btn = ctk.CTkButton(
            mode_frame,
            text="📷 Live Camera",
            font=ctk.CTkFont(size=20),
            width=300,
            height=100,
            command=self.start_live_mode
        )
        live_btn.grid(row=0, column=1, padx=20)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self.root,
            text="Choose a mode to begin body measurements",
            font=ctk.CTkFont(size=16)
        )
        instructions.pack(pady=20)
        
        # Features list
        features_frame = ctk.CTkFrame(self.root)
        features_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        features_title = ctk.CTkLabel(
            features_frame,
            text="Features",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        features_title.pack(pady=10)
        
        features = [
            "✓ Upload Mode: Process front, side, and reference images",
            "✓ Live Mode: Real-time pose detection with auto-capture",
            "✓ Reference object calibration for accurate measurements",
            "✓ Color-coded feedback (Red/Amber/Green)",
            "✓ Temporal stability checks with RNN/LSTM",
            "✓ Instance segmentation with Mask R-CNN",
            "✓ MediaPipe landmarks for precise measurements",
            "✓ Voice guidance (optional)",
        ]
        
        for feature in features:
            label = ctk.CTkLabel(
                features_frame,
                text=feature,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            label.pack(pady=5, padx=20, anchor="w")
    
    def start_upload_mode(self):
        """Start upload mode"""
        self.mode = 'upload'
        self.clear_window()
        self.build_upload_ui()
    
    def start_live_mode(self):
        """Start live camera mode"""
        self.mode = 'live'
        self.clear_window()
        self.build_live_ui()
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def build_upload_ui(self):
        """Build upload mode UI"""
        # Title
        title = ctk.CTkLabel(
            self.root,
            text="Upload Images Mode",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)
        
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Left panel - Upload controls
        left_panel = ctk.CTkFrame(main_frame)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Reference object section
        ref_label = ctk.CTkLabel(
            left_panel,
            text="Reference Object",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        ref_label.pack(pady=10)
        
        # Reference size input
        size_frame = ctk.CTkFrame(left_panel)
        size_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(size_frame, text="Known Size (cm):").pack(side="left", padx=5)
        self.ref_size_entry = ctk.CTkEntry(size_frame, width=100)
        self.ref_size_entry.pack(side="left", padx=5)
        self.ref_size_entry.insert(0, "29.7")  # A4 height default
        
        # Axis selection
        axis_frame = ctk.CTkFrame(left_panel)
        axis_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(axis_frame, text="Measurement Axis:").pack(side="left", padx=5)
        self.axis_var = tk.StringVar(value="height")
        ctk.CTkRadioButton(
            axis_frame, text="Width", variable=self.axis_var, value="width"
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            axis_frame, text="Height", variable=self.axis_var, value="height"
        ).pack(side="left", padx=5)
        
        # Upload buttons
        self.ref_img_btn = ctk.CTkButton(
            left_panel,
            text="📷 Upload Reference Image",
            command=lambda: self.upload_image('reference')
        )
        self.ref_img_btn.pack(pady=10, padx=20, fill="x")
        
        self.front_img_btn = ctk.CTkButton(
            left_panel,
            text="📷 Upload Front View",
            command=lambda: self.upload_image('front')
        )
        self.front_img_btn.pack(pady=10, padx=20, fill="x")
        
        self.side_img_btn = ctk.CTkButton(
            left_panel,
            text="📷 Upload Side View",
            command=lambda: self.upload_image('side')
        )
        self.side_img_btn.pack(pady=10, padx=20, fill="x")
        
        # Process button
        self.process_btn = ctk.CTkButton(
            left_panel,
            text="🔍 Process & Measure",
            command=self.process_uploaded_images,
            state="disabled"
        )
        self.process_btn.pack(pady=20, padx=20, fill="x")
        
        # Right panel - Preview and results
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Preview canvas
        self.upload_canvas = tk.Canvas(right_panel, width=800, height=600, bg="gray20")
        self.upload_canvas.pack(pady=10)
        
        # Results text
        self.results_text = ctk.CTkTextbox(right_panel, width=800, height=200)
        self.results_text.pack(pady=10)
        
        # Back button
        back_btn = ctk.CTkButton(
            self.root,
            text="← Back to Dashboard",
            command=self.back_to_dashboard
        )
        back_btn.pack(pady=10)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Storage for uploaded images
        self.uploaded_images = {}
    
    def build_live_ui(self):
        """Build live camera mode UI"""
        # Title
        title = ctk.CTkLabel(
            self.root,
            text="Live Camera Mode",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=10)
        
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Left panel - Controls
        left_panel = ctk.CTkFrame(main_frame, width=300)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_panel.grid_propagate(False)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            left_panel,
            text="⚫ Not Ready",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="red"
        )
        self.status_label.pack(pady=10)
        
        # Reference capture section
        ref_section = ctk.CTkFrame(left_panel)
        ref_section.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(
            ref_section,
            text="Step 1: Capture Reference",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        # Reference size input
        size_frame = ctk.CTkFrame(ref_section)
        size_frame.pack(pady=5, fill="x")
        
        ctk.CTkLabel(size_frame, text="Size (cm):").pack(side="left", padx=5)
        self.live_ref_size_entry = ctk.CTkEntry(size_frame, width=80)
        self.live_ref_size_entry.pack(side="left", padx=5)
        self.live_ref_size_entry.insert(0, "29.7")
        
        # Axis selection
        self.live_axis_var = tk.StringVar(value="height")
        axis_frame = ctk.CTkFrame(ref_section)
        axis_frame.pack(pady=5, fill="x")
        
        ctk.CTkRadioButton(
            axis_frame, text="Width", variable=self.live_axis_var, value="width"
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            axis_frame, text="Height", variable=self.live_axis_var, value="height"
        ).pack(side="left", padx=5)
        
        self.capture_ref_btn = ctk.CTkButton(
            ref_section,
            text="📷 Capture Reference",
            command=self.capture_reference_live
        )
        self.capture_ref_btn.pack(pady=10, fill="x")
        
        # Measurement section
        measure_section = ctk.CTkFrame(left_panel)
        measure_section.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(
            measure_section,
            text="Step 2: Align & Capture",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        self.countdown_label = ctk.CTkLabel(
            measure_section,
            text="",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.countdown_label.pack(pady=10)
        
        self.manual_capture_btn = ctk.CTkButton(
            measure_section,
            text="📸 Manual Capture",
            command=self.manual_capture,
            state="disabled"
        )
        self.manual_capture_btn.pack(pady=10, fill="x")
        
        # Feedback section
        feedback_section = ctk.CTkFrame(left_panel)
        feedback_section.pack(pady=10, padx=10, fill="both", expand=True)
        
        ctk.CTkLabel(
            feedback_section,
            text="Feedback",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        self.feedback_text = ctk.CTkTextbox(feedback_section, height=200)
        self.feedback_text.pack(pady=5, fill="both", expand=True)
        
        # TTS toggle
        self.tts_var = tk.BooleanVar(value=True)
        tts_check = ctk.CTkCheckBox(
            left_panel,
            text="Voice Guidance",
            variable=self.tts_var,
            command=self.toggle_tts
        )
        tts_check.pack(pady=10)
        
        # Right panel - Camera feed
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Camera canvas
        self.camera_canvas = tk.Canvas(right_panel, width=960, height=720, bg="gray20")
        self.camera_canvas.pack()
        
        # Back button
        back_btn = ctk.CTkButton(
            self.root,
            text="← Back to Dashboard",
            command=self.stop_camera_and_back
        )
        back_btn.pack(pady=10)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Start camera
        self.start_camera()
    
    def upload_image(self, image_type: str):
        """Upload an image"""
        file_path = filedialog.askopenfilename(
            title=f"Select {image_type} image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                self.uploaded_images[image_type] = img
                self.display_uploaded_image(img)
                self.update_process_button()
                messagebox.showinfo("Success", f"{image_type.title()} image uploaded!")
    
    def display_uploaded_image(self, img):
        """Display uploaded image on canvas"""
        # Resize for display
        h, w = img.shape[:2]
        max_w, max_h = 800, 600
        scale = min(max_w/w, max_h/h)
        new_w, new_h = int(w*scale), int(h*scale)
        
        img_resized = cv2.resize(img, (new_w, new_h))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        
        self.upload_canvas.delete("all")
        self.upload_canvas.create_image(400, 300, image=img_tk)
        self.upload_canvas.image = img_tk  # Keep reference
    
    def update_process_button(self):
        """Enable process button if all images uploaded"""
        if len(self.uploaded_images) >= 3:
            self.process_btn.configure(state="normal")
    
    def process_uploaded_images(self):
        """Process uploaded images and compute measurements"""
        try:
            # Get reference size
            ref_size = float(self.ref_size_entry.get())
            ref_axis = self.axis_var.get()
            
            # Process reference image
            ref_img = self.uploaded_images['reference']
            ref_px = self.reference_detector.detect_reference(ref_img, ref_axis)
            
            if ref_px is None:
                messagebox.showerror("Error", "Could not detect reference object!")
                return
            
            # Calculate scale factor
            scale_factor = ref_size / ref_px
            
            # Process front and side images
            results = {}
            for view in ['front', 'side']:
                if view in self.uploaded_images:
                    img = self.uploaded_images[view]
                    
                    # Segment person
                    mask = self.segmentation_model.segment_person(img)
                    
                    # Detect landmarks
                    landmarks = self.landmark_detector.detect(img)
                    
                    # Calculate measurements
                    measurements = self.measurement_engine.calculate_measurements(
                        landmarks, scale_factor, view
                    )
                    
                    results[view] = {
                        'mask': mask,
                        'landmarks': landmarks,
                        'measurements': measurements
                    }
            
            # Display results
            self.display_results(results, scale_factor)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid reference size!")
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
    
    def display_results(self, results: Dict, scale_factor: float):
        """Display measurement results"""
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "=== MEASUREMENT RESULTS ===\n\n")
        self.results_text.insert("end", f"Scale Factor: {scale_factor:.4f} cm/px\n\n")
        
        for view, data in results.items():
            self.results_text.insert("end", f"\n{view.upper()} VIEW:\n")
            self.results_text.insert("end", "-" * 40 + "\n")
            
            for name, value in data['measurements'].items():
                self.results_text.insert("end", f"{name}: {value:.2f} cm\n")
    
    def start_camera(self):
        """Start camera capture"""
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera_running = True
        
        # Start camera thread
        threading.Thread(target=self.camera_loop, daemon=True).start()
        
        # Start processing thread
        threading.Thread(target=self.process_camera_frames, daemon=True).start()
    
    def camera_loop(self):
        """Camera capture loop"""
        while self.camera_running:
            ret, frame = self.camera.read()
            if ret:
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
    
    def process_camera_frames(self):
        """Process camera frames"""
        import time
        
        while self.camera_running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Draw template overlay
                frame_with_overlay = self.draw_template_overlay(frame.copy())
                
                if self.reference_captured:
                    # Segment person
                    mask = self.segmentation_model.segment_person(frame)
                    
                    # Detect landmarks
                    landmarks = self.landmark_detector.detect(frame)
                    
                    # Check reference stability
                    ref_stable = self.temporal_stabilizer.check_reference_stability(frame)
                    
                    # Check alignment
                    alignment = self.check_alignment(landmarks, mask, ref_stable)
                    
                    # Update status
                    self.update_alignment_status(alignment)
                    
                    # Draw feedback
                    frame_with_overlay = self.draw_feedback(
                        frame_with_overlay, landmarks, mask, alignment
                    )
                    
                    # Check for auto-capture
                    if alignment == 'green':
                        self.handle_green_alignment()
                    else:
                        self.green_start_time = None
                        self.countdown_active = False
                
                # Display frame
                self.display_camera_frame(frame_with_overlay)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
    
    def draw_template_overlay(self, frame):
        """Draw semi-transparent body template overlay"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Draw body outline template
        # Head
        cv2.circle(overlay, (w//2, h//4), 40, (255, 255, 255), 2)
        
        # Body
        cv2.line(overlay, (w//2, h//4 + 40), (w//2, h//2 + 100), (255, 255, 255), 2)
        
        # Arms
        cv2.line(overlay, (w//2, h//4 + 60), (w//2 - 100, h//2 + 50), (255, 255, 255), 2)
        cv2.line(overlay, (w//2, h//4 + 60), (w//2 + 100, h//2 + 50), (255, 255, 255), 2)
        
        # Legs
        cv2.line(overlay, (w//2, h//2 + 100), (w//2 - 50, h - 50), (255, 255, 255), 2)
        cv2.line(overlay, (w//2, h//2 + 100), (w//2 + 50, h - 50), (255, 255, 255), 2)
        
        # Blend
        alpha = 0.3
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame
    
    def check_alignment(self, landmarks, mask, ref_stable):
        """Check alignment status"""
        if landmarks is None or mask is None:
            return 'red'
        
        if not ref_stable:
            return 'red'
        
        # Check if full body visible
        if not self.is_full_body_visible(landmarks):
            return 'red'
        
        # Check posture
        posture_score = self.calculate_posture_score(landmarks)
        
        if posture_score > 0.9:
            return 'green'
        elif posture_score > 0.7:
            return 'amber'
        else:
            return 'red'
    
    def is_full_body_visible(self, landmarks):
        """Check if full body is visible"""
        # Check if feet landmarks are visible
        return landmarks is not None
    
    def calculate_posture_score(self, landmarks):
        """Calculate posture alignment score"""
        # Simplified scoring
        return 0.85  # Placeholder
    
    def update_alignment_status(self, alignment):
        """Update status display"""
        self.alignment_status = alignment
        
        colors = {'red': 'red', 'amber': 'orange', 'green': 'green'}
        texts = {
            'red': '🔴 Adjust Position',
            'amber': '🟡 Almost Ready',
            'green': '🟢 Perfect!'
        }
        
        self.status_label.configure(
            text=texts[alignment],
            text_color=colors[alignment]
        )
    
    def handle_green_alignment(self):
        """Handle green alignment state"""
        import time
        
        if self.green_start_time is None:
            self.green_start_time = time.time()
            self.countdown_active = True
        
        elapsed = time.time() - self.green_start_time
        remaining = 3 - elapsed
        
        if remaining > 0:
            self.countdown_label.configure(text=f"{int(remaining) + 1}")
        else:
            # Auto-capture
            self.auto_capture()
            self.green_start_time = None
            self.countdown_active = False
            self.countdown_label.configure(text="")
    
    def draw_feedback(self, frame, landmarks, mask, alignment):
        """Draw visual feedback on frame"""
        # Draw colored overlay
        overlay = frame.copy()
        
        if alignment == 'green':
            color = (0, 255, 0)
        elif alignment == 'amber':
            color = (0, 165, 255)
        else:
            color = (0, 0, 255)
        
        # Draw border
        h, w = frame.shape[:2]
        cv2.rectangle(overlay, (10, 10), (w-10, h-10), color, 10)
        
        # Blend
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        
        return frame
    
    def display_camera_frame(self, frame):
        """Display frame on canvas"""
        # Resize for display
        h, w = frame.shape[:2]
        frame_resized = cv2.resize(frame, (960, 720))
        
        # Convert to PhotoImage
        img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        
        # Update canvas
        self.camera_canvas.delete("all")
        self.camera_canvas.create_image(480, 360, image=img_tk)
        self.camera_canvas.image = img_tk
    
    def capture_reference_live(self):
        """Capture reference object from live feed"""
        try:
            ref_size = float(self.live_ref_size_entry.get())
            ref_axis = self.live_axis_var.get()
            
            # Get current frame
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                
                # Detect reference
                ref_px = self.reference_detector.detect_reference(frame, ref_axis)
                
                if ref_px:
                    self.reference_size_cm = ref_size
                    self.reference_axis = ref_axis
                    self.reference_px_size = ref_px
                    self.reference_captured = True
                    
                    # Initialize temporal stabilizer
                    self.temporal_stabilizer.initialize_reference(frame, ref_px)
                    
                    self.manual_capture_btn.configure(state="normal")
                    messagebox.showinfo("Success", "Reference captured!")
                    self.speak("Reference captured successfully")
                else:
                    messagebox.showerror("Error", "Reference object not detected!")
                    self.speak("Reference object not found")
        except ValueError:
            messagebox.showerror("Error", "Invalid reference size!")
    
    def manual_capture(self):
        """Manual capture button"""
        self.auto_capture()
    
    def auto_capture(self):
        """Auto-capture measurement"""
        if not self.frame_queue.empty():
            frame = self.frame_queue.get()
            
            # Process and save
            self.speak("Capturing measurement")
            messagebox.showinfo("Captured", "Measurement captured!")
            
            # TODO: Process and display results
    
    def speak(self, text: str):
        """Text-to-speech output"""
        if self.tts_enabled:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
                pass
    
    def toggle_tts(self):
        """Toggle TTS on/off"""
        self.tts_enabled = self.tts_var.get()
    
    def stop_camera_and_back(self):
        """Stop camera and return to dashboard"""
        self.camera_running = False
        if self.camera:
            self.camera.release()
        self.back_to_dashboard()
    
    def back_to_dashboard(self):
        """Return to main dashboard"""
        self.clear_window()
        self.build_dashboard()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = BodyMeasurementDashboard()
    app.run()
