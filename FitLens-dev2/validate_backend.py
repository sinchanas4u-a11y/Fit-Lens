#!/usr/bin/env python3
"""Validate SMPL backend changes - check syntax and imports"""
import sys
import py_compile
import importlib.util

files_to_validate = [
    "smpl/smpl_estimator.py",
    "smpl/smpl_pipeline.py",
    "backend/app.py",
    "backend/app_updated.py"
]

print("=" * 60)
print("VALIDATING PYTHON SYNTAX AND IMPORTS")
print("=" * 60)

all_passed = True

# 1. Check syntax with py_compile
print("\n[1/3] Checking Python syntax...")
for filepath in files_to_validate:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"  ✓ {filepath}")
    except py_compile.PyCompileError as e:
        print(f"  ✗ {filepath}: {e}")
        all_passed = False

# 2. Check imports (basic validation by loading module)
print("\n[2/3] Checking imports...")
import_checks = {
    "smpl/smpl_estimator.py": ["numpy", "scipy.optimize", "smpl.smpl_loader"],
    "smpl/smpl_pipeline.py": ["numpy", "smpl.smpl_estimator", "smpl.measurement_extractor"],
    "backend/app.py": ["flask", "flask_cors", "flask_socketio", "cv2", "numpy", "PIL"],
    "backend/app_updated.py": ["flask", "flask_cors", "flask_socketio", "cv2", "numpy", "PIL"],
}

for filepath, imports in import_checks.items():
    for module_name in imports:
        try:
            __import__(module_name)
            print(f"  ✓ {filepath}: {module_name}")
        except ImportError as e:
            print(f"  ✗ {filepath}: {module_name} - {e}")
            all_passed = False

# 3. Validate file structure
print("\n[3/3] Validating file structure...")
required_classes_funcs = {
    "smpl/smpl_estimator.py": ["SMPLEstimator"],
    "smpl/smpl_pipeline.py": ["run_smpl_pipeline"],
    "backend/app.py": ["app", "socketio"],
    "backend/app_updated.py": ["app", "socketio"],
}

for filepath, expected in required_classes_funcs.items():
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for item in expected:
                if item in content:
                    print(f"  ✓ {filepath}: contains {item}")
                else:
                    print(f"  ✗ {filepath}: missing {item}")
                    all_passed = False
    except Exception as e:
        print(f"  ✗ {filepath}: {e}")
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("✓ ALL VALIDATIONS PASSED")
    print("=" * 60)
    sys.exit(0)
else:
    print("✗ SOME VALIDATIONS FAILED")
    print("=" * 60)
    sys.exit(1)
