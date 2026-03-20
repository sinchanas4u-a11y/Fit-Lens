"""
Multi-view body reconstruction.

Extracts real body measurements from front and side silhouette masks,
then drives SMPL shape betas via a Jacobian-based least-squares solve.
No generic template or average body shape is used — every beta is
determined by pixel evidence from the two input masks.

Pipeline
--------
1. Clean masks: binary threshold, morphological hole-fill, denoise.
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

# Vertical fractions from TOP of body bounding box for each region.
# Spec: chest=30%, waist=50%, hips=65% of body height from top.
REGION_Y_FRACTIONS = {
    'shoulder': 0.18,
    'chest':    0.30,
    'waist':    0.50,
    'hip':      0.65,
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
# 0.  Mask cleaning
# ─────────────────────────────────────────────────────────────────────────────

def clean_mask(mask: np.ndarray) -> np.ndarray:
    """
    Return a clean binary mask (uint8, values 0/255).

    Steps:
    1. Binarise (any non-zero → 255).
    2. Morphological close to fill small holes.
    3. Keep only the largest connected component (removes stray blobs).
    4. Final binary threshold.
    """
    import cv2

    if mask is None or mask.size == 0:
        return mask

    # 1. Binarise
    binary = np.where(mask > 0, np.uint8(255), np.uint8(0))

    # 2. Morphological close — fills holes up to ~15 px
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 3. Keep largest connected component
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    if num_labels > 1:
        # stats[0] is background; find largest foreground component
        fg_sizes = stats[1:, cv2.CC_STAT_AREA]
        largest  = int(np.argmax(fg_sizes)) + 1
        closed   = np.where(labels == largest, np.uint8(255), np.uint8(0))

    # 4. Light open to remove thin noise spikes
    kernel_sm = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_sm, iterations=1)

    return cleaned


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

    Masks are cleaned (binary, hole-filled, largest-component) before
    measurement extraction.

    Parameters
    ----------
    front_mask      : (H, W) uint8 — foreground > 0, front view
    side_mask       : (H, W) uint8 — foreground > 0, side view (may be None)
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
        fm = clean_mask(front_mask)
        bbox = _body_bbox(fm)
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
                span_px = _band_median(fm, y_px, band_half)
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
        sm = clean_mask(side_mask)
        bbox = _body_bbox(sm)
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
                span_px = _band_median(sm, y_px, band_half)
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


def direct_betas_from_measurements(mask_measurements: dict,
                                    user_height_cm: float,
                                    n_betas: int = 10) -> np.ndarray:
    """
    Fast direct beta initialisation from mask-derived measurements.

    Maps width/depth measurements linearly to the first few SMPL betas
    as a warm-start before the Jacobian refinement.  This avoids starting
    from zero betas when we already have good silhouette evidence.

    SMPL beta semantics (approximate, neutral model):
      beta[0]: overall body size (+= larger)
      beta[1]: height vs weight trade-off (+= taller/thinner)
      beta[2]: upper body width (+= wider shoulders/chest)
      beta[3]: waist width (+= wider waist)
      beta[4]: hip width (+= wider hips)
      beta[5]: body depth (+= deeper/thicker front-to-back)
    """
    betas = np.zeros(n_betas, dtype=np.float64)

    # Reference values for a neutral SMPL body at 170 cm
    REF_HEIGHT   = 170.0
    REF_CHEST_W  = 32.0
    REF_WAIST_W  = 27.0
    REF_HIP_W    = 34.0
    REF_CHEST_D  = 22.0

    # Scale factor: user is taller/shorter than reference
    h_scale = user_height_cm / REF_HEIGHT if user_height_cm > 0 else 1.0

    chest_w = mask_measurements.get('chest_width')
    waist_w = mask_measurements.get('waist_width')
    hip_w   = mask_measurements.get('hip_width')
    chest_d = mask_measurements.get('chest_depth')

    # beta[0]: overall size — driven by chest width deviation from reference
    if chest_w is not None:
        betas[0] = float(np.clip((chest_w / h_scale - REF_CHEST_W) / 8.0, -2.0, 2.0))

    # beta[1]: height/weight — thinner body → positive
    if waist_w is not None:
        betas[1] = float(np.clip((REF_WAIST_W - waist_w / h_scale) / 6.0, -2.0, 2.0))

    # beta[2]: upper body width
    if chest_w is not None:
        betas[2] = float(np.clip((chest_w / h_scale - REF_CHEST_W) / 6.0, -2.0, 2.0))

    # beta[3]: waist width
    if waist_w is not None:
        betas[3] = float(np.clip((waist_w / h_scale - REF_WAIST_W) / 5.0, -2.0, 2.0))

    # beta[4]: hip width
    if hip_w is not None:
        betas[4] = float(np.clip((hip_w / h_scale - REF_HIP_W) / 6.0, -2.0, 2.0))

    # beta[5]: body depth
    if chest_d is not None:
        betas[5] = float(np.clip((chest_d / h_scale - REF_CHEST_D) / 5.0, -2.0, 2.0))

    print(f"[DirectBeta] Initialised from mask: {np.round(betas[:6], 3).tolist()}")
    return betas


def validate_pose_projection(estimator, betas: np.ndarray, pose: np.ndarray,
                              landmarks_2d: list, image_width: int,
                              image_height: int, user_height_cm: float) -> dict:
    """
    Project 3D SMPL joints back to 2D and compare with MediaPipe landmarks.

    Returns a dict with per-joint errors and mean alignment error in pixels.
    Used for validation / logging only — does not modify betas or pose.
    """
    MP_TO_SMPL = {
        11: 16, 12: 17, 13: 18, 14: 19, 15: 20, 16: 21,
        23: 1,  24: 2,  25: 4,  26: 5,  27: 7,  28: 8,
    }

    try:
        verts = estimator.get_vertices(betas, pose)
        joints_3d = estimator.get_joints(verts)

        # Scale joints to cm then to image pixels
        y_span = float(joints_3d[:, 1].max() - joints_3d[:, 1].min())
        if y_span < 1e-6 or user_height_cm <= 0:
            return {}
        scale_to_cm = user_height_cm / (y_span * 100.0)  # raw→cm
        # Estimate pixels-per-cm from image height and user height
        px_per_cm = image_height / user_height_cm

        errors = {}
        for mp_idx, smpl_idx in MP_TO_SMPL.items():
            if mp_idx >= len(landmarks_2d) or landmarks_2d[mp_idx] is None:
                continue
            lm = landmarks_2d[mp_idx]
            vis = float(lm.get('visibility', 1.0))
            if vis < 0.3:
                continue

            # 2D landmark in pixels
            lm_x = float(lm['x']) * image_width
            lm_y = float(lm['y']) * image_height

            # Project 3D joint: X→image X, Y→image Y (inverted), ignore Z
            j3 = joints_3d[smpl_idx]
            # Align: find the top of the body in joint space
            j_top_y = joints_3d[:, 1].max()
            proj_x = float(j3[0]) * scale_to_cm * 100.0 * px_per_cm
            proj_y = float(j_top_y - j3[1]) * scale_to_cm * 100.0 * px_per_cm

            err = float(np.hypot(proj_x - lm_x, proj_y - lm_y))
            errors[mp_idx] = round(err, 1)

        if errors:
            mean_err = float(np.mean(list(errors.values())))
            print(f"[Validation] Mean 2D reprojection error: {mean_err:.1f} px  "
                  f"({len(errors)} joints)")
            return {'per_joint_px': errors, 'mean_px': mean_err}
    except Exception as e:
        print(f"[Validation] Skipped: {e}")

    return {}


def _measure_smpl_limb_ratios(estimator, betas: np.ndarray,
                               height_cm: float) -> dict:
    """
    Compute limb-length ratios from SMPL joints (scale-invariant).
    These are comparable to ratios derived from side-view landmarks.
    """
    raw_v = estimator._shape_vertices(betas)
    j = estimator.get_joints(raw_v)
    y_span = float(j[:, 1].max() - j[:, 1].min())
    if y_span < 1e-6:
        return {}
    # Normalise by body height so ratios are scale-invariant
    leg_len  = (np.linalg.norm(j[4] - j[1]) + np.linalg.norm(j[7] - j[4])) / y_span
    arm_len  = (np.linalg.norm(j[18] - j[16]) + np.linalg.norm(j[20] - j[18])) / y_span
    torso_h  = np.linalg.norm(j[12] - j[0]) / y_span  # pelvis → neck
    return {
        'leg_ratio':   float(leg_len),
        'arm_ratio':   float(arm_len),
        'torso_ratio': float(torso_h),
    }


def _extract_side_landmark_ratios(landmarks_2d: list,
                                   user_height_cm: float,
                                   image_width: int | None,
                                   image_height: int | None) -> dict:
    """
    Derive scale-invariant limb ratios from side-view MediaPipe landmarks.
    Returns ratios normalised by body height (nose-to-ankle span).
    """
    def _lm(idx):
        if idx >= len(landmarks_2d) or landmarks_2d[idx] is None:
            return None
        d = landmarks_2d[idx]
        vis = float(d.get('visibility', 1.0))
        if vis < 0.20:
            return None
        x, y = float(d['x']), float(d['y'])
        # Denormalise if needed
        if image_width and image_height:
            if x <= 1.5 and y <= 1.5:
                x *= image_width
                y *= image_height
        return x, y

    nose    = _lm(0)
    l_hip   = _lm(23)
    l_knee  = _lm(25)
    l_ankle = _lm(27)
    l_sho   = _lm(11)
    l_elb   = _lm(13)
    l_wri   = _lm(15)

    if nose is None or l_ankle is None:
        return {}

    body_h = abs(l_ankle[1] - nose[1])
    if body_h < 1e-6:
        return {}

    ratios = {}

    if l_hip and l_knee and l_ankle:
        leg = (np.hypot(l_knee[0]-l_hip[0], l_knee[1]-l_hip[1]) +
               np.hypot(l_ankle[0]-l_knee[0], l_ankle[1]-l_knee[1]))
        ratios['leg_ratio'] = float(leg / body_h)

    if l_sho and l_elb and l_wri:
        arm = (np.hypot(l_elb[0]-l_sho[0], l_elb[1]-l_sho[1]) +
               np.hypot(l_wri[0]-l_elb[0], l_wri[1]-l_elb[1]))
        ratios['arm_ratio'] = float(arm / body_h)

    if l_sho and l_hip:
        torso = np.hypot(l_sho[0]-l_hip[0], l_sho[1]-l_hip[1])
        ratios['torso_ratio'] = float(torso / body_h)

    return ratios


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
    side_landmarks_2d: list | None = None,
    side_image_width:  int  | None = None,
    side_image_height: int  | None = None,
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
    side_landmarks_2d : optional MediaPipe landmarks from side view (33 dicts)
    side_image_width  : side image width in pixels
    side_image_height : side image height in pixels

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

    # ── Step 1b: Augment targets with side-landmark limb ratios ──────────────
    # Side view gives us forward/back proportions (depth) that silhouettes
    # already capture, but also limb-length ratios that constrain betas further.
    side_lm_ratios = {}
    if side_landmarks_2d and len(side_landmarks_2d) >= 28:
        try:
            side_lm_ratios = _extract_side_landmark_ratios(
                side_landmarks_2d, user_height_cm,
                side_image_width, side_image_height,
            )
            print(f"[MultiView] Side landmark ratios: {side_lm_ratios}")
        except Exception as e:
            print(f"[MultiView] Side landmark ratio extraction skipped: {e}")

    if not targets:
        print("[MultiView] No valid targets — returning init betas unchanged")
        base = (np.clip(np.asarray(init_betas, dtype=np.float64)[:n_betas],
                        -beta_clip, beta_clip)
                if init_betas is not None else np.zeros(n_betas, dtype=np.float64))
        return base, {}

    # ── Step 2: Warm-start betas ──────────────────────────────────────────────
    # Use direct beta mapping from mask measurements as warm-start when
    # no external init_betas are provided — much better than zeros.
    if init_betas is not None:
        base_betas = np.clip(
            np.asarray(init_betas, dtype=np.float64)[:n_betas],
            -beta_clip, beta_clip,
        )
    else:
        # Direct mapping gives a better starting point than zeros
        direct = direct_betas_from_measurements(targets, user_height_cm, n_betas)
        base_betas = np.clip(direct, -beta_clip, beta_clip)

    # ── Step 3: Base SMPL measurements ───────────────────────────────────────
    base_meas = _measure_smpl(estimator, base_betas, user_height_cm)

    # Only fit keys present in both targets and SMPL mesh output
    keys = [k for k in targets if k in base_meas]

    # Add side landmark ratio targets if available
    if side_lm_ratios:
        base_lm_meas = _measure_smpl_limb_ratios(estimator, base_betas, user_height_cm)
        for k, v in side_lm_ratios.items():
            if k in base_lm_meas:
                targets[k] = v
                base_meas[k] = base_lm_meas[k]
                keys.append(k)

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
        # Also compute limb ratio measurements for perturbed betas
        if side_lm_ratios:
            m_j.update(_measure_smpl_limb_ratios(estimator, b_j, user_height_cm))
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
