import numpy as np
import os
import sys
import pickle
from types import ModuleType


def mock_chumpy():
    fake = ModuleType('chumpy')

    class Ch(np.ndarray):
        def __new__(cls, val, *a, **kw):
            return np.asarray(val).view(cls)

        @property
        def r(self):
            return np.asarray(self)

    fake.Ch = Ch
    fake.array = np.array
    fake.zeros = np.zeros
    fake.ones = np.ones
    fake.concatenate = np.concatenate
    fake.sqrt = np.sqrt
    fake.sum = np.sum
    fake.dot = np.dot
    fake.mean = np.mean
    sys.modules['chumpy'] = fake
    sys.modules['chumpy.ch'] = fake
    sys.modules['chumpy.reordering'] = fake
    sys.modules['chumpy.utils'] = fake


mock_chumpy()

NEUTRAL_REF = {
    'chest': 97.0,
    'waist': 88.0,
    'hip': 96.0,
}

BETA_EFFECTS = np.array([
    [ 6.0,  5.0,  5.0],
    [ 2.0, -1.0,  2.5],
    [ 4.0,  2.0,  1.5],
    [-1.5,  3.5,  0.5],
    [ 0.5,  0.5,  4.0],
    [ 1.5,  0.5,  0.5],
    [ 0.5,  1.5,  0.5],
    [ 0.5,  0.5,  1.5],
    [ 1.5,  0.5,  0.5],
    [ 0.5,  0.5,  0.5],
])


def compute_betas_direct(
    target_chest_cm,
    target_waist_cm,
    target_hip_cm,
    user_height_cm=170.0,
):
    h_scale = user_height_cm / 170.0
    ref = {k: v * h_scale for k, v in NEUTRAL_REF.items()}

    print(f"Reference at {user_height_cm}cm:")
    print(f"  chest: {ref['chest']:.1f} cm")
    print(f"  waist: {ref['waist']:.1f} cm")
    print(f"  hip  : {ref['hip']:.1f} cm")

    target_diff = np.array([
        target_chest_cm - ref['chest'],
        target_waist_cm - ref['waist'],
        target_hip_cm   - ref['hip'],
    ])

    print(f"Differences:")
    print(f"  chest: {target_diff[0]:+.1f} cm")
    print(f"  waist: {target_diff[1]:+.1f} cm")
    print(f"  hip  : {target_diff[2]:+.1f} cm")

    A = BETA_EFFECTS.T
    betas, _, _, _ = np.linalg.lstsq(A, target_diff, rcond=None)
    betas = np.clip(betas, -2.0, 2.0)

    predicted = BETA_EFFECTS.T @ betas
    print(f"Predicted:")
    print(f"  chest: {ref['chest'] + predicted[0]:.1f}"
          f" (target: {target_chest_cm:.1f})")
    print(f"  waist: {ref['waist'] + predicted[1]:.1f}"
          f" (target: {target_waist_cm:.1f})")
    print(f"  hip  : {ref['hip']   + predicted[2]:.1f}"
          f" (target: {target_hip_cm:.1f})")
    print(f"Betas: {np.round(betas, 3)}")

    return betas


def get_shaped_vertices(
    betas,
    model_path,
    gender='neutral',
    user_height_cm=170.0,
):
    gender_map = {
        'neutral': 'SMPL_NEUTRAL',
        'male':    'SMPL_MALE',
        'female':  'SMPL_FEMALE',
    }
    model_name = gender_map.get(gender.lower(), 'SMPL_NEUTRAL')
    model_file = None

    search_paths = [
        os.path.join(model_path, model_name + '.pkl'),
        os.path.join(model_path, model_name + '.npz'),
        os.path.join(model_path, 'smpl', model_name + '.pkl'),
        os.path.join(model_path, 'smpl', model_name + '.npz'),
    ]

    for p in search_paths:
        if os.path.exists(p):
            model_file = p
            break

    if not model_file:
        print(f"SMPL model not found in {model_path}")
        print(f"Searched: {search_paths}")
        return None

    print(f"Loading: {model_file}")

    if model_file.endswith('.npz'):
        data = np.load(model_file, allow_pickle=True)
    else:
        data = pickle.load(open(model_file, 'rb'), encoding='latin1')

    v_template = np.array(data['v_template'])
    shapedirs  = np.array(data['shapedirs'])

    n = min(len(betas), shapedirs.shape[2])
    shaped = v_template + np.einsum(
        'ijk,k->ij',
        shapedirs[:, :, :n],
        betas[:n],
    )

    y_min  = shaped[:, 1].min()
    y_max  = shaped[:, 1].max()
    h_m    = y_max - y_min
    scale  = user_height_cm / (h_m * 100)
    v_sc   = shaped * scale * 100

    for ax in [0, 1, 2]:
        mid = (v_sc[:, ax].max() + v_sc[:, ax].min()) / 2
        v_sc[:, ax] -= mid

    print(f"Shaped vertices: {len(v_sc)}")
    return v_sc


def compute_betas_from_measurements(
    measurements,
    user_height_cm,
    model_path=None,
    gender='neutral',
):
    chest = measurements.get('chest_circumference')
    waist = measurements.get('waist_circumference')
    hip   = measurements.get('hip_circumference')

    # Validate and fix unrealistic values
    if chest and float(chest) < 70:
        print(f"WARNING chest {chest} too "
              f"small, using width * 3.2")
        chest_w = measurements.get('chest_width', 0)
        chest = (float(chest_w) * 3.2 if chest_w else 90.0)

    if chest and float(chest) > 130:
        print(f"WARNING chest {chest} too "
              f"large, capping at 130")
        chest = 130.0

    if hip and float(hip) > 135:
        print(f"WARNING hip {hip} too "
              f"large, recalculating")
        hip_w = measurements.get('hip_width', 0)
        if hip_w and 33 <= float(hip_w) <= 55:
            hip = float(hip_w) * 3.0
        else:
            hip = float(waist or 85) + 12

    if hip and float(hip) < 75:
        print(f"WARNING hip {hip} too "
              f"small, using waist + 12")
        hip = float(waist or 85) + 12

    print(f"Validated measurements:")
    print(f"  chest: {chest}")
    print(f"  waist: {waist}")
    print(f"  hip  : {hip}")

    if not chest or not waist or not hip:
        print("Missing measurements")
        return np.zeros(10), None

    print(f"\nComputing betas from measurements:")
    betas = compute_betas_direct(
        target_chest_cm=float(chest),
        target_waist_cm=float(waist),
        target_hip_cm=float(hip),
        user_height_cm=float(user_height_cm),
    )

    shaped_verts = None
    if model_path and os.path.exists(model_path):
        shaped_verts = get_shaped_vertices(
            betas=betas,
            model_path=model_path,
            gender=gender,
            user_height_cm=float(user_height_cm),
        )
    else:
        print(f"No model path provided or "
              f"path does not exist: {model_path}")

    return betas, shaped_verts
