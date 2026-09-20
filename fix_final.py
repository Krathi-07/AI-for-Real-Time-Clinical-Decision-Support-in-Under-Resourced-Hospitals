# -*- coding: utf-8 -*-
# fix_final.py

with open("src/api/main.py", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Fix 1: Fix navbar - replace garbled emoji and fix toggle button text
OLD_NAV = '<h1>\xf0\x9f\x8f\xa5 ClinicalAI \xe2\x80\x93 Decision Support</h1>'
NEW_NAV = '<h1>ClinicalAI — Decision Support</h1>'

# Fix 2: Fix toggle button - use plain text instead of HTML entities
OLD_BTN = """    <button id="themeBtn" onclick="toggleTheme()"
      style="background:var(--navy-800);border:1px solid var(--border);color:var(--text);
             padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-size:.78rem;
             font-weight:600;font-family:Inter,sans-serif;transition:.2s">
      &#9728; Light
    </button>"""

NEW_BTN = """    <button id="themeBtn" onclick="toggleTheme()"
      style="background:var(--navy-800);border:1px solid var(--border);color:var(--text);
             padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-size:.78rem;
             font-weight:600;font-family:Inter,sans-serif;transition:.2s">
      Dark Mode
    </button>"""

# Fix 3: Fix light mode text contrast
OLD_LIGHT = """  [data-theme="light"]{{
    --navy-950:#f0f4ff!important;--navy-900:#ffffff!important;
    --navy-800:#e8edf8!important;--navy-700:#d1daf0!important;
    --text:#0f1c3f!important;--text-muted:#4a6080!important;--border:#c5d0e8!important;
  }}
  [data-theme="light"] .navbar h1{{color:#1d4ed8}}
  [data-theme="light"] .navbar a{{color:#4a6080}}
  [data-theme="light"] .navbar a:hover{{color:#1d4ed8}}
  [data-theme="light"] h1,[data-theme="light"] h2,[data-theme="light"] h3{{color:#0f1c3f}}
  [data-theme="light"] td{{color:#0f1c3f}}
  [data-theme="light"] tr:hover td{{background:#e8edf8}}"""

NEW_LIGHT = """  [data-theme="light"]{{
    --navy-950:#f0f4ff!important;--navy-900:#ffffff!important;
    --navy-800:#e8edf8!important;--navy-700:#d1daf0!important;
    --text:#0f1c3f!important;--text-muted:#4a6080!important;--border:#c5d0e8!important;
  }}
  [data-theme="light"] .navbar{{background:#ffffff;border-bottom:1px solid #c5d0e8}}
  [data-theme="light"] .navbar h1{{color:#1d4ed8!important}}
  [data-theme="light"] .navbar a{{color:#4a6080!important}}
  [data-theme="light"] .navbar a:hover{{color:#1d4ed8!important}}
  [data-theme="light"] h1,[data-theme="light"] h2,[data-theme="light"] h3{{color:#0f1c3f!important}}
  [data-theme="light"] td{{color:#0f1c3f!important}}
  [data-theme="light"] p,[data-theme="light"] span,[data-theme="light"] div{{color:#0f1c3f}}
  [data-theme="light"] tr:hover td{{background:#e8edf8}}
  [data-theme="light"] #themeBtn{{background:#e8edf8;color:#0f1c3f;border-color:#c5d0e8}}"""

fixes = [
    ("navbar h1", OLD_NAV, NEW_NAV),
    ("toggle button", OLD_BTN, NEW_BTN),
    ("light mode", OLD_LIGHT, NEW_LIGHT),
]

ok = True
for name, old, new in fixes:
    if old not in content:
        print(f"ERROR: Could not find {name}")
        ok = False

if ok:
    for name, old, new in fixes:
        content = content.replace(old, new, 1)
    with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)
    print("SUCCESS: All fixes applied.")
    