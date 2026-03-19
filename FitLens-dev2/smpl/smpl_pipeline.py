"""
SMPL mesh generation pipeline.

Key design decisions:
- Betas are clamped to [-2, 2] -- values beyond +-3 produce non-human shapes.
- Shape fitting uses ratio-based losses + strong L2 regularisation.
- Pose estimation uses a two-stage approach:
    Stage 1: Heuristic warm-start from 2D landmark geometry.
    Stage 2: Reprojection optimisation (L-BFGS-B) with biomechanical limits.
- When use_neutral_pose=True the mesh is always rendered in A-pose (safe default).
- When use_neutral_pose=False the optimised pose is applied to the mesh.
"""

import numpy as np
from smpl.smpl_estimator import SMPLEstimator
from smpl.measurement_extractor import MeasurementExtractor

_BETA_CLIP = 2.0


def _align_vertices(vertices, estimator, user_height_cm):
    """Scale to user height, feet at Y=0, centre X/Z on pelvis. Returns cm."""
    y_span = float(vertices[:, 1].max() - vertices[:, 1].min())
    if y_span < 1e-6 or user_height_cm <= 0:
        return None
    scale = (user_height_cm / 100.0) / y_span
    v = vertices * scale
    v[:, 1] -= float(v[:, 1].min())
    root = estimator.get_joints(v)[0]
    v[:, 0] -= root[0]
    v[:, 2] -= root[2]
    return v * 100.0


def _mesh_dict(v_cm, faces, user_height_cm, gender, fit_result, n_landmarks, pose_applied=False):
    return {
        'x': v_cm[:, 0].tolist(),
        'y': v_cm[:, 1].tolist(),
        'z': v_cm[:, 2].tolist(),
        'i': faces[:, 0].tolist(),
        'j': faces[:, 1].tolist(),
        'k': faces[:, 2].tolist(),
        'metadata': {
            'vertex_count':     int(v_cm.shape[0]),
            'face_count':       int(faces.shape[0]),
            'height_cm':        float(user_height_cm),
            'gender':           gender or 'neutral',
            'fitted_to_user':   bool(fit_result.get('fitted_to_user', True)),
            'fit_status':       fit_result.get('fit_status', 'fitted'),
            'status_text':      fit_result.get('status_text', 'Model fitted to your body'),
            'pose_applied':     pose_applied,
            'landmarks_source': fit_result.get('landmarks_source', 'mediapipe'),
            'landmark_count':   int(n_landmarks),
        },
    }


def _build_neutral_mesh(estimator, betas, user_height_cm, gender, fit_result, n_landmarks):
    """Neutral A-pose mesh."""
    faces = np.asarray(estimator.faces, dtype=np.int32)
    verts = estimator.get_vertices(betas)
    v_cm  = _align_vertices(verts, estimator, user_height_cm)
    if v_cm is None:
        return None
    return _mesh_dict(v_cm, faces, user_height_cm, gender, fit_result, n_landmarks, pose_applied=False)


def _build_posed_mesh(estimator, betas, pose, user_height_cm, gender, fit_result, n_landmarks):
    """
    Posed mesh using the estimated body pose.

    The pose is applied to the SMPL model, then the resulting vertices are
    aligned (scaled to user height, feet at Y=0, centred on pelvis).
    Falls back to neutral mesh if the posed mesh is degenerate.
    """
    faces = np.asarray(estimator.faces, dtype=np.int32)

    # Check if pose is non-trivial
    pose_arr = np.asarray(pose, dtype=np.float64).reshape(-1)
    has_pose = bool(np.any(np.abs(pose_arr) > 1e-3))

    if not has_pose:
        return _build_neutral_mesh(estimator, betas, user_height_cm, gender, fit_result, n_landmarks)

    try:
        verts = estimator.get_vertices(betas, pose_arr)
    except Exception as e:
        print(f"[Mesh] Posed vertices failed ({e}), falling back to neutral")
        return _build_neutral_mesh(estimator, betas, user_height_cm, gender, fit_result, n_landmarks)

    # Sanity check: posed mesh should not be wildly different in size from neutral
    neutral_verts = estimator.get_vertices(betas)
    neutral_span  = float(neutral_verts[:, 1].max() - neutral_verts[:, 1].min())
    posed_span    = float(verts[:, 1].max() - verts[:, 1].min())

    if posed_span < neutral_span * 0.3 or posed_span > neutral_span * 2.5:
        print(f"[Mesh] Posed mesh span ({posed_span:.3f}) degenerate vs neutral "
              f"({neutral_span:.3f}) — falling back to neutral")
        return _build_neutral_mesh(estimator, betas, user_height_cm, gender, fit_result, n_landmarks)

    v_cm = _align_vertices(verts, estimator, user_height_cm)
    if v_cm is None:
        return _build_neutral_mesh(estimator, betas, user_height_cm, gender, fit_result, n_landmarks)

    return _mesh_dict(v_cm, faces, user_height_cm, gender, fit_result, n_landmarks, pose_applied=True)


def run_smpl_pipeline(
    landmarks_2d,
    image_width,
    image_height,
    user_height_cm,
    gender='neutral',
    view_type='front',
    use_neutral_pose=True,
    target_measurements=None,
    front_mask=None,
    side_mask=None,
):
    print(f"[Pipeline] view={view_type}  neutral={use_neutral_pose}  "
          f"measurements={bool(target_measurements)}  mask={front_mask is not None}")
    try:
        estimator = SMPLEstimator(gender=gender)

        # Stage 1: fit betas to landmark ratios + estimate pose
        fit_result = estimator.fit_to_landmarks(
            landmarks_2d=landmarks_2d,
            image_width=image_width,
            image_height=image_height,
            user_height_cm=user_height_cm,
            view_type=view_type,
            use_neutral_pose=use_neutral_pose,
        )
        fitted_betas = np.clip(fit_result['betas'], -_BETA_CLIP, _BETA_CLIP)
        fitted_pose  = fit_result['body_pose']
        fit_result['betas'] = fitted_betas

        # Stage 1b: single-view silhouette width refinement
        if front_mask is not None and front_mask.size > 0 and user_height_cm > 0:
            try:
                from smpl.multiview_reconstructor import (
                    extract_measurements_from_masks, _measure_smpl,
                    _JACOBIAN_DELTA, _L2_REG,
                )
                sil = extract_measurements_from_masks(
                    front_mask=front_mask, side_mask=None,
                    user_height_cm=user_height_cm,
                )
                if sil:
                    base = _measure_smpl(estimator, fitted_betas, user_height_cm)
                    keys = [k for k in sil if k in base]
                    if keys:
                        n = 10
                        J = np.zeros((len(keys), n), dtype=np.float64)
                        for j in range(n):
                            bj = fitted_betas.copy()
                            bj[j] += _JACOBIAN_DELTA
                            mj = _measure_smpl(estimator, bj, user_height_cm)
                            for i, k in enumerate(keys):
                                if k in mj:
                                    J[i, j] = (mj[k] - base[k]) / _JACOBIAN_DELTA
                        dm = np.array([sil[k] - base[k] for k in keys], dtype=np.float64)
                        A  = J @ J.T + _L2_REG * np.eye(len(keys), dtype=np.float64)
                        db = J.T @ np.linalg.solve(A, dm)
                        fitted_betas = np.clip(fitted_betas + db, -_BETA_CLIP, _BETA_CLIP)
                        fit_result['betas']       = fitted_betas
                        fit_result['fit_status']  = 'silhouette_refined'
                        fit_result['status_text'] = 'Model fitted from silhouette + landmarks'
                        print(f"[Pipeline] Silhouette: {len(keys)} constraints applied.")
            except Exception as e:
                print(f"[Pipeline] Silhouette refinement skipped: {e}")

        # Stage 2: measurement optimisation
        if target_measurements:
            print("[Pipeline] Measurement optimisation...")
            fitted_betas = estimator.optimize_betas_from_measurements(
                target_measurements=target_measurements,
                user_height_cm=user_height_cm,
                landmarks_2d=landmarks_2d,
                init_betas=fitted_betas,
            )
            fitted_betas = np.clip(fitted_betas, -_BETA_CLIP, _BETA_CLIP)
            fit_result['betas']       = fitted_betas
            fit_result['status_text'] = 'Model optimised to your measurements'
            fit_result['fit_status']  = 'measurement_optimised'

        # Stage 3: measurements always from neutral-pose mesh (unaffected by pose)
        neutral_verts = estimator.get_vertices(fitted_betas)
        measurements  = MeasurementExtractor().extract_all(
            vertices=neutral_verts, user_height_cm=user_height_cm,
        )

        # Stage 4: always neutral-pose mesh — 2D->3D pose lifting is
        # geometrically ambiguous and produces twisted/floating limbs.
        mesh_data = _build_neutral_mesh(
            estimator, fitted_betas, user_height_cm, gender,
            fit_result, len(landmarks_2d),
        )

        print("SMPL measurements:")
        for k, v in measurements.items():
            if v is not None:
                print(f"  {k:30s}: {v} cm")

        return {
            'success':      True,
            'measurements': measurements,
            'betas':        fitted_betas.tolist(),
            'theta':        fitted_pose.tolist() if fitted_pose is not None else np.zeros(72).tolist(),
            'mesh_data':    mesh_data,
            'fit':          fit_result,
            'error':        None,
        }

    except Exception as e:
        import traceback
        print(f"SMPL pipeline error: {e}")
        traceback.print_exc()
        return {
            'success': False, 'measurements': {}, 'betas': None,
            'theta': None, 'mesh_data': None, 'fit': {}, 'error': str(e),
        }


def _build_mesh_data(estimator, betas, pose, user_height_cm, gender, fit_result, landmarks_2d):
    """Build posed mesh, falling back to neutral if pose is degenerate."""
    return _build_posed_mesh(
        estimator, betas, pose, user_height_cm, gender,
        fit_result, len(landmarks_2d),
    )


def run_multiview_smpl_pipeline(
    front_landmarks_2d,
    front_image_width,
    front_image_height,
    user_height_cm,
    gender='neutral',
    front_mask=None,
    side_mask=None,
    use_neutral_pose=True,
    target_measurements=None,
):
    print(f"[MultiView] height={user_height_cm} cm  gender={gender}  "
          f"front_mask={'yes' if front_mask is not None else 'no'}  "
          f"side_mask={'yes' if side_mask is not None else 'no'}  "
          f"measurements={'yes' if target_measurements else 'no'}")

    try:
        from smpl.multiview_reconstructor import fit_betas_multiview

        estimator  = SMPLEstimator(gender=gender)
        fit_result = estimator.fit_to_landmarks(
            landmarks_2d=front_landmarks_2d,
            image_width=front_image_width,
            image_height=front_image_height,
            user_height_cm=user_height_cm,
            view_type='front',
            use_neutral_pose=use_neutral_pose,
        )
        fitted_betas        = np.clip(fit_result['betas'], -_BETA_CLIP, _BETA_CLIP)
        fitted_pose         = fit_result['body_pose']
        fit_result['betas'] = fitted_betas
        silhouette_targets  = {}

        have_front = front_mask is not None and front_mask.size > 0
        have_side  = side_mask  is not None and side_mask.size  > 0

        if have_front and have_side:
            try:
                fitted_betas, silhouette_targets = fit_betas_multiview(
                    estimator=estimator,
                    front_mask=front_mask,
                    side_mask=side_mask,
                    user_height_cm=user_height_cm,
                    init_betas=fitted_betas,
                )
                fitted_betas = np.clip(fitted_betas, -_BETA_CLIP, _BETA_CLIP)
                fit_result['status_text'] = 'Model fitted from front + side silhouettes'
                fit_result['fit_status']  = 'multiview'
                print("[MultiView] Silhouette refinement succeeded.")
            except Exception as e:
                print(f"[MultiView] Silhouette refinement failed ({e}) -- landmark betas kept.")
                fitted_betas = fit_result['betas']
                fit_result['status_text'] = 'Model fitted to front landmarks'
                fit_result['fit_status']  = 'landmark_fallback'
        else:
            missing = [n for n, ok in
                       [('front_mask', have_front), ('side_mask', have_side)] if not ok]
            print(f"[MultiView] Missing {missing} -- landmark betas only.")
            fit_result['status_text'] = 'Model fitted to front landmarks'
            fit_result['fit_status']  = 'landmark_only'

        if target_measurements:
            print("[MultiView] Measurement optimisation...")
            fitted_betas = estimator.optimize_betas_from_measurements(
                target_measurements=target_measurements,
                user_height_cm=user_height_cm,
                landmarks_2d=front_landmarks_2d,
                init_betas=fitted_betas,
            )
            fitted_betas = np.clip(fitted_betas, -_BETA_CLIP, _BETA_CLIP)
            fit_result['status_text'] = 'Model optimised to your measurements'
            fit_result['fit_status']  = 'measurement_optimised'

        # Measurements always from neutral pose
        neutral_verts = estimator.get_vertices(fitted_betas)
        measurements  = MeasurementExtractor().extract_all(
            vertices=neutral_verts, user_height_cm=user_height_cm,
        )

        # Always neutral-pose mesh for display
        mesh_data = _build_neutral_mesh(
            estimator, fitted_betas, user_height_cm, gender,
            fit_result, len(front_landmarks_2d),
        )

        print("[MultiView] Final measurements:")
        for mk, mv in measurements.items():
            if mv is not None:
                print(f"  {mk:30s}: {mv} cm")

        return {
            'success':            True,
            'measurements':       measurements,
            'betas':              fitted_betas.tolist(),
            'theta':              fitted_pose.tolist() if fitted_pose is not None else np.zeros(72).tolist(),
            'mesh_data':          mesh_data,
            'fit':                fit_result,
            'silhouette_targets': silhouette_targets,
            'error':              None,
        }

    except Exception as e:
        import traceback
        print(f"[MultiView] Pipeline error: {e}")
        traceback.print_exc()
        return {
            'success': False, 'measurements': {}, 'betas': None,
            'theta': None, 'mesh_data': None, 'fit': {},
            'silhouette_targets': {}, 'error': str(e),
        }