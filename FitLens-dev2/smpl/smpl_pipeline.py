import numpy as np
from smpl.smpl_estimator import SMPLEstimator
from smpl.measurement_extractor import MeasurementExtractor

def run_smpl_pipeline(
  landmarks_2d: list,
  image_width: int,
  image_height: int,
  user_height_cm: float,
  gender: str = 'neutral'
) -> dict:

  print("Running SMPL pipeline...")

  try:
    # Step 1: Fit shape to landmarks
    estimator  = SMPLEstimator(gender=gender)
    fit_result = estimator.fit_to_landmarks(
      landmarks_2d   = landmarks_2d,
      image_width    = image_width,
      image_height   = image_height,
      user_height_cm = user_height_cm
    )
    fitted_betas = fit_result['betas']
    fitted_pose  = fit_result['body_pose']

    # Step 2: Get 3D vertices
    neutral_vertices = estimator.get_vertices(fitted_betas)
    posed_vertices   = estimator.get_vertices(fitted_betas, fitted_pose)

    # Step 3: Extract measurements
    extractor    = MeasurementExtractor()
    measurements = extractor.extract_all(
      vertices       = neutral_vertices,
      user_height_cm = user_height_cm
    )

    # Step 4: Build mesh data for Plotly (x,y,z,i,j,k format)
    faces = np.asarray(estimator.faces, dtype=np.int32)
    
    # Scale vertices to cm for frontend
    y_min = float(posed_vertices[:, 1].min())
    y_max = float(posed_vertices[:, 1].max())
    smpl_height_cm = (y_max - y_min) * 100.0
    
    if smpl_height_cm > 0 and user_height_cm > 0:
      scale = float(user_height_cm) / smpl_height_cm
      vertices_cm = posed_vertices * 100.0 * scale
      
      # Center vertically
      mid_y = (vertices_cm[:, 1].max() + vertices_cm[:, 1].min()) / 2.0
      vertices_cm[:, 1] -= mid_y
      
      # Split for Plotly format
      x = vertices_cm[:, 0].tolist()
      y = vertices_cm[:, 1].tolist()
      z = vertices_cm[:, 2].tolist()
      
      # Faces: split into i, j, k index arrays
      i = faces[:, 0].tolist()
      j = faces[:, 1].tolist()
      k = faces[:, 2].tolist()
      
      mesh_data = {
        'x': x,
        'y': y,
        'z': z,
        'i': i,
        'j': j,
        'k': k,
        'metadata': {
          'vertex_count': int(vertices_cm.shape[0]),
          'face_count': int(faces.shape[0]),
          'height_cm': float(user_height_cm),
          'gender': gender or 'neutral',
          'fitted_to_user': bool(fit_result.get('fitted_to_user')),
          'fit_status': fit_result.get('fit_status', 'fitted'),
          'status_text': fit_result.get('status_text', '✓ Model fitted to your body'),
          'pose_applied': bool(fit_result.get('pose_applied')),
          'landmarks_source': fit_result.get('landmarks_source', 'mediapipe'),
          'landmark_count': int(fit_result.get('landmark_count', len(landmarks_2d))),
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
      'error':        None
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
      'error':        str(e)
    }
