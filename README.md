## 🔧 Tech Stack

- Python 3.10+
- OpenCV
- DeepFace (ArcFace – 512D embeddings)
- Supabase PostgreSQL + pgvector
- psycopg2
- Haar Cascade (face detection)

---

## 📁 Project Structure


aeroface/
│
├── face/
│ ├── register_face.py # Face registration (auto-capture)
│ ├── checkin.py # Lounge check-in (green/red)
│ ├── embedding.py # Embedding generation
│ ├── detector.py # Face detection helpers
│ └── init.py
│
├── db/
│ ├── store_embedding.py # Supabase pgvector operations
│ └── init.py
│
├── data/
│ └── registered/ # Saved face images (local)
│
├── venv/ # Virtual environment (ignored)
├── requirements.txt
└── README.md


---

## ⚙️ Setup Instructions

### 1️⃣ Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
2️⃣ Install Dependencies
pip install -r requirements.txt
🗄️ Supabase Database Setup

Create a Supabase project

Open SQL Editor

Run:

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE face_embeddings (
    user_id TEXT PRIMARY KEY,
    embedding VECTOR(512),
    model_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

Update database credentials inside:

db/store_embedding.py

⚠️ Use Session Pooler credentials (port 6543) with sslmode="require"

🧑 Face Registration (ONE TIME)

Registers a user’s face and stores the embedding in Supabase.

python -m face.register_face

Enter user_id

Look at the camera

Hold still for ~1.5 seconds

Face is auto-captured and registered

🚪 Lounge Check-In (EVERY ENTRY)

Verifies a live face against all registered users.

python -m face.checkin
Result:

🟢 ACCESS GRANTED → Match found

🔴 ACCESS DENIED → No match