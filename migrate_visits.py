import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "sslmode": "require",
}

def migrate():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Create table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lounge_visits (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lounge_id UUID NOT NULL REFERENCES lounges(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                user_name TEXT,
                user_email TEXT,
                in_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                out_time TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # In case the table already exists, try to add the columns
        try:
            cur.execute("ALTER TABLE lounge_visits ADD COLUMN user_name TEXT;")
            cur.execute("ALTER TABLE lounge_visits ADD COLUMN user_email TEXT;")
        except psycopg2.Error:
            conn.rollback() # Ignore if columns already exist
        else:
            conn.commit()
        
        # Enable RLS
        cur.execute("""
            ALTER TABLE lounge_visits ENABLE ROW LEVEL SECURITY;
        """)
        
        # Drop policy if exists then recreate
        cur.execute("""
            DROP POLICY IF EXISTS "Lounge owners can view visits" ON lounge_visits;
            CREATE POLICY "Lounge owners can view visits" ON lounge_visits
            FOR SELECT USING (
                lounge_id IN (
                    SELECT id FROM lounges WHERE owner_id = auth.uid()
                )
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Migration successful: created lounge_visits and policies.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
