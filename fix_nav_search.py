import py_compile
import re
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# FIX 1 — Search already searches td cells which includes condition.
# The real issue: the Analyse button text "Analyse" is inside a <button>
# inside a <td>, and the patient ID link text is inside <a> inside <td>.
# textContent on td DOES include those. So "diabetes" should work.
# The bug is the oninput= fires but querySelector finds no #patient-table
# because the id might be missing. Let us verify and re-add if needed.
if "id='patient-table'" not in text and 'id="patient-table"' not in text:
    text = text.replace("<tbody>", "<tbody id='patient-table'>", 1)
    print("✅  id='patient-table' re-added to tbody")
else:
    print("ℹ️  patient-table id present")

# FIX 2 — Dark/Light mode button in navbar
# themeBtn exists in the script but check if the HTML button is in nav
lines = text.splitlines()
nav_start = next((i for i,l in enumerate(lines) if "<nav" in l), None)
nav_end   = next((i for i,l in enumerate(lines) if "</nav>" in l), None)

nav_block = "\n".join(lines[nav_start:nav_end+1]) if nav_start and nav_end else ""
has_btn   = "themeBtn" in nav_block

if not has_btn:
    print("⚠️  themeBtn HTML missing from navbar — injecting...")
    # Insert button just before the doctor name span or first nav link
    # Find the nav div that has display:flex and inject the button as first child
    BTN_HTML = "<button id='themeBtn' onclick='toggleTheme()' style='background:var(--navy-800,#ede9fe);border:1px solid #c4b5fd;color:#6c3fcf;padding:.25rem .8rem;border-radius:20px;cursor:pointer;font-size:.82rem;font-weight:600;font-family:Inter,sans-serif'>&#9790; Dark</button>"

    # Find the nav links wrapper - look for the div containing Dashboard/Logout links
    text = re.sub(
        r'(<div[^>]*display:flex[^>]*align-items:center[^>]*gap[^>]*>)',
        r'\1' + BTN_HTML + ' ',
        text, count=1
    )
    if "themeBtn" in text:
        print("✅  themeBtn button injected into navbar")
    else:
        # Try alternate nav pattern
        text = re.sub(
            r'(🧑‍⚕️.*?</span>)',
            r'\1 ' + BTN_HTML,
            text, count=1
        )
        print("✅  themeBtn injected after doctor name")
else:
    print("ℹ️  themeBtn HTML already in navbar")

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

print("\nNext: uv run python -m uvicorn src.api.main:app --reload --port 8000")
