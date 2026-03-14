import glob
import os
import shutil
import subprocess
import time


BASE_DIR = r"C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2"
SMPLIFYX_DIR = r"C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2\smplify-x"
DATA_DIR = r"C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2\data"
OUTPUT_DIR = r"C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2\output"
CONFIG_PATH = r"C:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2\smplify-x\configs\fit_smplx.yaml"
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")


def _python_executable() -> str:
    if os.path.exists(VENV_PYTHON):
        return VENV_PYTHON
    return "python"


def prepare_input(front_image_path: str, side_image_path: str = None) -> str:
    """Copy uploaded images to SMPLify-X input folder."""
    img_dir = os.path.join(DATA_DIR, "images")
    kp_dir = os.path.join(DATA_DIR, "keypoints")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(kp_dir, exist_ok=True)

    for file_path in glob.glob(os.path.join(img_dir, "*")):
        try:
            os.remove(file_path)
        except OSError:
            pass

    front_dest = os.path.join(img_dir, "front.jpg")
    shutil.copy2(front_image_path, front_dest)
    print(f"Copied front image to: {front_dest}")

    if side_image_path and os.path.exists(side_image_path):
        side_dest = os.path.join(img_dir, "side.jpg")
        shutil.copy2(side_image_path, side_dest)
        print(f"Copied side image to: {side_dest}")

    return DATA_DIR


def _ensure_keypoints(timeout_seconds: int) -> None:
    script_path = os.path.join(BASE_DIR, "make_keypoints.py")
    if not os.path.exists(script_path):
        return

    cmd = [_python_executable(), script_path]
    subprocess.run(
        cmd,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def run_smplifyx(
    front_image_path: str,
    side_image_path: str = None,
    timeout_seconds: int = 120,
) -> dict:
    """Run SMPLify-X and return most recent mesh path."""
    try:
        prepare_input(front_image_path, side_image_path)

        mesh_dir = os.path.join(OUTPUT_DIR, "meshes")
        if os.path.exists(mesh_dir):
            for pattern in ("*.ply", "*.obj"):
                for file_path in glob.glob(os.path.join(mesh_dir, "**", pattern), recursive=True):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

        # Ensure keypoints exist for copied images.
        _ensure_keypoints(timeout_seconds=timeout_seconds)

        print("Running SMPLify-X...")
        start = time.time()

        cmd = [
            _python_executable(),
            os.path.join(SMPLIFYX_DIR, "smplifyx", "main.py"),
            "--config",
            CONFIG_PATH,
        ]

        result = subprocess.run(
            cmd,
            cwd=SMPLIFYX_DIR,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        elapsed = time.time() - start
        print(f"SMPLify-X finished in {elapsed:.1f} seconds")

        if result.returncode != 0:
            print(f"SMPLify-X stderr: {result.stderr}")
            return {
                "success": False,
                "mesh_path": None,
                "error": f"SMPLify-X failed: {result.stderr[-500:]}",
            }

        mesh_files = glob.glob(os.path.join(mesh_dir, "**", "*.ply"), recursive=True)
        if not mesh_files:
            mesh_files = glob.glob(os.path.join(mesh_dir, "**", "*.obj"), recursive=True)

        if not mesh_files:
            return {"success": False, "mesh_path": None, "error": "No mesh file generated"}

        mesh_path = max(mesh_files, key=os.path.getmtime)
        print(f"Mesh generated: {mesh_path}")

        return {"success": True, "mesh_path": mesh_path, "error": None}

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "mesh_path": None,
            "error": f"SMPLify-X timed out after {timeout_seconds} seconds",
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return {"success": False, "mesh_path": None, "error": str(exc)}