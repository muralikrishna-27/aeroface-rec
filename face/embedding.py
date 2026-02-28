"""
AeroFace - Face Embedding Generator (High Accuracy Edition)

Accuracy improvements:
  1. Facenet512 model (99.65% LFW accuracy, better than ArcFace 99.4%)
  2. SSD detector (DNN-based, eye-independent)
  3. enforce_detection=False (never fails on real webcam images)
  4. align=True (face alignment before embedding)
  5. L2 normalization for stable cosine similarity
  6. Multi-shot support for registration (average multiple embeddings)
"""

import numpy as np
from deepface import DeepFace

MODEL_NAME = "Facenet512"
DETECTOR   = "ssd"


def generate_embedding(face_img):
    """
    Generate a 512-D L2-normalized Facenet512 embedding from a single image.
    """
    try:
        result = DeepFace.represent(
            img_path=face_img,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR,
            enforce_detection=False,
            align=True,
        )

        if result and len(result) > 0:
            emb = np.array(result[0]["embedding"], dtype="float32")

            if emb.shape[0] != 512:
                print("[WARN] Unexpected embedding size: %d" % emb.shape[0])
                return None

            # L2 normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            return emb

    except Exception as e:
        print("[ERROR] Embedding failed: %s" % str(e))

    return None


def generate_multi_embedding(face_imgs):
    """
    Generate a robust embedding by averaging multiple face images.
    Used during registration for higher accuracy.

    Args:
        face_imgs: list of numpy arrays (BGR images)

    Returns:
        L2-normalized average embedding (512-D), or None
    """
    embeddings = []

    for img in face_imgs:
        emb = generate_embedding(img)
        if emb is not None:
            embeddings.append(emb)

    if not embeddings:
        return None

    # Average all valid embeddings
    avg = np.mean(embeddings, axis=0).astype("float32")

    # Re-normalize the average
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm

    print("[OK] Multi-shot: averaged %d/%d embeddings" % (len(embeddings), len(face_imgs)))
    return avg