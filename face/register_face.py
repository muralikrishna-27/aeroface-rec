import cv2
import os
import time

from face.embedding import generate_embedding
from db.store_embedding import store_embedding

SAVE_DIR = "data/registered"
os.makedirs(SAVE_DIR, exist_ok=True)


def register_face(user_id):
    # Force stable webcam backend on Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cv2.namedWindow("AeroFace - Face Registration", cv2.WINDOW_NORMAL)

    print(f"🟢 Registering face for user_id = {user_id}")
    print("🟢 Look at the camera and hold still")

    stable_frames = 0
    REQUIRED_STABLE = 40  # ~0.5 seconds

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

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"Hold still... {int((stable_frames/REQUIRED_STABLE)*100)}%",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        else:
            stable_frames = 0

        cv2.imshow("AeroFace - Face Registration", frame)

        # AUTO CAPTURE
        if stable_frames >= REQUIRED_STABLE:
            face_img = frame[y:y+h, x:x+w]

            filename = f"{user_id}_{int(time.time())}.jpg"
            path = os.path.join(SAVE_DIR, filename)
            cv2.imwrite(path, face_img)
            print("📸 Face auto-captured")

            embedding = generate_embedding(face_img)
            if embedding is None:
                print("❌ Registration failed: embedding error")
                break
            print("🧠 Embedding generated")

            store_embedding(user_id, embedding)
            print("💾 Embedding stored in database")

            break

        # ESC key to force quit (more reliable than 'q')
        if cv2.waitKey(1) == 27:
            print("❌ Registration cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    user_id = input("Enter user_id to register: ").strip()
    if not user_id:
        print("❌ user_id cannot be empty")
    else:
        register_face(user_id)