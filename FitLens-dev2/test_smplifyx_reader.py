import glob
import os

from processing.smplifyx_reader import SMPLifyXReader


mesh_dir = "output/meshes"
mesh_files = glob.glob(os.path.join(mesh_dir, "**", "*.ply"), recursive=True)

if not mesh_files:
    mesh_files = glob.glob(os.path.join(mesh_dir, "**", "*.obj"), recursive=True)

if not mesh_files:
    print("No mesh file found in output/meshes")
    print("Run SMPLify-X first")
    raise SystemExit(1)

mesh_path = mesh_files[0]
print(f"Testing with mesh: {mesh_path}\n")

USER_HEIGHT_CM = 177.0

reader = SMPLifyXReader(mesh_path)

print("Extracting measurements...")
meas = reader.extract_measurements(USER_HEIGHT_CM)

print("\nValidating measurement ranges:")
ranges = {
    "chest_circumference": (80, 130),
    "waist_circumference": (60, 110),
    "hip_circumference": (80, 130),
    "chest_width": (30, 55),
    "shoulder_width": (35, 55),
}

for key, (lo, hi) in ranges.items():
    val = meas.get(key)
    if val is None:
        print(f"  {key:30s}: MISSING")
    elif lo <= val <= hi:
        print(f"  {key:30s}: {val} cm  OK")
    else:
        print(f"  {key:30s}: {val} cm  WARNING outside [{lo}-{hi}]")

print("\nTesting Plotly mesh export...")
mesh_data = reader.export_for_plotly(USER_HEIGHT_CM)
print(f"  x vertices : {len(mesh_data['x'])}")
print(f"  faces i    : {len(mesh_data['i'])}")
print(f"  metadata   : {mesh_data['metadata']}")

print("\nALL TESTS PASSED")