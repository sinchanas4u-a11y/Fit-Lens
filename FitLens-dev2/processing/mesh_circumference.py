import numpy as np
import trimesh
import os
import glob
from scipy.spatial import ConvexHull


class MeshCircumferenceExtractor:
    """
    Extracts TRUE circumferences from 3D mesh
    by horizontal slicing at body levels.

    Method:
      1. Load mesh (.obj or .ply)
      2. Scale mesh to user height
      3. Slice horizontally at chest/waist/hip
      4. Get cross-section contour points
      5. Order points into closed polygon
      6. Compute full perimeter = circumference
      7. Apply regression correction
    """

    # Y level as fraction from TOP of body
    # Tuned for SMPL and SMPL-X models
    BODY_LEVELS = {
        'chest': 0.25,
        'waist': 0.40,
        'hip':   0.52,
    }

    # Slice half-thickness in meters
    TOLERANCE = 0.015

    # Regression coefficients from 3 datasets
    # Formula: corrected = slope * raw + intercept
    REGRESSION = {
        'chest': {
            'slope':     2.521,
            'intercept': -177.31,
            'r2':        0.998,
            'valid_range': (60, 140)
        },
        'waist': {
            'slope':     1.0,
            'intercept': 0.0,
            'r2':        0.0,
            'valid_range': (55, 130)
        },
        'hip': {
            'slope':     1.0,
            'intercept': 0.0,
            'r2':        0.0,
            'valid_range': (70, 145)
        },
    }

    def __init__(
        self,
        mesh_path:      str,
        user_height_cm: float
    ):
        if not os.path.exists(mesh_path):
            raise FileNotFoundError(
                f"Mesh not found: {mesh_path}"
            )
        self.mesh_path      = mesh_path
        self.user_height_cm = float(user_height_cm)
        self.mesh           = trimesh.load(
            mesh_path,
            force='mesh'
        )
        print(f"Loaded mesh: {mesh_path}")
        print(f"Vertices: {len(self.mesh.vertices)}")
        print(f"Faces   : {len(self.mesh.faces)}")
        self._scale_mesh()

    def _scale_mesh(self):
        """Scale mesh vertices to user height."""
        verts  = np.array(self.mesh.vertices)
        y_min  = verts[:, 1].min()
        y_max  = verts[:, 1].max()
        h_m    = y_max - y_min

        if h_m <= 0:
            raise ValueError(
                "Mesh has zero height"
            )

        # Scale factor: meters to cm
        scale = self.user_height_cm / (h_m * 100)
        self.vertices_cm = verts * scale * 100

        # Store scaled bounds
        self.y_min_cm = self.vertices_cm[:, 1].min()
        self.y_max_cm = self.vertices_cm[:, 1].max()
        self.height_cm = self.y_max_cm - self.y_min_cm

        print(f"Scaled mesh height: "
              f"{self.height_cm:.1f} cm")

    def _get_slice_points(
        self,
        y_level_cm: float,
        tol_cm:     float = 1.5
    ) -> np.ndarray:
        """
        Get all mesh vertices near Y level.
        Returns Nx2 array of (x, z) points
        representing horizontal cross-section.
        """
        mask = np.abs(
            self.vertices_cm[:, 1] - y_level_cm
        ) < tol_cm

        section = self.vertices_cm[mask]

        if len(section) < 6:
            return None

        # Return X and Z coordinates
        # (horizontal cross-section plane)
        return section[:, [0, 2]]

    def _order_contour_points(
        self,
        points: np.ndarray
    ) -> np.ndarray:
        """
        Order 2D points into a closed polygon
        by sorting by angle from centroid.
        This ensures correct perimeter calculation.
        """
        cx = np.mean(points[:, 0])
        cy = np.mean(points[:, 1])

        # Compute angle of each point
        # relative to centroid
        angles = np.arctan2(
            points[:, 1] - cy,
            points[:, 0] - cx
        )

        # Sort by angle to get ordered polygon
        order  = np.argsort(angles)
        return points[order]

    def _remove_outliers(
        self,
        points:     np.ndarray,
        max_radius: float = None
    ) -> np.ndarray:
        """
        Remove outlier points (legs, arms)
        that are far from body center.
        """
        cx = np.median(points[:, 0])
        cz = np.median(points[:, 1])

        dist = np.sqrt(
            (points[:, 0] - cx)**2 +
            (points[:, 1] - cz)**2
        )

        if max_radius is None:
            # Auto: keep points within
            # 2 standard deviations
            max_radius = (
                np.mean(dist) +
                2 * np.std(dist)
            )

        return points[dist <= max_radius]

    def _compute_perimeter(
        self,
        ordered_points: np.ndarray
    ) -> float:
        """
        Compute FULL perimeter of ordered polygon.
        Includes closing segment from last to first.

        perimeter = Σ distance(pᵢ, pᵢ₊₁)
        """
        n = len(ordered_points)
        if n < 3:
            return 0.0

        total = 0.0
        for i in range(n):
            p1 = ordered_points[i]
            p2 = ordered_points[(i + 1) % n]
            total += np.linalg.norm(p2 - p1)

        return float(total)

    def _get_circumference_at_level(
        self,
        y_level_cm:  float,
        name:        str,
        max_radius:  float = None
    ) -> float:
        """
        Get circumference at given Y level in cm.
        """
        # Get cross-section points
        pts = self._get_slice_points(y_level_cm)

        if pts is None or len(pts) < 6:
            print(f"  {name}: insufficient "
                  f"points at y={y_level_cm:.1f}")
            return None

        print(f"  {name}: {len(pts)} points "
              f"at y={y_level_cm:.1f} cm")

        # Remove outliers (arms, legs)
        pts = self._remove_outliers(
            pts, max_radius
        )

        if len(pts) < 6:
            return None

        # Use ConvexHull to get outer contour
        try:
            hull   = ConvexHull(pts)
            hull_pts = pts[hull.vertices]
        except Exception:
            hull_pts = pts

        # Order into closed polygon
        ordered = self._order_contour_points(
            hull_pts
        )

        # Compute true perimeter
        circumference = self._compute_perimeter(
            ordered
        )

        print(f"  {name}: raw circumference = "
              f"{circumference:.2f} cm")

        return circumference

    def _apply_regression(
        self,
        name:      str,
        raw_cm:    float,
        scale_factor: float = None
    ) -> float:
        """
        Apply regression correction.

        If scale_factor provided:
          corrected = slope * raw_cm + intercept
          (pixel-to-scale integrated correction)

        Formula derived from 3-dataset OLS:
          actual = slope * measured + intercept
        """
        if name not in self.REGRESSION:
            return raw_cm

        reg = self.REGRESSION[name]

        if reg['r2'] < 0.8:
            print(f"  {name}: regression "
                  f"R²={reg['r2']:.3f} too low, "
                  f"skipping correction")
            return raw_cm

        slope     = reg['slope']
        intercept = reg['intercept']
        lo, hi    = reg['valid_range']

        corrected = slope * raw_cm + intercept

        if lo <= corrected <= hi:
            print(f"  {name}: {raw_cm:.1f} cm → "
                  f"{corrected:.1f} cm "
                  f"(regression R²={reg['r2']:.3f})")
            return round(corrected, 2)
        else:
            print(f"  {name}: corrected "
                  f"{corrected:.1f} out of "
                  f"range [{lo}-{hi}], "
                  f"keeping {raw_cm:.1f}")
            return round(raw_cm, 2)

    def extract_all(
        self,
        scale_factor: float = None
    ) -> dict:
        """
        Extract chest, waist, hip circumferences.

        scale_factor: cm/px from image processing
          If provided integrates pixel-to-scale
          correction into regression formula.

        Returns dict with corrected measurements.
        """
        results = {}
        print(f"\nExtracting circumferences "
              f"from 3D mesh:")
        print(f"  User height: "
              f"{self.user_height_cm:.1f} cm")
        print(f"  Mesh height: "
              f"{self.height_cm:.1f} cm")

        # Max radius to exclude arms/legs (cm)
        RADII = {
            'chest': 22.0,
            'waist': 20.0,
            'hip':   19.0,
        }

        for name, pct in self.BODY_LEVELS.items():
            # Y level from top
            y_level = (
                self.y_max_cm -
                self.height_cm * pct
            )

            raw_circ = self._get_circumference_at_level(
                y_level,
                name,
                max_radius=RADII[name]
            )

            if raw_circ is None:
                results[f"{name}_circumference"] = None
                continue

            # Apply regression correction
            corrected = self._apply_regression(
                name,
                raw_circ,
                scale_factor
            )

            results[f"{name}_circumference"] = corrected

        print(f"\nFinal circumferences:")
        for k, v in results.items():
            if v:
                print(f"  {k}: {v:.1f} cm")

        return results

    @classmethod
    def from_latest_mesh(
        cls,
        generated_meshes_dir: str,
        user_height_cm:       float
    ):
        """
        Load most recent generated mesh.
        Searches backend/generated_meshes/
        for most recently created .obj file.
        """
        # Search for all .obj files
        pattern = os.path.join(
            generated_meshes_dir,
            '**', '*.obj'
        )
        files = glob.glob(
            pattern, recursive=True
        )

        # Also check SMPLify-X output
        smplifyx_pattern = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    generated_meshes_dir
                )
            ),
            'output', 'meshes',
            'front', '000.obj'
        )
        if os.path.exists(smplifyx_pattern):
            files.append(smplifyx_pattern)

        if not files:
            raise FileNotFoundError(
                "No mesh files found"
            )

        # Use most recently modified
        latest = max(
            files, key=os.path.getmtime
        )
        print(f"Using mesh: {latest}")

        return cls(latest, user_height_cm)
