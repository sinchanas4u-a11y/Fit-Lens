import numpy as np
from smpl.smpl_estimator import SMPLEstimator
from smpl.measurement_extractor import MeasurementExtractor


def run_smpl_pipeline(
  landmarks_2d: list,
  image_width: int,
  image_height: int,
  user_height_cm: float,
  gender: str = 'neutral',
  view_type: str = 'front',
  use_neutral_pose: bool = True,
  target_measurements: dict = None
) -> dict:

  print(f"Running SMPL pipeline (Neutral Pose: {use_neutral_pose}, Personalized: {target_measurements is not None})...")

  try:
    estimator  = SMPLEstimator(gender=gender)

    # Stage 1: fit betas to 2-D landmark ratios
    fit_result = estimator.fit_to_landmarks(
      landmarks_2d     = landmarks_2d,
      image_width      = image_width,
      image_height     = image_height,
      user_height_cm   = user_height_cm,
      view_type        = view_type,
      use_neutral_pose = use_neutral_pose,
    )
    fitted_betas = fit_result['betas']
    fitted_pose  = fit_result['body_pose']

    # Stage 2: iterative optimisation driven by user measurements
    if target_measurements:
      print("[Pipeline] Running measurement optimisation...")
      fitted_betas = estimator.optimize_betas_from_measurements(
        target_measurements = target_measurements,
        user_height_cm      = user_height_cm,
        landmarks_2d        = landmarks_2d,
        init_betas          = fitted_betas,
      )
      fit_result['betas']       = fitted_betas
      fit_result['status_text'] = "Model optimised to your measurements"
      fit_result['fit_status']  = 'measurement_optimised'

    # Stage 3: extract measurements from neutral-pose mesh
    neutral_vertices = estimator.get_vertices(fitted_betas)
    
    # RESET POSE: Ensure neutral, upright, centered pose for the output mesh
    # Instead of using potentially distorted 'fitted_pose' from landmark fitting
    output_pose = np.zeros((24, 3), dtype=np.float64)
    posed_vertices = estimator.get_vertices(fitted_betas, output_pose)

    extractor    = MeasurementExtractor()
    measurements = extractor.extract_all(
      vertices       = neutral_vertices,
      user_height_cm = user_height_cm,
    )

    # Stage 4: build Plotly mesh data
    faces = np.asarray(estimator.faces, dtype=np.int32)

    y_min = float(posed_vertices[:, 1].min())
    y_max = float(posed_vertices[:, 1].max())
    smpl_height_cm = (y_max - y_min) * 100.0

    if smpl_height_cm > 0 and user_height_cm > 0:
      scale       = float(user_height_cm) / smpl_height_cm
      vertices_cm = posed_vertices * 100.0 * scale

      mid_y = (vertices_cm[:, 1].max() + vertices_cm[:, 1].min()) / 2.0
      vertices_cm[:, 1] -= mid_y
      
      # Step: Centre on X and Z for a perfect upright placement
      for ax in [0, 2]:
          mid_ax = (vertices_cm[:, ax].max() + vertices_cm[:, ax].min()) / 2.0
          vertices_cm[:, ax] -= mid_ax

      mesh_data = {
        'x': vertices_cm[:, 0].tolist(),
        'y': vertices_cm[:, 1].tolist(),
        'z': vertices_cm[:, 2].tolist(),
        'i': faces[:, 0].tolist(),
        'j': faces[:, 1].tolist(),
        'k': faces[:, 2].tolist(),
        'metadata': {
          'vertex_count':     int(vertices_cm.shape[0]),
          'face_count':       int(faces.shape[0]),
          'height_cm':        float(user_height_cm),
          'gender':           gender or 'neutral',
          'fitted_to_user':   bool(fit_result.get('fitted_to_user')),
          'fit_status':       fit_result.get('fit_status', 'fitted'),
          'status_text':      fit_result.get('status_text', 'Model fitted to your body'),
          'pose_applied':     bool(fit_result.get('pose_applied')),
          'landmarks_source': fit_result.get('landmarks_source', 'mediapipe'),
          'landmark_count':   int(fit_result.get('landmark_count', len(landmarks_2d))),
        }
      }
    else:
      mesh_data = None

    print("SMPL measurements:")
    for k, v in measurements.items():
      if v is not None:
        print(f"  {k:30s}: {v} cm")

    return {
      'success':      True,
      'measurements': measurements,
      'betas':        fitted_betas.tolist(),
      'theta':        fitted_pose.tolist(),
      'mesh_data':    mesh_data,
      'fit':          fit_result,
      'error':        None,
    }

  except Exception as e:
    import traceback
    print(f"SMPL pipeline error: {e}")
    traceback.print_exc()
    return {
      'success':      False,
      'measurements': {},
      'betas':        None,
      'theta':        None,
      'mesh_data':    None,
      'fit':          {},
      'error':        str(e),
    }


def _build_mesh_data(estimator, betas, pose, user_height_cm, gender,
                     fit_result, landmarks_2d):
    """Scale posed vertices to cm, centre vertically, return Plotly mesh dict."""
    faces          = np.asarray(estimator.faces, dtype=np.int32)
    
    # RESET POSE: Force neutral, upright, centered pose for the output mesh
    # Instead of using 'pose' which might be distorted from 2D projection
    output_pose    = np.zeros((24, 3), dtype=np.float64)
    posed_vertices = estimator.get_vertices(betas, output_pose)

    y_min = float(posed_vertices[:, 1].min())
    y_max = float(posed_vertices[:, 1].max())
    smpl_height_cm = (y_max - y_min) * 100.0

    if smpl_height_cm <= 0 or user_height_cm <= 0:
        return None

    scale       = float(user_height_cm) / smpl_height_cm
    vertices_cm = posed_vertices * 100.0 * scale

    mid_y = (vertices_cm[:, 1].max() + vertices_cm[:, 1].min()) / 2.0
    vertices_cm[:, 1] -= mid_y
    
    # Step: Centre on X and Z for a perfect upright placement
    for ax in [0, 2]:
        mid_ax = (vertices_cm[:, ax].max() + vertices_cm[:, ax].min()) / 2.0
        vertices_cm[:, ax] -= mid_ax

    return {
        'x': vertices_cm[:, 0].tolist(),
        'y': vertices_cm[:, 1].tolist(),
        'z': vertices_cm[:, 2].tolist(),
        'i': faces[:, 0].tolist(),
        'j': faces[:, 1].tolist(),
        'k': faces[:, 2].tolist(),
        'metadata': {
            'vertex_count':     int(vertices_cm.shape[0]),
            'face_count':       int(faces.shape[0]),
            'height_cm':        float(user_height_cm),
            'gender':           gender or 'neutral',
            'fitted_to_user':   bool(fit_result.get('fitted_to_user')),
            'fit_status':       fit_result.get('fit_status', 'fitted'),
            'status_text':      fit_result.get('status_text', 'Model fitted to your body'),
            'pose_applied':     bool(fit_result.get('pose_applied')),
            'landmarks_source': fit_result.get('landmarks_source', 'mediapipe'),
            'landmark_count':   int(fit_result.get('landmark_count', len(landmarks_2d))),
        }
    }


def run_multiview_smpl_pipeline(
    front_landmarks_2d:  list,
    front_image_width:   int,
    front_image_height:  int,
    user_height_cm:      float,
    gender:              str        = 'neutral',
    front_mask:          np.ndarray = None,
    side_mask:           np.ndarray = None,
    use_neutral_pose:    bool       = True,
    target_measurements: dict       = None,
) -> dict:
    """
    Multi-view SMPL pipeline.

    Stage 1: Fit betas to front-view MediaPipe landmarks (warm-start).
    Stage 2: Silhouette refinement from front + side masks (Jacobian solve).
             Falls back to Stage-1 betas if masks are missing or solve fails.
    Stage 3: Iterative measurement optimisation using user measurements
             (height, chest/waist/hip circumferences, shoulder/arm/leg).
    """
    print(f"[MultiView] Starting pipeline  height={user_height_cm} cm  "
          f"gender={gender}  "
          f"front_mask={'yes' if front_mask is not None else 'no'}  "
          f"side_mask={'yes' if side_mask is not None else 'no'}  "
          f"measurements={'yes' if target_measurements else 'no'}")

    try:
        from smpl.multiview_reconstructor import fit_betas_multiview

        # Stage 1: landmark-based warm-start
        estimator  = SMPLEstimator(gender=gender)
        fit_result = estimator.fit_to_landmarks(
            landmarks_2d     = front_landmarks_2d,
            image_width      = front_image_width,
            image_height     = front_image_height,
            user_height_cm   = user_height_cm,
            view_type        = 'front',
            use_neutral_pose = use_neutral_pose,
        )
        landmark_betas = fit_result['betas']
        fitted_pose    = fit_result['body_pose']

        # Stage 2: silhouette refinement
        have_front = front_mask is not None and front_mask.size > 0
        have_side  = side_mask  is not None and side_mask.size  > 0

        if have_front and have_side:
            try:
                fitted_betas, silhouette_targets = fit_betas_multiview(
                    estimator      = estimator,
                    front_mask     = front_mask,
                    side_mask      = side_mask,
                    user_height_cm = user_height_cm,
                    init_betas     = landmark_betas,
                )
                fit_result['status_text'] = "Model fitted from front + side silhouettes"
                fit_result['fit_status']  = 'multiview'
                print("[MultiView] Silhouette refinement succeeded.")
            except Exception as e:
                print(f"[MultiView] Silhouette refinement failed ({e}) "
                      "-- falling back to landmark betas.")
                fitted_betas       = landmark_betas
                silhouette_targets = {}
                fit_result['status_text'] = "Model fitted to front landmarks"
                fit_result['fit_status']  = 'landmark_fallback'
        else:
            missing = [n for n, ok in
                       [('front_mask', have_front), ('side_mask', have_side)]
                       if not ok]
            print(f"[MultiView] Missing {missing} -- using landmark betas only.")
            fitted_betas       = landmark_betas
            silhouette_targets = {}
            fit_result['status_text'] = "Model fitted to front landmarks"
            fit_result['fit_status']  = 'landmark_only'

        # Stage 3: iterative measurement optimisation
        if target_measurements:
            print("[MultiView] Running measurement optimisation...")
            fitted_betas = estimator.optimize_betas_from_measurements(
                target_measurements = target_measurements,
                user_height_cm      = user_height_cm,
                landmarks_2d        = front_landmarks_2d,
                init_betas          = fitted_betas,
            )
            fit_result['status_text'] = "Model optimised to your measurements"
            fit_result['fit_status']  = 'measurement_optimised'

        # Stage 4: extract measurements from neutral-pose mesh
        neutral_vertices = estimator.get_vertices(fitted_betas)
        extractor        = MeasurementExtractor()
        measurements     = extractor.extract_all(
            vertices       = neutral_vertices,
            user_height_cm = user_height_cm,
        )

        # Stage 5: build Plotly mesh data
        mesh_data = _build_mesh_data(
            estimator      = estimator,
            betas          = fitted_betas,
            pose           = fitted_pose,
            user_height_cm = user_height_cm,
            gender         = gender,
            fit_result     = fit_result,
            landmarks_2d   = front_landmarks_2d,
        )

        print("[MultiView] Final measurements:")
        for mk, mv in measurements.items():
            if mv is not None:
                print(f"  {mk:30s}: {mv} cm")

        return {
            'success':            True,
            'measurements':       measurements,
            'betas':              fitted_betas.tolist(),
            'theta':              fitted_pose.tolist(),
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
            'success':            False,
            'measurements':       {},
            'betas':              None,
            'theta':              None,
            'mesh_data':          None,
            'fit':                {},
            'silhouette_targets': {},
            'error':              str(e),
        }
