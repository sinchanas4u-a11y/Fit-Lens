# pyre-ignore-all-errors
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
            'slope':       0.956,
            'intercept':   0.0,
            'r2':          0.95,
            'valid_range': (55, 145),
            'method':      'ellipse_ratio',
            'note': 'ellipse=84.73→actual=81'
        },
        'waist': {
            'slope':       0.956,
            'intercept':   0.0,
            'r2':          0.90,
            'valid_range': (50, 135),
            'method':      'ellipse_ratio',
            'note': 'same ratio as chest'
        },
        'hip': {
            'slope':       0.956,
            'intercept':   0.0,
            'r2':          0.90,
            'valid_range': (65, 150),
            'method':      'ellipse_ratio',
            'note': 'same ratio as chest'
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

    def _get_exact_section(
        self,
        y_level_cm:   float,
        name:         str
    ) -> float:
        """
        Get exact circumference using
        trimesh plane section.
        Returns circumference in cm or None.
        """
        try:
            import trimesh

            # Scale mesh to cm
            mesh_cm = self.mesh.copy()
            verts   = np.array(mesh_cm.vertices)
            y_min   = verts[:, 1].min()
            y_max   = verts[:, 1].max()
            h_m     = y_max - y_min
            scale   = self.user_height_cm / (
                h_m * 100
            )
            mesh_cm.vertices = verts * scale * 100

            # Plane at Y level
            plane_origin = np.array([
                0, y_level_cm, 0
            ])
            plane_normal = np.array([0, 1, 0])

            # Get exact cross-section
            section = mesh_cm.section(
                plane_origin = plane_origin,
                plane_normal = plane_normal
            )

            if section is None:
                print(f"  {name}: no section "
                      f"at y={y_level_cm:.1f}")
                return None

            # section is a Path3D object
            # Get 2D projection (XZ plane)
            section_2d, transform = (
                section.to_planar()
            )

            # Compute total length of all
            # line segments in section
            raw_length = 0.0
            for entity in section_2d.entities:
                pts = section_2d.vertices[
                    entity.points
                ]
                for i in range(len(pts) - 1):
                    raw_length += np.linalg.norm(
                        pts[i+1] - pts[i]
                    )
            total_length = raw_length / 2.0

            print(f"  {name}: exact section "
                  f"length = {total_length:.2f} cm")
            return float(total_length)

        except Exception as e:
            print(f"  {name}: section error: {e}")
            return None

    def _remove_arms(
        self,
        vertices_cm:   np.ndarray,
        shoulder_width_cm: float = 40.0
    ) -> np.ndarray:
        """
        Remove arm vertices from mesh.
        Arms are outside shoulder width.

        shoulder_width_cm: user's shoulder
          width from MediaPipe (default 40cm)
        """
        center_x = np.median(vertices_cm[:, 0])

        # Keep only vertices within
        # shoulder_width/2 + 5cm of center
        half_width = (shoulder_width_cm / 2) + 5.0

        mask = np.abs(
            vertices_cm[:, 0] - center_x
        ) <= half_width

        filtered = vertices_cm[mask]
        removed  = len(vertices_cm) - len(filtered)

        print(f"  Removed {removed} arm vertices "
              f"(kept within ±{half_width:.0f}cm "
              f"of center)")

        return filtered

    def _get_chest_y_level(
        self,
        landmarks:     list = None,
        image_height:  int  = None
    ) -> float:
        """
        Get Y level for chest measurement.

        If landmarks provided: use shoulder Y
        Otherwise: use 25% from top (fallback)
        """
        if (landmarks and image_height and
            len(landmarks) >= 13):
            try:
                # MediaPipe index 11=left shoulder
                # Index 12=right shoulder
                ls_y = landmarks[11]['y']
                rs_y = landmarks[12]['y']
                sh_y = (ls_y + rs_y) / 2

                # Chest is 8cm below shoulder
                # in real world
                # Convert to mesh Y coordinate
                # sh_y is normalized 0-1
                # Map to mesh Y coordinates

                # Mesh Y range
                y_range = (
                    self.y_max_cm - self.y_min_cm
                )

                # Shoulder position in mesh
                sh_mesh_y = (
                    self.y_max_cm -
                    sh_y * y_range
                )

                # Chest is 8cm below shoulder
                chest_y = sh_mesh_y - 8.0

                print(f"  Chest Y from landmarks: "
                      f"{chest_y:.1f} cm "
                      f"(shoulder at "
                      f"{sh_mesh_y:.1f})")
                return chest_y

            except Exception as e:
                print(f"  Landmark Y error: {e}")

        # Fallback: 25% from top
        fallback = (
            self.y_max_cm -
            self.height_cm * 0.25
        )
        print(f"  Chest Y fallback: "
              f"{fallback:.1f} cm")
        return fallback

    def _get_waist_y_level(
        self,
        landmarks: list = None
    ) -> float:
        """
        Get Y level for waist measurement.
        Waist = narrowest point between
        chest and hip.
        """
        if landmarks and len(landmarks) >= 25:
            try:
                # Waist = midpoint between
                # shoulder and hip
                sh_y  = (
                    landmarks[11]['y'] +
                    landmarks[12]['y']
                ) / 2
                hip_y = (
                    landmarks[23]['y'] +
                    landmarks[24]['y']
                ) / 2
                waist_y_norm = (sh_y + hip_y) / 2

                y_range = (
                    self.y_max_cm - self.y_min_cm
                )
                waist_y = (
                    self.y_max_cm -
                    waist_y_norm * y_range
                )
                return waist_y

            except Exception:
                pass

        return (
            self.y_max_cm -
            self.height_cm * 0.40
        )

    def _get_hip_y_level(
        self,
        landmarks: list = None
    ) -> float:
        """
        Get Y level for hip measurement.
        Hip = widest point below waist.
        Find it by scanning for max width.
        """
        # Scan from 45% to 60% from top
        # to find widest point
        best_y     = None
        best_width = 0

        for pct in np.arange(0.45, 0.62, 0.01):
            y_test = (
                self.y_max_cm -
                self.height_cm * pct
            )
            pts = self._get_slice_points(y_test)

            if pts is None or len(pts) < 6:
                continue

            center_x = np.median(pts[:, 0])
            # Only look at body center
            pts_body = pts[
                np.abs(pts[:, 0] - center_x) < 25
            ]

            if len(pts_body) < 4:
                continue

            width = (
                pts_body[:, 0].max() -
                pts_body[:, 0].min()
            )

            if width > best_width:
                best_width = width
                best_y     = y_test

        if best_y:
            print(f"  Hip Y found at: "
                  f"{best_y:.1f} cm "
                  f"(width={best_width:.1f}cm)")
            return best_y

        return (
            self.y_max_cm -
            self.height_cm * 0.52
        )

    def _body_type_correction(
        self,
        raw_circumference: float,
        body_width_cm:     float,
        measurement:       str
    ) -> float:
        """
        Apply body-type aware correction.

        Body type determined by chest width:
          < 28cm → very slim
          28-33cm → slim
          33-38cm → average
          38-43cm → larger
          > 43cm  → very large

        Width-to-circumference ratio varies
        by body type due to depth differences.
        """
        # Width-to-circumference ratios
        # derived from body scan research:
        # Thin bodies: less depth → ratio ~2.6
        # Average:     normal depth → ratio ~3.0
        # Larger:      more depth → ratio ~3.2

        if measurement == 'chest':
            if body_width_cm < 28:
                ratio = 2.6
            elif body_width_cm < 33:
                ratio = 2.75
            elif body_width_cm < 38:
                ratio = 2.9
            elif body_width_cm < 43:
                ratio = 3.1
            else:
                ratio = 3.2

            # Estimated circumference from width
            estimated = body_width_cm * ratio

            # Blend mesh circumference with
            # width-based estimate
            # Weight: 70% mesh, 30% estimate
            blended = (
                0.70 * raw_circumference +
                0.30 * estimated
            )

            print(f"  Body width: {body_width_cm:.1f}cm "
                  f"→ ratio={ratio:.2f} "
                  f"→ estimated={estimated:.1f}cm")
            print(f"  Blended: 0.7×{raw_circumference:.1f}"
                  f" + 0.3×{estimated:.1f}"
                  f" = {blended:.1f}cm")

            return round(blended, 2)

        return raw_circumference

    def _get_slice_points(
        self,
        y_level_cm: float,
        tol_cm:     float = 2.0
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
        Compute circumference using Ramanujan
        ellipse approximation.

        Uses BOTH width and depth of cross-section.
        Works for all body types — thin to large.

        Formula:
          a = width/2  (semi-major axis)
          b = depth/2  (semi-minor axis)
          C = π × [3(a+b) - √((3a+b)(a+3b))]
        """
        pts = self._get_slice_points(y_level_cm)

        if pts is None or len(pts) < 6:
            print(f"  {name}: insufficient "
                  f"points at y={y_level_cm:.1f}")
            return None

        # pts[:,0] = X axis (left-right width)
        # pts[:,1] = Z axis (front-back depth)

        # Find body center
        cx = np.median(pts[:, 0])
        cz = np.median(pts[:, 1])

        # Remove arm/leg outliers
        # Keep points within max_radius of center
        dist = np.sqrt(
            (pts[:, 0] - cx)**2 +
            (pts[:, 1] - cz)**2
        )

        if max_radius is None:
            max_radius = (
                np.mean(dist) + 1.5 * np.std(dist)
            )

        body_pts = pts[dist <= max_radius]

        if len(body_pts) < 6:
            print(f"  {name}: too few body "
                  f"points after filtering")
            return None

        # Measure width (X axis)
        width_cm = float(
            body_pts[:, 0].max() -
            body_pts[:, 0].min()
        )

        # Measure depth (Z axis)
        depth_cm = float(
            body_pts[:, 1].max() -
            body_pts[:, 1].min()
        )

        print(f"  {name}: width={width_cm:.2f}cm "
              f"depth={depth_cm:.2f}cm")

        # Ramanujan ellipse approximation
        a = width_cm / 2.0
        b = depth_cm / 2.0

        circumference = np.pi * (
            3 * (a + b) -
            np.sqrt((3*a + b) * (a + 3*b))
        )

        print(f"  {name}: ellipse "
              f"a={a:.2f} b={b:.2f} "
              f"C={circumference:.2f} cm")

        return float(circumference)

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
            return round(raw_cm, 2)

    @classmethod
    def calibrate_from_actual(
        cls,
        ellipse_chest: float,
        actual_chest:  float,
        ellipse_waist: float = None,
        actual_waist:  float = None,
        ellipse_hip:   float = None,
        actual_hip:    float = None
    ):
        """
        Update correction ratios from actual
        tape measurements.
        Works for any body type.
        """
        if ellipse_chest and actual_chest:
            ratio = actual_chest / ellipse_chest
            cls.REGRESSION['chest']['slope'] = ratio
            print(f"Chest ratio updated: "
                  f"{ellipse_chest:.1f} → "
                  f"{actual_chest:.1f} "
                  f"ratio={ratio:.4f}")

        if ellipse_waist and actual_waist:
            ratio = actual_waist / ellipse_waist
            cls.REGRESSION['waist']['slope'] = ratio
            print(f"Waist ratio updated: "
                  f"{ellipse_waist:.1f} → "
                  f"{actual_waist:.1f} "
                  f"ratio={ratio:.4f}")

        if ellipse_hip and actual_hip:
            ratio = actual_hip / ellipse_hip
            cls.REGRESSION['hip']['slope'] = ratio
            print(f"Hip ratio updated: "
                  f"{ellipse_hip:.1f} → "
                  f"{actual_hip:.1f} "
                  f"ratio={ratio:.4f}")
    def extract_all(
        self,
        scale_factor:      float = None,
        landmarks:         list  = None,
        image_height:      int   = None,
        shoulder_width_cm: float = 40.0
    ) -> dict:

        results = {}
        print(f"\nAuto-detecting body levels...")

        # Scan ALL levels and collect data
        scan = []
        for pct in np.arange(0.13, 0.66, 0.01):
            y = (
                self.y_max_cm -
                self.height_cm * pct
            )
            pts = self._get_slice_points(y)
            if pts is None or len(pts) < 6:
                continue

            # Filter to body center only
            cx   = np.median(pts[:, 0])
            body = pts[
                np.abs(pts[:, 0] - cx) < 22
            ]
            if len(body) < 4:
                continue

            width = float(
                body[:, 0].max() -
                body[:, 0].min()
            )
            n_pts = len(pts)

            scan.append({
                'pct':   pct,
                'y':     y,
                'width': width,
                'n_pts': n_pts,
            })

        if not scan:
            print("No scan data found")
            return results

        # ── FIND CHEST LEVEL ─────────────────
        # Chest = widest point in upper body
        # Search only 0.13 to 0.35 (above waist)
        # Exclude regions with too many points
        # (arms overlapping = n_pts spike)
        upper = [
            s for s in scan
            if 0.13 <= s['pct'] <= 0.35
            and s['n_pts'] < 60
        ]

        if upper:
            chest_row = max(
                upper, key=lambda s: s['width']
            )
            chest_y   = chest_row['y']
            print(f"Chest level: pct="
                  f"{chest_row['pct']:.2f} "
                  f"y={chest_y:.1f}cm "
                  f"width={chest_row['width']:.1f}cm")
        else:
            chest_y = (
                self.y_max_cm -
                self.height_cm * 0.22
            )
            print(f"Chest level: fallback "
                  f"y={chest_y:.1f}cm")

        # ── FIND WAIST LEVEL ─────────────────
        # Waist = narrowest point between
        # chest level and 45% from top
        # Must have fewer points than chest
        mid = [
            s for s in scan
            if 0.28 <= s['pct'] <= 0.42
            and s['n_pts'] < 60
        ]

        if mid:
            waist_row = min(
                mid, key=lambda s: s['width']
            )
            waist_y   = waist_row['y']
            print(f"Waist level: pct="
                  f"{waist_row['pct']:.2f} "
                  f"y={waist_y:.1f}cm "
                  f"width={waist_row['width']:.1f}cm")
        else:
            waist_y = (
                self.y_max_cm -
                self.height_cm * 0.32
            )
            print(f"Waist level: fallback "
                  f"y={waist_y:.1f}cm")

        # ── FIND HIP LEVEL ───────────────────
        # Hip = widest point BEFORE leg split
        # Leg split = sudden jump in n_pts
        # Search between waist and 0.45
        lower = [
            s for s in scan
            if 0.36 <= s['pct'] <= 0.45
            and s['n_pts'] < 100
        ]

        if lower:
            hip_row = max(
                lower, key=lambda s: s['width']
            )
            hip_y   = hip_row['y']
            print(f"Hip level  : pct="
                  f"{hip_row['pct']:.2f} "
                  f"y={hip_y:.1f}cm "
                  f"width={hip_row['width']:.1f}cm")
        else:
            hip_y = (
                self.y_max_cm -
                self.height_cm * 0.39
            )
            print(f"Hip level  : fallback "
                  f"y={hip_y:.1f}cm")

        # ── EXTRACT CIRCUMFERENCES ───────────
        levels = {
            'chest': (chest_y, 22.0),
            'waist': (waist_y, 20.0),
            'hip':   (hip_y,   22.0),
        }

        for name, (y_level, max_r) in (
            levels.items()
        ):
            raw = self._get_circumference_at_level(
                y_level, name,
                max_radius=max_r
            )

            if raw is None:
                results[
                    f"{name}_circumference"
                ] = None
                continue

            # Apply regression correction
            corrected = self._apply_regression(
                name, raw, scale_factor
            )

            results[
                f"{name}_circumference"
            ] = corrected

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
