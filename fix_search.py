import py_compile
import re
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

OLD_FILTER = """function filterPatients() {{
            var inp = document.getElementById('searchInput');
            if (!inp) return;
            var q = inp.value.toLowerCase();
            document.querySelectorAll('#patient-table tr').forEach(function(row) {{
                row.style.display = !q || row.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
            }});
        }}"""

NEW_FILTER = """function filterPatients() {{
            var inp = document.getElementById('searchInput');
            if (!inp) return;
            var q = inp.value.toLowerCase().trim();
            document.querySelectorAll('#patient-table tr').forEach(function(row) {{
                if (!q) {{ row.style.display = ''; return; }}
                var cells = row.querySelectorAll('td');
                var matched = false;
                cells.forEach(function(td) {{
                    if (td.textContent.toLowerCase().indexOf(q) >= 0) matched = true;
                }});
                row.style.display = matched ? '' : 'none';
            }});
        }}"""

if OLD_FILTER in text:
    text = text.replace(OLD_FILTER, NEW_FILTER)
    print("✅  filterPatients fixed — now searches cell text only")
else:
    print("⚠️  Exact match not found — using regex replace")
    text = re.sub(
        r'function filterPatients\(\) \{\{.*?\}\}',
        NEW_FILTER,
        text, flags=re.DOTALL, count=1
    )
    print("✅  filterPatients replaced via regex")

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
