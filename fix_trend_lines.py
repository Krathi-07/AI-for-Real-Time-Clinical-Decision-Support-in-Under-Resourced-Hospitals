import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
lines = MAIN.read_text(encoding="utf-8").splitlines(keepends=True)

# Find the exact line numbers of the endpoint
start = next(i for i,l in enumerate(lines) if '@app.get("/patient-trend/{patient_id}")' in l)
end   = next(i for i,l in enumerate(lines) if i > start and l.strip().startswith('@app.') or (i > start+30))

print(f"Replacing lines {start+1} to {end}")

NEW_ENDPOINT = '''@app.get("/patient-trend/{patient_id}")
async def patient_trend(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3 as _sq2
    rows = []
    try:
        with _get_trend_db() as conn:
            rows = conn.execute(
                "SELECT analysed_at, risk_score, risk_level FROM analyses WHERE patient_id = ? ORDER BY analysed_at ASC LIMIT 20",
                (patient_id,),
            ).fetchall()
    except Exception:
        rows = []
    if not rows:
        db_path = Path("data/clinical.db")
        if db_path.exists():
            con2 = _sq2.connect(str(db_path))
            try:
                rows = con2.execute(
                    "SELECT created_at, risk_score, risk_level FROM analyses WHERE patient_id = ? ORDER BY created_at ASC LIMIT 20",
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
    return JSONResponse(content={"patient_id": patient_id, "points": points})

'''

new_lines = lines[:start] + [NEW_ENDPOINT] + lines[end:]
MAIN.write_text("".join(new_lines), encoding="utf-8")
print("✅  Endpoint replaced by line numbers")

tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"❌  {e}")
finally:
    tmp.unlink(missing_ok=True)
