#!/usr/bin/env python3
"""Direct validation of SMPL backend files - syntax and import checks"""

import sys
import os
import py_compile

os.chdir(r'C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2')
sys.path.insert(0, os.getcwd())

print("=" * 70)
print("DIRECT PYTHON SYNTAX & IMPORT VALIDATION")
print("=" * 70)

files_to_check = [
    ("smpl/smpl_estimator.py", "SMPL Estimator Core"),
    ("smpl/smpl_pipeline.py", "SMPL Pipeline Execution"),
    ("backend/app.py", "Flask Backend API"),
    ("backend/app_updated.py", "Updated Backend Workflow"),
]

all_syntax_ok = True

print("\n[STEP 1] Python Syntax Validation")
print("-" * 70)

for filepath, description in files_to_check:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"✓ {filepath:30s} - {description}")
    except py_compile.PyCompileError as e:
        print(f"✗ {filepath:30s} - SYNTAX ERROR")
        print(f"  {e}")
        all_syntax_ok = False

print("\n[STEP 2] File Content Validation")
print("-" * 70)

all_content_ok = True

validation_rules = {
    "smpl/smpl_estimator.py": {
        "contains": ["class SMPLEstimator", "def fit_to_landmarks", "def get_vertices"],
        "imports": ["numpy", "scipy.optimize", "smpl.smpl_loader"]
    },
    "smpl/smpl_pipeline.py": {
        "contains": ["def run_smpl_pipeline", "SMPLEstimator", "MeasurementExtractor"],
        "imports": ["numpy", "smpl.smpl_estimator", "smpl.measurement_extractor"]
    },
    "backend/app.py": {
        "contains": ["app = Flask", "socketio = SocketIO", "from smpl.smpl_pipeline"],
        "imports": ["flask", "flask_cors", "flask_socketio", "cv2"]
    },
    "backend/app_updated.py": {
        "contains": ["app = Flask", "socketio = SocketIO", "from smpl.smpl_pipeline"],
        "imports": ["flask", "flask_cors", "flask_socketio", "cv2"]
    }
}

for filepath, rules in validation_rules.items():
    print(f"\n{filepath}:")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check contains patterns
        all_found = True
        for pattern in rules.get("contains", []):
            if pattern in content:
                print(f"  ✓ Contains '{pattern}'")
            else:
                print(f"  ✗ Missing '{pattern}'")
                all_found = False
                all_content_ok = False
        
        # Check imports
        for imp in rules.get("imports", []):
            if f"import {imp}" in content or f"from {imp}" in content:
                print(f"  ✓ Imports '{imp}'")
            else:
                print(f"  ✗ Missing import '{imp}'")
                all_content_ok = False
                
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        all_content_ok = False

print("\n[STEP 3] Import Testing (if dependencies available)")
print("-" * 70)

all_imports_ok = True

import_tests = [
    ("numpy", "NumPy"),
    ("scipy.optimize", "SciPy Optimization"),
    ("flask", "Flask"),
    ("flask_cors", "Flask-CORS"),
    ("cv2", "OpenCV"),
]

for module_name, description in import_tests:
    try:
        __import__(module_name)
        print(f"✓ {module_name:20s} - {description}")
    except ImportError as e:
        print(f"✗ {module_name:20s} - {description} (NOT INSTALLED)")
        all_imports_ok = False

print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(f"Syntax Validation:  {'✓ PASS' if all_syntax_ok else '✗ FAIL'}")
print(f"Content Validation: {'✓ PASS' if all_content_ok else '✗ FAIL'}")
print(f"Import Validation:  {'✓ PASS' if all_imports_ok else '✗ FAIL (dependencies missing)'}")

if all_syntax_ok and all_content_ok:
    print("\n✓ DIRECT VALIDATION PASSED - No syntax errors detected")
    print("Files are syntactically correct and properly structured")
    sys.exit(0)
else:
    print("\n✗ VALIDATION FAILED - See errors above")
    sys.exit(1)
