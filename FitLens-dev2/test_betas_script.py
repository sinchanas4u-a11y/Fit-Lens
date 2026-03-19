import sys
import os
sys.path.insert(0, os.getcwd())
import numpy as np

from smpl.smpl_pipeline import run_smpl_pipeline

t_meas = {
    'chest_circumference': 95.0, 
    'waist_circumference': 80.0, 
    'hip_circumference': 100.0,
    'shoulder_width': 45.0
}
landmarks = [{'x': 0, 'y': 0, 'visibility': 1} for _ in range(33)]

res = run_smpl_pipeline(
    landmarks_2d=landmarks,
    image_width=640,
    image_height=480,
    user_height_cm=175.0,
    target_measurements=t_meas,
    use_neutral_pose=True
)

betas = res['betas']
print("Fitted betas:", betas)

if betas is not None:
    print("Max absolute beta:", np.max(np.abs(betas)))
