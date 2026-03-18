
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
        
        # Similarity thresholds as per requirements
        self.SAME_PERSON_THRESHOLD = 0.65  # >= 0.65 → same person
        self.DIFFERENT_PERSON_THRESHOLD = 0.50  # < 0.50 → different person
        # Between 0.50-0.65 → uncertain but allow with warning
        
        if self.is_ready:
            try:
                print(f"Initializing InsightFace with {model_name} model...")
                self.app = FaceAnalysis(name=model_name, providers=['CPUExecutionProvider'])
                self.app.prepare(ctx_id=0, det_size=det_size)
                print(f"✓ FaceVerifier initialized successfully with InsightFace")
            except Exception as e:
                print(f"Failed to initialize InsightFace: {e}")
                self.is_ready = False
        else:
            print("FaceVerifier disabled: InsightFace library missing.")

    def _detect_and_extract_embedding(self, img_array):
        """
        Detect face and extract 512-D embedding from image.
        
        Args:
            img_array: Image as numpy array (BGR format)
            
        Returns:
            tuple: (embedding, face_detected)
                - embedding: 512-D numpy array or None
                - face_detected: bool
        """
        if img_array is None:
            return None, False
            
        try:
            # InsightFace expects RGB
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.app.get(img_rgb)
            
            if len(faces) == 0:
                print("⚠ No face detected in image")
                return None, False
            
            # Use the first detected face (largest by default)
            face = faces[0]
            embedding = face.embedding
            
            # Normalize embedding (L2 normalization)
            embedding = embedding / np.linalg.norm(embedding)
            
            print(f"✓ Face detected, embedding shape: {embedding.shape}")
            return embedding, True
            
        except Exception as e:
            print(f"Error during face detection/embedding: {e}")
            traceback.print_exc()
            return None, False

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

    def verify_person(self, img1_array, img2_array, threshold=None):
        """
        Verify if two images belong to the same person with quality checks.
        
        Args:
            img1_array: Front image (numpy array BGR)
            img2_array: Side/Other image (numpy array BGR)
            threshold: Optional custom threshold override (default: 0.65)
            
        Returns:
            dict: {
                'verified': bool,
                'similarity': float,
                'threshold': float,
                'warning': bool,
                'no_face': bool,
                'error': str,
                'issues': {'front': [], 'side': []} 
            }
        """
        result = {
            'verified': False,
            'similarity': 0.0,
            'threshold': self.SAME_PERSON_THRESHOLD,
            'issues': {'front': [], 'side': []},
            'no_face': False
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
            
            # Extract embeddings and detect faces
            print("Processing Front image...")
            # We need the full face object for quality check, not just embedding
            # So we duplicate _detect_and_extract logic slightly or reuse app.get
            
            # --- PROCESS FRONT ---
            img1_rgb = cv2.cvtColor(img1_array, cv2.COLOR_BGR2RGB)
            faces1 = self.app.get(img1_rgb)
            
            face1 = None
            if len(faces1) == 0:
                print("✗ No face detected in Front image")
                result['issues']['front'].append("Face not detected")
            else:
                # Get largest face
                face1 = sorted(faces1, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
                # Quality Check
                result['issues']['front'].extend(self.analyze_face_quality(img1_array, face1))
            
            # --- PROCESS SIDE ---
            print("Processing Side image...")
            img2_rgb = cv2.cvtColor(img2_array, cv2.COLOR_BGR2RGB)
            faces2 = self.app.get(img2_rgb)
            
            face2 = None
            if len(faces2) == 0:
                print("✗ No face detected in Side image")
                result['issues']['side'].append("Face not detected")
            else:
                # Get largest face
                face2 = sorted(faces2, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
                # Quality Check
                result['issues']['side'].extend(self.analyze_face_quality(img2_array, face2))
                
            # If any face missing, fail
            if face1 is None or face2 is None:
                result['no_face'] = True
                result['error'] = "Face verification failed: Face not detected in one or both images."
                return result
                
            # Calculate Similarity
            emb1 = face1.embedding
            emb1 = emb1 / np.linalg.norm(emb1)
            
            emb2 = face2.embedding
            emb2 = emb2 / np.linalg.norm(emb2)
            
            similarity = self._calculate_cosine_similarity(emb1, emb2)
            
            # Use custom threshold or default
            thresh = threshold if threshold is not None else self.SAME_PERSON_THRESHOLD
            
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
