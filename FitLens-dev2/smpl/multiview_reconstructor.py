"""
Multi-view body reconstruction.

Uses front-view silhouette widths and side-view silhouette depths to
constrain SMPL shape betas via a Jacobian-based least-squares solve.

Pipeline
--------
1. Extract silhouette widths from front mask  (shoulder/chest/waist/hip)
2. Extract silhouette depths from side mask   (chest/waist/hip depth)
3. Align both views to a shared height scale
4. Build a combined measurement vector
5. Compute Jacobian of SMPL mesh measurements w.r.t. betas
6. Solve for betas that minimise ||J·Δβ - Δm||² + λ||β||²
7. Return fitted betas + per-region width/depth targets
"""

import numpy as np
from scipy.spatial import ConvexHull

from smpl.silhouette_extractor import (
    extract_silhouette_widths,
    REGION_Y_FRACTIONS,
    VALID_RANGES_CM,
)


# ── Anatomical region → SMPL height fraction (from top) ──────────────────────
# These must match REGION_Y_FRACTIONS in silhouette_extractor.py
_REGION_Y = {
    'shoulder': 0.18,
    'chest':    0.27,
    'waist':    0.40,
    'hip':      0.52,
    'thigh':    0.65,
}

# Measurement keys we actually use for fitting
_FIT_KEYS_WIDTH = [
    'shoulder_width',
    'chest_width',
    'waist_width',
    'hip_width',
]
_FIT_KEYS_DEPTH = [
    'chest_depth',
    'waist_depth',
    'hip_depth',
]

# Arm-exclusion radius (cm from body centre X) for width slices
_ARM_EXCL_CM = 22.0


def _mesh_width_at(v_cm: np.ndarray, y_frac: float,
                   height_cm: float, tol_cm: float = 2.0) -> float | None:
    """Width of the torso cross-section at a fractional height."""
    y_max = v_cm[:, 1].max()
    y_level = y_max - height_cm * y_frac
    mask = np.abs(v_cm[:, 1] - y_level) < tol_cm
    sec = v_cm[mask]
    if len(sec) < 6:
        return None
    cx = 0.0  # SMPL is symmetric around x=0
    torso = sec[np.abs(sec[:, 0] - cx) < _ARM_EXCL_CM]
    if len(torso) < 4:
        return None
    return float(torso[:, 0].max() - torso[:, 0].min())


def _mesh_depth_at(v_cm: np.ndarray, y_frac: float,
                   height_cm: float, tol_cm: float = 2.0) -> float | None:
    """Depth (Z extent) of the torso cross-section at a fractional height."""
    y_max = v_cm[:, 1].max()
    y_level = y_max - height_cm * y_frac
    mask = np.abs(v_cm[:, 1] - y_level) < tol_cm
    sec = v_cm[mask]
    if len(sec) < 6:
        return None
    cx = 0.0
    torso = sec[np.abs(sec[:, 0] - cx) < _ARM_EXCL_CM]
    if len(torso) < 4:
        return None
    return float(torso[:, 2].max() - torso[:, 2].min())


def _mesh_circumference_at(v_cm: np.ndarray, y_frac: float,
                            height_cm: float, tol_cm: float = 2.0) -> float | None:
    """Convex-hull circumference of the torso cross-section."""
    y_max = v_cm[:, 1].max()
    y_level = y_max - height_cm * y_frac
    mask = np.abs(v_cm[:, 1] - y_level) < tol_cm
    sec = v_cm[mask]
    if len(sec) < 10:
        return None
    cx = 0.0
    torso = sec[np.abs(sec[:, 0] - cx) < _ARM_EXCL_CM]
    if len(torso) < 8:
        return None
    try:
        pts = torso[:, [0, 2]]
        hull = ConvexHull(pts)
        vh = pts[hull.vertices]
        n = len(vh)
        return float(sum(np.linalg.norm(vh[(i + 1) % n] - vh[i]) for i in range(n)))
    except Exception:
        return None


def _scale_vertices(raw_v: np.ndarray, height_cm: float) -> np.ndarray:
    """Scale raw SMPL vertices (metres) to centimetres at user height."""
    y_span = (raw_v[:, 1].max() - raw_v[:, 1].min()) * 100.0
    if y_span <= 0:
        return raw_v * 100.0
    scale = height_cm / y_span
    return raw_v * 100.0 * scale


# ── Public API ────────────────────────────────────────────────────────────────

def extract_multiview_targets(
    front_mask: np.ndarray | None,
    side_mask:  np.ndarray | None,
    user_height_cm: float,
) -> dict:
    """
    Extract width (front) and depth (side) targets from silhouette masks.

    Returns
    -------
    dict  {measurement_key: value_cm}
    """
    targets = {}

    if front_mask is not None:
        front_dims = extract_silhouette_widths(
            front_mask, user_height_cm, view='front'
        )
        targets.update(front_dims)
        print(f"[MultiView] Front widths: {front_dims}")

    if side_mask is not None:
        side_dims = extract_silhouette_widths(
            side_mask, user_height_cm, view='side'
        )
        targets.update(side_dims)
        print(f"[MultiView] Side depths: {side_dims}")

    return targets


def fit_betas_multiview(
    estimator,
    front_mask:     np.ndarray | None,
    side_mask:      np.ndarray | None,
    user_height_cm: float,
    init_betas:     np.ndarray | None = None,
    n_betas:        int = 10,
    l2_reg:         float = 2.0,
    beta_clip:      float = 2.0,
) -> tuple[np.ndarray, dict]:
    """
    Fit SMPL betas to multi-view silhouette measurements.

    Parameters
    ----------
    estimator       : SMPLEstimator instance
    front_mask      : binary mask from front view (H×W uint8)
    side_mask       : binary mask from side view  (H×W uint8)
    user_height_cm  : known body height in cm
    init_betas      : warm-start betas (from landmark fit)
    n_betas         : number of shape coefficients to optimise
    l2_reg          : Tikhonov regularisation weight
    beta_clip       : hard clamp on beta magnitude

    Returns
    -------
    (fitted_betas, targets_used)
    """
    # ── 1. Extract silhouette targets ─────────────────────────────────────────
    targets = extract_multiview_targets(front_mask, side_mask, user_height_cm)

    if not targets:
        print("[MultiView] No silhouette targets extracted — returning init betas")
        return (
            np.clip(init_betas, -beta_clip, beta_clip)
            if init_betas is not None
            else np.zeros(n_betas),
            {},
        )

    # ── 2. Warm-start ─────────────────────────────────────────────────────────
    base_betas = (
        np.clip(np.asarray(init_betas, dtype=np.float64)[:n_betas], -beta_clip, beta_clip)
        if init_betas is not None
        else np.zeros(n_betas, dtype=np.float64)
    )

    # ── 3. Compute base measurements at init_betas ────────────────────────────
    def _measure(betas: np.ndarray) -> dict:
        raw_v = estimator._shape_vertices(betas)
        v_cm  = _scale_vertices(raw_v, user_height_cm)
        out   = {}
        for region, y_frac in _REGION_Y.items():
            w = _mesh_width_at(v_cm, y_frac, user_height_cm)
            d = _mesh_depth_at(v_cm, y_frac, user_height_cm)
            if w is not None:
                out[f'{region}_width'] = w
            if d is not None:
                out[f'{region}_depth'] = d
        return out

    base_meas = _measure(base_betas)

    # Keep only keys present in both targets and base measurements
    keys = [k for k in targets if k in base_meas]
    if not keys:
        print("[MultiView] No overlapping keys between targets and mesh — returning init betas")
        return base_betas, targets

    print(f"[MultiView] Fitting {len(keys)} constraints: {keys}")

    # ── 4. Build Jacobian ─────────────────────────────────────────────────────
    DELTA = 0.25
    J = np.zeros((len(keys), n_betas), dtype=np.float64)

    for j in range(n_betas):
        b_j = base_betas.copy()
        b_j[j] += DELTA
        m_j = _measure(b_j)
        for i, k in enumerate(keys):
            if k in m_j:
                J[i, j] = (m_j[k] - base_meas[k]) / DELTA

    # ── 5. Residual vector ────────────────────────────────────────────────────
    delta_m = np.array(
        [targets[k] - base_meas[k] for k in keys],
        dtype=np.float64,
    )

    print(f"[MultiView] Residuals (target - base):")
    for k, dm in zip(keys, delta_m):
        print(f"  {k:<30}: {dm:+.2f} cm  "
              f"(target={targets[k]:.1f}, base={base_meas[k]:.1f})")

    # ── 6. Tikhonov solve ─────────────────────────────────────────────────────
    JT = J.T
    try:
        delta_betas = JT @ np.linalg.solve(
            J @ JT + l2_reg * np.eye(len(keys), dtype=np.float64),
            delta_m,
        )
    except np.linalg.LinAlgError:
        print("[MultiView] Singular matrix — returning init betas")
        return base_betas, targets

    fitted = np.clip(base_betas + delta_betas, -beta_clip, beta_clip)

    # ── 7. Verify improvement ─────────────────────────────────────────────────
    fitted_meas = _measure(fitted)
    for k in keys:
        bv = base_meas.get(k, 0)
        fv = fitted_meas.get(k, 0)
        tv = targets[k]
        print(f"  {k:<30}: base={bv:.1f}  fitted={fv:.1f}  target={tv:.1f}")

    return fitted, targets
