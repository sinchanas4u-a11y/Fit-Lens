import os

import numpy as np
import trimesh
from scipy.spatial import ConvexHull


class SMPLifyXReader:
    def __init__(self, mesh_file_path: str):
        if not os.path.exists(mesh_file_path):
            raise FileNotFoundError(f"Mesh file not found: {mesh_file_path}")

        self.mesh = trimesh.load(mesh_file_path, process=False)
        self.vertices = np.array(self.mesh.vertices)
        self.faces = np.array(self.mesh.faces)

        print(f"Loaded mesh: {mesh_file_path}")
        print(f"Vertices   : {len(self.vertices)}")
        print(f"Faces      : {len(self.faces)}")

    def get_scaled_vertices(self, user_height_cm: float) -> np.ndarray:
        verts = self.vertices.copy()
        y_min = verts[:, 1].min()
        y_max = verts[:, 1].max()
        mesh_h = (y_max - y_min) * 100.0

        if mesh_h <= 0:
            return verts

        scale = float(user_height_cm) / mesh_h
        v_sc = verts * scale
        mid_y = (v_sc[:, 1].max() + v_sc[:, 1].min()) / 2.0
        v_sc[:, 1] -= mid_y
        return v_sc

    def _get_section(self, v_sc, y_level, tol=0.02):
        mask = np.abs(v_sc[:, 1] - y_level) < tol
        return v_sc[mask]

    def _get_circumference(self, v_sc, y_level, body_radius=0.18) -> float:
        section = self._get_section(v_sc, y_level)
        if len(section) < 10:
            return None

        pts = section[:, [0, 2]]
        center_x = np.median(pts[:, 0])
        center_z = np.median(pts[:, 1])
        dist =np.sqrt((pts[:, 0] - center_x)**2 + (pts[:, 1] - center_z)**2)
        pts = pts[dist < body_radius]
        if len(pts) < 10:
            return None

        try:
            hull = ConvexHull(pts)
            vh = pts[hull.vertices]
            n = len(vh)
            perim = sum(np.linalg.norm(vh[(i + 1) % n] - vh[i]) for i in range(n))
            return round(float(perim * 100.0), 2)
        except Exception:
            return None

    def _get_width(self, v_sc, y_level, x_limit=0.25):
        section = self._get_section(v_sc, y_level)
        if len(section) < 3:
            return None

        center_x = np.median(section[:, 0])
        section = section[np.abs(section[:, 0] - center_x) < x_limit]
        if len(section) < 3:
            return None

        return round(float(section[:, 0].max() - section[:, 0].min()) * 100.0, 2)

    def extract_measurements(self, user_height_cm: float) -> dict:
        v_sc = self.get_scaled_vertices(user_height_cm)
        y_max = v_sc[:, 1].max()
        y_min = v_sc[:, 1].min()
        h = (y_max - y_min) * 100.0

        levels = {
            "chest": y_max - (h * 0.25 / 100.0),
            "waist": y_max - (h * 0.38 / 100.0),
            "hip": y_max - (h * 0.50 / 100.0),
        }

        meas = {"full_height": round(float(user_height_cm), 2)}

        circ_params= {
            "chest": (levels["chest"], 0.22),
            "waist": (levels["waist"], 0.20),
            "hip":   (y_max - (h * 0.48 / 100.0), 0.21),
        }

        for name, (y_level, radius) in circ_params.items():
            meas[f"{name}_circumference"] = self._get_circumference(
                v_sc, y_level, body_radius=radius
            )
            meas[f"{name}_width"] = self._get_width(v_sc, y_level)

        sh_y = y_max - (h * 0.18 / 100.0)
        sh_sect = self._get_section(v_sc, sh_y, tol=0.025)
        if len(sh_sect) >= 3:
            center_x = np.median(sh_sect[:, 0])
            sh_sect = sh_sect[np.abs(sh_sect[:, 0] - center_x) < 0.22]
            if len(sh_sect) >= 3:
                meas["shoulder_width"] = round(
                    float(sh_sect[:, 0].max() - sh_sect[:, 0].min()) * 100.0, 2
                )

        print("\n=== SMPLify-X MEASUREMENTS ===")
        for key, value in meas.items():
            if value is not None:
                print(f"  {key:30s}: {value} cm")
        print("==============================\n")

        return meas

    def export_for_plotly(
        self,
        user_height_cm: float,
        measurements: dict = None,
        model_path: str = None,
        gender: str = 'neutral'
    ) -> dict:
        # Always export an A-pose mesh from the body-shape model template.
        # If beta fitting fails, use zero betas rather than falling back
        # to the posed SMPLify-X output mesh.
        if model_path and os.path.exists(model_path):
            try:
                from processing.beta_calculator import (
                    BetaCalculator,
                    compute_betas_from_measurements
                )

                calc = BetaCalculator(model_path=model_path, gender=gender)
                fitted_betas = np.zeros(10, dtype=float)
                betas_fitted = False

                if measurements:
                    print("Fitting betas to user measurements...")
                    fitted_betas = compute_betas_from_measurements(
                        measurements=measurements,
                        user_height_cm=user_height_cm,
                        model_path=model_path,
                        gender=gender
                    )
                    betas_fitted = np.any(np.abs(fitted_betas) > 1e-6)

                shaped_verts = calc.get_vertices(fitted_betas)

                y_min = shaped_verts[:, 1].min()
                y_max = shaped_verts[:, 1].max()
                h_m = y_max - y_min
                if h_m <= 0:
                    raise ValueError("Invalid template height while building A-pose")

                scale = user_height_cm / (h_m * 100)
                v_sc = shaped_verts * scale * 100

                mid_y = (
                    v_sc[:, 1].max() +
                    v_sc[:, 1].min()
                ) / 2
                v_sc[:, 1] -= mid_y

                print("Using template A-pose vertices for 3D model")

                f = self.faces
                return {
                    "x": v_sc[:, 0].tolist(),
                    "y": v_sc[:, 1].tolist(),
                    "z": v_sc[:, 2].tolist(),
                    "i": f[:, 0].tolist(),
                    "j": f[:, 1].tolist(),
                    "k": f[:, 2].tolist(),
                    "metadata": {
                        "vertex_count": int(len(v_sc)),
                        "face_count": int(len(f)),
                        "height_cm": float(user_height_cm),
                        "source": "SMPL-X Template A-Pose",
                        "betas_fitted": bool(betas_fitted)
                    }
                }
            except Exception as e:
                print(f"A-pose generation failed, using raw mesh fallback: {e}")
                import traceback
                traceback.print_exc()

        # Fallback: use raw SMPLify-X mesh only if model template is unavailable.
        v_sc = self.get_scaled_vertices(user_height_cm)
        f = self.faces

        return {
            "x": v_sc[:, 0].tolist(),
            "y": v_sc[:, 1].tolist(),
            "z": v_sc[:, 2].tolist(),
            "i": f[:, 0].tolist(),
            "j": f[:, 1].tolist(),
            "k": f[:, 2].tolist(),
            "metadata": {
                "vertex_count": int(len(v_sc)),
                "face_count": int(len(f)),
                "height_cm": float(user_height_cm),
                "source": "SMPLify-X",
                "betas_fitted": False
            },
        }
