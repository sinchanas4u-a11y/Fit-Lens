"""
Flask Backend API for Body Measurement System
Updated workflow: Upload -> Detect Reference -> YOLOv8 Masking -> MediaPipe -> Measurements
Includes Live Camera Mode via WebSockets
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import io
from PIL import Image
import traceback
import sys
import os
import time
import json
import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reference_detector import ReferenceDetector
from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector

# Directory for storing measurement images
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "measurement_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

def save_measurement_image(image_data, view_name, source='upload'):
    """
    Save the measurement image to disk with metadata.
    Args:
        image_data: base64 string or numpy array
        view_name: 'front', 'side', 'right', 'left', etc.
        source: 'upload' or 'camera'
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}_{source}_{view_name}.png"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        # Determine image format and save
        if isinstance(image_data, str):
            # Base64 string
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
        elif isinstance(image_data, np.ndarray):
            # Numpy array
            cv2.imwrite(filepath, image_data)
        else:
            print(f"Warning: Unsupported image format for saving: {type(image_data)}")
            return

        # Save metadata
        metadata = {
            "filename": filename,
            "timestamp": timestamp,
            "view": view_name,
            "source": source
        }
        
        metadata_path = os.path.join(IMAGES_DIR, "metadata.jsonl")
        with open(metadata_path, "a") as f:
            f.write(json.dumps(metadata) + "\n")
            
        print(f"Saved measurement image: {filename}")
        
    except Exception as e:
        print(f"Error saving measurement image: {e}")
        traceback.print_exc()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize models
print("Initializing models...")
reference_detector = ReferenceDetector()
measurement_engine = MeasurementEngine()
segmentation_model = SegmentationModel(model_size='n')  # YOLOv8 nano for speed
landmark_detector = LandmarkDetector()
print("✓ Models initialized")

# Live Session State
class LiveSession:
    def __init__(self):
        self.reset()

    def reset(self):
        self.captured_images = {}
        self.current_view = 'front'  # front, right, back, left
        self.stability_start_time = None
        self.is_stable = False
        self.last_instruction = ""
        self.last_instruction_time = 0
        self.user_height_cm = 0
        self.scale_factor = 0

live_session = LiveSession()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'models_loaded': {
            'yolov8_segmentation': segmentation_model.model is not None,
            'mediapipe_landmarks': landmark_detector.pose is not None,
            'reference_detector': True
        }
    })

# --- WebSocket Events for Live Camera ---

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    live_session.reset()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('reset_session')
def handle_reset():
    live_session.reset()
    print('Session reset')

@socketio.on('process_frame')
def handle_frame(data):
    try:
        # Decode image
        image_data = data.get('image')
        view = data.get('view')
        user_height = data.get('user_height')
        height_unit = data.get('height_unit')

        if not image_data:
            return

        # Update user height if provided
        if user_height:
            height_cm = float(user_height)
            if height_unit == 'inches':
                height_cm *= 2.54
            elif height_unit == 'feet':
                height_cm *= 30.48
            live_session.user_height_cm = height_cm

        # Decode base64 to OpenCV image
        img = decode_image(image_data)
        if img is None:
            return

        # Process frame for alignment
        alignment, instruction, countdown = process_alignment(img, view)

        # Check if we should speak the instruction
        should_speak = False
        current_time = time.time()
        if instruction != live_session.last_instruction and (current_time - live_session.last_instruction_time > 3):
            should_speak = True
            live_session.last_instruction = instruction
            live_session.last_instruction_time = current_time

        # Auto-capture logic
        if countdown == 0:
            # Capture!
            print(f"Capturing {view} view!")
            live_session.captured_images[view] = image_data # Store base64
            
            # Save captured image
            save_measurement_image(image_data, view, source='camera')
            
            # Determine next view
            next_view = get_next_view(view)
            live_session.current_view = next_view
            live_session.stability_start_time = None # Reset timer
            
            # Generate "after capture" voice alert
            after_capture_alerts = {
                'front': 'Front view captured.',
                'right': 'Right side view captured.',
                'back': 'Back view captured.',
                'left': 'Left side view captured.'
            }
            
            # Simple "turn left" message for all except last
            before_msg = 'Turn towards your left.' if next_view != 'complete' else ''
            
            # Combine messages
            after_msg = after_capture_alerts.get(view, '')
            voice_message = f"{after_msg} {before_msg}".strip()
            
            emit('capture_complete', {
                'view': view,
                'image': image_data,
                'next_view': next_view,
                'voice_message': voice_message
            })
            
            if next_view == 'complete':
                # Trigger final processing
                process_all_captured_images()


        emit('frame_processed', {
            'alignment': alignment,
            'instruction': instruction,
            'countdown': countdown if countdown is not None else None,
            'speak': should_speak
        })

    except Exception as e:
        print(f"Error processing frame: {e}")
        traceback.print_exc()

def get_next_view(current):
    # Order: Front → Right → Back → Left
    order = ['front', 'right', 'back', 'left']
    try:
        idx = order.index(current)
        if idx < len(order) - 1:
            return order[idx + 1]
    except ValueError:
        pass
    return 'complete'


def process_alignment(image, view):
    """
    Check if user is aligned (centered + distance + full body visible)
    Returns: alignment_status ('red', 'green'), instruction, countdown
    
    Requirements for GREEN:
    1. Full body visible (all key landmarks detected with good confidence)
    2. User at approximately 1 meter distance
    3. User centered in frame
    """
    h, w, _ = image.shape
    landmarks = landmark_detector.detect(image)

    if landmarks is None:
        live_session.stability_start_time = None
        return 'red', 'No person detected. Please stand in front of camera.', None

    # 1. CHECK FULL BODY VISIBILITY
    # Verify all critical landmarks are visible and have good confidence
    # MediaPipe landmarks: 0=nose, 11,12=shoulders, 23,24=hips, 27,28=ankles
    critical_landmarks = [0, 11, 12, 23, 24, 27, 28]
    
    for idx in critical_landmarks:
        if idx >= len(landmarks):
            live_session.stability_start_time = None
            return 'red', 'Full body not visible. Step back.', None
        
        # Check if landmark is visible (confidence > 0.5)
        # MediaPipe returns [x, y, visibility] for each landmark
        if len(landmarks[idx]) >= 3 and landmarks[idx][2] < 0.5:
            live_session.stability_start_time = None
            return 'red', 'Full body not visible. Adjust position.', None
    
    # Check if feet are visible (ankles should be in frame)
    left_ankle = landmarks[27]
    right_ankle = landmarks[28]
    
    # Ankles should not be at the very edge of frame
    if left_ankle[1] > h * 0.95 or right_ankle[1] > h * 0.95:
        live_session.stability_start_time = None
        return 'red', 'Step back. Feet not fully visible.', None
    
    # Check if head is visible (nose should not be at top edge)
    nose = landmarks[0]
    if nose[1] < h * 0.05:
        live_session.stability_start_time = None
        return 'red', 'Move back. Head too close to edge.', None

    # 2. CHECK CENTERING (horizontal alignment)
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    center_x = (left_shoulder[0] + right_shoulder[0]) / 2
    
    frame_center_x = w / 2
    offset_x = abs(center_x - frame_center_x)
    threshold_x = w * 0.08  # 8% tolerance

    if offset_x > threshold_x:
        live_session.stability_start_time = None
        direction = "left" if center_x < frame_center_x else "right"
        return 'red', f'Move {direction} to center yourself.', None

    # 3. CHECK DISTANCE (target: 1 meter)
    # Calculate person's height in pixels
    ankle_y = max(left_ankle[1], right_ankle[1])
    height_px = ankle_y - nose[1]
    
    # For 1 meter distance, person should occupy approximately 60-80% of frame height
    target_ratio_min = 0.60
    target_ratio_max = 0.80
    current_ratio = height_px / h
    
    if current_ratio < target_ratio_min:
        live_session.stability_start_time = None
        return 'red', 'Move closer. Stand at 1 meter distance.', None
    elif current_ratio > target_ratio_max:
        live_session.stability_start_time = None
        return 'red', 'Move back. Stand at 1 meter distance.', None

    # 4. ALL CONDITIONS MET - START/CONTINUE COUNTDOWN
    if live_session.stability_start_time is None:
        live_session.stability_start_time = time.time()
        return 'green', 'Perfect! Hold still...', 5
    
    # Calculate countdown (5 seconds)
    elapsed = time.time() - live_session.stability_start_time
    remaining = max(0, 5 - int(elapsed))
    

    return 'green', 'Hold still...', remaining

def process_all_captured_images():
    """
    Process all 4 captured images using the existing pipeline
    """
    print("Processing all captured images...")
    try:
        results = {}
        
        # 1. Calculate scale from Front view
        front_img = decode_image(live_session.captured_images.get('front'))
        if front_img is None:
            emit('error', {'message': 'Front image missing'})
            return

        # Detect landmarks for scale
        temp_landmarks = landmark_detector.detect(front_img)
        if temp_landmarks is None:
             emit('error', {'message': 'Could not detect person in front view'})
             return
             
        nose = temp_landmarks[0]
        left_ankle = temp_landmarks[27]
        right_ankle = temp_landmarks[28]
        ankle_y = max(left_ankle[1], right_ankle[1])
        height_px = ankle_y - nose[1]
        
        scale_factor = live_session.user_height_cm / height_px
        live_session.scale_factor = scale_factor
        
        # 2. Process each view
        # 2. Process each view
        views_to_process = ['front', 'right', 'back', 'left']
        
        for view_name in views_to_process:
            img_data = live_session.captured_images.get(view_name)
            if img_data:
                print(f"Processing {view_name} view...")
                img = decode_image(img_data)
                
                # Use 'side' logic for right/left views if needed, or pass specific view name
                # The measurement engine likely expects 'front' or 'side' for specific formulas
                # For now, we pass the actual view name, assuming measurement engine handles it
                # or we map it: right/left -> side
                
                # Map view name for measurement logic if necessary
                # If measurement_engine only knows 'front' and 'side':
                engine_view_name = 'side' if view_name in ['right', 'left'] else view_name
                
                view_results = process_single_view(img, scale_factor, engine_view_name)
                
                # Add original image to results for display
                view_results['original_image'] = img_data
                
                results[view_name] = view_results

        # Construct final response similar to /api/process
        final_response = {
            'success': True,
            'calibration': {
                'user_height_cm': live_session.user_height_cm,
                'height_in_image_px': float(height_px),
                'scale_factor': float(scale_factor),
                'formula': f'{live_session.user_height_cm} cm ÷ {height_px:.2f} px = {scale_factor:.4f} cm/px',
                'description': f'1 pixel = {scale_factor:.4f} cm'
            },
            'results': results
        }
        
        emit('processing_complete', final_response)
        
    except Exception as e:
        print(f"Error in final processing: {e}")
        traceback.print_exc()
        emit('error', {'message': str(e)})


# --- Existing API Routes ---

@app.route('/api/process', methods=['POST'])
def process_images():
    """
    Complete workflow:
    1. Upload photos
    2. Use user's height as reference
    3. YOLOv8-seg masking (detect only human body)
    4. MediaPipe pose (get landmarks)
    5. Compute pixel distances and convert to cm using height
    6. Return measurements as JSON
    """
    try:
        data = request.json
        
        print("\n" + "="*60)
        print("STEP 1: RECEIVING UPLOADED PHOTOS")
        print("="*60)
        
        # Decode images
        front_img = decode_image(data.get('front_image'))
        side_img = decode_image(data.get('side_image'))
        
        if front_img is None:
            return jsonify({'error': 'Front image is required', 'step': 1}), 400
        
        print(f"✓ Front image: {front_img.shape}")
        if side_img is not None:
            print(f"✓ Side image: {side_img.shape}")
            
        # Save uploaded images
        if data.get('front_image'):
            save_measurement_image(data.get('front_image'), 'front', source='upload')
            
        if data.get('side_image'):
            save_measurement_image(data.get('side_image'), 'side', source='upload')
        
        # Get user's height
        user_height_cm = float(data.get('user_height', 0))
        
        if user_height_cm <= 0:
            return jsonify({'error': 'User height is required', 'step': 1}), 400
        
        print(f"✓ User height: {user_height_cm} cm")
        
        print("\n" + "="*60)
        print("STEP 2: CALCULATING SCALE USING USER HEIGHT")
        print("="*60)
        
        # First, we need to detect landmarks to measure height in pixels
        # We'll do a preliminary landmark detection on front image
        print("Detecting landmarks to measure height in pixels...")
        temp_landmarks = landmark_detector.detect(front_img)
        
        if temp_landmarks is None:
            return jsonify({
                'error': 'Could not detect person in image. Please ensure full body is visible.',
                'step': 2
            }), 400
        
        # Calculate height in pixels (from top of head to feet)
        # Use nose (top) to ankle (bottom) as height approximation
        nose = temp_landmarks[0]  # nose
        left_ankle = temp_landmarks[27]  # left ankle
        right_ankle = temp_landmarks[28]  # right ankle
        
        # Use the lower ankle
        ankle_y = max(left_ankle[1], right_ankle[1])
        height_px = ankle_y - nose[1]
        
        if height_px <= 0:
            return jsonify({
                'error': 'Could not measure height in image. Please ensure full body is visible.',
                'step': 2
            }), 400
        
        # Calculate scale factor
        scale_factor = user_height_cm / height_px
        
        print(f"✓ Height in image: {height_px:.2f} pixels")
        print(f"✓ User height: {user_height_cm} cm")
        print(f"✓ Scale factor: {scale_factor:.4f} cm/px")
        print(f"✓ Formula: {user_height_cm} cm ÷ {height_px:.2f} px = {scale_factor:.4f} cm/px")
        
        # Process front view
        print("\n" + "="*60)
        print("PROCESSING FRONT VIEW")
        print("="*60)
        
        front_results = process_single_view(
            front_img, scale_factor, 'front'
        )
        
        results = {
            'front': front_results
        }
        
        # Process side view if provided
        if side_img is not None:
            print("\n" + "="*60)
            print("PROCESSING SIDE VIEW")
            print("="*60)
            
            side_results = process_single_view(
                side_img, scale_factor, 'side'
            )
            results['side'] = side_results
        
        # Prepare final response
        print("\n" + "="*60)
        print("STEP 6: RETURNING MEASUREMENTS AS JSON")
        print("="*60)
        
        response = {
            'success': True,
            'calibration': {
                'user_height_cm': user_height_cm,
                'height_in_image_px': float(height_px),
                'scale_factor': float(scale_factor),
                'formula': f'{user_height_cm} cm ÷ {height_px:.2f} px = {scale_factor:.4f} cm/px',
                'description': f'1 pixel = {scale_factor:.4f} cm'
            },
            'results': results
        }
        
        print("✓ Processing complete!")
        print("="*60 + "\n")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': f'Processing failed: {str(e)}',
            'step': 'unknown'
        }), 500


def process_single_view(image, scale_factor, view_name):
    """
    Process a single view through the complete pipeline:
    Step 3: YOLOv8 segmentation
    Step 4: MediaPipe landmarks
    Step 5: Compute measurements
    """
    try:
        print(f"\nSTEP 3: YOLOv8-SEG MASKING ({view_name.upper()} VIEW)")
        print("-" * 60)
        
        # Run YOLOv8 segmentation to detect only human body
        mask = segmentation_model.segment_person(image, conf_threshold=0.5)
        
        if mask is None:
            print("✗ No person detected in image")
            return {
                'error': 'No person detected',
                'step': 3
            }
        
        print("✓ Human body detected and masked")
        
        # Apply mask to get clean human outline
        masked_image = segmentation_model.apply_mask(image, mask, background_mode='dim')
        
        # Get bounding box of person
        bbox = segmentation_model.get_person_bbox(mask)
        if bbox:
            x, y, w, h = bbox
            print(f"✓ Person bounding box: {w}x{h} at ({x}, {y})")
        
        print(f"\nSTEP 4: MEDIAPIPE POSE LANDMARKS ({view_name.upper()} VIEW)")
        print("-" * 60)
        
        # Run MediaPipe on original image (works better than masked)
        landmarks = landmark_detector.detect(image)
        
        if landmarks is None:
            print("✗ No landmarks detected")
            return {
                'error': 'No landmarks detected',
                'step': 4,
                'mask_available': True
            }
        
        print(f"✓ Detected {len(landmarks)} body landmarks")
        
        print(f"\nSTEP 5: COMPUTING MEASUREMENTS ({view_name.upper()} VIEW)")
        print("-" * 60)
        
        print(f"Calling measurement_engine.calculate_measurements_with_confidence")
        print(f"  Landmarks shape: {landmarks.shape if hasattr(landmarks, 'shape') else 'N/A'}")
        print(f"  Scale factor: {scale_factor}")
        print(f"  View: {view_name}")
        
        # Calculate measurements with pixel distances
        measurements = measurement_engine.calculate_measurements_with_confidence(
            landmarks, scale_factor, view_name
        )
        
        print(f"\n✓ Measurement engine returned: {type(measurements)}")
        print(f"✓ Number of measurements: {len(measurements) if measurements else 0}")
        if measurements:
            print(f"✓ Measurement keys: {list(measurements.keys())[:5]}...")  # Show first 5
        
        # Format measurements for JSON response
        formatted_measurements = {}
        print(f"\n📊 Raw measurements received: {len(measurements)} items")
        print(f"Measurements type: {type(measurements)}")
        print(f"Measurements keys: {list(measurements.keys()) if measurements else 'None'}")
        
        for name, data in measurements.items():
            print(f"\n  Processing measurement: {name}")
            print(f"    Data type: {type(data)}")
            print(f"    Data value: {data}")
            
            if isinstance(data, tuple) and len(data) == 3:
                cm_value, confidence, source = data
                pixel_distance = cm_value / scale_factor if scale_factor > 0 else 0
                
                formatted_measurements[name] = {
                    'value_cm': round(float(cm_value), 2),
                    'value_px': round(float(pixel_distance), 2),
                    'confidence': round(float(confidence), 3),
                    'source': source,
                    'formula': f"{pixel_distance:.2f} px × {scale_factor:.4f} cm/px = {cm_value:.2f} cm"
                }
                
                print(f"  ✓ {name}: {cm_value:.2f} cm (confidence: {confidence:.2f})")
            else:
                print(f"  ⚠️ Unexpected data format for {name}: {data}")
        
        print(f"\n✓ Formatted {len(formatted_measurements)} measurements")
        print(f"Formatted measurements keys: {list(formatted_measurements.keys())}")
        
        # Create visualization
        vis_image = landmark_detector.draw_landmarks(masked_image.copy(), landmarks)
        vis_base64 = encode_image(vis_image)
        
        # Encode mask
        mask_base64 = encode_image(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))
        
        return {
            'success': True,
            'measurements': formatted_measurements,
            'landmark_count': len(landmarks),
            'visualization': vis_base64,
            'mask': mask_base64,
            'bbox': bbox if bbox else None
        }
        
    except Exception as e:
        print(f"✗ Processing error: {e}")
        traceback.print_exc()
        return {
            'error': str(e),
            'step': 'processing'
        }


def decode_image(base64_str):
    """Decode base64 image to numpy array"""
    if not base64_str:
        return None
    
    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        img_data = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(img_data))
        img_array = np.array(img)
        
        # Convert RGB to BGR for OpenCV
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_array
    except Exception as e:
        print(f"Image decode error: {e}")
        return None


def encode_image(img_array):
    """Encode numpy array to base64"""
    try:
        # Convert BGR to RGB
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        
        img = Image.fromarray(img_array)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Image encode error: {e}")
        return None


if __name__ == '__main__':
    print("\n" + "="*60)
    print("BODY MEASUREMENT SYSTEM - BACKEND SERVER")
    print("="*60)
    print("\nWorkflow:")
    print("  1. Upload photos")
    print("  2. Detect reference object")
    print("  3. YOLOv8-seg masking (human body only)")
    print("  4. MediaPipe pose landmarks")
    print("  5. Compute measurements (px → cm)")
    print("  6. Return JSON results")
    print("\n" + "="*60 + "\n")
    
    # Use socketio.run instead of app.run
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
