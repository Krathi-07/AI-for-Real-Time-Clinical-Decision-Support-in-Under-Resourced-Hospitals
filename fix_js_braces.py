import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)

# Find the body += ''' block start and end
start = None
end = None
for i, line in enumerate(lines):
    if "body += '''" in line:
        start = i
    if start and i > start and "'''" in line:
        end = i
        break

print(f"Notes block: lines {start+1} to {end+1}")

# Replace {{ and }} with { and } only in this block
for i in range(start, end+1):
    if "{{" in lines[i] or "}}" in lines[i]:
        lines[i] = lines[i].replace("{{", "{").replace("}}", "}")

Path("src/api/main.py").write_text("".join(lines), encoding="utf-8")
print("Fixed: {{ }} → { } in body += block")

tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"❌  {e}")
finally:
    tmp.unlink(missing_ok=True)
