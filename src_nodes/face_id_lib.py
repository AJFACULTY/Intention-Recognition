"""
face_id_lib.py

Shared logic for the Cognition project's facial recognition pipeline.
Model: InsightFace 'buffalo_sc' pack (RetinaFace-500MF detector +
MobileFaceNet/MBF@WebFace600K recognizer, 512-d ArcFace embeddings).

This module is intentionally the ONLY place that knows about the model
choice. If we ever need to swap buffalo_sc for a hand-converted
MobileFaceNet ONNX file later (e.g. if the ARM64 install on the Pi
fails), only this file needs to change -- enroll_faces.py and
recognize_live.py stay untouched.
"""

import os
import pickle
from pathlib import Path

import numpy as np

try:
    from insightface.app import FaceAnalysis
except ImportError:
    raise SystemExit(
        "insightface is not installed in this environment.\n"
        "Run: pip install insightface onnxruntime opencv-python numpy"
    )

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

MODEL_PACK = "buffalo_sc"       # smallest InsightFace pack (~16MB)
DET_SIZE = (320, 320)           # detector input size; smaller = faster,
                                 # fine for a single face reasonably close
                                 # to camera. Raise to (640, 640) only if
                                 # you see missed detections at distance.

# Cosine similarity threshold for "same person".
# InsightFace embeddings are L2-normalized, so cosine similarity and
# dot product are equivalent here. Start conservative; tune against
# your own enrolled set rather than trusting a benchmark number --
# InsightFace's own docs note mobile MBF-class models can show wider
# accuracy gaps across different faces than server-class models.
MATCH_THRESHOLD = 0.45

# Where the enrolled-face database lives. On the dev machine this is
# just a local folder; on the Pi this path becomes the bind-mounted
# /home/pi/faces directory so it survives container restarts.
DEFAULT_DB_DIR = os.environ.get("FACE_DB_DIR", "./face_data")
DB_FILENAME = "known_embeddings.pkl"


def _db_path(db_dir: str) -> str:
    return os.path.join(db_dir, DB_FILENAME)


def load_face_app() -> FaceAnalysis:
    """Initialize and return the FaceAnalysis app. Call this once at
    startup, not per-frame -- model loading is comparatively slow."""
    app = FaceAnalysis(name=MODEL_PACK, providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=DET_SIZE)
    return app


def get_faces(app: FaceAnalysis, image_bgr: np.ndarray):
    """Run detection + embedding extraction on a single BGR image
    (as returned by cv2.VideoCapture / cv2.imread).

    Returns a list of insightface Face objects. Each has:
      .bbox            -- [x1, y1, x2, y2]
      .embedding        -- raw 512-d embedding
      .normed_embedding -- L2-normalized 512-d embedding (use this one)
      .det_score        -- detector confidence
    """
    return app.get(image_bgr)


def load_db(db_dir: str = DEFAULT_DB_DIR) -> dict:
    """Load the enrolled-face database: {name: [embedding, ...]}."""
    path = _db_path(db_dir)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return {}


def save_db(db: dict, db_dir: str = DEFAULT_DB_DIR) -> None:
    Path(db_dir).mkdir(parents=True, exist_ok=True)
    with open(_db_path(db_dir), "wb") as f:
        pickle.dump(db, f)


def enroll_embedding(db: dict, name: str, embedding: np.ndarray) -> dict:
    """Add one averaged embedding for `name` to the in-memory db."""
    db.setdefault(name, []).append(embedding)
    return db


def best_match(embedding: np.ndarray, db: dict):
    """Compare one embedding against every enrolled identity's stored
    embedding(s) and return (best_name, best_score) or (None, best_score)
    if nothing clears MATCH_THRESHOLD.

    Since embeddings are L2-normalized, cosine similarity == dot product.
    """
    best_name = None
    best_score = -1.0

    for name, embeddings_list in db.items():
        for stored_emb in embeddings_list:
            score = float(np.dot(embedding, stored_emb))
            if score > best_score:
                best_score = score
                best_name = name

    if best_score >= MATCH_THRESHOLD:
        return best_name, best_score
    return None, best_score
