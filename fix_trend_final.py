import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

OLD = '''@app.get("/patient-trend/{patient_id}")
async def patient_trend(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    with _get_trend_db() as conn:
        rows = conn.execute(
            """SELECT analysed_at, risk_score, risk_level
                 FROM analyses
                 WHERE patient_id = ?
                 ORDER BY analysed_at ASC
                 LIMIT 20""",
            (patient_id,),
        ).fetchall()
    points = [
        {"timestamp": r[0], "risk_score": round(r[1] * 100, 1), "risk_level": r[2]}
        for r in rows
    ]
    return JSONResponse(content={"patient_id": patient_id, "points": points})'''

NEW = '''@app.get("/patient-trend/{patient_id}")
async def patient_trend(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3 as _sq2
    # Try trend DB first
    rows = []
    try:
        with _get_trend_db() as conn:
            rows = conn.execute(
                """SELECT analysed_at, risk_score, risk_level
                     FROM analyses
                     WHERE patient_id = ?
                     ORDER BY analysed_at ASC
                     LIMIT 20""",
                (patient_id,),
            ).fetchall()
    except Exception:
        rows = []
    # Fall back to main clinical.db which uses created_at
    if not rows:
        db_path = Path("data/clinical.db")
        if db_path.exists():
            con2 = _sq2.connect(str(db_path))
            try:
                rows = con2.execute(
                    """SELECT created_at, risk_score, risk_level
                         FROM analyses
                         WHERE patient_id = ?
                         ORDER BY created_at ASC
                         LIMIT 20""",
                    (patient_id,),
                ).fetchall()
            except Exception:
                rows = []
            finally:
                con2.close()
    points = [
        {"timestamp": r[0], "risk_score": round(float(r[1]) * 100, 1), "risk_level": r[2]}
        for r in rows
    ]
    return JSONResponse(content={"patient_id": patient_id, "points": points})'''

if OLD in text:
    text = text.replace(OLD, NEW)
    print("✅  patient-trend endpoint replaced with fallback version")
else:
    print("❌  Pattern not found")

MAIN.write_text(text, encoding="utf-8")
tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"❌  {e}")
finally:
    tmp.unlink(missing_ok=True)
