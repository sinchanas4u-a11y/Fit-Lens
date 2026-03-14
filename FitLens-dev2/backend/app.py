"""
Flask Backend API for Body Measurement System
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import io
from PIL import Image
import threading
import queue
import time

from reference_detector import ReferenceDetector
from temporal_stabilizer import TemporalStabilizer
from measurement_engine import MeasurementEngine
from segmentation_model import SegmentationModel
from landmark_detector import LandmarkDetector
from smpl.smpl_pipeline import run_smpl_pipeline
from smpl.smpl_estimator import SMPLEstimator

import sys
import os

# Add parent directory to path so we can
# import from processing/ folder
parent_dir = os.path.dirname(
  os.path.dirname(os.path.abspath(__file__))
)
if parent_dir not in sys.path:
  sys.path.insert(0, parent_dir)

from processing.smplifyx_runner import (
  run_smplifyx
)
from processing.smplifyx_reader import (
  SMPLifyXReader
)

try:
    from face_verifier import FaceVerifier
except Exception:
    FaceVerifier = None

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize models
reference_detector = ReferenceDetector()
temporal_stabilizer = TemporalStabilizer()
measurement_engine = MeasurementEngine()
segmentation_model = SegmentationModel()
landmark_detector = LandmarkDetector()

# Optional face model used for best-effort gender detection.
if FaceVerifier is not None:
    try:
        face_verifier = FaceVerifier(model_name="buffalo_l", det_size=(640, 640))
    except Exception:
        face_verifier = None
else:
    face_verifier = None

# Global state
camera = None
camera_active = False
reference_captured = False
reference_data = {}


def _estimate_height_from_landmarks_px(landmarks):
    if landmarks is None or len(landmarks) < 29:
        return 0.0
    try:
        nose = landmarks[0]
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]
        return float(max(left_ankle[1], right_ankle[1]) - nose[1])
    except Exception:
        return 0.0


def _landmarks_to_smpl_list(landmarks, image_shape):
    if landmarks is None or len(landmarks) < 33:
        return []

    h, w = image_shape[:2]
    smpl_landmarks = []
    for idx in range(33):
        lm = landmarks[idx]
        x = float(lm[0]) if len(lm) > 0 else 0.0
        y = float(lm[1]) if len(lm) > 1 else 0.0
        visibility = float(lm[2]) if len(lm) > 2 else 1.0

        if x > 1.5 or y > 1.5:
            x = x / float(w) if w > 0 else 0.0
            y = y / float(h) if h > 0 else 0.0

        smpl_landmarks.append({
            'x': float(max(0.0, min(1.0, x))),
            'y': float(max(0.0, min(1.0, y))),
            'visibility': float(max(0.0, min(1.0, visibility))),
        })

    return smpl_landmarks


def run_gender_detection(image):
    """Best-effort gender detection. Returns male/female/neutral."""
    try:
        if face_verifier is None or not getattr(face_verifier, 'is_ready', False):
            return 'neutral'
        if not hasattr(face_verifier, 'app') or face_verifier.app is None:
            return 'neutral'

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces = face_verifier.app.get(rgb)
        if not faces:
            return 'neutral'

        face = max(
            faces,
            key=lambda f: float((f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        )

        raw_gender = getattr(face, 'sex', None)
        if raw_gender is None:
            raw_gender = getattr(face, 'gender', None)

        if isinstance(raw_gender, str):
            g = raw_gender.strip().lower()
            if g in ('male', 'm', 'man'):
                return 'male'
            if g in ('female', 'f', 'woman'):
                return 'female'

        if isinstance(raw_gender, (int, float)):
            return 'male' if float(raw_gender) >= 0.5 else 'female'
    except Exception:
        pass

    return 'neutral'


def _build_smpl_merged_measurements(mp_measurements, smpl_m, smpl_success):
    def _mp_entry(name):
        return mp_measurements.get(name, {}) if isinstance(mp_measurements, dict) else {}

    def _mp_cm(name, fallback=None):
        val = _mp_entry(name).get('value_cm')
        return val if val is not None else fallback

    def _mp_px(name, fallback=None):
        val = _mp_entry(name).get('value_px')
        return val if val is not None else fallback

    chest_width_cm = _mp_cm('chest_width', _mp_cm('chest_circumference'))
    waist_width_cm = _mp_cm('waist_width', _mp_cm('waist_circumference'))
    hip_width_cm = _mp_cm('hip_width')

    if smpl_success:
        chest_circ = smpl_m.get('chest_circumference', chest_width_cm)
        waist_circ = smpl_m.get('waist_circumference', waist_width_cm)
        hip_circ = smpl_m.get('hip_circumference', hip_width_cm)
        circ_source = 'SMPL 3D Model'
    else:
        chest_circ = round(chest_width_cm * 3.0, 2) if chest_width_cm is not None else None
        waist_circ = round(waist_width_cm * 3.0, 2) if waist_width_cm is not None else None
        hip_circ = round(hip_width_cm * 3.0, 2) if hip_width_cm is not None else None
        circ_source = 'Estimated'

    merged = {
        'full_height': {
            'value_cm': _mp_cm('full_height'),
            'value_px': _mp_px('full_height'),
            'source': 'MediaPipe',
            'label': 'Full Height',
        },
        'arm_length': {
            'value_cm': _mp_cm('arm_length'),
            'value_px': _mp_px('arm_length'),
            'source': 'MediaPipe',
            'label': 'Arm Length',
        },
        'leg_length': {
            'value_cm': _mp_cm('leg_length'),
            'value_px': _mp_px('leg_length'),
            'source': 'MediaPipe',
            'label': 'Leg Length',
        },
        'torso_length': {
            'value_cm': _mp_cm('torso_length'),
            'value_px': _mp_px('torso_length'),
            'source': 'MediaPipe',
            'label': 'Torso Length',
        },
        'chest_circumference': {
            'value_cm': chest_circ,
            'value_px': None,
            'source': circ_source,
            'label': 'Chest Circumference',
        },
        'waist_circumference': {
            'value_cm': waist_circ,
            'value_px': None,
            'source': circ_source,
            'label': 'Waist Circumference',
        },
        'hip_circumference': {
            'value_cm': hip_circ,
            'value_px': None,
            'source': circ_source,
            'label': 'Hip Circumference',
        },
        'shoulder_width': {
            'value_cm': smpl_m.get('shoulder_width', _mp_cm('shoulder_width')),
            'value_px': _mp_px('shoulder_width'),
            'source': 'SMPL + MediaPipe',
            'label': 'Shoulder Width',
        },
        'chest_width': {
            'value_cm': smpl_m.get('chest_width', chest_width_cm),
            'value_px': _mp_px('chest_width', _mp_px('chest_circumference')),
            'source': 'SMPL + MediaPipe',
            'label': 'Chest Width',
        },
        'waist_width': {
            'value_cm': smpl_m.get('waist_width', waist_width_cm),
            'value_px': _mp_px('waist_width', _mp_px('waist_circumference')),
            'source': 'SMPL + MediaPipe',
            'label': 'Waist Width',
        },
        'hip_width': {
            'value_cm': smpl_m.get('hip_width', hip_width_cm),
            'value_px': _mp_px('hip_width'),
            'source': 'SMPL + MediaPipe',
            'label': 'Hip Width',
        },
    }

    for key, value in mp_measurements.items():
        if key not in merged:
            merged[key] = value

    cleaned = {}
    for key, value in merged.items():
        if not isinstance(value, dict):
            continue
        cm = value.get('value_cm')
        px = value.get('value_px')
        if cm is None and px is None:
            continue
        cleaned[key] = value

    return cleaned, circ_source


def _build_smpl_mesh_data(smpl_result, user_height_cm, gender='neutral'):
    """Build frontend-ready mesh data from fitted SMPL betas."""
    try:
        if not smpl_result or not smpl_result.get('success'):
            return None

        betas = smpl_result.get('betas')
        if betas is None or user_height_cm is None or float(user_height_cm) <= 0:
            return None

        estimator = SMPLEstimator(gender=gender or 'neutral')
        betas_arr = np.array(betas, dtype=np.float32)

        vertices = estimator.get_vertices(betas_arr)
        faces = np.asarray(estimator.faces, dtype=np.int32)

        y_min = float(vertices[:, 1].min())
        y_max = float(vertices[:, 1].max())
        smpl_height_cm = (y_max - y_min) * 100.0
        if smpl_height_cm <= 0:
            return None

        scale = float(user_height_cm) / smpl_height_cm
        vertices_cm = vertices * 100.0 * scale

        return {
            'vertices': vertices_cm.astype(np.float32).reshape(-1).tolist(),
            'faces': faces.reshape(-1).tolist(),
            'metadata': {
                'vertex_count': int(vertices_cm.shape[0]),
                'face_count': int(faces.shape[0]),
                'height_cm': float(user_height_cm),
                'gender': gender or 'neutral',
            },
        }
    except Exception as mesh_err:
        print(f"Warning: failed to build SMPL mesh data: {mesh_err}")
        return None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'models_loaded': {
            'segmentation': segmentation_model.model is not None,
            'landmarks': landmark_detector.pose is not None,
            'temporal': True
        }
    })


@app.route('/api/upload/process', methods=['POST'])
def process_upload():
    """Process uploaded images"""
    try:
        data = request.json
        
        # Decode images
        front_img = decode_image(data['front_image'])
        side_img = decode_image(data.get('side_image'))
        ref_img = decode_image(data['reference_image'])
        
        # Get reference parameters safely
        try:
            ref_size = float(data.get('reference_size', 29.7))
        except (TypeError, ValueError):
            ref_size = 29.7
            
        ref_axis = data.get('reference_axis', 'height')
        
        # Detect reference
        ref_px = reference_detector.detect_reference(ref_img, ref_axis)
        
        if ref_px is None:
            return jsonify({'error': 'Reference object not detected'}), 400
        
        # Calculate scale factor safely
        try:
            scale_factor = float(ref_size) / float(ref_px)
        except (TypeError, ValueError, ZeroDivisionError):
            scale_factor = 0.0

        user_height_cm = None
        if data.get('user_height') is not None:
            try:
                user_height_cm = float(data.get('user_height'))
            except (TypeError, ValueError):
                user_height_cm = None

        requested_gender = data.get('gender', 'neutral')
        
        # Process front view
        results = {}
        
        if front_img is not None:
            front_results = process_single_image(
                front_img, scale_factor, 'front', user_height_cm=user_height_cm, gender=requested_gender
            )
            results['front'] = front_results
        
        if side_img is not None:
            side_results = process_single_image(
                side_img, scale_factor, 'side', user_height_cm=user_height_cm, gender=requested_gender
            )
            results['side'] = side_results

        import tempfile, cv2, numpy as np

        # Save front image to disk for SMPLify-X
        front_temp_path = os.path.join(
            parent_dir, 'data', 'images', 'front.jpg'
        )
        os.makedirs(
            os.path.dirname(front_temp_path),
            exist_ok=True
        )
        # front_img is a numpy array (cv2 image)
        cv2.imwrite(front_temp_path, front_img)
        print(f"Saved front image: {front_temp_path}")

        # Save side image if provided
        side_temp_path = None
        if side_img is not None:
            side_temp_path = os.path.join(
                parent_dir, 'data', 'images', 'side.jpg'
            )
            cv2.imwrite(side_temp_path, side_img)
            print(f"Saved side image: {side_temp_path}")

        # ── SMPLify-X Integration ──────────────────
        mesh_data    = None
        smplx_meas   = {}
        smplx_status = "not_run"

        try:
            # Get user height safely
            user_height_safe = 170.0  # safe default

            try:
                # Priority 1: from request form data
                if request.form.get('height'):
                    user_height_safe = float(
                        request.form.get('height')
                    )
                    print(f"Height from form: {user_height_safe} cm")

                # Priority 2: from request JSON body
                elif (request.is_json and
                      request.get_json() and
                      request.get_json().get('user_height')): # Checking for user_height which is in data
                    user_height_safe = float(
                        request.get_json().get('user_height')
                    )
                    print(f"Height from JSON: {user_height_safe} cm")
                
                # Priority 2b: check 'height' key too
                elif (request.is_json and
                      request.get_json() and
                      request.get_json().get('height')):
                    user_height_safe = float(
                        request.get_json().get('height')
                    )
                    print(f"Height from JSON (key 'height'): {user_height_safe} cm")

                # Priority 3: from processed results
                else:
                    if 'front' in results:
                        front_meas = (
                            results['front'].get(
                                'measurements', {}
                            ) or {}
                        )
                        for key in [
                            'full_height', 'height',
                            'Height',      'Full Height',
                            'body_height', 'user_height'
                        ]:
                            val = front_meas.get(key)
                            if val is not None:
                                try:
                                    # Handle dict structure in results
                                    if isinstance(val, dict):
                                        user_height_safe = float(val.get('value_cm', 170.0))
                                    else:
                                        user_height_safe = float(val)
                                    print(f"Height from results key '{key}': {user_height_safe} cm")
                                    break
                                except (TypeError, ValueError):
                                    continue

            except (TypeError, ValueError) as e:
                print(f"Height parse error: {e}, using default 170.0 cm")
                user_height_safe = 170.0

            # If user_height_cm was passed in and is valid, use it
            if user_height_cm is not None and user_height_cm > 0:
                final_height = user_height_cm
            else:
                final_height = user_height_safe

            print(f"Final final_height: {final_height} cm")

            print(f"Running SMPLify-X with "
                  f"height={final_height}cm...")

            smplifyx_result = run_smplifyx(
                front_image_path = front_temp_path,
                side_image_path  = side_temp_path,
                timeout_seconds  = 120
            )

            if smplifyx_result["success"]:
                reader = SMPLifyXReader(
                    smplifyx_result["mesh_path"]
                )
                smplx_meas = reader.extract_measurements(
                    final_height
                )
                mesh_data    = reader.export_for_plotly(
                    final_height
                )
                smplx_status = "success"
                print("SMPLify-X completed successfully")

                # Merge SMPLify-X measurements into results
                # SMPLify-X overrides circumferences only
                try:
                    if 'front' in results:
                        m = results['front'].get(
                            'measurements', {}
                        ) or {}
                        for key in [
                            'chest_circumference',
                            'waist_circumference',
                            'hip_circumference',
                            'shoulder_width'
                        ]:
                            val = smplx_meas.get(key)
                            if val is not None:
                                # Ensure we preserve the result structure
                                m[key] = {
                                    'value_cm': float(val),
                                    'source': 'SMPLify-X',
                                    'label': key.replace('_', ' ').title()
                                }
                        results['front']['measurements'] = m
                except Exception as merge_err:
                    print(f"Measurement merge error: {merge_err}")

            else:
                smplx_status = "failed"
                print(f"SMPLify-X failed: "
                      f"{smplifyx_result['error']}")

        except Exception as e:
            smplx_status = "error"
            print(f"SMPLify-X exception: {e}")
            import traceback
            traceback.print_exc()
        # ── End SMPLify-X ─────────────────────────

        return jsonify({
            'success':      True,
            'scale_factor': scale_factor,
            'reference_px': ref_px,
            'calibration': {
                'reference_size_cm': ref_size,
                'reference_size_px': float(ref_px),
                'scale_factor':      float(scale_factor),
                'formula': (
                    f'{ref_size} cm ÷ '
                    f'{ref_px:.2f} px = '
                    f'{scale_factor:.4f} cm/px'
                ),
                'description': (
                    f'1 pixel = {scale_factor:.4f} cm'
                )
            },
            'results':      results,
            'mesh_data':    mesh_data,
            'smplx_status': smplx_status,
            'smplx_measurements': smplx_meas
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_single_image(image, scale_factor, view, user_height_cm=None, gender='neutral'):
    """Process a single image using hybrid vision approach"""
    try:
        print(f"Processing {view} image with scale factor: {scale_factor}")
        
        # Segment person with YOLOv8
        mask = segmentation_model.segment_person(image, conf_threshold=0.5)
        print(f"Segmentation complete: {mask is not None}")
        
        # Apply mask to get clean image (optional - for visualization)
        if mask is not None:
            masked_image = segmentation_model.apply_mask(image, mask, background_mode='dim')
        else:
            masked_image = image
        
        # Detect landmarks on original image (MediaPipe works better on full image)
        landmarks = landmark_detector.detect(image)
        print(f"Landmarks detected: {landmarks is not None}")
        
        if landmarks is None:
            print("ERROR: No landmarks detected")
            return {'error': 'No person detected'}
        
        print(f"Number of landmarks: {len(landmarks)}")

        # SMPL integration right after MediaPipe detection.
        detected_gender = run_gender_detection(image)
        input_gender = gender if gender in ('male', 'female', 'neutral') else 'neutral'
        smpl_gender = detected_gender if detected_gender != 'neutral' else input_gender

        landmarks_list = _landmarks_to_smpl_list(landmarks, image.shape)
        # Guard effective_height_cm against None
        try:
            effective_height_cm = float(user_height_cm) if user_height_cm and float(user_height_cm) > 0 else 0.0
        except (TypeError, ValueError):
            effective_height_cm = 0.0

        if effective_height_cm <= 0 and scale_factor:
            try:
                sf = float(scale_factor)
                if sf > 0:
                    estimated_height_px = _estimate_height_from_landmarks_px(landmarks)
                    if estimated_height_px > 0:
                        effective_height_cm = sf * float(estimated_height_px)
            except (TypeError, ValueError):
                pass

        smpl_success = False
        smpl_m = {}
        smpl_error = None
        smpl_mesh_data = None
        smpl_fit_info = {}
        if len(landmarks_list) == 33 and effective_height_cm > 0:
            h, w = image.shape[:2]
            smpl_result = run_smpl_pipeline(
                landmarks_2d=landmarks_list,
                image_width=w,
                image_height=h,
                user_height_cm=effective_height_cm,
                gender=smpl_gender or 'neutral'
            )
            smpl_success = bool(smpl_result.get('success'))
            if smpl_success:
                smpl_m = smpl_result.get('measurements', {}) or {}
                smpl_fit_info = smpl_result.get('fit', {}) or {}
                # Use mesh_data directly from SMPL pipeline (already computed and scaled)
                smpl_mesh_data = smpl_result.get('mesh_data')
            else:
                smpl_error = smpl_result.get('error')
        else:
            smpl_error = 'Insufficient data for SMPL (height or landmarks unavailable)'
        
        # Extract edge reference points from segmentation for hybrid approach
        edge_reference_points = None
        if mask is not None:
            try:
                # Extract edge reference points (shoulder/chest/waist/hip) from mask rows.
                edge_reference_points = landmark_detector.extract_body_edge_keypoints(mask, landmarks)
                if edge_reference_points:
                    print(f"Edge reference points extracted: {edge_reference_points.get('is_valid')}")
            except Exception as e:
                print(f"Warning: Could not extract edge points: {e}")
                edge_reference_points = None
        
        # Calculate measurements with hybrid approach
        # Uses edge points for width measurements, MediaPipe for others
        measurements = measurement_engine.calculate_measurements_with_confidence(
            landmarks, scale_factor, view, edge_reference_points=edge_reference_points
        )
        
        print(f"Measurements calculated: {len(measurements)} measurements")
        
        # Build MediaPipe measurement payload first, then merge with SMPL.
        mp_measurements = {}
        for name, val in measurements.items():
            cm_value, confidence, source = val
            
            # Calculate pixel distance
            pixel_distance = cm_value / scale_factor if scale_factor > 0 else 0
            
            try:
                cm = float(cm_value) if cm_value is not None else 0.0
                px = float(pixel_distance) if pixel_distance is not None else 0.0
                conf = float(confidence) if confidence is not None else 0.0
                
                mp_measurements[name] = {
                    'value_cm': cm,
                    'value_px': px,
                    'value_pixels': px,
                    'confidence': conf,
                    'source': source,
                    'calculation': f"{px:.2f} px × {float(scale_factor or 0):.4f} cm/px = {cm:.2f} cm"
                }
            except (TypeError, ValueError):
                continue

        measurements_with_pixels, smpl_source_label = _build_smpl_merged_measurements(
            mp_measurements,
            smpl_m,
            smpl_success,
        )
        
        print(f"Measurements with pixels: {len(measurements_with_pixels)}")
    except Exception as e:
        print(f"ERROR in process_single_image: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Processing failed: {str(e)}'}
    
    def _draw_edge_width_overlays(img, edge_points):
        if not edge_points or not edge_points.get('is_valid'):
            return

        # Colors (BGR)
        BLUE = (255, 0, 0)
        ORANGE = (0, 165, 255)
        GREEN = (0, 255, 0)

        def _draw_width_line(left_pt, right_pt, color, radius):
            if not left_pt or not right_pt:
                return
            lx, ly = int(left_pt[0]), int(left_pt[1])
            rx, ry = int(right_pt[0]), int(right_pt[1])
            if (lx == 0 and ly == 0) or (rx == 0 and ry == 0):
                return

            # Draw using identical endpoints for both dots and line.
            cv2.line(img, (lx, ly), (rx, ry), color, 2)
            cv2.circle(img, (lx, ly), radius, color, -1)
            cv2.circle(img, (rx, ry), radius, color, -1)

        _draw_width_line(edge_points.get('shoulder_left'), edge_points.get('shoulder_right'), BLUE, 8)
        _draw_width_line(edge_points.get('chest_left'), edge_points.get('chest_right'), ORANGE, 6)
        _draw_width_line(edge_points.get('waist_left'), edge_points.get('waist_right'), GREEN, 6)

    # Check if we have measurements
    if not measurements_with_pixels:
        print("WARNING: No measurements calculated!")
        # Return basic info even if no measurements
        vis_img = landmark_detector.draw_landmarks(image, landmarks)
        _draw_edge_width_overlays(vis_img, edge_reference_points)
        vis_base64 = encode_image(vis_img)
        return {
            'measurements': {},
            'visualization': vis_base64,
            'landmark_count': len(landmarks),
            'smpl': {
                'enabled': True,
                'success': smpl_success,
                'status': 'active' if smpl_success else 'estimated',
                'source': 'SMPL 3D Model' if smpl_success else 'Estimated',
                'gender': smpl_gender if 'smpl_gender' in locals() else 'neutral',
                'error': smpl_error,
                'fit_status': smpl_fit_info.get('fit_status', 'fitted' if smpl_success else 'estimated'),
                'status_text': smpl_fit_info.get('status_text', '✓ Model fitted to your body' if smpl_success else 'Estimated from default body'),
                'fitted_to_user': bool(smpl_fit_info.get('fitted_to_user', smpl_success)),
                'landmarks_source': smpl_fit_info.get('landmarks_source', 'mediapipe'),
                'landmarks_mode': smpl_fit_info.get('landmarks_mode', 'real' if smpl_success else 'unavailable'),
                'landmark_count': int(smpl_fit_info.get('landmark_count', len(landmarks_list))),
                'visible_landmark_count': int(smpl_fit_info.get('visible_landmark_count', 0)),
                'pose_applied': bool(smpl_fit_info.get('pose_applied', False)),
            },
            'mesh_data': smpl_mesh_data,
            'scale_info': {
                'scale_factor': float(scale_factor),
                'unit': 'cm/pixel',
                'description': f'1 pixel = {scale_factor:.4f} cm'
            },
            'warning': 'No measurements could be calculated. Check if all required landmarks are visible.'
        }
    
    # Draw visualization with measurements
    vis_img = landmark_detector.draw_landmarks(image, landmarks)
    _draw_edge_width_overlays(vis_img, edge_reference_points)
    
    # Add measurement annotations
    h, w = vis_img.shape[:2]
    y_offset = 30
    for name, data in list(measurements_with_pixels.items())[:5]:  # Show first 5
        source_label = "Edge" if data['source'] == "Segmentation Edge" else "MediaPipe"
        text = f"{name}: {data['value_cm']:.1f}cm ({source_label})"
        cv2.putText(vis_img, text, (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        y_offset += 25
    
    vis_base64 = encode_image(vis_img)
    
    print(f"Returning {len(measurements_with_pixels)} measurements")
    
    # Add hybrid approach metadata to response
    source_summary = {
        'mediapipe': len([m for m in measurements_with_pixels.values() if m.get('source') == 'MediaPipe']),
        'smpl_model': len([m for m in measurements_with_pixels.values() if m.get('source') == 'SMPL 3D Model']),
        'smpl_mediapipe': len([m for m in measurements_with_pixels.values() if m.get('source') == 'SMPL + MediaPipe']),
        'estimated': len([m for m in measurements_with_pixels.values() if m.get('source') == 'Estimated']),
    }
    
    return {
        'measurements': measurements_with_pixels,
        'visualization': vis_base64,
        'landmark_count': len(landmarks),
        'smpl': {
            'enabled': True,
            'success': smpl_success,
            'status': 'active' if smpl_success else 'estimated',
            'source': smpl_source_label,
            'gender': smpl_gender,
            'error': smpl_error,
            'fit_status': smpl_fit_info.get('fit_status', 'fitted' if smpl_success else 'estimated'),
            'status_text': smpl_fit_info.get('status_text', '✓ Model fitted to your body' if smpl_success else 'Estimated from default body'),
            'fitted_to_user': bool(smpl_fit_info.get('fitted_to_user', smpl_success)),
            'landmarks_source': smpl_fit_info.get('landmarks_source', 'mediapipe'),
            'landmarks_mode': smpl_fit_info.get('landmarks_mode', 'real' if smpl_success else 'unavailable'),
            'landmark_count': int(smpl_fit_info.get('landmark_count', len(landmarks_list))),
            'visible_landmark_count': int(smpl_fit_info.get('visible_landmark_count', 0)),
            'pose_applied': bool(smpl_fit_info.get('pose_applied', False)),
        },
        'mesh_data': smpl_mesh_data,
        'scale_info': {
            'scale_factor': float(scale_factor),
            'unit': 'cm/pixel',
            'description': f'1 pixel = {scale_factor:.4f} cm'
        },
        'hybrid_approach': {
            'enabled': True,
            'edge_points_available': edge_reference_points is not None and edge_reference_points.get('is_valid'),
            'source_summary': source_summary
        }
    }


@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    """Start camera stream"""
    global camera, camera_active
    
    try:
        print("Starting camera...")
        if camera is None:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                print("ERROR: Failed to open camera")
                return jsonify({'error': 'Failed to open camera. Check if camera is available.'}), 500
            
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            print("Camera opened successfully")
        
        camera_active = True
        
        # Start camera thread
        print("Starting camera thread...")
        threading.Thread(target=camera_stream_thread, daemon=True).start()
        print("Camera thread started")
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"ERROR starting camera: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Stop camera stream"""
    global camera, camera_active
    
    camera_active = False
    if camera:
        camera.release()
        camera = None
    
    return jsonify({'success': True})


@app.route('/api/camera/capture-reference', methods=['POST'])
def capture_reference():
    """Capture reference object from camera"""
    global reference_captured, reference_data
    
    try:
        data = request.json
        ref_size = float(data['reference_size'])
        ref_axis = data['reference_axis']
        
        if camera is None:
            return jsonify({'error': 'Camera not started'}), 400
        
        # Capture frame
        ret, frame = camera.read()
        if not ret:
            return jsonify({'error': 'Failed to capture frame'}), 500
        
        # Detect reference
        ref_px = reference_detector.detect_reference(frame, ref_axis)
        
        if ref_px is None:
            return jsonify({'error': 'Reference object not detected'}), 400
        
        # Store reference data
        reference_data = {
            'size_cm': ref_size,
            'size_px': ref_px,
            'axis': ref_axis,
            'scale_factor': ref_size / ref_px
        }
        reference_captured = True
        
        # Initialize temporal stabilizer
        temporal_stabilizer.initialize_reference(frame, ref_px)
        
        return jsonify({
            'success': True,
            'reference_px': ref_px,
            'scale_factor': reference_data['scale_factor']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/camera/capture-measurement', methods=['POST'])
def capture_measurement():
    """Capture and process measurement"""
    global reference_captured, reference_data
    
    if not reference_captured:
        return jsonify({'error': 'Reference not captured'}), 400
    
    try:
        # Capture frame
        ret, frame = camera.read()
        if not ret:
            return jsonify({'error': 'Failed to capture frame'}), 500
        
        # Process frame
        result = process_single_image(
            frame,
            reference_data['scale_factor'],
            'front'
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def camera_stream_thread():
    """Camera streaming thread"""
    global camera_active, reference_captured, reference_data
    
    print("Camera thread running...")
    green_frame_count = 0
    countdown_started = False
    
    try:
        while camera_active:
            if camera is None:
                print("Camera is None, breaking")
                break
            
            ret, frame = camera.read()
            if not ret:
                print("Failed to read frame")
                time.sleep(0.1)
                continue
            
            # Flip for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame
            try:
                processed_frame, alignment_status, has_object = process_camera_frame(frame)
            except Exception as e:
                print(f"Error processing frame: {e}")
                processed_frame = frame
                alignment_status = 'red'
                has_object = False
        
        # Auto-capture logic
        if reference_captured and has_object:
            if alignment_status == 'green':
                green_frame_count += 1
                countdown = max(0, 90 - green_frame_count) // 30  # 3 seconds at 30 FPS
                
                if green_frame_count >= 90:  # 3 seconds
                    # Auto-capture
                    try:
                        result = process_single_image(
                            frame,
                            reference_data['scale_factor'],
                            'front'
                        )
                        socketio.emit('auto_capture', {
                            'success': True,
                            'result': result
                        })
                        green_frame_count = 0
                    except Exception as e:
                        print(f"Auto-capture error: {e}")
                        green_frame_count = 0
            else:
                green_frame_count = 0
                countdown = None
        else:
            green_frame_count = 0
            countdown = None
        
            # Encode and emit
            try:
                _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                socketio.emit('camera_frame', {
                    'frame': frame_base64,
                    'timestamp': time.time(),
                    'alignment': alignment_status,
                    'has_object': has_object,
                    'countdown': countdown
                })
            except Exception as e:
                print(f"Error encoding/emitting frame: {e}")
            
            time.sleep(0.033)  # ~30 FPS
    except Exception as e:
        print(f"Camera thread error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Camera thread stopped")


def process_camera_frame(frame):
    """Process camera frame with overlays"""
    if not reference_captured:
        # Draw template overlay
        frame = draw_template_overlay(frame)
        return frame, 'red', False
    
    # Detect landmarks
    landmarks = landmark_detector.detect(frame)
    
    # Detect object in hand
    has_object = detect_object_in_hand(frame, landmarks)
    
    if landmarks is not None:
        # Check alignment
        alignment = check_alignment(landmarks, frame, has_object)
        
        # Draw feedback
        frame = draw_feedback_overlay(frame, landmarks, alignment, has_object)
    else:
        alignment = 'red'
    
    return frame, alignment, has_object


def detect_object_in_hand(frame, landmarks):
    """Detect if person is holding an object in hand"""
    if landmarks is None:
        return False
    
    try:
        # Get wrist and hand landmarks
        left_wrist = landmarks[15]  # left wrist
        right_wrist = landmarks[16]  # right wrist
        left_index = landmarks[19]  # left index finger
        right_index = landmarks[20]  # right index finger
        
        # Check if hands are visible and in front of body
        if left_wrist[2] > 0.5 or right_wrist[2] > 0.5:
            # Simple heuristic: if wrist is visible and elevated
            # (above hip level), assume holding object
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            hip_y = (left_hip[1] + right_hip[1]) / 2
            
            # Check if either wrist is above hip level
            if (left_wrist[2] > 0.5 and left_wrist[1] < hip_y) or \
               (right_wrist[2] > 0.5 and right_wrist[1] < hip_y):
                return True
        
        return False
    except:
        return False


def draw_template_overlay(frame):
    """Draw body template overlay"""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    
    # Simple stick figure template
    center_x, center_y = w // 2, h // 2
    
    # Head
    cv2.circle(overlay, (center_x, center_y - 150), 40, (255, 255, 255), 2)
    
    # Body
    cv2.line(overlay, (center_x, center_y - 110), (center_x, center_y + 100), (255, 255, 255), 2)
    
    # Arms
    cv2.line(overlay, (center_x, center_y - 80), (center_x - 100, center_y), (255, 255, 255), 2)
    cv2.line(overlay, (center_x, center_y - 80), (center_x + 100, center_y), (255, 255, 255), 2)
    
    # Legs
    cv2.line(overlay, (center_x, center_y + 100), (center_x - 50, center_y + 250), (255, 255, 255), 2)
    cv2.line(overlay, (center_x, center_y + 100), (center_x + 50, center_y + 250), (255, 255, 255), 2)
    
    # Blend
    frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
    
    return frame


def check_alignment(landmarks, frame, has_object):
    """Check alignment status"""
    # Simplified alignment check
    if landmarks is None:
        return 'red'
    
    # Must have object in hand
    if not has_object:
        return 'red'
    
    # Check if full body visible
    h, w = frame.shape[:2]
    
    # Check feet visibility
    left_ankle = landmarks[27]
    right_ankle = landmarks[28]
    
    if left_ankle[2] < 0.5 or right_ankle[2] < 0.5:
        return 'red'
    
    # Check centering
    center_x = np.mean(landmarks[:, 0])
    if abs(center_x - w/2) > w * 0.2:
        return 'amber'
    
    # Check if standing straight
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
    
    if shoulder_diff > h * 0.05:  # Shoulders not level
        return 'amber'
    
    return 'green'


def draw_feedback_overlay(frame, landmarks, alignment, has_object):
    """Draw feedback overlay"""
    h, w = frame.shape[:2]
    
    # Color based on alignment
    colors = {
        'red': (0, 0, 255),
        'amber': (0, 165, 255),
        'green': (0, 255, 0)
    }
    color = colors.get(alignment, (0, 0, 255))
    
    # Draw border
    cv2.rectangle(frame, (10, 10), (w-10, h-10), color, 8)
    
    # Draw landmarks
    frame = landmark_detector.draw_landmarks(frame, landmarks)
    
    # Draw status text
    if not has_object:
        text = 'Hold Object in Hand'
        color = (0, 0, 255)
    else:
        texts = {
            'red': 'Adjust Position',
            'amber': 'Almost Ready',
            'green': 'Perfect! Hold Still'
        }
        text = texts.get(alignment, '')
    
    cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
               1.2, color, 3, cv2.LINE_AA)
    
    # Draw object indicator
    if has_object:
        cv2.putText(frame, 'Object Detected', (20, h - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
    
    return frame


def decode_image(base64_str):
    """Decode base64 image to numpy array"""
    if not base64_str:
        return None
    
    # Remove data URL prefix if present
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    
    img_data = base64.b64decode(base64_str)
    img = Image.open(io.BytesIO(img_data))
    img_array = np.array(img)
    
    # Convert RGB to BGR for OpenCV
    if len(img_array.shape) == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    return img_array


def encode_image(img_array):
    """Encode numpy array to base64"""
    # Convert BGR to RGB
    if len(img_array.shape) == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


# ========== SHOULDER EDGE DETECTION ENDPOINTS ==========

@app.route('/api/shoulder/detect', methods=['POST'])
def detect_shoulder_edges():
    """
    Detect shoulder edge points from uploaded image
    
    Expected JSON:
    {
        "image": "base64_encoded_image",
        "shoulder_type": "both" (or "left", "right")
    }
    
    Returns:
    {
        "frame_number": int,
        "shoulder_edge_points": [{"x": float, "y": float}, ...],
        "confidence_score": float,
        "detection_quality": {...},
        "visualization": "base64_encoded_image"
    }
    """
    try:
        data = request.json
        
        if 'image' not in data:
            return jsonify({'error': 'Image required'}), 400
        
        # Decode image
        image = decode_image(data['image'])
        shoulder_type = data.get('shoulder_type', 'both')
        
        # Detect landmarks first
        landmarks = landmark_detector.detect(image)
        
        if landmarks is None:
            return jsonify({
                'error': 'No person detected in image'
            }), 400
        
        # Detect shoulder edges
        shoulder_data = landmark_detector.detect_shoulder_edge_points(
            image, landmarks, shoulder_type=shoulder_type
        )
        
        # Create visualization
        annotated_frame = landmark_detector.draw_shoulder_edges(image, shoulder_data)
        vis_base64 = encode_image(annotated_frame)
        
        # Prepare response
        response = {
            'success': True,
            'frame_number': shoulder_data['frame_number'],
            'shoulder_edge_points': shoulder_data['shoulder_edge_points'],
            'confidence_score': shoulder_data['confidence_score'],
            'detection_quality': landmark_detector._assess_detection_quality(shoulder_data),
            'visualization': vis_base64
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shoulder/batch', methods=['POST'])
def batch_detect_shoulder_edges():
    """
    Process multiple frames and detect shoulder edges
    
    Expected JSON:
    {
        "images": ["base64_image1", "base64_image2", ...],
        "shoulder_type": "both"
    }
    
    Returns:
    {
        "success": true,
        "frames": [detection_result1, detection_result2, ...],
        "statistics": {...}
    }
    """
    try:
        data = request.json
        
        if 'images' not in data:
            return jsonify({'error': 'Images array required'}), 400
        
        images = [decode_image(img) for img in data['images']]
        shoulder_type = data.get('shoulder_type', 'both')
        
        results = []
        all_shoulder_data = []
        
        for image in images:
            try:
                # Detect landmarks
                landmarks = landmark_detector.detect(image)
                
                if landmarks is None:
                    results.append({
                        'error': 'No person detected'
                    })
                    continue
                
                # Detect shoulder edges
                shoulder_data = landmark_detector.detect_shoulder_edge_points(
                    image, landmarks, shoulder_type=shoulder_type
                )
                all_shoulder_data.append(shoulder_data)
                results.append(shoulder_data)
            
            except Exception as e:
                results.append({'error': str(e)})
        
        # Calculate statistics
        valid_results = [r for r in all_shoulder_data if isinstance(r, dict)]
        stats = landmark_detector.get_detection_statistics(valid_results)
        
        response = {
            'success': True,
            'total_frames': len(images),
            'frames': results,
            'statistics': stats
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shoulder/export-json', methods=['POST'])
def export_shoulder_json():
    """
    Export shoulder detection data in formatted JSON
    
    Expected JSON:
    {
        "image": "base64_encoded_image",
        "include_raw_points": true
    }
    
    Returns:
    {
        "json_data": {...},
        "json_string": "..." (formatted JSON string)
    }
    """
    try:
        data = request.json
        
        if 'image' not in data:
            return jsonify({'error': 'Image required'}), 400
        
        # Decode and process image
        image = decode_image(data['image'])
        include_raw_points = data.get('include_raw_points', True)
        
        # Detect landmarks
        landmarks = landmark_detector.detect(image)
        if landmarks is None:
            return jsonify({'error': 'No person detected'}), 400
        
        # Detect shoulder edges
        shoulder_data = landmark_detector.detect_shoulder_edge_points(image, landmarks)
        
        # Export to JSON string
        json_string = landmark_detector.export_shoulder_data_json(
            shoulder_data, include_raw_points=include_raw_points
        )
        
        # Parse back to return both string and object
        json_obj = json.loads(json_string)
        
        return jsonify({
            'success': True,
            'json_object': json_obj,
            'json_string': json_string
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shoulder/stats', methods=['POST'])
def get_shoulder_stats():
    """
    Get statistics from multiple shoulder detections
    
    Expected JSON:
    {
        "images": ["base64_image1", "base64_image2", ...]
    }
    
    Returns:
    {
        "statistics": {
            "total_frames": int,
            "average_confidence": float,
            "detection_success_rate": float,
            ...
        }
    }
    """
    try:
        data = request.json
        
        if 'images' not in data:
            return jsonify({'error': 'Images array required'}), 400
        
        images = [decode_image(img) for img in data['images']]
        results_list = landmark_detector.batch_detect_shoulder_edges(images)
        
        # Calculate statistics
        stats = landmark_detector.get_detection_statistics(results_list)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'recommendation': get_detection_recommendation(stats)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_detection_recommendation(stats: dict) -> str:
    """Get recommendation based on detection statistics"""
    success_rate = stats.get('detection_success_rate', 0)
    avg_conf = stats.get('average_confidence', 0)
    
    if success_rate >= 0.9 and avg_conf >= 0.85:
        return 'Excellent detection quality. Ready for production use.'
    elif success_rate >= 0.75 and avg_conf >= 0.70:
        return 'Good detection quality. Suitable for most applications.'
    elif success_rate >= 0.6 and avg_conf >= 0.60:
        return 'Fair detection quality. May need manual review for critical uses.'
    else:
        return 'Poor detection quality. Recommend retaking measurements or adjusting capture conditions.'


# ========== SEGMENTATION-BASED SHOULDER REFINEMENT ENDPOINTS ==========

@app.route('/api/shoulder/detect-refined', methods=['POST'])
def detect_refined_shoulders():
    """
    Detect and refine shoulder landmarks using segmentation mask
    
    This endpoint uses YOLOv8 segmentation to refine shoulder landmarks
    for improved accuracy in shoulder-based measurements.
    
    Expected JSON:
    {
        "image": "base64_encoded_image",
        "enable_refinement": true,
        "confidence_threshold": 0.5,
        "scale_factor": 0.2 (pixels to cm conversion)
    }
    
    Returns:
    {
        "success": true,
        "refined_shoulders": {
            "left_shoulder": {"x": float, "y": float, "confidence": float},
            "right_shoulder": {"x": float, "y": float, "confidence": float},
            "shoulder_width_cm": float,
            "refinement_quality": float,
            "is_refined": true
        },
        "original_shoulders": {
            "left_shoulder": {...},
            "right_shoulder": {...},
            "shoulder_width_cm": float
        },
        "measurements": {
            "shoulder_width": [value_cm, confidence, source],
            "chest_width": [value_cm, confidence, source],
            "arm_span": [value_cm, confidence, source]
        },
        "comparison": {
            "improvement_percent": float,
            "quality_gain": float,
            "recommendation": string
        },
        "visualization": "base64_annotated_image"
    }
    """
    try:
        data = request.json
        
        if 'image' not in data:
            return jsonify({'error': 'Image required'}), 400
        
        # Decode image
        image = decode_image(data['image'])
        enable_refinement = data.get('enable_refinement', True)
        scale_factor = data.get('scale_factor', 0.2)  # Default: 1 pixel = 0.2 cm
        
        # Detect landmarks from image
        landmarks = landmark_detector.detect(image)
        
        if landmarks is None:
            return jsonify({
                'error': 'No person detected in image'
            }), 400
        
        # Get original shoulder positions
        left_shoulder_idx = 11
        right_shoulder_idx = 12
        left_shoulder_orig = landmarks[left_shoulder_idx]
        right_shoulder_orig = landmarks[right_shoulder_idx]
        
        original_shoulders = {
            'left_shoulder': {
                'x': float(left_shoulder_orig[0]),
                'y': float(left_shoulder_orig[1]),
                'confidence': float(left_shoulder_orig[2])
            },
            'right_shoulder': {
                'x': float(right_shoulder_orig[0]),
                'y': float(right_shoulder_orig[1]),
                'confidence': float(right_shoulder_orig[2])
            },
            'shoulder_width_cm': float(
                np.linalg.norm(left_shoulder_orig[:2] - right_shoulder_orig[:2]) * scale_factor
            )
        }
        
        refined_data = None
        measurements_with_refinement = None
        
        # Apply segmentation-based refinement if enabled
        if enable_refinement:
            # Generate segmentation mask
            mask = segmentation_model.segment_person(image, conf_threshold=0.5)
            
            if mask is not None:
                # Refine shoulder landmarks using segmentation
                refined_data = landmark_detector.refine_shoulder_landmarks(
                    image, landmarks, mask
                )
                
                # Calculate measurements with refined shoulders
                measurements_with_refinement = (
                    measurement_engine.calculate_shoulder_measurements_only(
                        landmarks, scale_factor, refined_data
                    )
                )
            else:
                # Fallback if segmentation failed
                measurements_with_refinement = (
                    measurement_engine.calculate_shoulder_measurements_only(
                        landmarks, scale_factor, None
                    )
                )
        else:
            # Calculate without refinement
            measurements_with_refinement = (
                measurement_engine.calculate_shoulder_measurements_only(
                    landmarks, scale_factor, None
                )
            )
        
        # Format measurements
        measurements_formatted = {}
        for name, (value, conf, source) in measurements_with_refinement.items():
            measurements_formatted[name] = [value, conf, source]
        
        # Create refined shoulders response
        refined_shoulders_response = None
        comparison = None
        
        if refined_data and refined_data.get('is_refined'):
            refined_shoulders_response = {
                'left_shoulder': {
                    'x': float(refined_data['left_shoulder']['x']),
                    'y': float(refined_data['left_shoulder']['y']),
                    'confidence': float(refined_data['left_shoulder']['confidence'])
                },
                'right_shoulder': {
                    'x': float(refined_data['right_shoulder']['x']),
                    'y': float(refined_data['right_shoulder']['y']),
                    'confidence': float(refined_data['right_shoulder']['confidence'])
                },
                'shoulder_width_cm': float(
                    np.linalg.norm(
                        np.array([refined_data['left_shoulder']['x'], refined_data['left_shoulder']['y']]) -
                        np.array([refined_data['right_shoulder']['x'], refined_data['right_shoulder']['y']])
                    ) * scale_factor
                ),
                'refinement_quality': float(refined_data.get('refinement_quality', 0.0)),
                'is_refined': True
            }
            
            # Calculate comparison
            orig_width = original_shoulders['shoulder_width_cm']
            refined_width = refined_shoulders_response['shoulder_width_cm']
            
            # Check if refinement is realistic (shoulder width should be 30-60cm)
            if 30 <= refined_width <= 60:
                improvement_percent = abs(refined_width - orig_width) / orig_width * 100
                quality_gain = refined_data.get('refinement_quality', 0.0)
                
                if quality_gain >= 0.8:
                    recommendation = 'Excellent refinement. Use refined shoulders for measurements.'
                elif quality_gain >= 0.6:
                    recommendation = 'Good refinement. Refined shoulders recommended.'
                elif quality_gain >= 0.4:
                    recommendation = 'Moderate refinement. Consider original landmarks.'
                else:
                    recommendation = 'Poor refinement. Use original landmarks.'
            else:
                improvement_percent = 0
                quality_gain = 0
                recommendation = 'Refinement produced unrealistic values. Using original landmarks.'
                refined_shoulders_response = None
            
            comparison = {
                'improvement_percent': improvement_percent,
                'quality_gain': quality_gain,
                'recommendation': recommendation,
                'original_shoulder_width': float(original_shoulders['shoulder_width_cm']),
                'refined_shoulder_width': float(refined_shoulders_response['shoulder_width_cm']) if refined_shoulders_response else None
            }
        else:
            refined_shoulders_response = {
                'is_refined': False,
                'reason': 'Segmentation mask unavailable or refinement disabled'
            }
        
        # Create visualization
        annotated_frame = image.copy()
        
        # Draw original shoulders (red)
        cv2.circle(annotated_frame, 
                  (int(left_shoulder_orig[0]), int(left_shoulder_orig[1])),
                  8, (0, 0, 255), -1)
        cv2.circle(annotated_frame,
                  (int(right_shoulder_orig[0]), int(right_shoulder_orig[1])),
                  8, (0, 0, 255), -1)
        
        # Draw shoulder width line (red)
        cv2.line(annotated_frame,
                (int(left_shoulder_orig[0]), int(left_shoulder_orig[1])),
                (int(right_shoulder_orig[0]), int(right_shoulder_orig[1])),
                (0, 0, 255), 2)
        
        # Draw refined shoulders if available (green)
        if refined_shoulders_response and refined_shoulders_response.get('is_refined'):
            left_ref = refined_shoulders_response['left_shoulder']
            right_ref = refined_shoulders_response['right_shoulder']
            
            cv2.circle(annotated_frame, (int(left_ref['x']), int(left_ref['y'])), 8, (0, 255, 0), -1)
            cv2.circle(annotated_frame, (int(right_ref['x']), int(right_ref['y'])), 8, (0, 255, 0), -1)
            
            # Draw refined shoulder line (green)
            cv2.line(annotated_frame,
                    (int(left_ref['x']), int(left_ref['y'])),
                    (int(right_ref['x']), int(right_ref['y'])),
                    (0, 255, 0), 2)
            
            # Add legend
            cv2.putText(annotated_frame, 'Original (Red)', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(annotated_frame, 'Refined (Green)', (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        vis_base64 = encode_image(annotated_frame)
        
        response = {
            'success': True,
            'refined_shoulders': refined_shoulders_response,
            'original_shoulders': original_shoulders,
            'measurements': measurements_formatted,
            'comparison': comparison,
            'visualization': vis_base64
        }
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/shoulder/refine-batch', methods=['POST'])
def refine_batch_shoulders():
    """
    Process multiple images and refine shoulder landmarks
    
    Expected JSON:
    {
        "images": ["base64_image1", "base64_image2", ...],
        "scale_factor": 0.2
    }
    
    Returns:
    {
        "success": true,
        "total_frames": int,
        "results": [refined_result1, refined_result2, ...],
        "average_refinement_quality": float,
        "average_improvement": float
    }
    """
    try:
        data = request.json
        
        if 'images' not in data:
            return jsonify({'error': 'Images array required'}), 400
        
        images = [decode_image(img) for img in data['images']]
        scale_factor = data.get('scale_factor', 0.2)
        
        results = []
        refinement_qualities = []
        improvements = []
        
        for image in images:
            try:
                # Detect landmarks
                landmarks = landmark_detector.detect(image)
                
                if landmarks is None:
                    results.append({'error': 'No person detected'})
                    continue
                
                # Get original shoulders
                left_shoulder = landmarks[11]
                right_shoulder = landmarks[12]
                orig_width = np.linalg.norm(left_shoulder[:2] - right_shoulder[:2]) * scale_factor
                
                # Generate segmentation mask
                mask = segmentation_model.segment_person(image, conf_threshold=0.5)
                
                if mask is not None:
                    # Refine shoulders
                    refined_data = landmark_detector.refine_shoulder_landmarks(
                        image, landmarks, mask
                    )
                    
                    if refined_data.get('is_refined'):
                        left_ref = refined_data['left_shoulder']
                        right_ref = refined_data['right_shoulder']
                        refined_width = np.linalg.norm(
                            np.array([left_ref['x'], left_ref['y']]) -
                            np.array([right_ref['x'], right_ref['y']])
                        ) * scale_factor
                        
                        improvement = abs(refined_width - orig_width) / orig_width * 100
                        quality = refined_data.get('refinement_quality', 0.0)
                        
                        refinement_qualities.append(quality)
                        improvements.append(improvement)
                        
                        results.append({
                            'success': True,
                            'refined_width': refined_width,
                            'original_width': orig_width,
                            'improvement_percent': improvement,
                            'quality': quality
                        })
                    else:
                        results.append({'error': 'Refinement failed'})
                else:
                    results.append({'error': 'Segmentation mask unavailable'})
            
            except Exception as e:
                results.append({'error': str(e)})
        
        response = {
            'success': True,
            'total_frames': len(images),
            'results': results,
            'average_refinement_quality': float(np.mean(refinement_qualities)) if refinement_qualities else 0.0,
            'average_improvement': float(np.mean(improvements)) if improvements else 0.0,
            'successful_refinements': len([r for r in results if r.get('success')])
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
