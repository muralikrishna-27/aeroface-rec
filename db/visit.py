from db.store_embedding import get_connection
import psycopg2

def record_lounge_visit(lounge_id: str, user_id: str, user_email: str = None) -> str:
    """
    Records a visit. 
    If currently IN and < 1 minute, ignores => "Checked in recently"
    If currently IN and >= 1 minute, checks OUT => "Checked out"
    If currently OUT (or first time), checks IN => "Checked in"
    """
    if not lounge_id:
        return "No lounge ID provided"
        
    conn = get_connection()
    if not conn:
        return ""
        
    try:
        cur = conn.cursor()
        
        # Find the most recent visit
        cur.execute("""
            SELECT id, in_time, out_time, EXTRACT(EPOCH FROM (NOW() - in_time)) AS seconds_since_in
            FROM lounge_visits
            WHERE lounge_id = %s AND user_id = %s
            ORDER BY in_time DESC
            LIMIT 1
        """, (lounge_id, user_id))
        
        row = cur.fetchone()
        
        if row:
            visit_id, in_time, out_time, seconds_since_in = row
            
            # If out_time is NULL, the user is currently inside the lounge
            if out_time is None:
                if seconds_since_in < 60:
                    return f"Checked in recently ({int(60 - seconds_since_in)}s remaining to checkout)"
                else:
                    cur.execute("""
                        UPDATE lounge_visits
                        SET out_time = NOW()
                        WHERE id = %s
                    """, (visit_id,))
                    conn.commit()
                    return "Checked out"
                    
        # If we got here: no recent visit, or the last visit already has an out_time
        cur.execute("""
            INSERT INTO lounge_visits (lounge_id, user_id, user_email)
            VALUES (%s, %s, %s)
        """, (lounge_id, user_id, user_email))
        conn.commit()
        return "Checked in"
        
    except psycopg2.Error as e:
        print(f"Database error in record_lounge_visit: {e}")
        conn.rollback()
        return ""
    finally:
        if conn:
            cur.close()
            conn.close()
