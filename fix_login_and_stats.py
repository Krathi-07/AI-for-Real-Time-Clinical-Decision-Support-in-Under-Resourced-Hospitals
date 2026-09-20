# fix_login_and_stats.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python fix_login_and_stats.py

import re
from pathlib import Path

# ================================================================
# FIX 1 — src/dashboard/login.html
# Remove the dark/light toggle button
# Left-align the left panel feature list
# ================================================================

LOGIN = Path("src/dashboard/login.html")
if not LOGIN.exists():
    # Try alternate path
    for p in Path("src").rglob("login.html"):
        LOGIN = p
        break

if not LOGIN.exists():
    print("❌  login.html not found — searching...")
    for p in Path(".").rglob("login.html"):
        print(f"   Found: {p}")
else:
    print(f"✅  Found login.html at: {LOGIN}")
    html = LOGIN.read_text(encoding="utf-8")

    # --- Remove the dark toggle button (top-right pill) ---
    # It's typically a <button> or <div> with toggleTheme/toggleDark
    original_len = len(html)

    # Remove any fixed-position theme toggle div
    html = re.sub(
        r'<div[^>]*style=["\'][^"\']*position\s*:\s*fixed[^"\']*["\'][^>]*>.*?</div>\s*',
        '', html, flags=re.DOTALL | re.IGNORECASE
    )

    # Remove standalone theme toggle buttons
    html = re.sub(
        r'<button[^>]*(toggleTheme|toggleDark|themeBtn)[^>]*>.*?</button>\s*',
        '', html, flags=re.DOTALL | re.IGNORECASE
    )

    # Remove by id
    html = re.sub(
        r'<button[^>]*id=["\']themeBtn["\'][^>]*>.*?</button>\s*',
        '', html, flags=re.DOTALL | re.IGNORECASE
    )

    if len(html) < original_len:
        print("✅  Dark toggle button removed from login.html")
    else:
        print("⚠️  Button not found by regex — trying line-by-line")
        lines = html.splitlines()
        new_lines = []
        skip = False
        for line in lines:
            if ("themeBtn" in line or "toggleTheme" in line or
                    "toggleDark" in line or
                    ("Dark" in line and "button" in line.lower() and "position:fixed" in line.replace(" ", ""))):
                skip = True
            if skip:
                # Skip until we close the element
                if "</button>" in line or "</div>" in line:
                    skip = False
                continue
            new_lines.append(line)
        html = "\n".join(new_lines)
        print("✅  Attempted line-by-line removal")

    # --- Left-align the left panel feature list ---
    # Features are in a div — add text-align:left
    # Look for the features container and patch it
    html = re.sub(
        r'(class=["\']features?["\'])',
        r'\1 style="text-align:left"',
        html
    )
    # Also patch any centred feature items
    html = re.sub(
        r'(text-align\s*:\s*center\s*;?\s*)(.*?feature)',
        r'text-align:left;\2',
        html, flags=re.DOTALL
    )

    # Direct approach: find the left panel wrapper and ensure left alignment
    # Add a <style> patch to the <head>
    LEFT_ALIGN_CSS = """
    <style>
      /* Left-align login page left panel */
      .left-panel, .features, .feature-list, .hero-features { text-align: left !important; }
      .left-panel *, .features *, .feature-item { text-align: left !important; }
    </style>
    """
    if "left-panel" in html or "features" in html:
        html = html.replace("</head>", LEFT_ALIGN_CSS + "</head>", 1)
        print("✅  Left-align CSS injected into login.html <head>")

    LOGIN.write_text(html, encoding="utf-8")
    print("✅  login.html saved")

    # Show what the button area looks like now
    print("\n── First 60 lines of login.html after fix ──")
    for i, line in enumerate(html.splitlines()[:60], 1):
        if any(k in line for k in ["button", "Dark", "toggle", "theme", "fixed"]):
            print(f"{i:4d}  >>> {line}")

# ================================================================
# FIX 2 — main.py: move stat cards OUT of <h2> tag
# Currently: <h2>\n  <div class='stats-row'>...</div>\nYour Patients</h2>
# Fix:       <div class='stats-row'>...</div>\n<h2>Your Patients</h2>
# ================================================================

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# The broken pattern (stat cards injected inside h2)
OLD_H2 = """<h2>
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
Your Patients</h2>"""

NEW_H2 = """<!-- Live stats -->
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
              <h3 style='font-size:1.1rem;font-weight:700;margin-bottom:.75rem'>Your Patients</h3>"""

if OLD_H2 in text:
    text = text.replace(OLD_H2, NEW_H2)
    MAIN.write_text(text, encoding="utf-8")
    print("\n✅  Stat cards moved outside <h2> tag in main.py")
else:
    # Fallback: use regex
    new = re.sub(
        r'<h2>\s*<!-- Live stats -->.*?</div>\s*Your Patients</h2>',
        NEW_H2,
        text,
        flags=re.DOTALL
    )
    if new != text:
        MAIN.write_text(new, encoding="utf-8")
        print("\n✅  Stat cards fixed via regex")
    else:
        print("\n⚠️  Could not auto-fix h2 wrapping — checking current state...")
        # Find and show the area around 'Your Patients'
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "Your Patients" in line or "stats-row" in line:
                start = max(0, i-2)
                end = min(len(lines), i+5)
                for j in range(start, end):
                    print(f"  {j+1:4d}  {lines[j]}")
                print()

# ── Syntax check ─────────────────────────────────────────────────
import py_compile
import shutil
import tempfile

tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  main.py syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"❌  Syntax error: {e}")
finally:
    tmp.unlink(missing_ok=True)

print("\nNext:")
print("  uv run python -m uvicorn src.api.main:app --reload --port 8000")
