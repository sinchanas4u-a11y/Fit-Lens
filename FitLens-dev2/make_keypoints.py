import mediapipe as mp
import cv2
import json
import numpy as np
import os

# MediaPipe landmark index → OpenPose index
# MediaPipe has 33 landmarks
# OpenPose expects 25 keypoints
MP_TO_OPENPOSE = {
  0:  0,   # Nose
  # Neck = midpoint of shoulders (11, 12)
  # computed separately
  12: 2,   # Right Shoulder
  14: 3,   # Right Elbow
  16: 4,   # Right Wrist
  11: 5,   # Left Shoulder
  13: 6,   # Left Elbow
  15: 7,   # Left Wrist
  # MidHip = midpoint of hips (23, 24)
  # computed separately
  24: 9,   # Right Hip
  26: 10,  # Right Knee
  28: 11,  # Right Ankle
  23: 12,  # Left Hip
  25: 13,  # Left Knee
  27: 14,  # Left Ankle
  5:  15,  # Right Eye
  2:  16,  # Left Eye
  8:  17,  # Right Ear
  7:  18,  # Left Ear
  32: 19,  # Left BigToe
  31: 20,  # Left SmallToe
  29: 21,  # Left Heel
  30: 22,  # Right BigToe (approximate)
  30: 23,  # Right SmallToe (approximate)
  30: 24,  # Right Heel (approximate)
}

def mediapipe_to_openpose(
  image_path: str,
  output_path: str
):
  # Load image
  image = cv2.imread(image_path)
  if image is None:
    print(f"Cannot load image: {image_path}")
    return False

  h, w = image.shape[:2]
  rgb   = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

  # Run MediaPipe
  mp_pose = mp.solutions.pose
  with mp_pose.Pose(
    static_image_mode       = True,
    model_complexity        = 2,
    min_detection_confidence= 0.5
  ) as pose:
    results = pose.process(rgb)

  if not results.pose_landmarks:
    print(f"No person detected: {image_path}")
    return False

  lm = results.pose_landmarks.landmark

  # Build 25-point OpenPose array
  # Each point: [x_px, y_px, confidence]
  keypoints = [[0.0, 0.0, 0.0]] * 25

  # Fill mapped landmarks
  for mp_idx, op_idx in MP_TO_OPENPOSE.items():
    if mp_idx < len(lm):
      kp = lm[mp_idx]
      keypoints[op_idx] = [
        float(kp.x * w),
        float(kp.y * h),
        float(kp.visibility)
      ]

  # Compute Neck = midpoint of shoulders
  ls = lm[11]  # left shoulder
  rs = lm[12]  # right shoulder
  neck_x    = (ls.x + rs.x) / 2 * w
  neck_y    = (ls.y + rs.y) / 2 * h
  neck_conf = min(ls.visibility, rs.visibility)
  keypoints[1] = [neck_x, neck_y, neck_conf]

  # Compute MidHip = midpoint of hips
  lh = lm[23]  # left hip
  rh = lm[24]  # right hip
  hip_x    = (lh.x + rh.x) / 2 * w
  hip_y    = (lh.y + rh.y) / 2 * h
  hip_conf = min(lh.visibility, rh.visibility)
  keypoints[8] = [hip_x, hip_y, hip_conf]

  # Compute Right foot keypoints from
  # right ankle (28) area
  ra = lm[28]  # right ankle
  keypoints[22] = [  # Right BigToe
    float(ra.x * w + 20),
    float(ra.y * h + 40),
    float(ra.visibility * 0.7)
  ]
  keypoints[23] = [  # Right SmallToe
    float(ra.x * w + 10),
    float(ra.y * h + 40),
    float(ra.visibility * 0.6)
  ]
  keypoints[24] = [  # Right Heel
    float(ra.x * w - 10),
    float(ra.y * h + 10),
    float(ra.visibility * 0.7)
  ]

  # -----------------------------------------------------
  # COMPUTE LEG ANGLE
  # Generate realistic leg posture by correcting knee joint
  # behavior and aligning it with the user's actual pose.
  # Ensure the 3D mesh legs accurately match the image and remain straight.
  # -----------------------------------------------------
  def align_knee(hip_idx, knee_idx, ankle_idx):
      # Extract points: [x, y, confidence]
      hip = np.array(keypoints[hip_idx][:2])
      knee = np.array(keypoints[knee_idx][:2])
      ankle = np.array(keypoints[ankle_idx][:2])
      
      # For each leg:
      #   upper_leg = hip -> knee
      #   lower_leg = knee -> ankle
      upper_leg = knee - hip
      lower_leg = ankle - knee
      
      norm_upper = np.linalg.norm(upper_leg)
      norm_lower = np.linalg.norm(lower_leg)
      
      if norm_upper > 1e-6 and norm_lower > 1e-6:
          # Compute leg angle using dot product
          cos_theta = np.dot(upper_leg, lower_leg) / (norm_upper * norm_lower)
          cos_theta = np.clip(cos_theta, -1.0, 1.0)
          angle = np.degrees(np.arccos(cos_theta))
          
          # If leg is relatively straight (e.g. angle < 25 degrees from being a straight line)
          if angle < 25.0:
              # Project the knee onto the line segment connecting hip and ankle
              hip_to_ankle = ankle - hip
              length_sq = np.sum(hip_to_ankle**2)
              if length_sq > 0:
                  t = np.dot(knee - hip, hip_to_ankle) / length_sq
                  # Constrain parameter t to [0, 1] bounds (between hip and ankle)
                  t = np.clip(t, 0.0, 1.0)
                  # Calculate corrected straight knee position
                  perfect_knee = hip + t * hip_to_ankle
                  
                  # Update the keypoint coordinates, keep original confidence
                  keypoints[knee_idx][0] = float(perfect_knee[0])
                  keypoints[knee_idx][1] = float(perfect_knee[1])

  # OpenPose Indices: 
  # Right leg: Hip=9, Knee=10, Ankle=11
  # Left leg:  Hip=12, Knee=13, Ankle=14
  align_knee(9, 10, 11)   # Right leg
  align_knee(12, 13, 14)  # Left leg

  # Flatten to 1D array [x,y,c, x,y,c, ...]
  flat = []
  for kp in keypoints:
    flat.extend(kp)

  # Write OpenPose JSON format
  output = {
    "version": 1.3,
    "people": [{
      "pose_keypoints_2d":    flat,
      "face_keypoints_2d":    [],
      "hand_left_keypoints_2d":  [],
      "hand_right_keypoints_2d": []
    }]
  }

  os.makedirs(
    os.path.dirname(output_path),
    exist_ok=True
  )

  with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

  print(f"Saved {len(keypoints)} keypoints"
        f" to: {output_path}")
  return True


def generate_keypoints_for_smplifyx(
  front_image_path: str,
  side_image_path:  str = None,
  keypoints_dir:    str = "data/keypoints"
):
  os.makedirs(keypoints_dir, exist_ok=True)

  # Clear old keypoints
  import glob
  for f in glob.glob(
    os.path.join(keypoints_dir, '*.json')
  ):
    os.remove(f)

  # Generate front keypoints
  front_name = os.path.splitext(
    os.path.basename(front_image_path)
  )[0]
  front_kp_path = os.path.join(
    keypoints_dir,
    f"{front_name}_keypoints.json"
  )
  ok = mediapipe_to_openpose(
    front_image_path,
    front_kp_path
  )
  if not ok:
    return False

  # Generate side keypoints if provided
  if side_image_path and os.path.exists(
    side_image_path
  ):
    side_name = os.path.splitext(
      os.path.basename(side_image_path)
    )[0]
    side_kp_path = os.path.join(
      keypoints_dir,
      f"{side_name}_keypoints.json"
    )
    mediapipe_to_openpose(
      side_image_path,
      side_kp_path
    )

  return True


if __name__ == "__main__":
  # Test with existing images
  generate_keypoints_for_smplifyx(
    front_image_path = "data/images/front.jpg",
    side_image_path  = "data/images/side.jpg",
    keypoints_dir    = "data/keypoints"
  )
