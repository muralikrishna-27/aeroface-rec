import psycopg2
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "sslmode": "require",
}


def get_connection():
    """
    Establish database connection with error handling
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️  Make sure .env file is configured correctly")
        return None
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        return None


def store_embedding(user_id, embedding):
    """
    Store face embedding in database with error handling
    
    Args:
        user_id: Unique user identifier
        embedding: 512D numpy array (ArcFace)
    
    Returns:
        True if successful, False otherwise
    """
    if embedding is None or embedding.shape[0] != 512:
        print("❌ Invalid embedding: must be 512D array")
        return False
    
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        
        cur.execute(
            """
            INSERT INTO face_embeddings (user_id, embedding, model_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET embedding = EXCLUDED.embedding, updated_at = NOW()
            """,
            (user_id, embedding.tolist(), "ArcFace")
        )
        
        conn.commit()
        cur.close()
        print("✅ Embedding stored in PostgreSQL")
        return True
    
    except psycopg2.IntegrityError as e:
        conn.rollback()
        print(f"❌ Database integrity error: {e}")
        return False
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        conn.rollback()
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        conn.close()


def fetch_all_embeddings():
    """
    Fetch all registered embeddings from database
    
    Returns:
        Dictionary: {user_id: np.array(512), ...}
        Empty dict if connection fails
    """
    conn = get_connection()
    if conn is None:
        return {}
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, embedding FROM face_embeddings ORDER BY user_id")
        rows = cur.fetchall()
        cur.close()
        
        users = {}
        for user_id, vector_str in rows:
            try:
                vector_str = vector_str.strip("[]")
                vector = np.array(
                    [float(x) for x in vector_str.split(",")],
                    dtype="float32"
                )
                
                if vector.shape[0] == 512:
                    users[user_id] = vector
                else:
                    print(f"⚠️  Skipping {user_id}: invalid embedding size {vector.shape[0]}")
            
            except ValueError as e:
                print(f"⚠️  Error parsing embedding for {user_id}: {e}")
                continue
        
        print(f"🟢 Loaded {len(users)} registered users from database")
        return users
    
    except psycopg2.Error as e:
        print(f"❌ Database query failed: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {}
    finally:
        conn.close()


if __name__ == "__main__":
    # Test connection
    print("🧪 Testing database connection...")
    test_conn = get_connection()
    if test_conn:
        print("✅ Connection successful")
        test_conn.close()
    else:
        print("❌ Connection failed")