"""
Silhouette extractor: derives body width/depth profiles from YOLOv8 segmentation masks.
Used by the multi-view SMPL optimization pipeline.
"""
import numpy as np

# Anatomical validity ranges (cm) — measurements outside these are dropped
VALID_RANGES_CM = {
    'shoulder_width':  (25.0, 65.0),
    'chest_width':     (20.0, 70.0),
    'waist_width':     (18.0, 65.0),
    'hip_width':       (22.0, 75.0),
    'thigh_width':     (10.0, 45.0),
    'shoulder_depth':  (10.0, 55.0),
    'chest_depth':     (10.0, 55.0),
    'waist_depth':     (10.0, 55.0),
    'hip_depth':       (10.0, 60.0),
    'thigh_depth':     (8.0,  40.0),
}

# Vertical positions as fraction of body height (top-down) for each region
REGION_Y_FRACTIONS = {
    'shoulder': 0.18,
    'chest':    0.27,
    'waist':    0.40,
    'hip':      0.52,
    'thigh':    0.65,
}


def _torso_width_px(row_pixels: np.ndarray) -> float:
    """
    Return the width of the central (torso) contiguous run of foreground pixels
    in a single row, excluding arms which appear as separate runs on the sides.
    """
    if row_pixels.size == 0:
        return 0.0

    # Find contiguous runs of non-zero pixels
    padded = np.concatenate(([0], (row_pixels > 0).astype(np.int8), [0]))
    diff = np.diff(padded)
    starts = np.where(diff == 1)[0]
    ends   = np.where(diff == -1)[0]

    if len(starts) == 0:
        return 0.0

    widths = ends - starts
    centers = (starts + ends) / 2.0
    col_center = row_pixels.size / 2.0

    # Pick the run whose center is closest to the image horizontal center
    closest_idx = int(np.argmin(np.abs(centers - col_center)))
    return float(widths[closest_idx])


def extract_silhouette_widths(mask: np.ndarray, user_height_cm: float,
                               view: str = 'front') -> dict:
    """
    Extract body region widths (front view) or depths (side view) from a
    binary segmentation mask.

    Parameters
    ----------
    mask : np.ndarray  (H, W) uint8 — foreground > 0
    user_height_cm : float
    view : 'front' | 'side'

    Returns
    -------
    dict  {region_name: value_cm}  — only entries within VALID_RANGES_CM
    """
    if mask is None or mask.size == 0:
        return {}

    h, w = mask.shape[:2]
    if h == 0 or w == 0:
        return {}

    # Bounding box of the person
    rows = np.any(mask > 0, axis=1)
    if not rows.any():
        return {}
    y_top    = int(np.argmax(rows))
    y_bottom = int(len(rows) - 1 - np.argmax(rows[::-1]))
    body_height_px = max(y_bottom - y_top, 1)

    px_per_cm = body_height_px / user_height_cm

    suffix = '_width' if view == 'front' else '_depth'
    results = {}

    for region, y_frac in REGION_Y_FRACTIONS.items():
        y_px = int(y_top + y_frac * body_height_px)
        # Sample over a ±1.5% band
        band_half = max(1, int(0.015 * body_height_px))
        y_lo = max(0, y_px - band_half)
        y_hi = min(h - 1, y_px + band_half)

        band_widths = []
        for row_idx in range(y_lo, y_hi + 1):
            w_px = _torso_width_px(mask[row_idx])
            if w_px > 0:
                band_widths.append(w_px)

        if not band_widths:
            continue

        median_px = float(np.median(band_widths))
        value_cm  = median_px / px_per_cm

        key = region + suffix
        lo, hi = VALID_RANGES_CM.get(key, (0.0, 999.0))
        if lo <= value_cm <= hi:
            results[key] = round(value_cm, 2)
        else:
            print(f"[Silhouette] {key} = {value_cm:.1f} cm out of valid range "
                  f"[{lo}, {hi}] — dropped")

    print(f"[Silhouette] {view} view extracted {len(results)} region dimensions:")
    for k, v in results.items():
        print(f"  {k:<30}: {v} cm")

    return results


def build_multiview_constraints(front_mask: np.ndarray, side_mask: np.ndarray,
                                 user_height_cm: float) -> dict:
    """
    Build combined width + depth constraints from front and side masks.

    Returns
    -------
    dict with keys 'front' and 'side', each a dict of {measurement: cm}
    """
    front_dims = extract_silhouette_widths(front_mask, user_height_cm, view='front') \
        if front_mask is not None else {}
    side_dims  = extract_silhouette_widths(side_mask,  user_height_cm, view='side')  \
        if side_mask  is not None else {}

    return {'front': front_dims, 'side': side_dims}


def build_normalised_profile(mask: np.ndarray, user_height_cm: float,
                              n_slices: int = 20) -> np.ndarray:
    """
    Build a normalised width profile (n_slices,) from a mask using
    arm-excluding torso width measurement.
    """
    if mask is None or mask.size == 0:
        return np.zeros(n_slices)

    h = mask.shape[0]
    rows = np.any(mask > 0, axis=1)
    if not rows.any():
        return np.zeros(n_slices)

    y_top    = int(np.argmax(rows))
    y_bottom = int(len(rows) - 1 - np.argmax(rows[::-1]))
    body_h   = max(y_bottom - y_top, 1)

    profile = np.zeros(n_slices)
    for i in range(n_slices):
        y_px = int(y_top + (i / n_slices) * body_h)
        y_px = min(y_px, h - 1)
        profile[i] = _torso_width_px(mask[y_px])

    max_val = profile.max()
    if max_val > 0:
        profile /= max_val

    return profile
