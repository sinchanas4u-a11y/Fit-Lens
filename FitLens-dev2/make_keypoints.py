import os
import json
import cv2
import mediapipe as mp
import numpy as np

IMG_DIR = "data/images"
OUT_DIR = "data/keypoints"

os.makedirs(OUT_DIR, exist_ok=True)

mp_pose = mp.solutions.pose

def mediapipe_to_openpose(kps):
    mp_idx = {
        "nose": 0,
        "neck": 0,          # approximate
        "r_shoulder": 12,
        "r_elbow": 14,
        "r_wrist": 16,
        "l_shoulder": 11,
        "l_elbow": 13,
        "l_wrist": 15,
        "mid_hip": 24,
        "r_hip": 26,
        "r_knee": 28,
        "r_ankle": 30,
        "l_hip": 23,
        "l_knee": 25,
        "l_ankle": 27,
        "r_eye": 2,
        "l_eye": 5,
        "r_ear": 7,
        "l_ear": 8,
    }

    order = [
        "nose", "neck",
        "r_shoulder", "r_elbow", "r_wrist",
        "l_shoulder", "l_elbow", "l_wrist",
        "mid_hip",
        "r_hip", "r_knee", "r_ankle",
        "l_hip", "l_knee", "l_ankle",
        "r_eye", "l_eye", "r_ear", "l_ear"
    ]

    op_kps = []
    for name in order:
        idx = mp_idx[name]
        x, y, v = kps[idx]
        c = v
        op_kps.extend([float(x), float(y), float(c)])

    return op_kps

with mp_pose.Pose(static_image_mode=True, model_complexity=2) as pose:
    for fname in os.listdir(IMG_DIR):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        img_path = os.path.join(IMG_DIR, fname)
        img = cv2.imread(img_path)
        if img is None:
            print(f"Could not read {img_path}")
            continue

        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)

        if not res.pose_landmarks:
            print(f"No landmarks for {fname}")
            continue

        kps = []
        for lm in res.pose_landmarks.landmark:
            kps.append((lm.x * w, lm.y * h, lm.visibility))

        op_kps = mediapipe_to_openpose(kps)

        out = {
            "version": 1.3,
            "people": [
                {
                    "pose_keypoints_2d": op_kps,
                    "face_keypoints_2d": [],
                    "hand_left_keypoints_2d": [],
                    "hand_right_keypoints_2d": []
                }
            ]
        }

        base = os.path.splitext(fname)[0]
        out_path = os.path.join(OUT_DIR, f"{base}_keypoints.json")
        with open(out_path, "w") as f:
            json.dump(out, f)

        print(f"Wrote {out_path}")
