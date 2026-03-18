import numpy as np
import pickle
import sys, os

# Mock chumpy before any pickle load
from types import ModuleType

def mock_chumpy():
    fake = ModuleType('chumpy')
    class Ch(np.ndarray):
        def __new__(cls, val, *a, **kw):
            return np.asarray(val).view(cls)
        @property
        def r(self): return np.asarray(self)
    fake.Ch     = Ch
    fake.array  = np.array
    fake.zeros  = np.zeros
    fake.ones   = np.ones
    fake.concatenate = np.concatenate
    fake.sqrt   = np.sqrt
    fake.sum    = np.sum
    fake.dot    = np.dot
    fake.mean   = np.mean
    sys.modules['chumpy']          = fake
    sys.modules['chumpy.ch']       = fake
    sys.modules['chumpy.reordering'] = fake
    sys.modules['chumpy.utils']    = fake

mock_chumpy()

class BetaCalculator:
  """
  Compute SMPL-X betas directly from
  body measurements using PCA inversion.

  Instead of relying on SMPLify-X 2D
  fitting (which fails without depth),
  we analytically solve for betas that
  produce the user's measurements.
  """

  def __init__(
    self,
    model_path: str,
    gender:     str = 'neutral'
  ):
    self.gender     = gender
    self.model_path = model_path
    self._load_model()

  def _load_model(self):
    # Load SMPL-X model pkl
    model_file = os.path.join(
      self.model_path,
      f'SMPLX_{self.gender.upper()}.npz'
    )
    if not os.path.exists(model_file):
      # Try pkl format
      model_file = os.path.join(
        self.model_path,
        f'SMPL_{self.gender.upper()}.pkl'
      )

    print(f"Loading model: {model_file}")
    if model_file.endswith('.npz'):
      data = np.load(
        model_file, allow_pickle=True
      )
    else:
      data = pickle.load(
        open(model_file, 'rb'),
        encoding='latin1'
      )

    self.v_template  = np.array(
      data['v_template']
    )
    self.shapedirs   = np.array(
      data['shapedirs']
    )
    print(f"Template vertices: "
          f"{len(self.v_template)}")
    print(f"Shape dirs: "
          f"{self.shapedirs.shape}")

  def get_vertices(
    self, betas: np.ndarray
  ) -> np.ndarray:
    """Get mesh vertices for given betas."""
    n = min(len(betas), self.shapedirs.shape[2])
    shaped = self.v_template + np.einsum(
      'ijk,k->ij',
      self.shapedirs[:, :, :n],
      betas[:n]
    )
    return shaped

  def measure_mesh(
    self,
    verts:         np.ndarray,
    user_height_cm: float
  ) -> dict:
    """Extract measurements from mesh."""
    # Scale to user height
    y_min  = verts[:, 1].min()
    y_max  = verts[:, 1].max()
    h_m    = y_max - y_min
    scale  = user_height_cm / (h_m * 100)
    v_sc   = verts * scale * 100  # to cm

    y_max_cm = v_sc[:, 1].max()
    y_min_cm = v_sc[:, 1].min()
    h_cm     = y_max_cm - y_min_cm

    def circ_at(pct, radius_cm=20):
      y_level = y_max_cm - h_cm * pct
      section = v_sc[
        np.abs(v_sc[:, 1] - y_level) < 2.0
      ]
      if len(section) < 10:
        return None
      pts  = section[:, [0, 2]]
      cx   = np.median(pts[:, 0])
      cz   = np.median(pts[:, 1])
      dist = np.sqrt(
        (pts[:, 0] - cx)**2 +
        (pts[:, 1] - cz)**2
      )
      pts = pts[dist < radius_cm]
      if len(pts) < 10:
        return None
      from scipy.spatial import ConvexHull
      try:
        hull  = ConvexHull(pts)
        vh    = pts[hull.vertices]
        n     = len(vh)
        perim = sum(
          np.linalg.norm(
            vh[(i+1)%n] - vh[i]
          )
          for i in range(n)
        )
        return float(perim)
      except Exception:
        return None

    return {
      'chest': circ_at(0.25, 22),
      'waist': circ_at(0.38, 20),
      'hip':   circ_at(0.48, 21),
    }

  def fit_betas_to_measurements(
    self,
    target_chest_cm:  float,
    target_waist_cm:  float,
    target_hip_cm:    float,
    user_height_cm:   float,
    n_betas:          int   = 10,
    n_iterations:     int   = 200
  ) -> np.ndarray:
    """
    Analytically compute betas directly from
    target measurements using a Jacobian 
    pseudo-inverse mapping.
    """
    targets = {
      'chest': target_chest_cm,
      'waist': target_waist_cm,
      'hip':   target_hip_cm,
    }

    print(f"Analytically fitting betas to measurements:")
    print(f"  Target chest : {target_chest_cm} cm")
    print(f"  Target waist : {target_waist_cm} cm")
    print(f"  Target hip   : {target_hip_cm} cm")

    # 1. Base measurements at beta = 0
    base_betas = np.zeros(n_betas)
    base_verts = self.get_vertices(base_betas)
    base_meas = self.measure_mesh(base_verts, user_height_cm)

    # Use only valid keys
    keys = [k for k in ['chest', 'waist', 'hip'] if targets.get(k) and base_meas.get(k)]
    if not keys:
      print("No valid measurements found. Returning zero betas.")
      return base_betas

    # 2. Compute Jacobian matrix J (num_measurements x n_betas)
    J = np.zeros((len(keys), n_betas))
    delta = 1.0  # 1 standard deviation step for finite differences
    
    for j in range(n_betas):
      betas_j = np.zeros(n_betas)
      betas_j[j] = delta
      verts_j = self.get_vertices(betas_j)
      meas_j = self.measure_mesh(verts_j, user_height_cm)
      
      for i, k in enumerate(keys):
        if meas_j.get(k) is not None:
          J[i, j] = (meas_j[k] - base_meas[k]) / delta

    # 3. Compute delta measurements
    delta_m = np.array([targets[k] - base_meas[k] for k in keys])
    
    # 4. Direct analytic solution: beta = J^T (J J^T + lambda I)^-1 delta_m
    # We use Tikhonov regularization (lambda) to avoid extreme shapes
    l2_reg = 0.5
    J_T = J.T
    matrix_to_inv = J @ J_T + l2_reg * np.eye(len(keys))
    
    try:
      fitted_betas = J_T @ np.linalg.solve(matrix_to_inv, delta_m)
    except np.linalg.LinAlgError:
      print("Singular matrix encountered, returning zero betas.")
      fitted_betas = np.zeros(n_betas)

    print(f"Fitted betas  : {np.round(fitted_betas, 3)}")

    # Verify
    verts = self.get_vertices(fitted_betas)
    final = self.measure_mesh(verts, user_height_cm)
    print(f"Final measurements:")
    for k, v in final.items():
      t = targets.get(k, 0)
      if v:
        print(f"  {k:8s}: {v:.1f} cm (target: {t:.1f} cm)")

    return fitted_betas


def compute_betas_from_measurements(
  measurements:   dict,
  user_height_cm: float,
  model_path:     str,
  gender:         str = 'neutral'
) -> np.ndarray:
  """
  Main entry point.
  Takes measurements dict from SMPLify-X
  reader and returns fitted betas.
  """
  chest = measurements.get(
    'chest_circumference'
  )
  waist = measurements.get(
    'waist_circumference'
  )
  hip   = measurements.get(
    'hip_circumference'
  )

  if not all([chest, waist, hip]):
    print("Missing measurements for "
          "beta fitting")
    return np.zeros(10)

  calc = BetaCalculator(model_path, gender)
  return calc.fit_betas_to_measurements(
    target_chest_cm = chest,
    target_waist_cm = waist,
    target_hip_cm   = hip,
    user_height_cm  = user_height_cm
  )
