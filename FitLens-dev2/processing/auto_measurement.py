from smpl.smpl_pipeline import run_smpl_pipeline

def get_smpl_measurements(
  landmarks_2d: list,
  image_width: int,
  image_height: int,
  user_height_cm: float,
  gender: str = 'neutral'
) -> dict:

  smpl_result = run_smpl_pipeline(
    landmarks_2d   = landmarks_2d,
    image_width    = image_width,
    image_height   = image_height,
    user_height_cm = user_height_cm,
    gender         = gender
  )

  if not smpl_result['success']:
    print(f"SMPL failed: {smpl_result['error']}")
    return {}

  m = smpl_result['measurements']

  return {
    'chest_circumference': m.get('chest_circumference'),
    'waist_circumference': m.get('waist_circumference'),
    'hip_circumference':   m.get('hip_circumference'),
    'shoulder_width':      m.get('shoulder_width'),
    'chest_width':         m.get('chest_width'),
    'waist_width':         m.get('waist_width'),
    'hip_width':           m.get('hip_width'),
    'source':              'SMPL 3D Model'
  }
