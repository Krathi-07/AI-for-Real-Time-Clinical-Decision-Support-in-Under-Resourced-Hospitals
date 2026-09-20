# final_fix.py
import py_compile
import re
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# Clear old broken JS blocks
text = re.sub(r'\s*<script>\s*function filterPatients.*?setInterval\(refreshStats,\s*30000\);\s*\}\}\s*</script>', '', text, flags=re.DOTALL)
text = re.sub(r'\s*<script>\s*//\s*── Patient search filter.*?</script>', '', text, flags=re.DOTALL)
print("✅  Old JS cleared")

# Inject working JS before </body>
JS = """
        <script>
        function filterPatients() {{
            var inp = document.getElementById('searchInput');
            if (!inp) return;
            var q = inp.value.toLowerCase();
            document.querySelectorAll('#patient-table tr').forEach(function(row) {{
                row.style.display = !q || row.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
            }});
        }}
        async function refreshStats() {{
            try {{
                var r = await fetch('/stats');
                if (!r.ok) return;
                var d = await r.json();
                ['total_analysed','critical_count','high_count','avg_risk_score'].forEach(function(k,i) {{
                    var ids = ['sc-total-val','sc-crit-val','sc-high-val','sc-avg-val'];
                    var el = document.getElementById(ids[i]);
                    if (el) el.textContent = d[k];
                }});
            }} catch(e) {{ console.log('stats err',e); }}
        }}
        refreshStats();
        setInterval(refreshStats, 30000);
        </script>
"""

pos = text.rfind("</body>")
if pos == -1:
    pos = text.rfind("</html>")
if pos != -1:
    text = text[:pos] + JS + text[pos:]
    print("✅  JS injected")
else:
    print("❌  No </body> found")

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
