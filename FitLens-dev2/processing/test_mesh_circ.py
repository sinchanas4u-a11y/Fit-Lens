import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(__file__)
))
from processing.mesh_circumference import (
    MeshCircumferenceExtractor
)

# Test with existing mesh
MESH_PATH = (
    "output/meshes/front/000.obj"
)
USER_HEIGHT = 165.0

print("Testing mesh circumference extractor")
print("="*50)

extractor = MeshCircumferenceExtractor(
    MESH_PATH, USER_HEIGHT
)

# Test without scale factor
results = extractor.extract_all()

print("\nRESULTS:")
for k, v in results.items():
    print(f"  {k}: {v} cm")

# Test with scale factor
SCALE = 0.1926  # from DS1
results_scaled = extractor.extract_all(
    scale_factor=SCALE
)

print("\nRESULTS WITH SCALE FACTOR:")
for k, v in results_scaled.items():
    print(f"  {k}: {v} cm")
