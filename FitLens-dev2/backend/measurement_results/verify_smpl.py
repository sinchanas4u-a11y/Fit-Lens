# verify_smpl.py
import pickle
import os

model_dir = "models/smpl"
files = [
    "SMPL_NEUTRAL.pkl",
    "SMPL_MALE.pkl",
    "SMPL_FEMALE.pkl"
]

for fname in files:
    fpath = os.path.join(model_dir, fname)
    if os.path.exists(fpath):
        size_mb = os.path.getsize(fpath) / (1024*1024)
        try:
            with open(fpath, "rb") as f:
                data = pickle.load(
                    f, encoding="latin1"
                )
            keys = list(data.keys())
            print(f"✅ {fname}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   Keys: {keys[:4]}...")
        except Exception as e:
            print(f"❌ {fname} — Error: {e}")
    else:
        print(f"❌ {fname} — FILE NOT FOUND")