# Quick Reference Guide

## 🚀 Running the Application

```bash
# Activate environment
venv\Scripts\activate

# Run main menu
python main.py

# Choose option:
# [1] Register new user
# [2] Check-in (access control)  
# [3] Test face detection
# [4] Exit
```

---

## ⚙️ First-Time Setup (5 minutes)

```bash
# 1. Create .env from template
copy .env.example .env

# 2. Edit .env with your Supabase credentials
# (Get from: Supabase Settings > Database > Connection String)

# 3. Test connection
python db/store_embedding.py

# 4. Create database table (SQL)
# Run in Supabase SQL Editor:
CREATE TABLE IF NOT EXISTS face_embeddings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    embedding vector(512),
    model_name VARCHAR(50) DEFAULT 'ArcFace',
    created_at TIMESTAMP DEFAULT NOW()
);

# 5. Run application
python main.py
```

---

## 📝 Environment Variables

Edit `.env`:

```ini
# Database (from Supabase)
DB_HOST=aws-1-ap-southeast-2.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.xxxxx
DB_PASSWORD=your_password
DB_PORT=5432
DB_SSLMODE=require

# Tuning (optional - defaults work fine)
THRESHOLD=0.78              # Match confidence (0-1)
REQUIRED_STABLE_FRAMES=25   # Stabilization time (~1 frame = 33ms)
MATCH_FRAMES=3              # Averaging for stability
DETECT_EVERY_N_FRAMES=5     # Skip frames for speed
RESIZE_SCALE=0.5            # Frame resize (0.5 = 50%)
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| ".env file not found" | Create: `copy .env.example .env` |
| "Database connection failed" | Check credentials in .env |
| "Camera not accessible" | Check camera permissions / Try different USB port |
| "Face not detected" | Better lighting + move 30-50cm from camera |
| "All faces denied access" | Lower THRESHOLD in .env (try 0.75) |
| "Process too slow" | Increase DETECT_EVERY_N_FRAMES (try 10) |

---

## 📊 Configuration Presets

### Fast & Loose (Security Kiosk)
```ini
THRESHOLD=0.76
REQUIRED_STABLE_FRAMES=15
DETECT_EVERY_N_FRAMES=10
RESIZE_SCALE=0.3
```

### Balanced (Default)
```ini
THRESHOLD=0.78
REQUIRED_STABLE_FRAMES=25
DETECT_EVERY_N_FRAMES=5
RESIZE_SCALE=0.5
```

### Slow & Strict (High Security)
```ini
THRESHOLD=0.82
REQUIRED_STABLE_FRAMES=50
DETECT_EVERY_N_FRAMES=1
RESIZE_SCALE=1.0
```

---

## 🎯 Typical Workflows

### Register a New User
```
python main.py
→ Choose [1]
→ Enter user ID (e.g., john_doe_001)
→ Position face in camera
→ Hold still ~0.5 seconds (auto-captures)
→ Done! Returns to menu
```

### Check-in/Access Control
```
python main.py
→ Choose [2]
→ Look at camera
→ Hold still ~0.8 seconds for face recognition
→ Result shows (green = access granted, red = denied)
→ Window closes after 3 seconds
→ Done! Returns to menu
```

### Test Face Detection
```
python main.py
→ Choose [3]
→ Camera shows face detection rectangles
→ Press 'q' to quit
→ Loop shows detection speed ~30FPS
```

---

## 🗄️ Database Queries

Check registered users:
```sql
SELECT user_id, created_at, updated_at 
FROM face_embeddings 
ORDER BY user_id;
```

Delete a user:
```sql
DELETE FROM face_embeddings 
WHERE user_id = 'john_doe_001';
```

Count users:
```sql
SELECT COUNT(*) FROM face_embeddings;
```

---

## 📚 Documentation Map

| Document | When to Read |
|----------|--------------|
| **README.md** | Project overview |
| **SETUP.md** | First-time installation |
| **CODE_ANALYSIS.md** | Understanding how it works |
| **ARCHITECTURE.md** | Before/after comparison |
| **IMPROVEMENTS.md** | What changed and why |
| **This file** | Quick reference |

---

## 🔐 Security Quick Tips

```bash
# DO:
✅ git add .gitignore  # Exclude .env
✅ Keep .env in local only
✅ Use strong DB passwords
✅ Don't share credentials
✅ Rotate passwords monthly

# DON'T:
❌ Commit .env to GitHub
❌ Share passwords via email
❌ Use default passwords
❌ Store credentials in source code
❌ Leave .env in backups
```

---

## 🐛 Debug Steps

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Check installed packages:**
   ```bash
   pip list | grep deepface
   ```

3. **Test camera:**
   ```bash
   python main.py → [3] Test Face Detection
   ```

4. **Test database:**
   ```bash
   python db/store_embedding.py
   ```

5. **Check .env file:**
   ```bash
   cat .env  # Verify all values are present
   ```

---

## 📞 Common Questions

**Q: Can I register same person multiple times?**
A: Yes, but the new embedding overwrites the old one (database UPSERT).

**Q: Is it case-sensitive?**
A: Yes - `alice_001` ≠ `ALICE_001` ≠ `Alice_001`

**Q: How many users can it handle?**
A: Database supports unlimited. Performance degrades at 10,000+ due to image comparison.

**Q: Can I use a different camera?**
A: Yes - change VideoCapture(0) to VideoCapture(1) for second camera.

**Q: How do I back up user data?**
A: Export from Supabase dashboard or run SQL backup.

**Q: Can I reduce recognition time?**
A: Yes - see Configuration Presets above.

---

## 🎯 Performance Benchmarks

| Operation | Time |
|-----------|------|
| Register user (capture) | 0.5s |
| Generate embedding | 300-500ms |
| Check-in (match) | 1-2s total |
| Database store | 50-200ms |
| Face detection | 30-50ms |

---

## 🚀 Next Steps

1. ✅ Run `python main.py`
2. ✅ Register a test user
3. ✅ Verify check-in works
4. ✅ Read SETUP.md for advanced config
5. ✅ Deploy to production!

---

## 📱 Mobile/Kiosk Setup

For fullscreen kiosk:
```python
# Add to main.py before cv2.namedWindow():
cv2.namedWindow("window_name", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("window_name", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
```

---

## 💾 Backup Commands

```bash
# Backup all embeddings to files
python -c "
from db.store_embedding import fetch_all_embeddings
import numpy as np
import os
os.makedirs('backup', exist_ok=True)
users = fetch_all_embeddings()
for uid, emb in users.items():
    np.save(f'backup/{uid}.npy', emb)
print(f'Backed up {len(users)} users')
"

# Export to CSV
psql -h <host> -U <user> -d postgres -c \
  "COPY face_embeddings TO 'backup.csv' CSV"
```

---

## ✨ Tips & Tricks

- **Speed:** Lower `REQUIRED_STABLE_FRAMES` for faster capture
- **Accuracy:** Increase `THRESHOLD` for stricter matching
- **Accuracy:** Use good lighting, frontal face angle
- **Latency:** Use `DETECT_EVERY_N_FRAMES=10` to skip frames
- **Testing:** Use option [3] to debug detection issues
- **Admin:** Query database directly if needed

---

*Quick Reference v1.0 (2026-02-28)*
**Everything you need to know in 2 minutes** ⚡
