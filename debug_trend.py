import sqlite3
from pathlib import Path

db = sqlite3.connect("data/clinical.db")
db.row_factory = sqlite3.Row
cur = db.cursor()

print("=== analyses table sample ===")
cur.execute("SELECT patient_id, risk_level, risk_score, created_at FROM analyses ORDER BY patient_id")
for row in cur.fetchall():
    print(f"  {row['patient_id']} | {row['risk_level']} | {row['risk_score']} | {row['created_at']}")

print("\n=== patient-trend endpoint check ===")
# Find the endpoint in main.py
text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()
for i, line in enumerate(lines, 1):
    if "patient-trend" in line or "patient_trend" in line:
        for j in range(i-1, min(i+20, len(lines))):
            print(f"{j+1:4d}  {lines[j]}")
        print("---")
