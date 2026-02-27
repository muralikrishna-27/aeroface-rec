# AeroFace Setup & Configuration Guide

## 🚀 Quick Start

### Step 1: Clone and Setup Environment
```bash
cd aeroface
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Database Credentials
```bash
# Create .env file from template
copy .env.example .env  # Windows
# or
cp .env.example .env  # macOS/Linux
```

Edit `.env` file with your Supabase credentials:
```
DB_HOST=aws-1-ap-southeast-2.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.xxxxxxxxxxxxxx
DB_PASSWORD=your_actual_password_here
DB_PORT=5432
DB_SSLMODE=require
```

### Step 4: Create Database Table
Run this SQL in your Supabase SQL Editor:
```sql
CREATE TABLE IF NOT EXISTS face_embeddings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    embedding vector(512),
    model_name VARCHAR(50) DEFAULT 'ArcFace',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_id ON face_embeddings(user_id);
```

**Enable pgvector extension:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 5: Run Application
```bash
python main.py
```

---

## 📋 Configuration Parameters

Edit these in `.env` to customize behavior:

```ini
# Face Stabilization (milliseconds at 30fps)
REQUIRED_STABLE_FRAMES=25  # 25 frames ≈ 830ms @ 30fps

# Matching Algorithm
THRESHOLD=0.78            # Confidence threshold (0.0-1.0)
MATCH_FRAMES=3            # Average N embeddings for stability

# Performance Optimization
DETECT_EVERY_N_FRAMES=5   # Check every N frames (skip for speed)
RESIZE_SCALE=0.5          # Resize frame to 50% (for faster processing)
```

### Tuning Guide

**For Faster Recognition (Security Kiosk):**
```ini
REQUIRED_STABLE_FRAMES=15
DETECT_EVERY_N_FRAMES=10
THRESHOLD=0.76
```

**For Maximum Accuracy (Verification System):**
```ini
REQUIRED_STABLE_FRAMES=50
DETECT_EVERY_N_FRAMES=1
THRESHOLD=0.82
MATCH_FRAMES=5
```

---

## 🔐 Security Checklist

- ✅ **Never commit `.env` to git**
  ```bash
  # Add to .gitignore
  echo ".env" >> .gitignore
  ```

- ✅ **Use strong database passwords**
- ✅ **Rotate credentials periodically**
- ✅ **Use HTTPS/SSL connections only**
- ✅ **Limit database user permissions** (read-only for check-in, write for registration)

### Create Read-Only User for Check-In (Recommended):
```sql
CREATE USER checkin_user WITH PASSWORD 'strong_password';
GRANT SELECT ON face_embeddings TO checkin_user;
```

Then use separate `.env` variables:
```ini
DB_USER_CHECKIN=checkin_user
DB_PASSWORD_CHECKIN=strong_password
```

---

## 🧪 Testing

### 1. Test Database Connection
```bash
python -c "from db.store_embedding import get_connection; get_connection()"
```

### 2. Test Face Detection
```bash
python main.py
# Choose option 3: Test Face Detection
```

### 3. Register Test User
```bash
python main.py
# Choose option 1: Register New Face
# Enter user_id: test_user_001
```

### 4. Check-in Test
```bash
python main.py
# Choose option 2: Check-in
# Should recognize test_user_001
```

---

## 🐛 Troubleshooting

### Problem: "Cannot read from camera"
**Solution:**
- Check if camera is connected
- Try in another application first
- On Windows, use DirectShow backend (already configured)
- Check permissions: `Settings > Privacy > Camera`

### Problem: "Database connection failed"
**Solution:**
- Verify `.env` file exists and has correct credentials
- Check internet connection
- Verify Supabase project is active
- Check firewall: Supabase uses port 5432

### Problem: "No embeddings generated"
**Solution:**
- Ensure good lighting
- Move closer to camera (face should be 20-50cm away)
- Keep face straight, avoid extreme angles
- Wait for "Hold still" message

### Problem: "Access denied for all faces"
**Solution:**
- Verify threshold in `.env` (default 0.78)
- Try decreasing threshold: `THRESHOLD=0.75`
- Check face angle (frontal face works best)
- Re-register the user (requirements may have changed)

### Problem: "Slow check-in process"
**Solution:**
- Increase `DETECT_EVERY_N_FRAMES`: 10 or 15
- Decrease `REQUIRED_STABLE_FRAMES`: 15 or 20
- Check database query performance: may need indexing

---

## 📊 Adding More Users

### Batch Registration Script

Create `batch_register.py`:
```python
from face.register_face import register_face
import time

users = ["alice_001", "bob_002", "charlie_003"]

for user_id in users:
    print(f"\n🟢 Registering {user_id}")
    try:
        register_face(user_id)
        time.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
```

Run it:
```bash
python batch_register.py
```

---

## 📈 Performance Tips

1. **Use connection pooling** (for production)
2. **Cache embeddings** in memory for check-in
3. **Pre-detect faces** in background thread
4. **Use GPU acceleration** for DeepFace (CUDA required)
5. **Optimize image size** (currently 512x512)

---

## 🔄 Backup & Recovery

### Backup embeddings:
```bash
# Export from Supabase
python -c "
from db.store_embedding import fetch_all_embeddings
import numpy as np
users = fetch_all_embeddings()
for uid, emb in users.items():
    np.save(f'backup/{uid}.npy', emb)
"
```

### Restore embeddings:
```bash
python -c "
import numpy as np
from db.store_embedding import store_embedding
from pathlib import Path
for file in Path('backup').glob('*.npy'):
    user_id = file.stem
    emb = np.load(file)
    store_embedding(user_id, emb)
"
```

---

## 📞 Support

- Check `CODE_ANALYSIS.md` for detailed technical documentation
- Review logs in console output
- Enable debug mode: Add `DEBUG=true` to `.env`

---

*Last updated: 2026-02-28*
