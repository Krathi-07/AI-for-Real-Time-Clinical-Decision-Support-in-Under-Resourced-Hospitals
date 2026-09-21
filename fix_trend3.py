import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# The trend DB uses analysed_at — we accidentally changed it to created_at
# Change it back to analysed_at for the _get_trend_db() query
text = text.replace(
    '"SELECT created_at, risk_score, risk_level\n                     FROM analyses\n                     WHERE patient_id = ?\n                     ORDER BY created_at ASC',
    '"SELECT analysed_at, risk_score, risk_level\n                     FROM analyses\n                     WHERE patient_id = ?\n                     ORDER BY analysed_at ASC'
)

# Also fix the simple replacement we did earlier (if it hit the trend DB query)
# Find both queries and make sure trend DB uses analysed_at, fallback uses created_at
lines = text.splitlines()
in_trend_db_block = False
fixed = []
for i, line in enumerate(lines):
    # Detect we are inside the _get_trend_db() with block
    if "_get_trend_db()" in line:
        in_trend_db_block = True
    if in_trend_db_block and "created_at" in line:
        line = line.replace("created_at", "analysed_at")
        print(f"✅  Line {i+1} restored to analysed_at: {line.strip()}")
    # Once we hit the fallback sqlite3 block, stop correcting
    if "clinical.db" in line:
        in_trend_db_block = False
    fixed.append(line)

text = "\n".join(fixed)
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

print("\nNow open: http://localhost:8000/patient-trend/PT-20260917-0007")
print("Should return JSON with 3 points")
