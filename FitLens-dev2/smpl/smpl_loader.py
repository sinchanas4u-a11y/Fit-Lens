import sys, os, pickle
import numpy as np
from types import ModuleType
from scipy.sparse import issparse

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
      for attr in ['r', '_r', 'val', 'data', '_d']:
        v = getattr(self, attr, None)
        if v is not None:
          arr = np.asarray(v)
          if arr.shape != ():
             if arr.size == 206700: return arr.reshape(6890, 3)
             if arr.size % 206700 == 0 and arr.size > 0: return arr.reshape(6890, 3, -1)
             return arr
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

def load_smpl_pkl(pkl_path: str) -> dict:
  mock_chumpy()
  with open(pkl_path, 'rb') as f:
    data = pickle.load(f, encoding='latin1')

  clean = {}
  for key, val in data.items():
    try:
      # Handle 0-d object arrays
      if isinstance(val, np.ndarray) and val.dtype == object and val.shape == ():
        val = val.item()

      if issparse(val):
        clean[key] = val.toarray()
      elif hasattr(val, '__array__'):
        arr = np.array(val)
        if arr.shape == () and hasattr(val, '__dict__'):
          # Aggressive fallback for chumpy-like objects
          found = False
          for dk, dv in val.__dict__.items():
            if isinstance(dv, np.ndarray) and dv.size > 100:
              if dv.size == 206700: clean[key] = dv.reshape(6890, 3)
              elif dv.size % 206700 == 0: clean[key] = dv.reshape(6890, 3, -1)
              else: clean[key] = dv
              found = True
              break
          if not found: clean[key] = arr
        else:
          clean[key] = arr
      else:
        clean[key] = val
    except Exception:
      clean[key] = val

  return clean

def load_smpl_model(gender: str = 'neutral') -> dict:
  gender_map = {
    'neutral': 'SMPL_NEUTRAL.pkl',
    'male':    'SMPL_MALE.pkl',
    'female':  'SMPL_FEMALE.pkl'
  }
  fname    = gender_map.get(gender, 'SMPL_NEUTRAL.pkl')
  pkl_path = os.path.join('models', 'smpl', fname)

  if not os.path.exists(pkl_path):
    raise FileNotFoundError(
      f"SMPL model not found: {pkl_path}\n"
      f"Download from smpl.is.tue.mpg.de"
    )

  print(f"Loading SMPL {gender} model...")
  model = load_smpl_pkl(pkl_path)
  print(f"Loaded. Vertices: {model['v_template'].shape}")
  return model
