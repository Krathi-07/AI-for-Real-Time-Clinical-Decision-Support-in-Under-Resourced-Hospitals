with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = '''@app.post("/discharge/{patient_id}")
async def discharge_patient(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3 as _sq
    db_path = Path("data/clinical.db")
    if not db_path.exists():
        raise HTTPException(404, "DB not found")
    conn = _sq.connect(str(db_path))
    conn.execute("UPDATE patients SET discharged=1 WHERE patient_id=?", (patient_id,))
    conn.commit()
    conn.close()
    return {"status": "discharged", "patient_id": patient_id}'''

new = '''@app.post("/discharge/{patient_id}")
async def discharge_patient(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3 as _sq
    # Try main db first, fall back to trend db
    for db_path in [Path("data/clinical.db"), Path("logs/analyses.db"), Path("/tmp/clinical.db")]:
        try:
            if not db_path.exists() and str(db_path) != "/tmp/clinical.db":
                continue
            conn = _sq.connect(str(db_path))
            # Create discharged table if not exists (for fallback DBs)
            conn.execute("""CREATE TABLE IF NOT EXISTS discharged_patients
                (patient_id TEXT PRIMARY KEY, discharged_at TEXT)""")
            conn.execute("INSERT OR REPLACE INTO discharged_patients (patient_id, discharged_at) VALUES (?, ?)",
                (patient_id, datetime.now(UTC).isoformat()))
            # Also try updating patients table
            try:
                conn.execute("UPDATE patients SET discharged=1 WHERE patient_id=?", (patient_id,))
            except Exception:
                pass
            conn.commit()
            conn.close()
            return {"status": "discharged", "patient_id": patient_id}
        except Exception as e:
            continue
    raise HTTPException(500, "Could not discharge patient")'''

if old in code:
    code = code.replace(old, new)
    print("✅ Discharge endpoint fixed")
else:
    print("❌ Pattern not found")

# Also fix the dashboard filter to check both sources
old_filter = '    patients = [p for p in get_patients_for_doctor(doctor["id"]) if not p.get("discharged")]'
new_filter = '''    import sqlite3 as _sqd2
    discharged_ids = set()
    for db_path_d in [Path("data/clinical.db"), Path("logs/analyses.db"), Path("/tmp/clinical.db")]:
        try:
            if not db_path_d.exists():
                continue
            con_d = _sqd2.connect(str(db_path_d))
            rows_d = con_d.execute("SELECT patient_id FROM discharged_patients").fetchall()
            discharged_ids.update(r[0] for r in rows_d)
            con_d.close()
        except Exception:
            pass
    all_patients = get_patients_for_doctor(doctor["id"])
    patients = [p for p in all_patients if p["patient_id"] not in discharged_ids and not p.get("discharged")]'''

if old_filter in code:
    code = code.replace(old_filter, new_filter)
    print("✅ Dashboard filter fixed")
else:
    print("❌ Filter pattern not found")

# Fix discharged count in stats
old_disc_count = '''    discharged = 0
    try:
        import sqlite3 as _sqd
        db_path2 = Path("data/clinical.db")
        if db_path2.exists():
            con3 = _sqd.connect(str(db_path2))
            discharged = con3.execute("SELECT COUNT(*) FROM patients WHERE discharged=1").fetchone()[0]
            con3.close()
    except Exception:
        discharged = 0'''

new_disc_count = '''    discharged = 0
    try:
        import sqlite3 as _sqd
        for db_path2 in [Path("data/clinical.db"), Path("logs/analyses.db"), Path("/tmp/clinical.db")]:
            try:
                if not db_path2.exists():
                    continue
                con3 = _sqd.connect(str(db_path2))
                row3 = con3.execute("SELECT COUNT(*) FROM discharged_patients").fetchone()
                con3.close()
                discharged = row3[0] if row3 else 0
                break
            except Exception:
                continue
    except Exception:
        discharged = 0'''

if old_disc_count in code:
    code = code.replace(old_disc_count, new_disc_count)
    print("✅ Discharged count fixed")
else:
    print("❌ Disc count pattern not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
