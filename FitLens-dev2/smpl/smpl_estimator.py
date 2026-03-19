import numpy as np
from scipy.optimize import minimize

from smpl.smpl_loader import load_smpl_model


class SMPLEstimator:
    MP_TO_SMPL = {
        11: 16,  # left shoulder
        12: 17,  # right shoulder
        13: 18,  # left elbow
        14: 19,  # right elbow
        15: 20,  # left wrist
        16: 21,  # right wrist
        23: 1,   # left hip
        24: 2,   # right hip
        25: 4,   # left knee
        26: 5,   # right knee
        27: 7,   # left ankle
        28: 8,   # right ankle
    }

    POSE_BONE_MAP = (
        (1, 23, 25, 1, 4),    # left hip -> knee
        (4, 25, 27, 4, 7),    # left knee -> ankle
        (2, 24, 26, 2, 5),    # right hip -> knee
        (5, 26, 28, 5, 8),    # right knee -> ankle
        (16, 11, 13, 16, 18), # left shoulder -> elbow
        (18, 13, 15, 18, 20), # left elbow -> wrist
        (17, 12, 14, 17, 19), # right shoulder -> elbow
        (19, 14, 16, 19, 21), # right elbow -> wrist
    )

    def __init__(self, gender="neutral"):
        self.model = load_smpl_model(gender)
        self.gender = gender
        self.v_template = np.asarray(self.model["v_template"], dtype=np.float64)
        self.shapedirs = np.asarray(self.model["shapedirs"], dtype=np.float64)
        self.J_regressor = np.asarray(self.model["J_regressor"], dtype=np.float64)
        self.faces = np.asarray(self.model["f"], dtype=np.int32)
        weights = self.model.get("weights")
        self.weights = np.asarray(weights, dtype=np.float64) if weights is not None else np.empty((0, 0), dtype=np.float64)
        self.posedirs = self._reshape_pose_dirs(self.model.get("posedirs"))
        self.parents = self._build_parent_array(self.model.get("kintree_table"))
        print(f"SMPLEstimator ready — gender: {gender}")

    def _reshape_pose_dirs(self, pose_dirs):
        if pose_dirs is None:
            return None
        pose_dirs = np.asarray(pose_dirs, dtype=np.float64)
        if pose_dirs.ndim == 3:
            return pose_dirs.reshape(-1, pose_dirs.shape[-1])
        return pose_dirs

    def _build_parent_array(self, kintree_table):
        if kintree_table is None:
            return np.full(24, -1, dtype=np.int32)
        table = np.asarray(kintree_table)
        if table.ndim == 1:
            parents = table.astype(np.int32)
            if parents.size > 0:
                parents[0] = -1
            return parents

        if table.shape[0] == 2:
            joint_count = table.shape[1]
            parents = np.full(joint_count, -1, dtype=np.int32)
            id_to_col = {int(table[1, i]): i for i in range(joint_count)}
            for i in range(1, joint_count):
                parent_id = int(table[0, i])
                parents[i] = id_to_col.get(parent_id, parent_id if parent_id < joint_count else 0)
            return parents

        parents = table[0].astype(np.int32)
        if parents.size > 0:
            parents[0] = -1
        return parents

    def _shape_vertices(self, betas: np.ndarray) -> np.ndarray:
        n_betas = min(betas.shape[0], self.shapedirs.shape[2])
        return self.v_template + np.einsum(
            "ijk,k->ij",
            self.shapedirs[:, :, :n_betas],
            betas[:n_betas],
        )

    def get_vertices(self, betas: np.ndarray, pose: np.ndarray = None, global_orient: np.ndarray = None) -> np.ndarray:
        v_shaped = self._shape_vertices(np.asarray(betas, dtype=np.float64))
        if pose is None:
            pose = np.zeros((24, 3), dtype=np.float64)
        else:
            pose = np.asarray(pose, dtype=np.float64).reshape(-1, 3)
            
        if pose.shape[0] < 24:
            padded = np.zeros((24, 3), dtype=np.float64)
            padded[:pose.shape[0]] = pose
            pose = padded
            
        # Apply global orientation if provided
        if global_orient is not None:
            pose[0] = np.asarray(global_orient, dtype=np.float64).reshape(3)

        if self.posedirs is None or self.weights.size == 0:
            return v_shaped

        joints = self.get_joints(v_shaped)
        rotations = self._rodrigues_batch(pose[:24])
        identity = np.eye(3, dtype=np.float64)
        pose_feature = (rotations[1:] - identity).reshape(-1)

        if self.posedirs.shape[1] == pose_feature.shape[0]:
            pose_offsets = (self.posedirs @ pose_feature).reshape(-1, 3)
            v_posed = v_shaped + pose_offsets
        else:
            v_posed = v_shaped

        transforms = np.zeros((24, 4, 4), dtype=np.float64)
        transforms[0] = self._with_zeros(np.hstack((rotations[0], joints[0].reshape(3, 1))))
        for joint_idx in range(1, 24):
            parent_idx = int(self.parents[joint_idx])
            rel_joint = joints[joint_idx] - joints[parent_idx]
            local_transform = self._with_zeros(
                np.hstack((rotations[joint_idx], rel_joint.reshape(3, 1)))
            )
            transforms[joint_idx] = transforms[parent_idx] @ local_transform

        joint_h = np.concatenate(
            (joints[:24], np.zeros((24, 1), dtype=np.float64)),
            axis=1,
        ).reshape(24, 4, 1)
        transforms = transforms - self._pack(np.matmul(transforms, joint_h))

        blend_transforms = np.tensordot(self.weights, transforms, axes=[[1], [0]])
        vertices_h = np.concatenate(
            (v_posed, np.ones((v_posed.shape[0], 1), dtype=np.float64)),
            axis=1,
        ).reshape(v_posed.shape[0], 4, 1)

        return np.matmul(blend_transforms, vertices_h).reshape(-1, 4)[:, :3]

    def get_joints(self, vertices: np.ndarray) -> np.ndarray:
        return self.J_regressor @ vertices

    def fit_to_measurements(self, target_measurements, user_height_cm, n_betas=10):
        """
        Fit body shape (betas) analytically to specific circumference and width
        measurements using a single Jacobian solve.  Used as a fast warm-start
        before the full iterative optimisation.
        """
        print(f"Analytically fitting SMPL betas to measurements: {target_measurements}")

        levels = {
            'chest_circumference': 0.27,
            'waist_circumference': 0.40,
            'hip_circumference':   0.52,
        }

        base_betas = np.zeros(n_betas, dtype=np.float64)
        base_v     = self._shape_vertices(base_betas)
        base_meas  = {}

        for name, y_pct in levels.items():
            if name in target_measurements:
                val = self._calculate_mesh_circumference(base_v, y_pct, user_height_cm)
                if val:
                    base_meas[name] = val

        if 'shoulder_width' in target_measurements:
            y_min, y_max = base_v[:, 1].min(), base_v[:, 1].max()
            scale  = user_height_cm / ((y_max - y_min) * 100.0)
            joints = self.get_joints(base_v)
            base_meas['shoulder_width'] = (
                np.linalg.norm(joints[16] - joints[17]) * 100.0 * scale
            )

        keys = list(base_meas.keys())
        if not keys:
            print("No valid measurements found. Returning base betas.")
            return base_betas

        J     = np.zeros((len(keys), n_betas), dtype=np.float64)
        delta = 1.0

        for j in range(n_betas):
            betas_j    = np.zeros(n_betas, dtype=np.float64)
            betas_j[j] = delta
            v_j        = self._shape_vertices(betas_j)
            meas_j     = {}

            for name, y_pct in levels.items():
                if name in target_measurements:
                    val = self._calculate_mesh_circumference(v_j, y_pct, user_height_cm)
                    if val:
                        meas_j[name] = val

            if 'shoulder_width' in target_measurements:
                y_min, y_max = v_j[:, 1].min(), v_j[:, 1].max()
                scale    = user_height_cm / ((y_max - y_min) * 100.0)
                joints_j = self.get_joints(v_j)
                meas_j['shoulder_width'] = (
                    np.linalg.norm(joints_j[16] - joints_j[17]) * 100.0 * scale
                )

            for i, k in enumerate(keys):
                if k in meas_j:
                    J[i, j] = (meas_j[k] - base_meas[k]) / delta

        delta_m      = np.array(
            [target_measurements[k] - base_meas[k] for k in keys],
            dtype=np.float64,
        )
        l2_reg       = 0.5
        J_T          = J.T
        matrix_to_inv = J @ J_T + l2_reg * np.eye(len(keys), dtype=np.float64)

        try:
            fitted_betas = J_T @ np.linalg.solve(matrix_to_inv, delta_m)
        except np.linalg.LinAlgError:
            print("Singular matrix encountered, falling back to zero betas.")
            fitted_betas = np.zeros(n_betas, dtype=np.float64)

        print(f"Analytical fit betas: {np.round(fitted_betas, 3)}")
        return fitted_betas

    # ── Measurement weights for the optimisation loss ─────────────────────────
    _OPT_WEIGHTS = {
        'chest_circumference': 2.0,
        'waist_circumference': 2.0,
        'hip_circumference':   2.0,
        'shoulder_width':      1.5,
        'height':              1.0,
        'arm_length':          0.8,
        'leg_length':          0.8,
    }

    def _extract_mesh_measurements(self, betas: np.ndarray,
                                   user_height_cm: float) -> dict:
        """
        Compute all optimisable measurements from shaped (neutral-pose) vertices.
        Returns a dict of {key: value_cm}.
        """
        v   = self._shape_vertices(betas)
        j   = self.get_joints(v)

        y_min, y_max = v[:, 1].min(), v[:, 1].max()
        h_m  = y_max - y_min
        if h_m < 1e-6:
            return {}
        scale = user_height_cm / (h_m * 100.0)   # cm per raw unit

        out = {}

        # Height
        out['height'] = float((y_max - y_min) * 100.0 * scale)

        # Circumferences
        for name, y_pct in (
            ('chest_circumference', 0.27),
            ('waist_circumference', 0.40),
            ('hip_circumference',   0.52),
        ):
            val = self._calculate_mesh_circumference(v, y_pct, user_height_cm)
            if val is not None:
                out[name] = val

        # Shoulder width (joint-based — robust, no arm contamination)
        out['shoulder_width'] = float(
            np.linalg.norm(j[16] - j[17]) * 100.0 * scale
        )

        # Arm length: shoulder → elbow → wrist  (left side, joints 16→18→20)
        arm = (
            np.linalg.norm(j[18] - j[16])
            + np.linalg.norm(j[20] - j[18])
        ) * 100.0 * scale
        out['arm_length'] = float(arm)

        # Leg length: hip → knee → ankle  (left side, joints 1→4→7)
        leg = (
            np.linalg.norm(j[4] - j[1])
            + np.linalg.norm(j[7] - j[4])
        ) * 100.0 * scale
        out['leg_length'] = float(leg)

        return out

    def optimize_betas_from_measurements(
        self,
        target_measurements: dict,
        user_height_cm:      float,
        landmarks_2d:        list  = None,
        init_betas:          np.ndarray = None,
        n_betas:             int   = 10,
        n_iter:              int   = 300,
        beta_clip:           float = 3.0,
    ) -> np.ndarray:
        """
        Iterative gradient-descent optimisation of SMPL shape betas.

        Minimises a weighted MSE loss between mesh-derived measurements and
        the user's real measurements, plus an optional landmark-ratio term
        and L2 regularisation on betas.

        Parameters
        ----------
        target_measurements : dict
            Any subset of: height, chest_circumference, waist_circumference,
            hip_circumference, shoulder_width, arm_length, leg_length.
            Values in cm.
        user_height_cm : float
            Known standing height — used to scale the mesh.
        landmarks_2d : list, optional
            33-item MediaPipe landmark list.  When provided, adds a joint-ratio
            term to the loss so the mesh proportions also match the 2-D pose.
        init_betas : np.ndarray, optional
            Warm-start betas (e.g. from fit_to_measurements or fit_to_landmarks).
        n_betas : int
            Number of shape coefficients to optimise (max 10).
        n_iter : int
            Maximum L-BFGS-B iterations.
        beta_clip : float
            Hard clamp applied to the final betas.

        Returns
        -------
        np.ndarray  shape (n_betas,)
        """
        print(f"[BetaOpt] Optimising {n_betas} betas  "
              f"targets={list(target_measurements.keys())}  "
              f"height={user_height_cm} cm")

        # Normalise target keys — accept both 'chest' and 'chest_circumference'
        _aliases = {
            'chest':  'chest_circumference',
            'waist':  'waist_circumference',
            'hips':   'hip_circumference',
            'hip':    'hip_circumference',
        }
        targets = {
            _aliases.get(k, k): float(v)
            for k, v in target_measurements.items()
            if v is not None
        }

        # Warm-start
        if init_betas is not None:
            x0 = np.clip(
                np.asarray(init_betas, dtype=np.float64)[:n_betas],
                -beta_clip, beta_clip,
            )
        else:
            x0 = np.zeros(n_betas, dtype=np.float64)

        # Pre-compute landmark targets for ratio loss (if provided)
        lm_targets = None
        if landmarks_2d is not None:
            lm_targets = self._prepare_landmark_targets(landmarks_2d)

        def loss_fn(betas_flat):
            betas = np.asarray(betas_flat, dtype=np.float64)
            pred  = self._extract_mesh_measurements(betas, user_height_cm)
            if not pred:
                return 1e6

            total = 0.0
            for key, target_val in targets.items():
                if key not in pred:
                    continue
                w   = self._OPT_WEIGHTS.get(key, 1.0)
                # Normalise residual by target value so all terms are unit-free
                res = (pred[key] - target_val) / max(target_val, 1.0)
                total += w * res * res

            # Landmark joint-ratio term (keeps proportions consistent with 2-D pose)
            if lm_targets and len(lm_targets) >= 4:
                joints = self.get_joints(self._shape_vertices(betas))
                total += 0.5 * self._ratio_loss(joints, lm_targets)

            # L2 regularisation — penalise extreme betas
            total += 0.02 * float(np.sum(betas ** 2))
            return float(total)

        result = minimize(
            loss_fn,
            x0=x0,
            method='L-BFGS-B',
            bounds=[(-beta_clip, beta_clip)] * n_betas,
            options={'maxiter': n_iter, 'ftol': 1e-10, 'gtol': 1e-7},
        )

        fitted = np.clip(
            np.asarray(result.x, dtype=np.float64),
            -beta_clip, beta_clip,
        )

        # Log final residuals
        pred_final = self._extract_mesh_measurements(fitted, user_height_cm)
        print(f"[BetaOpt] Converged in {result.nit} iters  "
              f"loss={result.fun:.6f}  success={result.success}")
        for key, target_val in targets.items():
            pred_val = pred_final.get(key)
            if pred_val is not None:
                print(f"  {key:<26}: target={target_val:.1f}  "
                      f"pred={pred_val:.1f}  "
                      f"err={pred_val - target_val:+.1f} cm")

        print(f"[BetaOpt] Final betas: {np.round(fitted, 3).tolist()}")
        return fitted

    def _calculate_mesh_circumference(self, vertices, y_pct, user_height_cm):
        """Helper to calculate mesh circumference at a relative height percentage."""
        y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
        h_m = y_max - y_min
        if h_m <= 0: return None
        
        scale = user_height_cm / (h_m * 100.0)
        v_cm = vertices * 100.0 * scale
        
        y_max_cm = v_cm[:, 1].max()
        h_cm = user_height_cm
        y_level = y_max_cm - h_cm * y_pct
        
        # Vertical slice with 2cm tolerance
        mask = np.abs(v_cm[:, 1] - y_level) < 1.0
        section = v_cm[mask]
        
        if len(section) < 15: return None
        
        # Use 2D convex hull for circumference approximation
        from scipy.spatial import ConvexHull
        try:
            pts = section[:, [0, 2]] # X, Z plane
            # Remove arms by x proximity
            center_x = pts[:, 0].mean()
            pts = pts[np.abs(pts[:, 0] - center_x) < 30.0]
            
            if len(pts) < 10: return None
            
            hull = ConvexHull(pts)
            vh = pts[hull.vertices]
            n = len(vh)
            perim = sum(np.linalg.norm(vh[(i+1)%n] - vh[i]) for i in range(n))
            return float(perim)
        except:
            return None

    def fit_to_landmarks(self, landmarks_2d, image_width, image_height, user_height_cm, view_type='front', use_neutral_pose=False):
        targets = self._prepare_landmark_targets(landmarks_2d)
        if len(targets) < 4:
            raise ValueError("Not enough visible MediaPipe landmarks for SMPL fitting")

        def objective(betas):
            betas = np.asarray(betas, dtype=np.float64)
            joints = self.get_joints(self._shape_vertices(betas))
            joint_loss = self._joint_reprojection_loss(joints, targets)
            ratio_loss = self._ratio_loss(joints, targets)
            return (joint_loss * 8.0) + (ratio_loss * 3.0) + (0.025 * np.sum(betas ** 2))

        result = minimize(
            objective,
            x0=np.zeros(10, dtype=np.float64),
            method="L-BFGS-B",
            options={"maxiter": 250, "ftol": 1e-9},
        )

        betas = np.asarray(result.x, dtype=np.float64)
        pose = self.estimate_pose_from_landmarks(landmarks_2d, betas, view_type=view_type, use_neutral=use_neutral_pose)
        visibility_values = np.array([item["visibility"] for item in targets.values()], dtype=np.float64)

        print(f"SMPL fit loss: {result.fun:.6f}")
        return {
            "betas": betas,
            "body_pose": pose,
            "fit_status": "fitted",
            "fitted_to_user": True,
            "pose_applied": not use_neutral_pose and bool(np.any(np.linalg.norm(pose.reshape(-1, 3)[1:], axis=1) > 1e-3)),
            "status_text": "✓ Model fitted to your body (Neutral Pose)" if use_neutral_pose else "✓ Model fitted to your body",
            "landmarks_source": "mediapipe",
            "landmarks_mode": "real",
            "landmark_count": len(landmarks_2d),
            "visible_landmark_count": int(len(targets)),
            "visibility_mean": float(visibility_values.mean()) if visibility_values.size else 0.0,
            "optimization_loss": float(result.fun),
            "optimization_success": bool(result.success),
            "image_width": int(image_width),
            "image_height": int(image_height),
            "user_height_cm": float(user_height_cm),
            "view_type": view_type
        }

    def estimate_pose_from_landmarks(self, landmarks_2d, betas, view_type='front', use_neutral=False):
        pose = np.zeros((24, 3), dtype=np.float64)
        
        if use_neutral:
            # Return neutral standing pose (all zeros)
            # pose[0] is global orientation; [0,0,0] is neutral upright in standard SMPL
            return pose.reshape(-1)

        joints = self.get_joints(self._shape_vertices(np.asarray(betas, dtype=np.float64)))
        
        # Set global orientation based on view
        if view_type == 'side':
            pose[0, 1] = np.pi / 2.0  # Rotate 90 degrees for side view
        elif view_type == 'back':
            pose[0, 1] = np.pi
            
        rest_xy = np.stack((joints[:, 0], -joints[:, 1]), axis=1)

        hip_center = self._average_target_point(landmarks_2d, (23, 24))
        shoulder_center = self._average_target_point(landmarks_2d, (11, 12))
        
        if hip_center is not None and shoulder_center is not None:
            target_torso = self._target_vector(hip_center, shoulder_center)
            rest_torso = (rest_xy[16] + rest_xy[17]) * 0.5 - (rest_xy[1] + rest_xy[2]) * 0.5
            # Root rotation (global z)
            pose[0, 2] = self._clamp_angle(self._signed_angle(rest_torso, target_torso), limit=0.8)

        cumulative_z = {0: pose[0, 2]}
        for joint_idx, mp_parent, mp_child, smpl_parent, smpl_child in self.POSE_BONE_MAP:
            parent_point = self._landmark_point(landmarks_2d, mp_parent)
            child_point = self._landmark_point(landmarks_2d, mp_child)
            if parent_point is None or child_point is None:
                continue

            target_vec = self._target_vector(parent_point, child_point)
            rest_vec = rest_xy[smpl_child] - rest_xy[smpl_parent]
            desired_global = self._vector_angle(target_vec)
            rest_global = self._vector_angle(rest_vec)
            
            p_idx = int(self.parents[joint_idx])
            parent_global = cumulative_z.get(p_idx, cumulative_z.get(0, 0.0))
            
            local_angle = self._wrap_angle(desired_global - rest_global - parent_global)
            pose[joint_idx, 2] = self._clamp_angle(local_angle)
            cumulative_z[joint_idx] = parent_global + pose[joint_idx, 2]

        return pose.reshape(-1)

    def _prepare_landmark_targets(self, landmarks_2d):
        targets = {}
        for mp_idx, smpl_idx in self.MP_TO_SMPL.items():
            point = self._landmark_point(landmarks_2d, mp_idx)
            visibility = self._landmark_visibility(landmarks_2d, mp_idx)
            if point is None or visibility <= 0.35:
                continue
            targets[smpl_idx] = {
                "xy": point,
                "visibility": visibility,
            }
        return targets

    def _joint_reprojection_loss(self, joints, targets):
        ordered = sorted(targets.keys())
        source = np.array([[joints[idx, 0], -joints[idx, 1]] for idx in ordered], dtype=np.float64)
        target = np.array([targets[idx]["xy"] for idx in ordered], dtype=np.float64)
        weights = np.array([targets[idx]["visibility"] for idx in ordered], dtype=np.float64)
        scale, translation = self._similarity_transform(source, target, weights)
        predicted = (source * scale) + translation
        squared_error = np.sum((predicted - target) ** 2, axis=1)
        return float(np.average(squared_error, weights=weights))

    def _ratio_loss(self, joints, targets):
        joint_xy = {idx: np.array([joints[idx, 0], -joints[idx, 1]], dtype=np.float64) for idx in range(joints.shape[0])}

        def ratio(a, b, c, d):
            if a not in targets or b not in targets or c not in targets or d not in targets:
                return None
            target_base = np.linalg.norm(targets[c]["xy"] - targets[d]["xy"])
            model_base = np.linalg.norm(joint_xy[c] - joint_xy[d])
            if target_base <= 1e-6 or model_base <= 1e-6:
                return None
            target_measure = np.linalg.norm(targets[a]["xy"] - targets[b]["xy"])
            model_measure = np.linalg.norm(joint_xy[a] - joint_xy[b])
            return ((model_measure / model_base) - (target_measure / target_base)) ** 2

        losses = [
            ratio(16, 17, 1, 2),  # shoulder / hip
            ratio(1, 2, 16, 17),  # hip / shoulder
            ratio(16, 18, 1, 4),  # upper arm / upper leg
            ratio(17, 19, 2, 5),
            ratio(18, 20, 16, 18),  # forearm / upper arm
            ratio(19, 21, 17, 19),
        ]
        valid = [loss for loss in losses if loss is not None]
        return float(np.mean(valid)) if valid else 0.0

    def _landmark_point(self, landmarks_2d, idx):
        if idx >= len(landmarks_2d):
            return None
        landmark = landmarks_2d[idx]
        if landmark is None:
            return None
        return np.array([float(landmark["x"]), float(landmark["y"])], dtype=np.float64)

    def _landmark_visibility(self, landmarks_2d, idx):
        if idx >= len(landmarks_2d):
            return 0.0
        landmark = landmarks_2d[idx]
        if landmark is None:
            return 0.0
        return float(landmark.get("visibility", 0.0))

    def _average_target_point(self, landmarks_2d, indices):
        points = [self._landmark_point(landmarks_2d, idx) for idx in indices]
        points = [point for point in points if point is not None]
        if not points:
            return None
        return np.mean(points, axis=0)

    def _similarity_transform(self, source, target, weights):
        weights = np.asarray(weights, dtype=np.float64)
        weights = weights / max(weights.sum(), 1e-8)
        source_mean = np.sum(source * weights[:, None], axis=0)
        target_mean = np.sum(target * weights[:, None], axis=0)
        source_centered = source - source_mean
        target_centered = target - target_mean
        numerator = np.sum(weights * np.sum(source_centered * target_centered, axis=1))
        denominator = np.sum(weights * np.sum(source_centered ** 2, axis=1))
        scale = numerator / denominator if denominator > 1e-8 else 1.0
        translation = target_mean - (source_mean * scale)
        return scale, translation

    def _target_vector(self, start, end):
        return np.array([end[0] - start[0], start[1] - end[1]], dtype=np.float64)

    def _vector_angle(self, vector):
        return float(np.arctan2(vector[1], vector[0]))

    def _signed_angle(self, source, target):
        source_norm = np.linalg.norm(source)
        target_norm = np.linalg.norm(target)
        if source_norm <= 1e-8 or target_norm <= 1e-8:
            return 0.0
        source_unit = source / source_norm
        target_unit = target / target_norm
        cross = (source_unit[0] * target_unit[1]) - (source_unit[1] * target_unit[0])
        dot = np.clip(np.dot(source_unit, target_unit), -1.0, 1.0)
        return float(np.arctan2(cross, dot))

    def _wrap_angle(self, angle):
        return float(np.arctan2(np.sin(angle), np.cos(angle)))

    def _clamp_angle(self, angle, limit=1.35):
        return float(np.clip(angle, -limit, limit))

    def _rodrigues_batch(self, pose):
        pose = np.asarray(pose, dtype=np.float64).reshape(-1, 3)
        angles = np.linalg.norm(pose, axis=1, keepdims=True)
        safe_angles = np.where(angles > 1e-8, angles, 1.0)
        axes = pose / safe_angles
        cos = np.cos(angles)[:, None]
        sin = np.sin(angles)[:, None]

        kx = axes[:, 0]
        ky = axes[:, 1]
        kz = axes[:, 2]
        zeros = np.zeros_like(kx)
        k_mats = np.stack(
            (
                np.stack((zeros, -kz, ky), axis=1),
                np.stack((kz, zeros, -kx), axis=1),
                np.stack((-ky, kx, zeros), axis=1),
            ),
            axis=1,
        )

        identity = np.eye(3, dtype=np.float64)[None, :, :]
        outer = axes[:, :, None] * axes[:, None, :]
        rotations = (cos * identity) + ((1.0 - cos) * outer) + (sin * k_mats)
        zero_angle_mask = angles[:, 0] <= 1e-8
        rotations[zero_angle_mask] = identity[0]
        return rotations

    def _with_zeros(self, matrix):
        return np.vstack((matrix, np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)))

    def _pack(self, matrix):
        zeros = np.zeros((matrix.shape[0], 4, 3), dtype=np.float64)
        return np.concatenate((zeros, matrix), axis=2)
