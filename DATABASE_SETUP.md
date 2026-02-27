# Database Setup for Attendance Tracking

## Required SQL Commands

Run these in your Supabase SQL Editor to set up attendance tracking:

### 1. Create Attendance Log Table

```sql
CREATE TABLE IF NOT EXISTS attendance_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    checkin_time TIMESTAMP DEFAULT NOW(),
    checkout_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES face_embeddings(user_id) ON DELETE CASCADE
);

-- Create an index for faster queries
CREATE INDEX idx_user_checkin ON attendance_log(user_id, checkin_time DESC);
CREATE INDEX idx_checkout_pending ON attendance_log(checkout_time) WHERE checkout_time IS NULL;
```

### 2. Enable pgvector (if not already enabled)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Verify tables created

```sql
-- Check face_embeddings table
SELECT * FROM face_embeddings LIMIT 1;

-- Check attendance_log table
SELECT * FROM attendance_log LIMIT 1;
```

### 4. Sample Queries for Reporting

**Get today's check-ins:**
```sql
SELECT user_id, checkin_time, checkout_time 
FROM attendance_log 
WHERE DATE(checkin_time) = CURRENT_DATE
ORDER BY checkin_time DESC;
```

**Get users currently checked in:**
```sql
SELECT user_id, checkin_time 
FROM attendance_log 
WHERE checkout_time IS NULL 
AND DATE(checkin_time) = CURRENT_DATE
ORDER BY checkin_time DESC;
```

**Get attendance summary for a user:**
```sql
SELECT 
    user_id,
    DATE(checkin_time) as date,
    COUNT(*) as checkins,
    AVG(EXTRACT(EPOCH FROM (checkout_time - checkin_time))/3600) as avg_hours
FROM attendance_log 
WHERE checkout_time IS NOT NULL
GROUP BY user_id, DATE(checkin_time)
ORDER BY DATE(checkin_time) DESC;
```

**Get duration of each session:**
```sql
SELECT 
    user_id,
    checkin_time,
    checkout_time,
    EXTRACT(EPOCH FROM (checkout_time - checkin_time))/3600 as hours_logged
FROM attendance_log 
WHERE checkout_time IS NOT NULL
ORDER BY checkin_time DESC
LIMIT 50;
```

---

## Application Features

### Check-in Function
- User looks at camera
- Face recognized and matched
- If matched: **Logged to database with current timestamp**
- Display shows: "ACCESS GRANTED", username, and check-in time

### Check-out Function
- User looks at camera
- Face recognized and matched
- If matched: **Latest pending check-in record gets checkout timestamp**
- Display shows: "CHECK OUT", username, and checkout time

### Status Tracking
- `get_current_status(user_id)` returns:
  - "checked_in" → User is currently inside
  - "checked_out" → User has logged out
  - "never" → User never checked in

---

## Real-time Display

Both check-in and check-out show the exact time on screen:

**Check-in Display:**
```
ACCESS GRANTED
alice_001
Checked in: 14:35:22
```

**Check-out Display:**
```
CHECK OUT
alice_001
Checked out: 15:42:18
```

---

## Database Structure

### face_embeddings table
```
id          | SERIAL PRIMARY KEY
user_id     | VARCHAR(100) UNIQUE
embedding   | vector(512)
model_name  | VARCHAR(50)
created_at  | TIMESTAMP
updated_at  | TIMESTAMP
```

### attendance_log table
```
id             | SERIAL PRIMARY KEY
user_id        | VARCHAR(100) - Foreign key to face_embeddings
checkin_time   | TIMESTAMP - Automatically set to NOW()
checkout_time  | TIMESTAMP - NULL until checkout
created_at     | TIMESTAMP - Record creation time
```

---

## Troubleshooting

**Q: "No registered users" error**
A: Run sample query to verify data:
```sql
SELECT COUNT(*) FROM face_embeddings;
```

**Q: Attendance not being logged**
A: Check if attendance_log table exists:
```sql
SELECT * FROM attendance_log;
```

If error, run the SQL commands above to create the table.

**Q: User checked in but can't checkout**
A: Verify user_id format matches exactly (case-sensitive)

---

## Optional: Automatic Database Backup

Add to cron (Linux/Mac):
```bash
0 3 * * * pg_dump -U postgres -h aws-1... postgres > backup_$(date +\%Y\%m\%d).sql
```

Or in Windows Task Scheduler, run:
```batch
pg_dump -U postgres -h aws-1-ap-southeast-2.pooler.supabase.com postgres > backup_%date:~10,4%%date:~4,2%%date:~7,2%.sql
```

---

*Updated: 2026-02-28*
