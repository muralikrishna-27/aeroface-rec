import psycopg2
import numpy as np

DB_CONFIG = {
    "host": "HOST_NAMER",
    "dbname": "postgres",
    "user": "USER_NAME",
    "password": "PASS",
    "port": 5432,
    "sslmode": "require"
}

def store_embedding(user_id, embedding):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO face_embeddings (user_id, embedding, model_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET embedding = EXCLUDED.embedding
        """,
        (user_id, embedding.tolist(), "ArcFace")
    )

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Embedding stored in PostgreSQL")

if __name__ == "__main__":
    embedding = np.load("data/embeddings/user_001.npy")
    store_embedding("user_001", embedding)

def fetch_all_embeddings():
    """
    Returns:
      {
        user_id: np.array(512),
        ...
      }
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT user_id, embedding FROM face_embeddings")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    users = {}
    for user_id, vector_str in rows:
        vector_str = vector_str.strip("[]")
        vector = np.array(
            [float(x) for x in vector_str.split(",")],
            dtype="float32"
        )
        users[user_id] = vector

    return users