import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# Fix: analysed_at → created_at in the patient-trend endpoint
OLD = """SELECT analysed_at, risk_score, risk_level
                 FROM analyses
                 WHERE patient_id = ?
                 ORDER BY analysed_at ASC
                 LIMIT 20"""

NEW = """SELECT created_at, risk_score, risk_level
                 FROM analyses
                 WHERE patient_id = ?
                 ORDER BY created_at ASC
                 LIMIT 20"""

if OLD in text:
    text = text.replace(OLD, NEW)
    print("✅  Fixed: analysed_at → created_at in patient-trend endpoint")
else:
    print("❌  Pattern not found")

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
