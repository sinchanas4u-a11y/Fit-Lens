# Manual Measurement Edge Refinement Guide

## Overview

This document explains the edge snapping and contour refinement features added to improve the accuracy of manual measurements in FitLens.

## Problem Statement

Manual measurements in the original implementation relied solely on user-marked points. This approach had several limitations:

1. **User Imprecision**: Users might click slightly inside or outside the actual body boundary
2. **Single Point Sampling**: No averaging or error correction
3. **No Body Boundary Detection**: Points were used as-is without validation

These issues resulted in manual measurements being less accurate than automatic measurements.

## Solution: Multi-Stage Edge Refinement

### Stage 1: Edge Detection with Canny Algorithm

**Function**: `snap_point_to_edge(point, image, mask, search_radius=20, sample_count=8)`

- **Purpose**: Snap a user-marked point to the nearest body contour edge
- **Algorithm**:
  1. Apply Canny edge detection to segmentation mask (thresholds: 50, 150)
  2. Search circular region around user point (default radius: 20px)
  3. Find all edge pixels using 8-directional sampling
  4. Select closest edge point
  5. Average nearby edge points (within 3px) for stability
  6. Return refined coordinates or original if no edge found

- **Parameters**:
  - `search_radius`: How far to search for edges (default: 20px)
  - `sample_count`: Number of radial directions to sample (default: 8)

### Stage 2: Multi-Sample Averaging

**Function**: `refine_measurement_with_contours(p1, p2, image, mask, num_samples=5)`

- **Purpose**: Refine a measurement line by sampling and averaging multiple edge points
- **Algorithm**:
  1. Sample points along measurement line near endpoints
  2. Snap each sample to nearest edge
  3. Average snapped samples to get refined p1 and p2
  4. Return tuple of refined points

- **Parameters**:
  - `num_samples`: Number of points to sample per endpoint (default: 5)

### Stage 3: Integration into Measurement Pipeline

**Location**: `process_manual_view()` function (lines 1340-1430)

Changes made:
1. **Early Mask Generation**: Segmentation mask generated before processing landmarks
2. **Point Refinement**: Each user point refined using `refine_measurement_with_contours()`
3. **Distance Calculation**: Pixel distance calculated with refined points
4. **Comparison Logging**: Original vs. refined distances logged for debugging
5. **Formula Preservation**: Scale factor formula unchanged: `pixel_distance × scale_factor = cm_distance`

## Visualization

The visualization now shows BOTH original and refined points for transparency:

- **Gray Line & Dots**: Original user-marked points
- **Yellow Line**: Refined measurement line
- **Green Dots**: Edge-snapped endpoints

This allows users to see how much their points were adjusted.

## Measurement Output

Each measurement now includes refinement metadata:

```json
{
  "value_cm": 42.5,
  "value_px": 234.7,
  "confidence": 0.95,
  "source": "Manual (Edge-Refined)",
  "formula": "234.70 px × 0.1812 cm/px = 42.52 cm",
  "refinement": {
    "original_px": 238.2,
    "refined_px": 234.7,
    "improvement_px": 3.5,
    "edge_snapped": true
  }
}
```

## Accuracy Improvements

Expected improvements:
- **±2-5 pixels**: Typical snapping correction per point
- **±0.5-2 cm**: Typical measurement improvement at human scale
- **95% confidence**: Increased from 100% to reflect algorithmic refinement

## Edge Cases

The refinement functions handle several edge cases:

1. **No Mask Available**: Falls back to image edge detection or uses original points
2. **No Edges Found**: Returns original points without modification
3. **Boundary Checks**: Validates all coordinates stay within image bounds
4. **Error Handling**: Try-catch blocks with fallback to original points

## Configuration

You can tune edge snapping behavior by modifying parameters:

```python
# In process_manual_view(), line ~1360
(x1, y1), (x2, y2) = refine_measurement_with_contours(
    (x1_orig, y1_orig), 
    (x2_orig, y2_orig),
    image, 
    mask,
    num_samples=5  # ← Increase for more averaging (slower but more stable)
)
```

```python
# In snap_point_to_edge(), line ~1140
def snap_point_to_edge(point, image, mask, search_radius=20, sample_count=8):
    # ↑ Increase search_radius to search farther from user point
    # ↑ Increase sample_count for more thorough edge search
```

## Testing Recommendations

1. **Test with various body parts**: Arms, legs, torso measurements
2. **Test with different lighting conditions**: Bright, dim, mixed
3. **Test with different clothing**: Tight-fitting vs. loose
4. **Compare with automatic measurements**: Validate improvements
5. **Check boundary cases**: Very thin/thick body parts, partial occlusion

## Constraints Maintained

✅ **Automatic mode unchanged**: No modifications to automatic measurement pipeline  
✅ **Formula preservation**: Scale factor calculation identical to before  
✅ **Backward compatibility**: Falls back to original behavior if refinement fails  
✅ **Frontend unchanged**: All changes in backend only; no API changes required

## Debug Output

When running manual measurements, you'll see detailed logs:

```
✓ Processing 5 manual landmarks
  Attempting automatic detection for scale calibration...
  ✓ Auto-calibration successful: 1234.5 px height -> 0.1456 cm/px
  Generating segmentation mask for edge refinement...
  ✓ Mask generated: (1920, 1080)

  Processing: Shoulder Width
    Original points: (234.0, 156.0) → (678.0, 162.0)
    Refined points: (230.5, 154.3) → (681.2, 163.8)
    ✓ Accuracy improvement: 4.2 px (0.61 cm)
  ✓ Shoulder Width: 65.43 cm (449.2 px) [Edge-Refined]
```

## Future Enhancements

Potential improvements for future versions:

1. **Adaptive Search Radius**: Auto-adjust based on body part size
2. **Smart Sampling**: More samples for curved body parts, fewer for straight lines
3. **Machine Learning**: Train model to predict optimal edge pixels
4. **User Feedback Loop**: Allow users to accept/reject refinements
5. **Confidence Scoring**: Calculate confidence based on edge strength and consistency

## References

- Original implementation: `app_updated.py` lines 1107-1500
- Edge snapping function: Lines 1140-1210
- Multi-sample refinement: Lines 1215-1250
- Frontend display: `frontend-vite/src/components/UploadMode.jsx` lines 620-753
