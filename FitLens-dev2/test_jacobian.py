import numpy as np
import logging
from smpl.smpl_estimator import SMPLEstimator

logging.basicConfig(level=logging.ERROR)

def test_analytic_betas():
    estimator = SMPLEstimator(gender='neutral')
    
    target_measurements = {
        'chest_circumference': 105.0,  # Average is ~90-95
        'waist_circumference': 90.0,   # Average is ~80
        'hip_circumference': 100.0,    # Average is ~95
        'shoulder_width': 50.0         # Average is ~40
    }
    user_height_cm = 180.0
    n_betas = 10
    
    levels = {
        'chest_circumference': 0.27,
        'waist_circumference': 0.40,
        'hip_circumference': 0.52,
    }
    
    print(f"Target measurements: {target_measurements}")
    
    # 1. Base measurements at beta = 0
    base_betas = np.zeros(n_betas, dtype=np.float64)
    base_v = estimator._shape_vertices(base_betas)
    base_meas = {}
    
    for name, y_pct in levels.items():
        if name in target_measurements:
            val = estimator._calculate_mesh_circumference(base_v, y_pct, user_height_cm)
            if val: base_meas[name] = val
            
    if 'shoulder_width' in target_measurements:
        joints = estimator.get_joints(base_v)
        y_min, y_max = base_v[:, 1].min(), base_v[:, 1].max()
        scale = user_height_cm / ((y_max - y_min) * 100.0)
        sh_dist = np.linalg.norm(joints[16] - joints[17]) * 100.0 * scale
        base_meas['shoulder_width'] = sh_dist
        
    print(f"Base measurements (beta=0): {base_meas}")
    
    keys = list(base_meas.keys())
    if not keys:
        print("No valid measurements found.")
        return
        
    # 2. Compute Jacobian matrix J (num_measurements x n_betas)
    J = np.zeros((len(keys), n_betas), dtype=np.float64)
    delta = 1.0 # beta units are roughly standard deviations, 1.0 is a good scale
    
    for j in range(n_betas):
        betas_j = np.zeros(n_betas, dtype=np.float64)
        betas_j[j] = delta
        v_j = estimator._shape_vertices(betas_j)
        
        meas_j = {}
        for name, y_pct in levels.items():
            if name in target_measurements:
                val = estimator._calculate_mesh_circumference(v_j, y_pct, user_height_cm)
                if val: meas_j[name] = val
                
        if 'shoulder_width' in target_measurements:
            joints_j = estimator.get_joints(v_j)
            y_min, y_max = v_j[:, 1].min(), v_j[:, 1].max()
            scale = user_height_cm / ((y_max - y_min) * 100.0)
            sh_dist = np.linalg.norm(joints_j[16] - joints_j[17]) * 100.0 * scale
            meas_j['shoulder_width'] = sh_dist
            
        for i, k in enumerate(keys):
            if k in meas_j:
                J[i, j] = (meas_j[k] - base_meas[k]) / delta
                
    # 3. Compute delta m
    delta_m = np.array([target_measurements[k] - base_meas[k] for k in keys], dtype=np.float64)
    print(f"Delta measurements: {dict(zip(keys, delta_m))}")
    
    # 4. Solve for betas: beta = J^T (J J^T + lambda I)^-1 delta_m
    # We use a small regularization lambda to avoid extreme betas and distribute the deformation
    l2_reg = 0.5 
    J_T = J.T
    matrix_to_inv = J @ J_T + l2_reg * np.eye(len(keys), dtype=np.float64)
    
    try:
        fitted_betas = J_T @ np.linalg.solve(matrix_to_inv, delta_m)
    except np.linalg.LinAlgError:
        print("Singular matrix encountered.")
        fitted_betas = np.zeros(n_betas, dtype=np.float64)
        
    print(f"\nAnalyically Fitted betas:\n{fitted_betas}")
    
    # 5. Verify the new measurements
    v_fit = estimator._shape_vertices(fitted_betas)
    fit_meas = {}
    for name, y_pct in levels.items():
        if name in target_measurements:
            val = estimator._calculate_mesh_circumference(v_fit, y_pct, user_height_cm)
            if val: fit_meas[name] = val
    if 'shoulder_width' in target_measurements:
        joints_fit = estimator.get_joints(v_fit)
        y_min, y_max = v_fit[:, 1].min(), v_fit[:, 1].max()
        scale = user_height_cm / ((y_max - y_min) * 100.0)
        sh_dist = np.linalg.norm(joints_fit[16] - joints_fit[17]) * 100.0 * scale
        fit_meas['shoulder_width'] = sh_dist
        
    print(f"Verified measurements with fitted betas: {fit_meas}")
    
if __name__ == '__main__':
    test_analytic_betas()
