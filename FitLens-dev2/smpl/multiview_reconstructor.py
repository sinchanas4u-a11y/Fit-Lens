"""
Multi-view body reconstruction.

Extracts real body measurements from front and side silhouette masks,
then drives SMPL shape betas via a Jacobian-based least-squares solve.
No generic template or average body shape is used — every beta is
determined by pixel evidence from the two input masks.

Pipeline
--------
1. Validate front_mask and side_mask (required).
2. extract_measurements_from_masks():
   - Scan each row of the body bounding box.
   - Front mask  → torso widths  at chest / waist / hip / shoulder.
   - Side  mask  → torso depths  at chest / waist / hip.
   - Convert pixel spans to cm using user_height_cm / body_height_px.
   - Smooth with a median filter; clip to anatomical validity ranges.
3. Compute base SMPL measurements at warm-start betas.
4. Build Jacobian: how each beta changes each measurement.
5. Tikhonov solve: Δβ = Jᵀ(JJᵀ + λI)⁻¹ Δm.
6. Return fitted betas + full measurement dict for debugging.
"""

import numpy as np
from scipy.spatial import ConvexHull


# ── Anatomical validity ranges (cm) ──────────────────────────────────────────
VALID_RANGES_CM = {
    'shoulder_width': (25.0, 65.0),
    'chest_width':    (20.0, 60.0),
    'waist_width':    (18.0, 55.0),
    'hip_width':      (22.0, 65.0),
    'chest_depth':    (12.0, 50.0),
    'waist_depth':    (10.0, 45.0),
    'hip_depth':      (12.0, 55.0),
}

# Vertical fractions from top of body bounding box for each region
REGION_Y_FRACTIONS = {
    'shoulder': 0.18,
    'chest':    0.27,
    'waist':    0.40,
    'hip':      0.52,
}

# Arm-exclusion half-width (cm from body centre X) when measuring SMPL mesh
_ARM_EXCL_CM = 22.0

# Jacobian perturbation step (beta units ≈ std-devs)
_JACOBIAN_DELTA = 0.30

# Regularisation weight — higher = stay closer to landmark-fit betas
_L2_REG = 2.5

# Hard beta clamp
_BETA_CLIP = 2.0


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Silhouette measurement extraction
# ─────────────────────────────────────────────────────────────────────────────

def _body_bbox(mask: np.ndarray):
    """Return (y_top, y_bottom, x_left, x_right) of the foreground region."""
    rows = np.any(mask > 0, axis=1)
    cols = np.any(mask > 0, axis=0)
    if not rows.any() or not cols.any():
        return None
    y_top    = int(np.argmax(rows))
    y_bottom = int(len(rows) - 1 - np.argmax(rows[::-1]))
    x_left   = int(np.argmax(cols))
    x_right  = int(len(cols) - 1 - np.argmax(cols[::-1]))
    return y_top, y_bottom, x_left, x_right


def _torso_span_px(row: np.ndarray) -> float:
    """
    Width of the central contiguous foreground run in a single mask row.
    Arms appear as separate runs on the sides — we pick the run whose
    centre is closest to the image horizontal centre.
    """
    if row.size == 0:
        return 0.0
    binary = (row > 0).astype(np.int8)
    padded = np.concatenate(([0], binary, [0]))
    diff   = np.diff(padded)
    starts = np.where(diff ==  1)[0]
    ends   = np.where(diff == -1)[0]
    if len(starts) == 0:
        return 0.0
    widths  = (ends - starts).astype(float)
    centres = (starts + ends) / 2.0
    col_mid = row.size / 2.0
    idx     = int(np.argmin(np.abs(centres - col_mid)))
    return float(widths[idx])


def _band_median(mask: np.ndarray, y_centre: int,
                 band_half: int) -> float:
    """Median torso span over a vertical band of rows."""
    h = mask.shape[0]
    y_lo = max(0, y_centre - band_half)
    y_hi = min(h - 1, y_centre + band_half)
    spans = []
    for r in range(y_lo, y_hi + 1):
        s = _torso_span_px(mask[r])
        if s > 0:
            spans.append(s)
    return float(np.median(spans)) if spans else 0.0


def extract_measurements_from_masks(
    front_mask: np.ndarray,
    side_mask:  np.ndarray,
    user_height_cm: float,
) -> dict:
    """
    Extract real-world body measurements from front and side silhouette masks.

    Parameters
    ----------
    front_mask      : (H, W) uint8 — foreground > 0, front view
    side_mask       : (H, W) uint8 — foreground > 0, side view
    user_height_cm  : known standing height in cm

    Returns
    -------
    dict  {measurement_key: value_cm}
        Keys: shoulder_width, chest_width, waist_width, hip_width,
              chest_depth, waist_depth, hip_depth
    """
    if user_height_cm <= 0:
        raise ValueError("user_height_cm must be > 0")

    results = {}

    # ── Front mask → widths ───────────────────────────────────────────────────
    if front_mask is not None and front_mask.size > 0:
        bbox = _body_bbox(front_mask)
        if bbox is not None:
            y_top, y_bottom, _, _ = bbox
            body_h_px = max(y_bottom - y_top, 1)
            px_per_cm = body_h_px / user_height_cm
            band_half = max(2, int(0.018 * body_h_px))  # ±1.8% band

            region_keys = {
                'shoulder': 'shoulder_width',
                'chest':    'chest_width',
                'waist':    'waist_width',
                'hip':      'hip_width',
            }
            for region, key in region_keys.items():
                y_frac  = REGION_Y_FRACTIONS[region]
                y_px    = int(y_top + y_frac * body_h_px)
                span_px = _band_median(front_mask, y_px, band_half)
                if span_px <= 0:
                    continue
                value_cm = span_px / px_per_cm
                lo, hi   = VALID_RANGES_CM.get(key, (0.0, 999.0))
                if lo <= value_cm <= hi:
                    results[key] = round(value_cm, 2)
                    print(f"[Masks] {key:<20}: {value_cm:.1f} cm  "
                          f"({span_px:.0f} px / {px_per_cm:.2f} px/cm)")
                else:
                    print(f"[Masks] {key:<20}: {value_cm:.1f} cm  "
                          f"OUT OF RANGE [{lo}, {hi}] — dropped")

    # ── Side mask → depths ────────────────────────────────────────────────────
    if side_mask is not None and side_mask.size > 0:
        bbox = _body_bbox(side_mask)
        if bbox is not None:
            y_top, y_bottom, _, _ = bbox
            body_h_px = max(y_bottom - y_top, 1)
            px_per_cm = body_h_px / user_height_cm
            band_half = max(2, int(0.018 * body_h_px))

            region_keys = {
                'chest': 'chest_depth',
                'waist': 'waist_depth',
                'hip':   'hip_depth',
            }
            for region, key in region_keys.items():
                y_frac  = REGION_Y_FRACTIONS[region]
                y_px    = int(y_top + y_frac * body_h_px)
                span_px = _band_median(side_mask, y_px, band_half)
                if span_px <= 0:
                    continue
                value_cm = span_px / px_per_cm
                lo, hi   = VALID_RANGES_CM.get(key, (0.0, 999.0))
                if lo <= value_cm <= hi:
                    results[key] = round(value_cm, 2)
                    print(f"[Masks] {key:<20}: {value_cm:.1f} cm  "
                          f"({span_px:.0f} px / {px_per_cm:.2f} px/cm)")
                else:
                    print(f"[Masks] {key:<20}: {value_cm:.1f} cm  "
                          f"OUT OF RANGE [{lo}, {hi}] — dropped")

    if not results:
        raise ValueError(
            "extract_measurements_from_masks: no valid measurements could be "
            "extracted from the provided masks. Check that masks are non-empty "
            "and the person is fully visible."
        )

    print(f"[Masks] Extracted {len(results)} measurements: {list(results.keys())}")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 2.  SMPL mesh measurement helpers
# ─────────────────────────────────────────────────────────────────────────────

def _scale_to_cm(raw_v: np.ndarray, height_cm: float) -> np.ndarray:
    """Scale raw SMPL vertices (metres) to centimetres at the given height."""
    y_span = (raw_v[:, 1].max() - raw_v[:, 1].min()) * 100.0
    if y_span <= 1e-6:
        return raw_v * 100.0
    return raw_v * (100.0 * height_cm / y_span)


def _mesh_width_at(v_cm: np.ndarray, y_frac: float,
                   height_cm: float, tol: float = 2.0) -> float | None:
    """Torso width (X extent) at a fractional body height."""
    y_level = v_cm[:, 1].max() - height_cm * y_frac
    sec = v_cm[np.abs(v_cm[:, 1] - y_level) < tol]
    if len(sec) < 6:
        return None
    torso = sec[np.abs(sec[:, 0]) < _ARM_EXCL_CM]
    if len(torso) < 4:
        return None
    return float(torso[:, 0].max() - torso[:, 0].min())


def _mesh_depth_at(v_cm: np.ndarray, y_frac: float,
                   height_cm: float, tol: float = 2.0) -> float | None:
    """Torso depth (Z extent) at a fractional body height."""
    y_level = v_cm[:, 1].max() - height_cm * y_frac
    sec = v_cm[np.abs(v_cm[:, 1] - y_level) < tol]
    if len(sec) < 6:
        return None
    torso = sec[np.abs(sec[:, 0]) < _ARM_EXCL_CM]
    if len(torso) < 4:
        return None
    return float(torso[:, 2].max() - torso[:, 2].min())


def _measure_smpl(estimator, betas: np.ndarray,
                  height_cm: float) -> dict:
    """
    Compute width and depth measurements from SMPL shaped vertices.
    Returns only the keys that overlap with what masks can provide.
    """
    raw_v = estimator._shape_vertices(betas)
    v_cm  = _scale_to_cm(raw_v, height_cm)
    out   = {}

    region_map = {
        'shoulder': ('shoulder_width', None),
        'chest':    ('chest_width',    'chest_depth'),
        'waist':    ('waist_width',    'waist_depth'),
        'hip':      ('hip_width',      'hip_depth'),
    }
    for region, (wkey, dkey) in region_map.items():
        y_frac = REGION_Y_FRACTIONS[region]
        w = _mesh_width_at(v_cm, y_frac, height_cm)
        if w is not None:
            out[wkey] = w
        if dkey is not None:
            d = _mesh_depth_at(v_cm, y_frac, height_cm)
            if d is not None:
                out[dkey] = d

    return out


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Jacobian-based beta fitting
# ─────────────────────────────────────────────────────────────────────────────

def fit_betas_multiview(
    estimator,
    front_mask:     np.ndarray,
    side_mask:      np.ndarray,
    user_height_cm: float,
    init_betas:     np.ndarray | None = None,
    n_betas:        int   = 10,
    l2_reg:         float = _L2_REG,
    beta_clip:      float = _BETA_CLIP,
) -> tuple[np.ndarray, dict]:
    """
    Fit SMPL betas so the mesh matches silhouette-derived measurements.

    Parameters
    ----------
    estimator       : SMPLEstimator instance
    front_mask      : (H, W) uint8 — required, front-view silhouette
    side_mask       : (H, W) uint8 — required, side-view silhouette
    user_height_cm  : standing height in cm
    init_betas      : warm-start from landmark fit (recommended)
    n_betas         : number of shape coefficients
    l2_reg          : Tikhonov regularisation weight
    beta_clip       : hard clamp on beta magnitude

    Returns
    -------
    (fitted_betas, targets_dict)
    """
    # ── Validate inputs ───────────────────────────────────────────────────────
    if front_mask is None or front_mask.size == 0:
        raise ValueError("fit_betas_multiview: front_mask is required and must be non-empty")
    if front_mask.ndim < 2:
        raise ValueError(f"fit_betas_multiview: front_mask must be 2-D, got shape {front_mask.shape}")

    if side_mask is None or side_mask.size == 0:
        raise ValueError("fit_betas_multiview: side_mask is required and must be non-empty")
    if side_mask.ndim < 2:
        raise ValueError(f"fit_betas_multiview: side_mask must be 2-D, got shape {side_mask.shape}")

    if user_height_cm <= 0:
        raise ValueError("fit_betas_multiview: user_height_cm must be > 0")

    # ── Step 1: Extract silhouette targets ────────────────────────────────────
    targets = extract_measurements_from_masks(front_mask, side_mask, user_height_cm)

    if not targets:
        print("[MultiView] No valid targets — returning init betas unchanged")
        base = (np.clip(np.asarray(init_betas, dtype=np.float64)[:n_betas],
                        -beta_clip, beta_clip)
                if init_betas is not None else np.zeros(n_betas, dtype=np.float64))
        return base, {}

    # ── Step 2: Warm-start betas ──────────────────────────────────────────────
    if init_betas is not None:
        base_betas = np.clip(
            np.asarray(init_betas, dtype=np.float64)[:n_betas],
            -beta_clip, beta_clip,
        )
    else:
        base_betas = np.zeros(n_betas, dtype=np.float64)

    # ── Step 3: Base SMPL measurements ───────────────────────────────────────
    base_meas = _measure_smpl(estimator, base_betas, user_height_cm)

    # Only fit keys present in both targets and SMPL mesh output
    keys = [k for k in targets if k in base_meas]
    if not keys:
        print("[MultiView] No overlapping keys — returning init betas")
        return base_betas, targets

    print(f"[MultiView] Fitting {len(keys)} silhouette constraints: {keys}")

    # ── Step 4: Build Jacobian (n_keys × n_betas) ─────────────────────────────
    J = np.zeros((len(keys), n_betas), dtype=np.float64)
    for j in range(n_betas):
        b_j = base_betas.copy()
        b_j[j] += _JACOBIAN_DELTA
        m_j = _measure_smpl(estimator, b_j, user_height_cm)
        for i, k in enumerate(keys):
            if k in m_j:
                J[i, j] = (m_j[k] - base_meas[k]) / _JACOBIAN_DELTA

    # ── Step 5: Residual vector ───────────────────────────────────────────────
    delta_m = np.array(
        [targets[k] - base_meas[k] for k in keys],
        dtype=np.float64,
    )

    print("[MultiView] Per-constraint residuals (target − base):")
    for k, dm in zip(keys, delta_m):
        print(f"  {k:<22}: {dm:+.2f} cm  "
              f"(target={targets[k]:.1f}  base={base_meas[k]:.1f})")

    # ── Step 6: Tikhonov solve ────────────────────────────────────────────────
    JT = J.T
    A  = J @ JT + l2_reg * np.eye(len(keys), dtype=np.float64)
    try:
        delta_betas = JT @ np.linalg.solve(A, delta_m)
    except np.linalg.LinAlgError:
        print("[MultiView] Singular matrix in Tikhonov solve — returning init betas")
        return base_betas, targets

    fitted = np.clip(base_betas + delta_betas, -beta_clip, beta_clip)

    # ── Step 7: Verify improvement ────────────────────────────────────────────
    fitted_meas = _measure_smpl(estimator, fitted, user_height_cm)
    print("[MultiView] Fit verification:")
    for k in keys:
        print(f"  {k:<22}: base={base_meas.get(k, 0):.1f}  "
              f"fitted={fitted_meas.get(k, 0):.1f}  "
              f"target={targets[k]:.1f}")

    print(f"[MultiView] Betas: {np.round(fitted, 3).tolist()}")
    return fitted, targets
