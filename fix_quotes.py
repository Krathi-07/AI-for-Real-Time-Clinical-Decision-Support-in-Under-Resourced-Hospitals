# fix_quotes.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python fix_quotes.py
#
# Fixes the SyntaxError caused by double-quotes inside the dark-mode button
# being injected into a Python f-string / regular string on line ~234.
# -----------------------------------------------------------------------

import re
from pathlib import Path

MAIN = Path("src/api/main.py")

if not MAIN.exists():
    print("❌  src/api/main.py not found. Run from C:\\Projects\\clinical-ai")
    raise SystemExit(1)

text = MAIN.read_text(encoding="utf-8")

# The broken injection — double-quoted attributes inside a Python string
BAD = """<button onclick="toggleDark()" style="background:#f1f0ff;border:1px solid #c4b5fd;color:#6c3fcf;padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-size:.85rem;">🌙 Dark Mode</button>"""

# Replace all inner double-quotes with single-quotes so Python string stays valid
GOOD = """<button onclick='toggleDark()' style='background:#f1f0ff;border:1px solid #c4b5fd;color:#6c3fcf;padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-size:.85rem;'>🌙 Dark Mode</button>"""

if BAD in text:
    text = text.replace(BAD, GOOD)
    MAIN.write_text(text, encoding="utf-8")
    print("✅  Quote conflict fixed — double-quotes inside button HTML replaced with single-quotes.")
else:
    # Fallback: find any toggleDark button line and fix all double-quotes in it
    lines = text.splitlines(keepends=True)
    changed = False
    for i, line in enumerate(lines):
        if "toggleDark" in line and 'onclick=' in line:
            # Replace " with ' only within the HTML attribute values on this line
            # Strategy: fix onclick="..." and style="..." patterns
            fixed = re.sub(r'onclick="([^"]*)"', r"onclick='\1'", line)
            fixed = re.sub(r'style="([^"]*)"', r"style='\1'", fixed)
            if fixed != line:
                lines[i] = fixed
                changed = True
                print(f"✅  Fixed line {i+1}: {fixed.strip()[:80]}…")
    if changed:
        MAIN.write_text("".join(lines), encoding="utf-8")
        print("✅  main.py saved.")
    else:
        print("⚠️  Could not find the broken toggleDark line automatically.")
        print("    Open main.py, go to line 234, and change any double-quotes")
        print('    inside the button tag to single-quotes. Example:')
        print('    onclick="toggleDark()"  →  onclick=\'toggleDark()\'')

print("\nNow run:")
print("  uv run python -m uvicorn src.api.main:app --reload --port 8000")
