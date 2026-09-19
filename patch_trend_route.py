import pathlib
import sys

path = pathlib.Path("src/api/main.py")
text = path.read_text(encoding="utf-8")

# ── Patch 1: add _db_write_analysis call after save_analysis ──────────────
OLD1 = "    return RedirectResponse(f\"/result/{analysis_id}\", status_code=303)"
NEW1 = """    _db_write_analysis(patient_id, result.risk_score, result.risk_level)
    return RedirectResponse(f"/result/{analysis_id}", status_code=303)"""

if OLD1 not in text:
    print("ERROR: Patch 1 target not found")
    sys.exit(1)
text = text.replace(OLD1, NEW1, 1)
print("Patch 1 OK")

# ── Patch 2: add patient-trend route and _db_write_analysis helper ────────
OLD2 = "# ── Health check"
NEW2 = """# ── Patient Risk Trend ────────────────────────────────────────────────────────

import sqlite3 as _sqlite3

TREND_DB = "logs/analyses.db"

def _get_trend_db():
    conn = _sqlite3.connect(TREND_DB)
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  TEXT NOT NULL,
            risk_score  REAL NOT NULL,
            risk_level  TEXT NOT NULL,
            analysed_at TEXT NOT NULL
        )
    \"\"\")
    conn.commit()
    return conn

def _db_write_analysis(patient_id: str, risk_score: float, risk_level: str) -> None:
    from datetime import datetime, timezone
    with _get_trend_db() as conn:
        conn.execute(
            "INSERT INTO analyses (patient_id, risk_score, risk_level, analysed_at) VALUES (?, ?, ?, ?)",
            (patient_id, risk_score, risk_level, datetime.now(timezone.utc).isoformat()),
        )

@app.get("/patient-trend/{patient_id}")
async def patient_trend(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    with _get_trend_db() as conn:
        rows = conn.execute(
            \"\"\"SELECT analysed_at, risk_score, risk_level
               FROM analyses
               WHERE patient_id = ?
               ORDER BY analysed_at ASC
               LIMIT 20\"\"\",
            (patient_id,),
        ).fetchall()
    points = [
        {"timestamp": r[0], "risk_score": round(r[1] * 100, 1), "risk_level": r[2]}
        for r in rows
    ]
    return JSONResponse(content={"patient_id": patient_id, "points": points})


# ── Health check"""

if OLD2 not in text:
    print("ERROR: Patch 2 target not found")
    sys.exit(1)
text = text.replace(OLD2, NEW2, 1)
print("Patch 2 OK")

path.write_text(patched := text, encoding="utf-8")
print("Done — main.py updated")
