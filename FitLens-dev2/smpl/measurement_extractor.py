import numpy as np
from scipy.spatial import ConvexHull

class MeasurementExtractor:

    def extract_all(self, vertices, user_height_cm):
        y_min  = vertices[:, 1].min()
        y_max  = vertices[:, 1].max()
        smpl_h = (y_max - y_min) * 100
        scale  = user_height_cm / smpl_h
        v_cm   = vertices * 100 * scale

        y_min_cm = v_cm[:, 1].min()
        y_max_cm = v_cm[:, 1].max()
        height   = y_max_cm - y_min_cm

        levels = {
            "chest": y_max_cm - height * 0.27,
            "waist": y_max_cm - height * 0.40,
            "hip":   y_max_cm - height * 0.52,
        }

        measurements = {}

        # Shoulder width — filter arms by X range
        # Arms extend far in X axis
        # Torso center X is near 0 in SMPL coords
        # Shoulder joint is max ~25cm from center
        shoulder_y  = y_max_cm - height * 0.20
        sh_all      = self._slice(v_cm, shoulder_y, tol=1.5)

        if len(sh_all) >= 3:
            # Find body center X
            center_x = v_cm[:, 0].mean()
            # Keep only vertices within 30cm of center
            # This removes arm vertices
            x_limit  = 30.0
            sh_torso = sh_all[
                np.abs(sh_all[:, 0] - center_x) < x_limit
            ]

            if len(sh_torso) >= 3:
                measurements["shoulder_width"] = round(
                    float(
                        sh_torso[:, 0].max() -
                        sh_torso[:, 0].min()
                    ), 2
                )
            else:
                measurements["shoulder_width"] = None
        else:
            measurements["shoulder_width"] = None

        # Chest, waist, hip
        for name, y_level in levels.items():
            measurements[f"{name}_circumference"] = (
                self._circumference(v_cm, y_level)
            )
            measurements[f"{name}_width"] = (
                self._width(v_cm, y_level)
            )
            measurements[f"{name}_depth"] = (
                self._depth(v_cm, y_level)
            )

        return measurements

    def _slice(self, v_cm, y_level, tol=2.5):
        mask = np.abs(v_cm[:, 1] - y_level) < tol
        return v_cm[mask]

    def _circumference(self, v_cm, y_level):
        section = self._slice(v_cm, y_level)
        if len(section) < 10:
            return None
        # Filter X to body center only
        center_x = v_cm[:, 0].mean()
        section  = section[
            np.abs(section[:, 0] - center_x) < 35.0
        ]
        if len(section) < 10:
            return None
        pts = section[:, [0, 2]]
        try:
            hull  = ConvexHull(pts)
            verts = pts[hull.vertices]
            n     = len(verts)
            perim = sum(
                np.linalg.norm(
                    verts[(i + 1) % n] - verts[i]
                )
                for i in range(n)
            )
            return round(perim, 2)
        except Exception:
            return None

    def _width(self, v_cm, y_level):
        section = self._slice(v_cm, y_level)
        if len(section) < 3:
            return None
        center_x = v_cm[:, 0].mean()
        section  = section[
            np.abs(section[:, 0] - center_x) < 35.0
        ]
        if len(section) < 3:
            return None
        return round(
            float(
                section[:, 0].max() -
                section[:, 0].min()
            ), 2
        )

    def _depth(self, v_cm, y_level):
        section = self._slice(v_cm, y_level)
        if len(section) < 3:
            return None
        return round(
            float(
                section[:, 2].max() -
                section[:, 2].min()
            ), 2
        )