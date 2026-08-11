"""
Dependency Checker for FitLens Backend
Safely checks optional facial verification and AI dependencies.
"""
import importlib.util

dependencies = [
    'insightface',
    'deepface',
    'onnxruntime',
    'mediapipe',
    'ultralytics',
    'cv2',
    'eventlet',
    'socketio'
]

print("=== FITLENS DEPENDENCY CHECK ===")
for dep in dependencies:
    spec = importlib.util.find_spec(dep)
    status = "INSTALLED" if spec is not None else "NOT INSTALLED"
    print(f"{dep}: {status}")
