import sqlite3

# Add discharged column to patients table
db_path = "data/clinical.db"
conn = sqlite3.connect(db_path)
try:
    conn.execute("ALTER TABLE patients ADD COLUMN discharged INTEGER DEFAULT 0")
    conn.commit()
    print("✅ DB: discharged column added")
except Exception as e:
    print(f"ℹ DB: {e}")
conn.close()
