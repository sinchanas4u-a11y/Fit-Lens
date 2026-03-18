
try:
    import deepface
    print("deepface: INSTALLED")
except ImportError:
    print("deepface: NOT INSTALLED")

try:
    import face_recognition
    print("face_recognition: INSTALLED")
except ImportError:
    print("face_recognition: NOT INSTALLED")
