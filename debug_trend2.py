import sqlite3
from pathlib import Path

# Simulate exactly what the endpoint does now
db_path = Path("data/clinical.db")
con = sqlite3.connect(str(db_path))
rows = con.execute(
    "SELECT created_at, risk_score, risk_level FROM analyses WHERE patient_id = ? ORDER BY created_at ASC LIMIT 20",
    ("PT-20260917-0007",)
).fetchall()
con.close()

print(f"Rows found: {len(rows)}")
for r in rows:
    score = round(float(r[1]) * 100, 1)
    print(f"  timestamp={r[0]}  score={score}  level={r[2]}")

# Also check what _get_trend_db points to
text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()
for i, line in enumerate(lines, 1):
    if "_get_trend_db" in line or "trend_db" in line.lower() or "trend.db" in line.lower():
        print(f"{i:4d}  {line}")
