import cv2
import numpy as np
from datetime import datetime

from face.embedding import generate_embedding
from db.store_embedding import fetch_all_embeddings, log_checkout, get_current_status

# ---------------- CONFIG ----------------
THRESHOLD = 0.78
REQUIRED_STABLE = 25          # frames to stabilize face
MATCH_FRAMES = 3              # embeddings to average
DETECT_EVERY_N_FRAMES = 5
RESIZE_SCALE = 0.5
# ---------------------------------------

print("🔥 CHECKOUT FILE LOADED 🔥", flush=True)


def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def checkout():
    # ---------- LOAD USERS ----------
    users = fetch_all_embeddings()
    if not users:
        print("❌ No registered users found", flush=True)
        return

    print(f"🟢 Loaded {len(users)} registered users", flush=True)

    # ---------- CAMERA ----------
    cap = cv2.VideoCapture(0)  # DO NOT use CAP_DSHOW
    if not cap.isOpened():
        print("❌ Camera not opened", flush=True)
        return

    print("📸 Camera opened", flush=True)

    cv2.namedWindow("AeroFace - Lounge Check-Out", cv2.WINDOW_NORMAL)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    stable_frames = 0
    scores_buffer = []
    last_face = None
    last_bbox = None
    frame_count = 0

    # ---------- MAIN LOOP ----------
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame", flush=True)
            break

        frame_count += 1

        # Resize for speed
        small = cv2.resize(frame, None, fx=RESIZE_SCALE, fy=RESIZE_SCALE)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        faces = []

        if frame_count % DETECT_EVERY_N_FRAMES == 0 or last_bbox is None:
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=6,
                minSize=(80, 80)
            )
            if len(faces) == 1:
                last_bbox = faces[0]
        else:
            faces = [last_bbox] if last_bbox is not None else []

        if len(faces) == 1:
            stable_frames += 1
            x, y, w, h = faces[0]

            # Scale bbox back
            x = int(x / RESIZE_SCALE)
            y = int(y / RESIZE_SCALE)
            w = int(w / RESIZE_SCALE)
            h = int(h / RESIZE_SCALE)

            last_face = frame[y:y+h, x:x+w]

            progress = min(100, int((stable_frames / REQUIRED_STABLE) * 100))

            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
            cv2.putText(
                frame,
                f"Stabilizing... {progress}%",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
        else:
            stable_frames = 0
            scores_buffer.clear()
            last_bbox = None

        cv2.imshow("AeroFace - Lounge Check-Out", frame)

        # ---------- MATCH ONCE ----------
        if stable_frames >= REQUIRED_STABLE and last_face is not None:
            print("🔍 Generating embedding...", flush=True)

            live_embedding = generate_embedding(last_face)
            if live_embedding is None:
                print("❌ Embedding failed", flush=True)
                break

            best_score = -1
            best_user = None

            for user_id, stored_embedding in users.items():
                score = cosine_similarity(live_embedding, stored_embedding)
                if score > best_score:
                    best_score = score
                    best_user = user_id

            scores_buffer.append(best_score)

            if len(scores_buffer) < MATCH_FRAMES:
                continue

            final_score = sum(scores_buffer) / len(scores_buffer)
            confidence = int(final_score * 100)

            if final_score >= THRESHOLD:
                color = (0, 255, 0)
                current_time = datetime.now().strftime("%H:%M:%S")
                status, checkin_time = get_current_status(best_user)
                
                print(f"🔵 CHECKOUT PROCESSED → {best_user} ({final_score:.3f}) at {current_time}", flush=True)
                
                # Log checkout to database
                log_checkout(best_user)
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 4)
                
                # Large "CHECK OUT" text
                cv2.putText(
                    frame,
                    "CHECK OUT",
                    (x, y - 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    color,
                    2
                )
                
                # Small username text
                cv2.putText(
                    frame,
                    best_user,
                    (x, y - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )
                
                # Checkout time text
                cv2.putText(
                    frame,
                    f"Checked out: {current_time}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1
                )
            else:
                color = (0, 0, 255)
                print(f"🔴 ACCESS DENIED ({final_score:.3f})", flush=True)
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 4)

            # Display result in same window
            cv2.imshow("AeroFace - Lounge Check-Out", frame)
            cv2.waitKey(3000)
            break

        # ESC to exit
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            print("❌ Check-out cancelled", flush=True)
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    checkout()
