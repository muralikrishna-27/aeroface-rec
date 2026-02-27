import cv2
import numpy as np

from face.embedding import generate_embedding
from db.store_embedding import fetch_all_embeddings

THRESHOLD = 0.70  # cosine similarity
REQUIRED_STABLE = 40  # ~1.5 seconds


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def checkin():
    # Load all registered users
    users = fetch_all_embeddings()

    if not users:
        print("❌ No registered users found")
        return

    print(f"🟢 Loaded {len(users)} registered users")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cv2.namedWindow("AeroFace - Lounge Check-In", cv2.WINDOW_NORMAL)

    print("🟢 Look at the camera for check-in")

    stable_frames = 0
    last_face = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(100, 100)
        )

        if len(faces) == 1:
            stable_frames += 1
            x, y, w, h = faces[0]
            last_face = frame[y:y+h, x:x+w]

            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
            cv2.putText(
                frame,
                f"Checking... {int((stable_frames/REQUIRED_STABLE)*100)}%",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
        else:
            stable_frames = 0
            last_face = None

        cv2.imshow("AeroFace - Lounge Check-In", frame)

        # AUTO CHECK-IN
        if stable_frames >= REQUIRED_STABLE and last_face is not None:
            print("🔍 Generating live embedding...")
            live_embedding = generate_embedding(last_face)

            if live_embedding is None:
                print("❌ Failed to generate live embedding")
                break

            best_score = -1
            best_user = None

            for user_id, stored_embedding in users.items():
                score = cosine_similarity(live_embedding, stored_embedding)

                if score > best_score:
                    best_score = score
                    best_user = user_id

            print(f"🔍 Best match: {best_user} ({best_score:.3f})")

            if best_score >= THRESHOLD:
                color = (0, 255, 0)
                text = f"ACCESS GRANTED : {best_user}"
                print("🟢 ACCESS GRANTED")
            else:
                color = (0, 0, 255)
                text = "ACCESS DENIED"
                print("🔴 ACCESS DENIED")

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 4)
            cv2.putText(
                frame,
                text,
                (x, y - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                color,
                2
            )

            cv2.imshow("AeroFace - Result", frame)
            cv2.waitKey(3000)
            break

        # ESC to exit
        if cv2.waitKey(1) == 27:
            print("❌ Check-in cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    checkin()