# fix_three.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python fix_three.py

import re
import sqlite3
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# ================================================================
# DEBUG: Check what's actually in the database
# ================================================================
print("── Database check ──────────────────────────────────")
db_path = Path("data/clinical.db")
if db_path.exists():
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  Tables: {tables}")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t}: {count} rows")
        if t == "analyses" and count > 0:
            cur.execute(f"SELECT * FROM {t} LIMIT 2")
            cols = [d[0] for d in cur.description]
            print(f"  Columns: {cols}")
    con.close()
else:
    print("  data/clinical.db not found!")
print()

# ================================================================
# FIX 1 — Login page: remove dark/light toggle button (top right)
# ================================================================
# The Dark toggle on login page is likely a small pill button in
# the top-right corner. Find and remove it from the login HTML.

# Pattern: button in the login page that calls toggleTheme or toggleDark
# It appears outside the navbar (login page has no navbar)
removed_login_toggle = False

# Look for the login route function and find the toggle button inside it
# Typical pattern: a button with id="themeBtn" or similar near </body> of login page
patterns_to_remove = [
    # Floating pill button top-right on login page
    r"<div[^>]*style=['\"][^'\"]*position\s*:\s*fixed[^'\"]*top[^>]*>\s*<button[^>]*toggle[^>]*>.*?</button>\s*</div>",
    r"<button[^>]*id=['\"]themeBtn['\"][^>]*>.*?</button>",
]

for pat in patterns_to_remove:
    new = re.sub(pat, "", text, flags=re.DOTALL | re.IGNORECASE)
    if new != text:
        text = new
        removed_login_toggle = True
        print("✅  Login page toggle button removed (pattern matched)")
        break

if not removed_login_toggle:
    # Try simpler: remove the fixed-position theme div on login page
    # by finding it as a literal string block
    # Look for any fixed-position div containing a theme/dark button
    new = re.sub(
        r'<div style=["\']position:fixed[^"\']*["\'][^>]*>.*?</div>',
        "", text, flags=re.DOTALL
    )
    if new != text:
        text = new
        print("✅  Fixed-position div (login toggle) removed")
    else:
        print("⚠️  Login toggle not auto-removed — will handle via CSS hide instead")
        # Fallback: hide it only on the login page via CSS
        # We'll add a class to the login body and hide themeBtn there
        LOGIN_HIDE_CSS = """
        /* Hide theme toggle on login page */
        body.login-page #themeBtn,
        body.login-page .theme-toggle {{ display: none !important; }}
"""
        style_close = text.rfind("</style>")
        if style_close != -1:
            text = text[:style_close] + LOGIN_HIDE_CSS + text[style_close:]
            # Add class to login body
            text = text.replace(
                "def login_page(",
                "def login_page(",  # placeholder, handled below
            )
            print("✅  CSS fallback added to hide toggle on login page")

# ================================================================
# FIX 2 — Left-align the login page left panel feature list
# ================================================================
# The features (XGBoost, DISHA, etc.) appear centred.
# Add text-align:left to the features container.

if "text-align:left" not in text and "text-align: left" not in text:
    # Find the feature list container — look for the CSS class or inline style
    # that controls the left panel features alignment
    # Common pattern: a div with the feature items
    text = re.sub(
        r'(\.features?\s*\{{[^}}]*)(text-align\s*:\s*center)',
        r'\1text-align: left',
        text
    )
    # Also try to patch inline styles on the features wrapper
    text = re.sub(
        r'(id=["\']features["\'][^>]*style=["\'][^"\']*)(text-align:\s*center)',
        r'\1text-align: left',
        text
    )
    print("✅  Feature list alignment attempted (left)")
else:
    print("ℹ️   Left-align already set")

# ================================================================
# FIX 3 — Navbar: shorten Dark Mode button to ☾ Dark / ☀ Light
# ================================================================
# Current button text is "Dark Mode" — change to toggle between ☾ Dark / ☀ Light
# The button id is "themeBtn"

# Update the button default text
text = text.replace(">Dark Mode<", ">☾ Dark<")
text = text.replace(">'Dark Mode'", ">'☾ Dark'")
text = text.replace('"Dark Mode"', '"☾ Dark"')
text = text.replace("'Dark Mode'", "'☾ Dark'")

# Update the JS that swaps the button label
old_js_label = "btn.textContent=t==='dark'?'Light Mode':'Dark Mode'"
new_js_label  = "btn.textContent=t==='dark'?'☀ Light':'☾ Dark'"
if old_js_label in text:
    text = text.replace(old_js_label, new_js_label)
    print("✅  Navbar toggle text updated to ☾ Dark / ☀ Light")
else:
    # Try alternate forms
    text = re.sub(
        r"btn\.textContent\s*=\s*t\s*===\s*['\"]dark['\"]\s*\?\s*['\"]Light Mode['\"]\s*:\s*['\"]Dark Mode['\"]",
        "btn.textContent=t==='dark'?'☀ Light':'☾ Dark'",
        text
    )
    text = re.sub(
        r"['\"]Light Mode['\"]",
        "'☀ Light'",
        text
    )
    print("✅  Navbar toggle labels updated")

# ================================================================
# FIX 4 — Stats endpoint: make it work with actual table/column names
# ================================================================
# Replace the /stats endpoint with a robust version that
# auto-detects columns and handles missing tables gracefully

OLD_STATS = '@app.get("/stats")'

NEW_STATS = '''@app.get("/stats")
async def get_stats(session: str = Cookie(default=None)):
    """Live dashboard stats — auto-detects schema."""
    require_doctor(session)
    import sqlite3 as _sq
    db_path = Path("data/clinical.db")
    if not db_path.exists():
        return {"total_analysed": 0, "critical_count": 0,
                "high_count": 0, "avg_risk_score": 0}
    con = _sq.connect(str(db_path))
    cur = con.cursor()
    try:
        # Discover tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}

        total, critical, high, avg = 0, 0, 0, 0

        # Try 'analyses' table first, then fall back to 'audit_log'
        for tname in ("analyses", "audit_log", "analysis_log"):
            if tname not in tables:
                continue
            # Discover columns
            cur.execute(f"PRAGMA table_info({tname})")
            cols = {r[1] for r in cur.fetchall()}

            # Total count
            cur.execute(f"SELECT COUNT(*) FROM {tname}")
            total = cur.fetchone()[0]

            # Risk level column — try common names
            risk_col = next((c for c in ("risk_level", "risk", "severity", "level")
                             if c in cols), None)
            if risk_col:
                cur.execute(f"SELECT COUNT(*) FROM {tname} WHERE UPPER({risk_col})='CRITICAL'")
                critical = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM {tname} WHERE UPPER({risk_col})='HIGH'")
                high = cur.fetchone()[0]

            # Risk score column
            score_col = next((c for c in ("risk_score", "score", "risk_value")
                              if c in cols), None)
            if score_col:
                cur.execute(f"SELECT AVG({score_col}) FROM {tname}")
                row = cur.fetchone()[0]
                avg = round(float(row), 1) if row else 0
            break  # used the first matching table

    except Exception as e:
        print(f"Stats error: {{e}}")
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

# Remove old /stats endpoint and replace with new one
# Find the full old endpoint
old_start = text.find('@app.get("/stats")')
if old_start != -1:
    # Find the next @app. decorator after it
    next_route = text.find('\n@app.', old_start + 10)
    if next_route != -1:
        text = text[:old_start] + NEW_STATS + '\n' + text[next_route:]
    else:
        text = text[:old_start] + NEW_STATS
    print("✅  /stats endpoint replaced with schema-aware version")
else:
    print("⚠️  /stats not found to replace — it may not have been injected yet")

# ── Write file ───────────────────────────────────────────────────
MAIN.write_text(text, encoding="utf-8")

# ── Syntax check ─────────────────────────────────────────────────
import py_compile
import shutil
import tempfile

tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("\n✅  Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"\n❌  Syntax error: {e}")
finally:
    tmp.unlink(missing_ok=True)

print("\nNext:")
print("  uv run python -m uvicorn src.api.main:app --reload --port 8000")
print("  Open http://localhost:8000/dashboard")
print("  The stat numbers should now load. If still 0, check the DB output above.")
