
import cv2
import numpy as np
import traceback
import os

# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Try to import InsightFace
try:
    import insightface
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    print("InsightFace not installed. Please run: pip install insightface onnxruntime")
    INSIGHTFACE_AVAILABLE = False

class FaceVerifier:
    """
    Handles face verification between two images using InsightFace (ArcFace).
    Uses cosine similarity with proper thresholds for front+side view verification.
    """
    
    def __init__(self, model_name="buffalo_l", det_size=(640, 640)):
        """
        Initialize FaceVerifier with InsightFace.
        
        Args:
            model_name: InsightFace model pack (buffalo_l, buffalo_s, antelopev2)
            det_size: Detection size for face detector
        """
        self.model_name = model_name
        self.det_size = det_size
        self.is_ready = INSIGHTFACE_AVAILABLE
        self.app = None
        
        # Similarity thresholds tuned for front+side view pairs.
        # Side-view faces are partially turned, so ArcFace scores are naturally
        # lower than front+front comparisons. Thresholds are relaxed accordingly.
        self.SAME_PERSON_THRESHOLD = 0.25      # RELAXED: >= 0.25 → verified (from 0.35)
        self.DIFFERENT_PERSON_THRESHOLD = 0.15  # RELAXED: < 0.15 → likely different person (from 0.20)
        # Between 0.15–0.25 → uncertain, allow with warning
        
        if self.is_ready:
            try:
                print(f"Initializing InsightFace with {model_name} model...")
                # Use CPUExecutionProvider for compatibility
                self.app = FaceAnalysis(name=model_name, providers=['CPUExecutionProvider'])
                # Larger det_size helps detect smaller or rotated faces (side profiles)
                self.app.prepare(ctx_id=0, det_size=(1024, 1024))
                print(f"✓ FaceVerifier initialized successfully with InsightFace (det_size=1024)")
            except Exception as e:
                print(f"Failed to initialize InsightFace: {e}")
                self.is_ready = False
        else:
            print("FaceVerifier disabled: InsightFace library missing.")

    def _detect_and_extract_embedding(self, img_array, label="image"):
        """
        Detect face and extract 512-D embedding from image.
        
        Args:
            img_array: Image as numpy array (BGR format)
            label: Descriptive label for logging (e.g. "front", "side")
            
        Returns:
            tuple: (embedding, face_detected, det_score)
                - embedding: 512-D numpy array or None
                - face_detected: bool
                - det_score: float (detection confidence)
        """
        if img_array is None:
            return None, False, 0.0
            
        try:
            # InsightFace expects RGB
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.app.get(img_rgb)
            
            if len(faces) == 0:
                print(f"⚠ No face detected in {label} image")
                return None, False, 0.0
            
            # Use the first detected face (largest by default)
            face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
            embedding = face.embedding
            det_score = float(face.det_score)
            
            # Normalize embedding (L2 normalization)
            embedding = embedding / (np.linalg.norm(embedding) + 1e-6)
            
            print(f"✓ Face detected in {label} (confidence: {det_score:.4f}), embedding shape: {embedding.shape}")
            return embedding, True, det_score
            
        except Exception as e:
            print(f"Error during face detection/embedding for {label}: {e}")
            traceback.print_exc()
            return None, False, 0.0

    def _calculate_cosine_similarity(self, emb1, emb2):
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding (normalized)
            emb2: Second embedding (normalized)
            
        Returns:
            float: Cosine similarity (0 to 1, higher = more similar)
        """
        # Since embeddings are already normalized, dot product = cosine similarity
        similarity = np.dot(emb1, emb2)
        return float(similarity)

    def analyze_face_quality(self, img, face):
        """
        Analyze face image quality for common issues.
        
        Args:
            img: Original image array
            face: InsightFace face object
            
        Returns:
            list: List of error strings (empty if quality is good)
        """
        issues = []
        try:
            h, w = img.shape[:2]
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # Ensure bbox is within image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            face_w = x2 - x1
            face_h = y2 - y1
            
            if face_w <= 0 or face_h <= 0:
                return ["Invalid face bounding box"]
            
            # 1. Face Size Check
            # Face area relative to image area
            face_area = face_w * face_h
            img_area = w * h
            face_ratio = face_area / img_area
            
            # Threshold: Face should be at least ~3-4% of image for reliable verification
            if face_ratio < 0.03:
                issues.append("Face too small / too far from camera")
            elif face_ratio > 0.60:
                issues.append("Face too large / too close to camera")

            # 1.5 Cropped Face Check
            # Check if bbox is touching image boundaries
            margin = 5
            if x1 <= margin or y1 <= margin or x2 >= w - margin or y2 >= h - margin:
                 issues.append("Face partially cropped / touching edges")

            # 1.6 Occlusion Check (Heuristic)
            # InsightFace doesn't always give explicit occlusion score, but we can check landmark spread or confidence if available.
            # Simplified heuristic: If detection score is low despite good size, maybe obscured.
            # Or if landmarks are tightly clustered?
            # For now, let's rely on detection score and blur.
            # If we want to be more specific, we could check eye distance ratio, etc.
            if face.det_score < 0.6: # If confidence is low but detected
                 issues.append("Face not clearly visible (occlusion or blur)")

                
            # 2. Blur Check
            # Laplacian variance on the face ROI
            face_roi = img[y1:y2, x1:x2]
            gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            # Resize slightly to standard size to make variance threshold more consistent
            # resize to 100px width
            scale = 100.0 / face_w
            if scale < 1: # only shrink, don't upscale blur
                h_new = int(face_h * scale)
                gray_roi_small = cv2.resize(gray_roi, (100, h_new))
            else:
                gray_roi_small = gray_roi
                
            laplacian_var = cv2.Laplacian(gray_roi_small, cv2.CV_64F).var()
            
            # Threshold needs tuning, often < 100 is blurry for direct variance
            # On resized (100px), < 50-100 might be blurry
            if laplacian_var < 80.0:
                issues.append("Image is blurry")
                
            # 3. Lighting Check
            # Mean brightness of face ROI
            mean_brightness = np.mean(gray_roi)
            if mean_brightness < 40:
                issues.append("Poor lighting (too dark)")
            elif mean_brightness > 220:
                issues.append("Poor lighting (too bright)")
                
            # 4. Pose Check
            # In InsightFace, kps (landmarks) can approximate pose
            # nose is index 2, eyes 0,1, mouth 3,4
            kps = face.kps
            if kps is not None:
                left_eye = kps[0]
                right_eye = kps[1]
                nose = kps[2]
                
                # Check horizontal position of nose relative to eyes
                eye_center_x = (left_eye[0] + right_eye[0]) / 2
                eye_dist = np.linalg.norm(left_eye - right_eye)
                
                # Deviation of nose from eye center
                nose_offset = nose[0] - eye_center_x
                
                # Normalize offset by eye distance
                # Ratio > 0.5 usually means significant turn
                yaw_ratio = abs(nose_offset) / (eye_dist + 1e-6)
                
                if yaw_ratio > 0.8: # Roughly > 45-60 degrees
                    issues.append("Face turned too away (extreme pose)")
                    
        except Exception as e:
            print(f"Error checking face quality: {e}")
            
        return issues

    def verify_body_clothing(self, img1, img2):
        """
        Compares upper-body clothing, lower-body clothing, and body color profiles
        between front and side view images with background wall filtering.
        """
        if img1 is None or img2 is None:
            return {'matched': True, 'similarity': 0.5, 'reason': 'Invalid image data'}

        try:
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]

            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

            # Torso ROI: front view (25% to 75% width), side view tighter crop (38% to 62% width)
            torso1 = hsv1[int(h1*0.20):int(h1*0.50), int(w1*0.25):int(w1*0.75)]
            torso2 = hsv2[int(h2*0.20):int(h2*0.50), int(w2*0.38):int(w2*0.62)]

            # Legs ROI: front view (25% to 75% width), side view tighter crop (38% to 62% width)
            legs1 = hsv1[int(h1*0.55):int(h1*0.85), int(w1*0.25):int(w1*0.75)]
            legs2 = hsv2[int(h2*0.55):int(h2*0.85), int(w2*0.38):int(w2*0.62)]

            def create_clothing_mask(hsv_crop):
                s = hsv_crop[:, :, 1]
                v = hsv_crop[:, :, 2]
                mask = (s > 20) | (v < 210)
                return mask.astype(np.uint8) * 255

            mask_t1 = create_clothing_mask(torso1)
            mask_t2 = create_clothing_mask(torso2)

            t_hist1 = cv2.calcHist([torso1], [0, 1], mask_t1, [24, 32], [0, 180, 0, 256])
            t_hist2 = cv2.calcHist([torso2], [0, 1], mask_t2, [24, 32], [0, 180, 0, 256])

            if cv2.countNonZero(t_hist1) > 0 and cv2.countNonZero(t_hist2) > 0:
                cv2.normalize(t_hist1, t_hist1, 0, 1, cv2.NORM_MINMAX)
                cv2.normalize(t_hist2, t_hist2, 0, 1, cv2.NORM_MINMAX)
                torso_sim = float(cv2.compareHist(t_hist1, t_hist2, cv2.HISTCMP_CORREL))
            else:
                torso_sim = 0.5

            mask_l1 = create_clothing_mask(legs1)
            mask_l2 = create_clothing_mask(legs2)

            l_hist1 = cv2.calcHist([legs1], [0, 1], mask_l1, [24, 32], [0, 180, 0, 256])
            l_hist2 = cv2.calcHist([legs2], [0, 1], mask_l2, [24, 32], [0, 180, 0, 256])

            if cv2.countNonZero(l_hist1) > 0 and cv2.countNonZero(l_hist2) > 0:
                cv2.normalize(l_hist1, l_hist1, 0, 1, cv2.NORM_MINMAX)
                cv2.normalize(l_hist2, l_hist2, 0, 1, cv2.NORM_MINMAX)
                legs_sim = float(cv2.compareHist(l_hist1, l_hist2, cv2.HISTCMP_CORREL))
            else:
                legs_sim = 0.5

            body_sim = 0.6 * max(0.0, torso_sim) + 0.4 * max(0.0, legs_sim)
            print(f"👕 Clothing similarity calculation: Torso={torso_sim:.4f}, Legs={legs_sim:.4f}, Overall={body_sim:.4f}")

            if torso_sim < 0.20 or body_sim < 0.25:
                return {
                    'matched': False,
                    'similarity': max(0.0, body_sim),
                    'reason': 'Clothing and appearance do not match between front and side photos (Different people detected)'
                }

            return {
                'matched': True,
                'similarity': max(0.0, body_sim),
                'reason': 'Body & clothing match'
            }
        except Exception as e:
            print(f"Error checking body/clothing match: {e}")
            return {'matched': False, 'similarity': 0.0, 'reason': str(e)}

    def verify_person(self, img1_array, img2_array, threshold=None):
        """
        Verify if two images belong to the same person with quality checks.

        Thresholds are relaxed for front+side pairs because a side-profile
        face naturally scores lower with ArcFace than two front-facing photos.

        Args:
            img1_array: Front image (numpy array BGR)
            img2_array: Side/Other image (numpy array BGR)
            threshold: Optional custom threshold override (default: 0.25)

        Returns:
            dict: {
                'verified': bool,
                'similarity': float,
                'threshold': float,
                'det_scores': {'front': float, 'side': float},
                'warning': bool,
                'no_face': bool,
                'face_fail_reason': str,
                'error': str,
                'issues': {'front': [], 'side': []}
            }
        """
        result = {
            'verified': False,
            'similarity': 0.0,
            'threshold': self.SAME_PERSON_THRESHOLD,
            'det_scores': {'front': 0.0, 'side': 0.0},
            'issues': {'front': [], 'side': []},
            'no_face': False,
            'face_fail_reason': None
        }

        if not self.is_ready:
            result['error'] = "Face verification unavailable (InsightFace library missing)"
            return result
            
        if img1_array is None or img2_array is None:
            result['error'] = "Invalid image data provided"
            return result

        try:
            print("\n" + "="*60)
            print("FACE VERIFICATION - InsightFace")
            print("="*60)
            
            # --- PROCESS FRONT ---
            print("Processing Front image...")
            img1_rgb = cv2.cvtColor(img1_array, cv2.COLOR_BGR2RGB)
            faces1 = self.app.get(img1_rgb)
            
            face1 = None
            if len(faces1) == 0:
                print("✗ No face detected in Front image")
                result['issues']['front'].append("Face not detected")
                result['no_face'] = True
                result['face_fail_reason'] = "No face detected in front image"
            elif len(faces1) > 1:
                print(f"⚠ Multiple faces ({len(faces1)}) detected in Front image")
                result['issues']['front'].append("Multiple faces detected")
                # Pick largest face
                face1 = sorted(faces1, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
            else:
                face1 = faces1[0]

            if face1:
                result['det_scores']['front'] = float(face1.det_score)
                result['issues']['front'].extend(self.analyze_face_quality(img1_array, face1))
            
            # --- PROCESS SIDE ---
            print("Processing Side image...")
            img2_rgb = cv2.cvtColor(img2_array, cv2.COLOR_BGR2RGB)
            faces2 = self.app.get(img2_rgb)
            
            face2 = None
            if len(faces2) == 0:
                print("✗ No face detected in Side image")
                result['issues']['side'].append("Face not detected")
                if not result['no_face']:
                    result['no_face'] = True
                    result['face_fail_reason'] = "No face detected in side image"
            elif len(faces2) > 1:
                print(f"⚠ Multiple faces ({len(faces2)}) detected in Side image")
                result['issues']['side'].append("Multiple faces detected")
                face2 = sorted(faces2, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
            else:
                face2 = faces2[0]

            if face2:
                result['det_scores']['side'] = float(face2.det_score)
                result['issues']['side'].extend(self.analyze_face_quality(img2_array, face2))
                
            # Perform Body & Clothing Consistency Matching
            body_clothing_res = self.verify_body_clothing(img1_array, img2_array)
            print(f"   👕 Body & Clothing Match: {body_clothing_res['matched']} (Similarity: {body_clothing_res['similarity']:.4f})")

            # Handle Missing Face scenarios with body/clothing verification
            if face1 is None or face2 is None:
                if face1 is not None and face2 is None:
                    # Side face not detected by face detector. Check clothing & body match!
                    if not body_clothing_res['matched']:
                        result['verified'] = False
                        result['face_fail_reason'] = body_clothing_res['reason']
                        result['message'] = f"Identity verification failed ({body_clothing_res['reason']})"
                        print(f"✗ REJECTED: Side face missing and clothing/body mismatch detected")
                    else:
                        result['message'] = "Unable to confidently verify face from side image."
                        result['verified'] = True 
                        result['warning'] = True
                        result['fallback_used'] = True
                        print(f"⚠ {result['message']} (Front face detected, Side face missing, Clothing matched)")
                else:
                    result['verified'] = False
                    result['no_face'] = True
                    if face1 is None and face2 is None:
                        result['face_fail_reason'] = "No face detected in either image"
                    else:
                        result['face_fail_reason'] = "No face detected in front image"
                
                return result

            # If clothing/body is a total mismatch (e.g. man in plaid vs woman in red), reject immediately!
            if not body_clothing_res['matched']:
                result['verified'] = False
                result['similarity'] = float(body_clothing_res['similarity'])
                result['face_fail_reason'] = body_clothing_res['reason']
                result['message'] = f"Identity verification failed ({body_clothing_res['reason']})"
                print(f"✗ REJECTED: Severe clothing/appearance mismatch between front and side photos")
                return result

            # Calculate ArcFace Face Cosine Similarity
            emb1 = face1.embedding
            emb1 = emb1 / (np.linalg.norm(emb1) + 1e-6)
            
            emb2 = face2.embedding
            emb2 = emb2 / (np.linalg.norm(emb2) + 1e-6)
            
            similarity = self._calculate_cosine_similarity(emb1, emb2)
            
            thresh = threshold if threshold is not None else self.SAME_PERSON_THRESHOLD
            
            print(f"   Front Confidence: {result['det_scores']['front']:.4f}")
            print(f"   Side Confidence: {result['det_scores']['side']:.4f}")
            print(f"   📊 Similarity Score: {similarity:.4f}")
            print(f"   📏 Threshold: {thresh:.4f}")
            
            verified = similarity >= thresh
            warning = False
            
            # Check for uncertain range
            if self.DIFFERENT_PERSON_THRESHOLD <= similarity < self.SAME_PERSON_THRESHOLD:
                warning = True
                verified = True  # Allow but warn
                print(f"⚠ UNCERTAIN: Similarity in range [{self.DIFFERENT_PERSON_THRESHOLD}, {self.SAME_PERSON_THRESHOLD})")
            
            if verified:
                print(f"✓ VERIFIED: Same person (similarity: {similarity:.4f} >= {thresh:.4f})")
            else:
                print(f"✗ REJECTED: Different person (similarity: {similarity:.4f} < {thresh:.4f})")
                if similarity < self.DIFFERENT_PERSON_THRESHOLD:
                    result['face_fail_reason'] = "Face similarity significantly below threshold (Different people detected)"
                else:
                    result['face_fail_reason'] = "Face similarity below threshold (Mismatch detected)"
            
            print("="*60 + "\n")
            
            result['verified'] = verified
            result['similarity'] = similarity
            result['threshold'] = thresh
            result['distance'] = 1.0 - similarity
            if warning:
                result['warning'] = True
                
            return result
            
            print(f"\n📊 Similarity Score: {similarity:.4f}")
            print(f"📏 Threshold: {thresh:.4f}")
            
            verified = similarity >= thresh
            warning = False
            
            # Check for uncertain range
            if self.DIFFERENT_PERSON_THRESHOLD <= similarity < self.SAME_PERSON_THRESHOLD:
                warning = True
                verified = True  # Allow but warn
                print(f"⚠ UNCERTAIN: Similarity in range [{self.DIFFERENT_PERSON_THRESHOLD}, {self.SAME_PERSON_THRESHOLD})")
            
            if verified:
                print(f"✓ VERIFIED: Same person (similarity: {similarity:.4f} >= {thresh:.4f})")
            else:
                print(f"✗ REJECTED: Different person (similarity: {similarity:.4f} < {thresh:.4f})")
            
            print("="*60 + "\n")
            
            result['verified'] = verified
            result['similarity'] = similarity
            result['threshold'] = thresh
            result['distance'] = 1.0 - similarity
            if warning:
                result['warning'] = True
                
            return result
            
        except Exception as e:
            print(f"Face verification critical error: {e}")
            traceback.print_exc()
            result['error'] = f"System error during verification: {str(e)}"
            return result
