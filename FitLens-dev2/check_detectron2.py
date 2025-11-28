"""
Check if Detectron2 is available and provide installation guidance
"""
import sys

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 12:
        print("⚠ WARNING: Python 3.12+ detected")
        print("  PyTorch and Detectron2 have limited support for Python 3.12")
        print("  Recommended: Python 3.11 or lower")
        print("  See: PYTHON_VERSION_FIX.md")
        return False
    elif version.major == 3 and version.minor >= 8:
        print("✓ Python version is compatible")
        return True
    else:
        print("✗ Python version too old (need 3.8+)")
        return False

def check_detectron2():
    """Check if Detectron2 is installed"""
    try:
        import detectron2
        print("✓ Detectron2 is installed")
        print(f"  Version: {detectron2.__version__}")
        return True
    except ImportError:
        print("✗ Detectron2 is NOT installed")
        return False

def check_pytorch():
    """Check if PyTorch is installed"""
    try:
        import torch
        print("✓ PyTorch is installed")
        print(f"  Version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA version: {torch.version.cuda}")
        return True
    except ImportError:
        print("✗ PyTorch is NOT installed")
        return False

def check_mediapipe():
    """Check if MediaPipe is available as alternative"""
    try:
        import mediapipe
        print("✓ MediaPipe is installed (alternative available)")
        print(f"  Version: {mediapipe.__version__}")
        return True
    except ImportError:
        print("✗ MediaPipe is NOT installed")
        return False

def main():
    print("=" * 60)
    print("Installation Check")
    print("=" * 60)
    print()
    
    python_ok = check_python_version()
    print()
    
    pytorch_ok = check_pytorch()
    print()
    
    detectron2_ok = check_detectron2()
    print()
    
    mediapipe_ok = check_mediapipe()
    print()
    
    print("=" * 60)
    print("Recommendations:")
    print("=" * 60)
    print()
    
    if not python_ok:
        print("⚠ PYTHON VERSION ISSUE:")
        print()
        print("You're using Python 3.12, which has limited support.")
        print()
        print("Options:")
        print("1. Install Python 3.11 and create virtual environment")
        print("   See: PYTHON_VERSION_FIX.md")
        print()
        print("2. Use MediaPipe version (works with Python 3.12):")
        if mediapipe_ok:
            print("   python pose_capture.py")
        else:
            print("   pip install mediapipe")
            print("   python pose_capture.py")
        print()
    elif detectron2_ok:
        print("✓ You can use the full R-CNN version:")
        print("  python main.py --height 175")
        print()
    else:
        print("⚠ Detectron2 not installed. Options:")
        print()
        
        if sys.platform == "win32":
            print("Windows Installation Options:")
            print()
            print("1. WSL2 (RECOMMENDED - Easiest):")
            print("   - See INSTALL_WINDOWS.md for detailed guide")
            print("   - Open PowerShell as Admin: wsl --install")
            print()
            print("2. Build from Source:")
            print("   - Install Visual Studio Build Tools")
            print("   - pip install git+https://github.com/facebookresearch/detectron2.git")
            print()
        else:
            print("Linux/Mac Installation:")
            print("   pip install git+https://github.com/facebookresearch/detectron2.git")
            print()
        
        if mediapipe_ok:
            print("3. Use MediaPipe Version (NO Detectron2 needed):")
            print("   python pose_capture.py")
            print("   (Faster, easier, but no body measurements)")
        else:
            print("3. Install MediaPipe (Lightweight alternative):")
            print("   pip install mediapipe")
            print("   python pose_capture.py")
        
        print()
    
    print("=" * 60)
    print("Documentation:")
    print("=" * 60)
    print("- Windows: See INSTALL_WINDOWS.md")
    print("- Quick Start: See QUICKSTART.md")
    print("- Full Guide: See README_RCNN.md")
    print()

if __name__ == "__main__":
    main()
