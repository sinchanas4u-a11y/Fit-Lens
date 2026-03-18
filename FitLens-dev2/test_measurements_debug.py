"""
Test script to debug measurement calculation
"""
import numpy as np
from measurement_engine import MeasurementEngine

# Create fake landmarks (33 landmarks with x, y, confidence)
landmarks = np.random.rand(33, 3)
landmarks[:, 2] = 0.9  # Set high confidence

# Create measurement engine
engine = MeasurementEngine()

# Test calculation
scale_factor = 0.05  # 1 pixel = 0.05 cm
measurements = engine.calculate_measurements_with_confidence(
    landmarks, scale_factor, 'front'
)

print("\n" + "="*60)
print("MEASUREMENT TEST RESULTS")
print("="*60)
print(f"\nTotal measurements: {len(measurements)}")
print("\nMeasurements:")
for name, (value_cm, confidence, source) in measurements.items():
    print(f"  {name}: {value_cm:.2f} cm (confidence: {confidence:.2f}, source: {source})")

print("\n" + "="*60)
