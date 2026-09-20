# restore_tier1.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python restore_tier1.py
#
# What this does (surgically, no rewrite):
#   1. Adds /stats API endpoint after the last @app.get route
#   2. Adds dark-mode CSS + stat-card CSS to the shared <style> block
#   3. Adds dark-mode toggle button to the navbar
#   4. Adds stat cards row above the patient table
#   5. Adds search box above the patient table
#   6. Adds filterPatients JS + dark-mode JS + auto-refresh JS
# ---------------------------------------------------------------

import re
import sys
from pathlib import Path

MAIN = Path("src/api/main.py")

if not MAIN.exists():
    print("❌  src/api/main.py not found. Run this from C:\\Projects\\clinical-ai")
    sys.exit(1)

original = MAIN.read_text(encoding="utf-8")
text = original  # we'll mutate this

ISSUES = []

# ================================================================
# 1.  /stats  ENDPOINT
# ================================================================
STATS_ENDPOINT = '''

@app.get("/stats")
async def get_stats(session: str = Cookie(default=None)):
    """Live dashboard stats — total analysed, critical count, risk scores."""
    require_doctor(session)
    import sqlite3 as _sq
    db_path = Path("data/clinical.db")
    if not db_path.exists():
        return {"total_analysed": 0, "critical_count": 0, "high_count": 0, "avg_risk_score": 0}
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

if '/stats' not in text:
    # Insert before the last function definition or at the end of the route block
    # Find last @app. decorator line
    matches = list(re.finditer(r'\n@app\.', text))
    if matches:
        insert_pos = matches[-1].start()
        text = text[:insert_pos] + STATS_ENDPOINT + text[insert_pos:]
        print("✅  /stats endpoint injected")
    else:
        ISSUES.append("Could not find @app. routes to anchor /stats — add manually")
else:
    print("ℹ️   /stats already present — skipped")

# ================================================================
# 2.  CSS — dark mode + stat cards
# ================================================================
EXTRA_CSS = """
        /* ── Dark mode ── */
        body.dark { background: #0f0f1a; color: #e2e8f0; }
        body.dark .card, body.dark .stat-card { background: #1a1a2e; border-color: #2d2d4e; }
        body.dark table thead { background: #1a1a2e; }
        body.dark table tbody tr:hover { background: #1f1f35; }
        body.dark .navbar { background: #0f0f1a; border-color: #2d2d4e; }
        body.dark input, body.dark select { background: #1a1a2e; color: #e2e8f0; border-color: #3d3d6e; }

        /* ── Stat cards ── */
        .stats-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
        .stat-card {
            flex: 1; min-width: 140px; background: #fff;
            border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 1rem 1.25rem; text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,.06);
        }
        .stat-card .stat-value { font-size: 2rem; font-weight: 700; color: #6c3fcf; }
        .stat-card .stat-label { font-size: .78rem; color: #64748b; margin-top: .2rem; }
        .stat-card.critical .stat-value { color: #ef4444; }
        .stat-card.high .stat-value    { color: #f97316; }
        .stat-card.avg .stat-value     { color: #0ea5e9; }

        /* ── Search box ── */
        .search-wrap { margin-bottom: 1rem; }
        .search-wrap input {
            width: 100%; padding: .55rem 1rem; border-radius: 8px;
            border: 1px solid #d1d5db; font-size: .95rem; outline: none;
        }
        .search-wrap input:focus { border-color: #6c3fcf; box-shadow: 0 0 0 3px rgba(108,63,207,.15); }
"""

# Find the closing </style> tag inside the HTML returned by dashboard
if 'stat-card' not in text:
    # Try to find an existing </style> inside a triple-quoted HTML string
    style_close = text.rfind('</style>')
    if style_close != -1:
        text = text[:style_close] + EXTRA_CSS + text[style_close:]
        print("✅  Dark-mode + stat-card CSS injected")
    else:
        ISSUES.append("No </style> found in main.py — CSS not injected. Add manually.")
else:
    print("ℹ️   stat-card CSS already present — skipped")

# ================================================================
# 3.  NAVBAR — dark mode toggle button
# ================================================================
DARK_BTN = '<button onclick="toggleDark()" style="background:#f1f0ff;border:1px solid #c4b5fd;color:#6c3fcf;padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-size:.85rem;">🌙 Dark Mode</button>'

if 'dark-mode' not in text and 'toggleDark' not in text:
    # Look for Logout link in navbar — insert button just before it
    logout_pat = re.search(r'(<a[^>]*href[^>]*/logout[^>]*>Logout</a>)', text)
    if logout_pat:
        insert_at = logout_pat.start()
        text = text[:insert_at] + DARK_BTN + '\n                    ' + text[insert_at:]
        print("✅  Dark-mode toggle button injected into navbar")
    else:
        ISSUES.append("Logout link not found in navbar — dark-mode button not injected. Add manually.")
else:
    print("ℹ️   Dark-mode toggle already present — skipped")

# ================================================================
# 4.  STAT CARDS ROW  (above patient table)
# ================================================================
STAT_CARDS_HTML = """
            <!-- ── Live stats ── -->
            <div class="stats-row">
              <div class="stat-card" id="sc-total">
                <div class="stat-value" id="sc-total-val">—</div>
                <div class="stat-label">Total Analysed</div>
              </div>
              <div class="stat-card critical" id="sc-crit">
                <div class="stat-value" id="sc-crit-val">—</div>
                <div class="stat-label">Critical Alerts</div>
              </div>
              <div class="stat-card high" id="sc-high">
                <div class="stat-value" id="sc-high-val">—</div>
                <div class="stat-label">High Risk</div>
              </div>
              <div class="stat-card avg" id="sc-avg">
                <div class="stat-value" id="sc-avg-val">—</div>
                <div class="stat-label">Avg Risk Score</div>
              </div>
            </div>
"""

if 'stat-card' not in text or 'sc-total' not in text:
    # Find "Your Patients" heading or the card/table wrapper
    anchor = re.search(r'Your Patients', text)
    if anchor:
        # Insert the stat cards just before "Your Patients"
        # Walk back to the start of the enclosing <div
        before = text[:anchor.start()]
        after = text[anchor.start():]
        text = before + STAT_CARDS_HTML + after
        print("✅  Stat cards HTML injected above patient table")
    else:
        ISSUES.append('"Your Patients" heading not found — stat cards not injected. Add manually.')
else:
    print("ℹ️   Stat cards HTML already present — skipped")

# ================================================================
# 5.  SEARCH BOX  (between stat cards and patient table)
# ================================================================
SEARCH_BOX_HTML = """
            <!-- ── Search ── -->
            <div class="search-wrap">
              <input type="text" id="searchInput" placeholder="🔍  Search by name, patient ID, or condition…"
                     oninput="filterPatients()" />
            </div>
"""

if 'searchInput' not in text:
    anchor = re.search(r'Your Patients', text)
    if anchor:
        # Insert after the stat-cards block we just added (after "Your Patients" heading)
        pos = text.find('Your Patients')
        # Find the end of that heading line
        eol = text.find('\n', pos)
        text = text[:eol+1] + SEARCH_BOX_HTML + text[eol+1:]
        print("✅  Search box HTML injected")
    else:
        ISSUES.append('"Your Patients" heading not found — search box not injected.')
else:
    print("ℹ️   Search box already present — skipped")

# ================================================================
# 6.  tbody id="patient-table"
# ================================================================
if 'id="patient-table"' not in text:
    # Replace first <tbody> that doesn't have an id
    text = text.replace('<tbody>', '<tbody id="patient-table">', 1)
    if 'id="patient-table"' in text:
        print("✅  id=\"patient-table\" added to <tbody>")
    else:
        ISSUES.append('<tbody> not found — add id="patient-table" manually')
else:
    print("ℹ️   id=\"patient-table\" already present — skipped")

# ================================================================
# 7.  JAVASCRIPT — filterPatients + toggleDark + auto-refresh
# ================================================================
JS_BLOCK = """
        <script>
        // ── Patient search filter ──
        function filterPatients() {
            const q = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('#patient-table tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        }

        // ── Dark mode toggle ──
        function toggleDark() {
            document.body.classList.toggle('dark');
            localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
        }
        if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');

        // ── Live stats auto-refresh ──
        async function refreshStats() {
            try {
                const r = await fetch('/stats');
                if (!r.ok) return;
                const d = await r.json();
                document.getElementById('sc-total-val').textContent = d.total_analysed ?? '—';
                document.getElementById('sc-crit-val').textContent  = d.critical_count ?? '—';
                document.getElementById('sc-high-val').textContent  = d.high_count ?? '—';
                document.getElementById('sc-avg-val').textContent   = d.avg_risk_score ?? '—';
            } catch(e) { /* silently skip on error */ }
        }
        refreshStats();
        setInterval(refreshStats, 30000);
        </script>
"""

if 'filterPatients' not in text:
    # Insert just before </body>
    body_close = text.rfind('</body>')
    if body_close != -1:
        text = text[:body_close] + JS_BLOCK + text[body_close:]
        print("✅  filterPatients + toggleDark + auto-refresh JS injected")
    else:
        ISSUES.append('</body> not found — JS block not injected. Add manually.')
else:
    print("ℹ️   filterPatients JS already present — skipped")

# ================================================================
# WRITE + REPORT
# ================================================================
if text == original:
    print("\n⚠️  No changes made — everything was already present or anchors not found.")
else:
    backup = MAIN.with_suffix('.py.bak')
    backup.write_text(original, encoding="utf-8")
    MAIN.write_text(text, encoding="utf-8")
    print(f"\n✅  main.py updated!  (backup saved → {backup.name})")

if ISSUES:
    print("\n⚠️  Manual steps needed:")
    for i, issue in enumerate(ISSUES, 1):
        print(f"  {i}. {issue}")
else:
    print("✅  All features restored — no manual steps needed.")

print("\nNext: uv run python -m uvicorn src.api.main:app --reload --port 8000")
print("      Then open http://localhost:8000/dashboard and verify all 4 stat cards + search appear.\n")
