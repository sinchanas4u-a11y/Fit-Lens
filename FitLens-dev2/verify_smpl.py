import sys, os, pickle, numpy as np
from types import ModuleType

# ── Step 1: Mock chumpy ────────────────────────
def mock_chumpy():
  fake = ModuleType('chumpy')
  class Ch:
    def __init__(self, *a, **kw):
      if a:
        self.r = np.asarray(a[0])
    def __setstate__(self, state):
      if isinstance(state, dict):
        for k, v in state.items():
          setattr(self, k, v)
      else:
        self.r = np.asarray(state)
    def __array__(self, *args, **kwargs):
      r = getattr(self, 'r', None)
      if r is not None: return np.asarray(r)
      d = getattr(self, '_d', None)
      if d is not None:
        d = np.asarray(d)
        if d.size == 206700: return d.reshape(6890, 3)
        if d.size % 206700 == 0: return d.reshape(6890, 3, -1)
        return d
      return np.array(0)
  fake.Ch          = Ch
  fake.Select      = Ch
  fake.PolyDynamicReshaper = Ch
  fake.array       = np.array
  fake.zeros       = np.zeros
  fake.ones        = np.ones
  fake.concatenate = np.concatenate
  fake.sqrt        = np.sqrt
  fake.sum         = np.sum
  fake.dot         = np.dot
  fake.mean        = np.mean
  sys.modules['chumpy']            = fake
  sys.modules['chumpy.ch']         = fake
  sys.modules['chumpy.reordering'] = fake
  sys.modules['chumpy.utils']      = fake

mock_chumpy()

# ── Step 2: Load and verify each pkl ──────────
model_dir = 'models/smpl'
files = [
  'SMPL_NEUTRAL.pkl',
  'SMPL_MALE.pkl',
  'SMPL_FEMALE.pkl'
]

all_ok = True
for fname in files:
  fpath = os.path.join(model_dir, fname)
  if not os.path.exists(fpath):
    print(f'NOT FOUND : {fname}')
    print(f'  Expected : {os.path.abspath(fpath)}')
    all_ok = False
    continue
  try:
    with open(fpath, 'rb') as f:
      data = pickle.load(f, encoding='latin1')
    verts = np.array(data['v_template'])
    faces = np.array(data['f'])
    print(f'OK : {fname}')
    print(f'     vertices : {verts.shape}')
    print(f'     faces    : {faces.shape}')
    print(f'     keys     : {list(data.keys())}')
  except Exception as e:
    print(f'FAIL : {fname} — {e}')
    all_ok = False
  print()

# ── Step 3: Test SMPLEstimator ─────────────────
if all_ok:
  print("Testing SMPLEstimator...")
  try:
    from smpl.smpl_estimator import SMPLEstimator
    est   = SMPLEstimator(gender='neutral')
    verts = est.get_vertices(np.zeros(10))
    print(f"Vertices shape : {verts.shape}")

    from smpl.measurement_extractor import (
      MeasurementExtractor
    )
    ext   = MeasurementExtractor()
    meas  = ext.extract_all(verts, 175.0)
    print("Measurements:")
    for k, v in meas.items():
      print(f"  {k:30s}: {v}")
    print()
    print("ALL SMPL TESTS PASSED")
  except Exception as e:
    import traceback
    print(f"FAIL: {e}")
    traceback.print_exc()
else:
  print("Fix missing files before running tests")
