
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

    def verify_person(self, img1_array, img2_array, threshold=None):
        """
        Verify if two images belong to the same person.
        
        Args:
            img1_array: First image (numpy array BGR)
            img2_array: Second image (numpy array BGR)
            threshold: Optional custom threshold override (default: 0.65)
            
        Returns:
            dict: {
                'verified': bool,
                'similarity': float,
                'threshold': float,
                'warning': bool (optional - for uncertain range),
                'no_face': bool (optional),
                'error': str (optional)
            }
        """
        if not self.is_ready:
            return {
                'verified': False,
                'error': "Face verification unavailable (InsightFace library missing)"
            }
            
        if img1_array is None or img2_array is None:
            return {
                'verified': False,
                'error': "Invalid image data provided"
            }

        try:
            print("\n" + "="*60)
            print("FACE VERIFICATION - InsightFace")
            print("="*60)
            
            # Extract embeddings from both images
            print("Processing image 1...")
            emb1, face1_detected = self._detect_and_extract_embedding(img1_array)
            
            print("Processing image 2...")
            emb2, face2_detected = self._detect_and_extract_embedding(img2_array)
            
            # Check if faces were detected
            if not face1_detected or not face2_detected:
                print("✗ Face detection failed")
                print("="*60)
                return {
                    'verified': False,
                    'no_face': True,
                    'error': "Face not detected clearly. Please upload clear front and side images."
                }
            
            # Calculate cosine similarity
            similarity = self._calculate_cosine_similarity(emb1, emb2)
            
            # Use custom threshold or default
            thresh = threshold if threshold is not None else self.SAME_PERSON_THRESHOLD
            
            print(f"\n📊 Similarity Score: {similarity:.4f}")
            print(f"📏 Threshold: {thresh:.4f}")
            
            # Determine verification result
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
            
            result = {
                'verified': verified,
                'similarity': similarity,
                'threshold': thresh,
                'distance': 1.0 - similarity  # For backward compatibility
            }
            
            if warning:
                result['warning'] = True
                
            return result
            
        except Exception as e:
            print(f"Face verification critical error: {e}")
            traceback.print_exc()
            return {
                'verified': False,
                'error': f"System error during verification: {str(e)}"
            }
