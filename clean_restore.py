# clean_restore.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python clean_restore.py
#
# Step 1: Restore main.py from the .bak made by restore_tier1.py
# Step 2: Inject all Tier 1 features correctly, with {{ }} escaping
#         for anything landing inside a Python f-string, and plain
#         { } for anything in a regular string or separate function.
# ----------------------------------------------------------------

import re
import sys
from pathlib import Path

MAIN = Path("src/api/main.py")
BAK  = Path("src/api/main.py.bak")

# ── Step 1: restore from backup ──────────────────────────────────
if not BAK.exists():
    print("❌  main.py.bak not found.")
    print("    Do you have an earlier backup? Check for main.py.bak in src/api/")
    sys.exit(1)

text = BAK.read_text(encoding="utf-8")
MAIN.write_text(text, encoding="utf-8")
print("✅  Restored main.py from backup (main.py.bak)")

# ── Step 2: verify baseline ───────────────────────────────────────
assert "require_doctor" in text, "backup looks wrong — require_doctor missing"
assert "import sqlite3" in text, "backup looks wrong — sqlite3 missing"
print("✅  Backup is valid")

# ================================================================
# FEATURE 1 — /stats endpoint
# This is a top-level Python function, NOT inside any string.
# Plain { } are fine here.
# ================================================================
STATS_ENDPOINT = '''

@app.get("/stats")
async def get_stats(session: str = Cookie(default=None)):
    """Live dashboard stats."""
    require_doctor(session)
    import sqlite3 as _sq
    db_path = Path("data/clinical.db")
    if not db_path.exists():
        return {"total_analysed": 0, "critical_count": 0,
                "high_count": 0, "avg_risk_score": 0}
    con = _sq.connect(str(db_path))
    cur = con.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM analyses")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM analyses WHERE risk_level = 'CRITICAL'")
        critical = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM analyses WHERE risk_level = 'HIGH'")
        high = cur.fetchone()[0]
        cur.execute("SELECT AVG(risk_score) FROM analyses")
        avg_row = cur.fetchone()[0]
        avg = round(float(avg_row), 1) if avg_row else 0
    except Exception:
        total, critical, high, avg = 0, 0, 0, 0
    finally:
        con.close()
    return {
        "total_analysed": total,
        "critical_count": critical,
        "high_count": high,
        "avg_risk_score": avg,
    }
'''

if "/stats" not in text:
    matches = list(re.finditer(r'\n@app\.', text))
    if matches:
        pos = matches[-1].start()
        text = text[:pos] + STATS_ENDPOINT + text[pos:]
        print("✅  /stats endpoint injected")
    else:
        print("⚠️  Could not find @app routes — /stats not injected")
else:
    print("ℹ️   /stats already present")

# ================================================================
# FEATURE 2 — CSS (dark mode + stat cards + search box)
#
# KEY RULE: If the </style> is inside a Python f-string (i.e. the
# _base() function returns f"""..."""), every CSS { } must be {{ }}.
# We detect this by checking whether the </style> sits inside an
# f-string context. Easiest safe approach: always use {{ }} in the
# CSS we add — valid Python f-string AND valid CSS.
# ================================================================

EXTRA_CSS = """
        /* ── Dark mode ── */
        body.dark {{ background: #0f0f1a; color: #e2e8f0; }}
        body.dark .card, body.dark .stat-card {{ background: #1a1a2e; border-color: #2d2d4e; }}
        body.dark table thead {{ background: #1a1a2e; }}
        body.dark table tbody tr:hover {{ background: #1f1f35; }}
        body.dark .navbar {{ background: #0f0f1a; border-color: #2d2d4e; }}
        body.dark input, body.dark select {{ background: #1a1a2e; color: #e2e8f0; border-color: #3d3d6e; }}

        /* ── Stat cards ── */
        .stats-row {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .stat-card {{
            flex: 1; min-width: 140px; background: #fff;
            border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 1rem 1.25rem; text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,.06);
        }}
        .stat-card .stat-value {{ font-size: 2rem; font-weight: 700; color: #6c3fcf; }}
        .stat-card .stat-label {{ font-size: .78rem; color: #64748b; margin-top: .2rem; }}
        .stat-card.critical .stat-value {{ color: #ef4444; }}
        .stat-card.high .stat-value    {{ color: #f97316; }}
        .stat-card.avg .stat-value     {{ color: #0ea5e9; }}

        /* ── Search box ── */
        .search-wrap {{ margin-bottom: 1rem; }}
        .search-wrap input {{
            width: 100%; padding: .55rem 1rem; border-radius: 8px;
            border: 1px solid #d1d5db; font-size: .95rem; outline: none;
        }}
        .search-wrap input:focus {{ border-color: #6c3fcf; box-shadow: 0 0 0 3px rgba(108,63,207,.15); }}
"""

if "stat-card" not in text:
    style_close = text.rfind("</style>")
    if style_close != -1:
        text = text[:style_close] + EXTRA_CSS + text[style_close:]
        print("✅  Dark-mode + stat-card CSS injected (with {{ }} escaping)")
    else:
        print("⚠️  No </style> found — CSS not injected")
else:
    print("ℹ️   stat-card CSS already present")

# ================================================================
# FEATURE 3 — Stat cards HTML (above "Your Patients")
# This lands inside a Python string (the body variable), so
# {{ }} is needed for any CSS inline styles too.
# ================================================================

STAT_CARDS_HTML = """
            <!-- Live stats -->
            <div class='stats-row'>
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
            </div>
"""

if "sc-total-val" not in text:
    anchor = text.find("Your Patients")
    if anchor != -1:
        text = text[:anchor] + STAT_CARDS_HTML + text[anchor:]
        print("✅  Stat cards HTML injected above 'Your Patients'")
    else:
        print("⚠️  'Your Patients' not found — stat cards not injected")
else:
    print("ℹ️   Stat cards HTML already present")

# ================================================================
# FEATURE 4 — Search box HTML
# ================================================================

SEARCH_BOX_HTML = """
            <!-- Search -->
            <div class='search-wrap'>
              <input type='text' id='searchInput'
                     placeholder='Search by name, patient ID, or condition...'
                     oninput='filterPatients()' />
            </div>
"""

if "searchInput" not in text:
    anchor = text.find("Your Patients")
    if anchor != -1:
        eol = text.find("\n", anchor)
        text = text[:eol+1] + SEARCH_BOX_HTML + text[eol+1:]
        print("✅  Search box injected")
    else:
        print("⚠️  'Your Patients' not found — search box not injected")
else:
    print("ℹ️   Search box already present")

# ================================================================
# FEATURE 5 — tbody id
# ================================================================

if 'id="patient-table"' not in text and "id='patient-table'" not in text:
    new = text.replace("<tbody>", "<tbody id='patient-table'>", 1)
    if new != text:
        text = new
        print("✅  id='patient-table' added to <tbody>")
    else:
        print("⚠️  <tbody> not found")
else:
    print("ℹ️   patient-table id already present")

# ================================================================
# FEATURE 6 — JavaScript block
#
# KEY RULE: JS uses { } heavily. If this lands inside an f-string
# we must escape them. Safest: inject before </body> which is
# typically inside the f-string. Use {{ }} for all JS braces.
# ================================================================

JS_BLOCK = """
        <script>
        function filterPatients() {{
            var q = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('#patient-table tr').forEach(function(row) {{
                row.style.display = row.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
            }});
        }}

        async function refreshStats() {{
            try {{
                var r = await fetch('/stats');
                if (!r.ok) return;
                var d = await r.json();
                document.getElementById('sc-total-val').textContent = d.total_analysed;
                document.getElementById('sc-crit-val').textContent  = d.critical_count;
                document.getElementById('sc-high-val').textContent  = d.high_count;
                document.getElementById('sc-avg-val').textContent   = d.avg_risk_score;
            }} catch(e) {{}}
        }}
        refreshStats();
        setInterval(refreshStats, 30000);
        </script>
"""

if "filterPatients" not in text:
    body_close = text.rfind("</body>")
    if body_close != -1:
        text = text[:body_close] + JS_BLOCK + text[body_close:]
        print("✅  filterPatients + refreshStats JS injected (with {{ }} escaping)")
    else:
        print("⚠️  </body> not found — JS not injected")
else:
    print("ℹ️   filterPatients JS already present")

# ── Write final file ─────────────────────────────────────────────
MAIN.write_text(text, encoding="utf-8")
print("\n✅  main.py written successfully.")

# ── Quick syntax check ───────────────────────────────────────────
import py_compile
import shutil
import tempfile

tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  Syntax check PASSED — no Python errors.")
except py_compile.PyCompileError as e:
    print(f"❌  Syntax error found: {e}")
    print("    The file was saved — paste the error above to Claude.")
finally:
    tmp.unlink(missing_ok=True)

print("\nNext:")
print("  uv run python -m uvicorn src.api.main:app --reload --port 8000")
print("  Open http://localhost:8000/dashboard")
