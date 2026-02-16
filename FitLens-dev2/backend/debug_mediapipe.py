import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    import mediapipe as mp
    print(f"MediaPipe imported successfully from: {mp.__file__}")
    print(f"MediaPipe dir: {dir(mp)}")
    if hasattr(mp, 'solutions'):
        print("mp.solutions found")
    else:
        print("mp.solutions NOT found")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
