#!/usr/bin/env python3
"""
Focused Backend Validation for SMPL changes
Tests syntax, imports, and runs critical tests
"""
import sys
import os
import subprocess
import traceback

os.chdir(r'C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2')

print("=" * 70)
print("FITLENS BACKEND VALIDATION - SMPL CHANGES")
print("=" * 70)

tests_to_run = [
    ("verify_smpl.py", "SMPL Model Loading & Measurement Extraction"),
    ("test_dependencies.py", "Python Dependency Verification"),
    ("test_application.py", "Core Application Modules"),
]

results = []

for test_file, description in tests_to_run:
    print(f"\n{'='*70}")
    print(f"TEST: {test_file}")
    print(f"Description: {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✓ PASSED")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout[:2000])  # Limit output
            results.append((test_file, "PASS", None))
        else:
            print(f"✗ FAILED (exit code: {result.returncode})")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            results.append((test_file, "FAIL", result.stderr or result.stdout))
    except subprocess.TimeoutExpired:
        print(f"✗ TIMEOUT (>60s)")
        results.append((test_file, "TIMEOUT", "Test exceeded 60 second timeout"))
    except Exception as e:
        print(f"✗ ERROR: {e}")
        traceback.print_exc()
        results.append((test_file, "ERROR", str(e)))

# Summary
print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")

all_passed = all(status == "PASS" for _, status, _ in results)

for test_file, status, error in results:
    status_icon = "✓" if status == "PASS" else "✗"
    print(f"{status_icon} {test_file:30s} : {status}")
    if error and status != "PASS":
        print(f"  Error: {error[:200]}")

print(f"{'='*70}")

if all_passed:
    print("✓ ALL TESTS PASSED")
    print("Backend SMPL changes validation: SUCCESS")
    sys.exit(0)
else:
    print("✗ SOME TESTS FAILED")
    print("Backend SMPL changes validation: FAILED")
    print("\nRefer to detailed output above for error traces")
    sys.exit(1)
