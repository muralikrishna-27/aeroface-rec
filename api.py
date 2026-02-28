#!/usr/bin/env python3
"""
AeroFace — FastAPI REST Service
Exposes face registration & verification via HTTP endpoints.
The Expo mobile app and future web verification app call these.
"""

import os
import io
import base64
import numpy as np
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load env before importing local modules
load_dotenv()

# Suppress TF warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from face.embedding import generate_embedding, generate_multi_embedding
from db.store_embedding import (
    store_embedding,
    fetch_all_embeddings,
    get_embedding_status,
    delete_embedding,
    get_connection,
)
from db.visit import record_lounge_visit

app = FastAPI(
    title="AeroFace Recognition API",
    description="Face registration & verification for AeroFace lounge access",
    version="1.0.0",
)

# CORS — allow the Expo app and web app to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────────

class RegisterRequest(BaseModel):
    image_base64: str | None = Field(None, description="Base64-encoded JPEG/PNG image of the user's face (legacy)")
    images_base64: list[str] | None = Field(None, description="List of Base64-encoded images for multi-shot high accuracy registration")
    user_id: str = Field(..., min_length=1, max_length=100, description="Supabase auth user UUID")
    lounge_id: str | None = Field(None, description="Lounge UUID the user subscribed to")

class RegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    embedding_size: int = 0
    shots_used: int = 1

class VerifyRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded face image to match")
    lounge_id: str | None = Field(None, description="Lounge UUID to record the visit")

class VerifyResponse(BaseModel):
    matched: bool
    user_id: str | None = None
    user_email: str | None = None
    confidence: float = 0.0
    message: str = ""

class StatusResponse(BaseModel):
    registered: bool
    user_id: str
    model_name: str | None = None
    lounge_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

class DeleteResponse(BaseModel):
    success: bool
    message: str


# ── Image Preprocessing Pipeline ──────────────────────────────────

def decode_image(image_base64: str) -> np.ndarray:
    """Decode base64 image to OpenCV numpy array."""
    import cv2

    # Strip data URL prefix if present
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    img_bytes = base64.b64decode(image_base64)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")

    return img


def preprocess_face(img: np.ndarray) -> np.ndarray:
    """
    Lightweight preprocessing for webcam/mobile images.
    Only applies CLAHE for low-light and mild denoising.
    Kept minimal to avoid distorting facial features.
    """
    import cv2

    h, w = img.shape[:2]

    # Upscale tiny images
    if min(h, w) < 200:
        scale = 200 / min(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # CLAHE on luminance channel — fixes low lighting
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    lab = cv2.merge([l_ch, a_ch, b_ch])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Light Gaussian denoise (very mild — kernel 3x3)
    img = cv2.GaussianBlur(img, (3, 3), 0)

    return img


# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "aeroface-recognition", "timestamp": datetime.now().isoformat()}


@app.post("/register", response_model=RegisterResponse)
async def register_face(req: RegisterRequest):
    """
    Register a user's face:
    Supports multi-shot registration for higher accuracy.
    """
    if not req.image_base64 and not req.images_base64:
        raise HTTPException(status_code=400, detail="Must provide image_base64 or images_base64")

    shots_used = 1

    try:
        if req.images_base64 and len(req.images_base64) > 0:
            # Multi-shot path
            face_imgs = [preprocess_face(decode_image(b64)) for b64 in req.images_base64]
            embedding = generate_multi_embedding(face_imgs)
            shots_used = len(req.images_base64)
        else:
            # Single-shot path
            face_img = preprocess_face(decode_image(req.image_base64))
            embedding = generate_embedding(face_img)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(e)}")

    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail="Could not extract facial features. Ensure face is clearly visible and well-lit."
        )

    if embedding.shape[0] != 512:
        raise HTTPException(status_code=500, detail=f"Unexpected embedding size: {embedding.shape[0]}")

    # Store in DB
    success = store_embedding(req.user_id, embedding, lounge_id=req.lounge_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store embedding in database")

    return RegisterResponse(
        success=True,
        message="Face registered successfully",
        user_id=req.user_id,
        embedding_size=embedding.shape[0],
        shots_used=shots_used,
    )


@app.post("/verify", response_model=VerifyResponse)
async def verify_face(req: VerifyRequest):
    """
    Verify a face against all registered embeddings.
    Returns the best match if confidence >= threshold.
    """
    THRESHOLD = float(os.getenv("THRESHOLD", "0.62"))

    try:
        face_img = decode_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Preprocess for low light / noise / blur
    face_img = preprocess_face(face_img)

    # Generate embedding for the probe image
    live_embedding = generate_embedding(face_img)
    if live_embedding is None:
        return VerifyResponse(matched=False, message="No face detected in image")

    # Fetch all stored embeddings
    users = fetch_all_embeddings()
    if not users:
        return VerifyResponse(matched=False, message="No registered users in database")

    # Find all matches via cosine similarity
    matches = []
    
    for uid, stored_emb in users.items():
        # Normalize stored embedding
        s_norm = np.linalg.norm(stored_emb)
        if s_norm > 0:
            stored_emb = stored_emb / s_norm

        # Cosine similarity via dot product (both vectors are unit-length)
        score = float(np.dot(live_embedding, stored_emb))
        matches.append((uid, score))

    # Sort matches by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    
    best_user, best_score = matches[0]
    second_best_score = matches[1][1] if len(matches) > 1 else 0.0
    
    # ── Mathematical Dynamic Threshold Model ─────────────────────────
    # We dynamically calculate the acceptable threshold based on the 
    # statistical "isolation" of the match.
    # 
    # Margin = Top Match Score - Second Best Match Score
    # A high margin means the face ambiguously belongs to ONLY one person.
    # A low margin means the face looks like multiple registered people.
    
    margin = best_score - second_best_score
    
    # Base threshold is 0.68 (strict). 
    # We gracefully reduce the threshold proportionally to the margin.
    # Meaning: Highly isolated matches can pass with lower absolute scores
    #          (e.g., bad lighting), but similar-looking faces require high scores.
    # We cap the reduction to ensure a minimum floor of 0.45.
    
    dynamic_threshold = max(0.45, 0.68 - (margin * 0.7))
    
    print(f"[SEARCH] Top: {best_user} ({best_score:.4f}) | 2nd: {second_best_score:.4f} | Margin: {margin:.4f}")
    print(f"[STATS] computed dynamic_threshold: {dynamic_threshold:.4f}")

    if best_score >= dynamic_threshold and best_user:
        # Fetch user email from auth.users first so we can record it in the visit log
        user_email = "Unknown"
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT email FROM auth.users WHERE id = %s", (best_user,))
                row = cur.fetchone()
                if row:
                    user_email = row[0]
            except Exception as e:
                print(f"Error fetching user email: {e}")
            finally:
                cur.close()
                conn.close()

        visit_msg = ""
        if req.lounge_id:
            visit_status = record_lounge_visit(req.lounge_id, best_user, user_email)
            if visit_status:
                visit_msg = f" — {visit_status}"
        return VerifyResponse(
            matched=True,
            user_id=best_user,
            user_email=user_email,
            confidence=round(best_score, 4),
            message=f"Match found: {user_email} (score: {best_score:.2f}, req: {dynamic_threshold:.2f}){visit_msg}"
        )

    return VerifyResponse(
        matched=False,
        confidence=round(best_score, 4),
        message=f"No match (score: {best_score:.2f}, req: {dynamic_threshold:.2f})"
    )


@app.get("/status/{user_id}", response_model=StatusResponse)
async def face_status(user_id: str):
    """Check if a user has a registered face embedding."""
    status = get_embedding_status(user_id)

    if status:
        return StatusResponse(
            registered=True,
            user_id=user_id,
            model_name=status.get("model_name"),
            lounge_id=status.get("lounge_id"),
            created_at=status.get("created_at"),
            updated_at=status.get("updated_at"),
        )

    return StatusResponse(registered=False, user_id=user_id)


@app.delete("/embedding/{user_id}", response_model=DeleteResponse)
async def remove_embedding(user_id: str):
    """Delete a user's face embedding (for re-registration)."""
    success = delete_embedding(user_id)

    if success:
        return DeleteResponse(success=True, message="Face data removed successfully")

    raise HTTPException(status_code=500, detail="Failed to remove face data")


# ── Run ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    print(f"\nAeroFace API starting on http://0.0.0.0:{port}")
    print(f"Docs: http://localhost:{port}/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
