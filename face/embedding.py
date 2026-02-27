import numpy as np
from deepface import DeepFace

def generate_embedding(face_img):
    """
    Always returns a 512-d embedding (ArcFace)
    Raises error if embedding fails
    """
    try:
        result = DeepFace.represent(
            img_path=face_img,
            model_name="ArcFace",
            enforce_detection=False
        )

        embedding = result[0]["embedding"]
        embedding = np.array(embedding, dtype="float32")

        if embedding.shape[0] != 512:
            raise ValueError("Embedding size mismatch")

        return embedding

    except Exception as e:
        print("❌ Embedding generation failed:", e)
        return None