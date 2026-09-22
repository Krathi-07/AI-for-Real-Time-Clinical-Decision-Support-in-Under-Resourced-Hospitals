with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# ── FIX 1: Light mode faded text — findings/recommendations ──────────────────
old_findings = "findings_html = \"\".join(f\"<li style='margin:.4rem 0;color:#fcd34d'>⚠ {f}</li>\" for f in findings)"
new_findings = "findings_html = \"\".join(f\"<li style='margin:.4rem 0;color:#fcd34d;font-weight:500'>⚠ {f}</li>\" for f in findings)"

old_recs = "recs_html = \"\".join(f\"<li style='margin:.4rem 0;color:#86efac'>→ {r}</li>\" for r in recs)"
new_recs = "recs_html = \"\".join(f\"<li style='margin:.4rem 0;color:#16a34a;font-weight:500'>→ {r}</li>\" for r in recs)"

old_theme_light_all = "  [data-theme=\"light\"] *{{color:#1e1b4b}}"
new_theme_light_all = """  [data-theme="light"] *{{color:#1e1b4b}}
  [data-theme="light"] li{{color:#1e1b4b!important;font-weight:500}}
  [data-theme="light"] .card li{{color:#1e1b4b!important}}"""

count = 0
for old, new in [(old_findings, new_findings), (old_recs, new_recs), (old_theme_light_all, new_theme_light_all)]:
    if old in code:
        code = code.replace(old, new)
        count += 1
print(f"✅ Fix 1: Light mode text ({count}/3)")

# ── FIX 2: Discharge button in dashboard table ────────────────────────────────
old_row = """          <td>
            <a href="/analyse/{p['patient_id']}">
              <button class="btn btn-primary" style="padding:.3rem .8rem;font-size:.8rem">Analyse</button>
            </a>
          </td>"""

new_row = """          <td style="display:flex;gap:.4rem;align-items:center">
            <a href="/analyse/{p['patient_id']}">
              <button class="btn btn-primary" style="padding:.3rem .8rem;font-size:.8rem">Analyse</button>
            </a>
            <button onclick="dischargePatient('{p['patient_id']}')"
              style="padding:.3rem .8rem;font-size:.8rem;background:#ef4444;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">
              Discharge
            </button>
          </td>"""

if old_row in code:
    code = code.replace(old_row, new_row)
    print("✅ Fix 2: Discharge button in table")
else:
    print("⚠ Fix 2: Row pattern not found")

# ── FIX 3: Discharged stats card ─────────────────────────────────────────────
old_stats_row = """              <div class='stats-row'>
                <div class='stat-card'>
                  <div class='stat-value' id='sc-total-val'>--</div>
                  <div class='stat-label'>Total Analysed</div>
                </div>
                <div class='stat-card critical'>
                  <div class='stat-value' id='sc-crit-val'>--</div>
                  <div class='stat-label'>Critical Alerts</div>
                </div>
                <div class='stat-card high'>
                  <div class='stat-value' id='sc-high-val'>--</div>
                  <div class='stat-label'>High Risk</div>
                </div>
                <div class='stat-card avg'>
                  <div class='stat-value' id='sc-avg-val'>--</div>
                  <div class='stat-label'>Avg Risk Score</div>
                </div>
              </div>"""

new_stats_row = """              <div class='stats-row'>
                <div class='stat-card'>
                  <div class='stat-value' id='sc-total-val'>--</div>
                  <div class='stat-label'>Total Analysed</div>
                </div>
                <div class='stat-card critical'>
                  <div class='stat-value' id='sc-crit-val'>--</div>
                  <div class='stat-label'>Critical Alerts</div>
                </div>
                <div class='stat-card high'>
                  <div class='stat-value' id='sc-high-val'>--</div>
                  <div class='stat-label'>High Risk</div>
                </div>
                <div class='stat-card avg'>
                  <div class='stat-value' id='sc-avg-val'>--</div>
                  <div class='stat-label'>Avg Risk Score</div>
                </div>
                <div class='stat-card' style='border-top:3px solid #6b7280'>
                  <div class='stat-value' id='sc-disc-val' style='color:#6b7280'>--</div>
                  <div class='stat-label'>Discharged</div>
                </div>
              </div>"""

if old_stats_row in code:
    code = code.replace(old_stats_row, new_stats_row)
    print("✅ Fix 3: Discharged stats card")
else:
    print("⚠ Fix 3: Stats row not found")

# ── FIX 4: Add discharge JS + update refreshStats ────────────────────────────
old_refresh = """        async function refreshStats() {
            try {
                var r = await fetch('/stats');
                if (!r.ok) return;
                var d = await r.json();
                ['total_analysed','critical_count','high_count','avg_risk_score'].forEach(function(k,i) {
                    var ids = ['sc-total-val','sc-crit-val','sc-high-val','sc-avg-val'];
                    var el = document.getElementById(ids[i]);
                    if (el) el.textContent = d[k];
                });
            } catch(e) { console.log('stats err',e); }
        }
        refreshStats();
        setInterval(refreshStats, 30000);"""

new_refresh = """        async function refreshStats() {
            try {
                var r = await fetch('/stats');
                if (!r.ok) return;
                var d = await r.json();
                ['total_analysed','critical_count','high_count','avg_risk_score'].forEach(function(k,i) {
                    var ids = ['sc-total-val','sc-crit-val','sc-high-val','sc-avg-val'];
                    var el = document.getElementById(ids[i]);
                    if (el) el.textContent = d[k];
                });
                var disc = document.getElementById('sc-disc-val');
                if (disc && d.discharged_count !== undefined) disc.textContent = d.discharged_count;
            } catch(e) { console.log('stats err',e); }
        }
        async function dischargePatient(pid) {
            if (!confirm('Discharge patient ' + pid + '? They will be hidden from active list.')) return;
            var r = await fetch('/discharge/' + pid, {method:'POST'});
            if (r.ok) { location.reload(); }
            else { alert('Could not discharge patient.'); }
        }
        refreshStats();
        setInterval(refreshStats, 30000);"""

if old_refresh in code:
    code = code.replace(old_refresh, new_refresh)
    print("✅ Fix 4: Discharge JS + stats update")
else:
    print("⚠ Fix 4: refreshStats pattern not found")

# ── FIX 5: Hide discharged patients from dashboard ───────────────────────────
old_patients = "    patients = get_patients_for_doctor(doctor[\"id\"])"
new_patients = "    patients = [p for p in get_patients_for_doctor(doctor[\"id\"]) if not p.get(\"discharged\")]"

if old_patients in code:
    code = code.replace(old_patients, new_patients)
    print("✅ Fix 5: Hide discharged from dashboard")
else:
    print("⚠ Fix 5: patients line not found")

# ── FIX 6: Add /discharge endpoint + update /stats ───────────────────────────
discharge_endpoint = '''
@app.post("/discharge/{patient_id}")
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
    return {"status": "discharged", "patient_id": patient_id}

'''

if "discharge_endpoint" not in code and "@app.get(\"/stats\")" in code:
    code = code.replace("@app.get(\"/stats\")", discharge_endpoint + "@app.get(\"/stats\")")
    print("✅ Fix 6: Discharge endpoint added")
else:
    print("⚠ Fix 6: already exists or stats not found")

# ── FIX 7: Add discharged_count to /stats ────────────────────────────────────
old_stats_return = """    return {
        "total_analysed": total,
        "critical_count": critical,
        "high_count": high,
        "avg_risk_score": avg,
    }"""

new_stats_return = """    # Count discharged patients
    discharged = 0
    try:
        import sqlite3 as _sqd
        db_path2 = Path("data/clinical.db")
        if db_path2.exists():
            con3 = _sqd.connect(str(db_path2))
            discharged = con3.execute("SELECT COUNT(*) FROM patients WHERE discharged=1").fetchone()[0]
            con3.close()
    except Exception:
        discharged = 0

    return {
        "total_analysed": total,
        "critical_count": critical,
        "high_count": high,
        "avg_risk_score": avg,
        "discharged_count": discharged,
    }"""

if old_stats_return in code:
    code = code.replace(old_stats_return, new_stats_return)
    print("✅ Fix 7: discharged_count in stats")
else:
    print("⚠ Fix 7: stats return not found")

# ── FIX 8: Duplicate patient warning on registration ─────────────────────────
old_register_post = """    doctor = require_doctor(session)
    patient_id = register_patient(full_name, age, gender, phone, address, disease_id, doctor["id"])
    return RedirectResponse(f"/analyse/{patient_id}?msg=Patient+registered", status_code=303)"""

new_register_post = """    doctor = require_doctor(session)
    # Check for duplicate patient (same name + age)
    import sqlite3 as _sqdup
    db_path_dup = Path("data/clinical.db")
    if db_path_dup.exists():
        con_dup = _sqdup.connect(str(db_path_dup))
        existing = con_dup.execute(
            "SELECT patient_id FROM patients WHERE LOWER(full_name)=LOWER(?) AND age=? AND doctor_id=?",
            (full_name, age, doctor["id"])
        ).fetchone()
        con_dup.close()
        if existing:
            return RedirectResponse(
                f"/register-patient?msg=WARNING:+Patient+{full_name}+age+{age}+already+exists+as+{existing[0]}",
                status_code=303
            )
    patient_id = register_patient(full_name, age, gender, phone, address, disease_id, doctor["id"])
    return RedirectResponse(f"/analyse/{patient_id}?msg=Patient+registered", status_code=303)"""

if old_register_post in code:
    code = code.replace(old_register_post, new_register_post)
    print("✅ Fix 8: Duplicate patient warning")
else:
    print("⚠ Fix 8: register post not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("\n✅ All fixes written to main.py")
