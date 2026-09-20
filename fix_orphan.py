import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# Remove the orphaned broken lines that sit between the two
# filterPatients functions (lines 268-275 in current file)
BAD = """        }}
                var cells = Array.from(row.querySelectorAll('td'));
                var hit = cells.some(function(td) {{
                    return td.textContent.toLowerCase().indexOf(q) >= 0;
                }});
                row.style.display = hit ? '' : 'none';
            }});
        }});
        }}"""

if BAD in text:
    text = text.replace(BAD, "        }}", 1)
    print("✅  Orphaned broken JS lines removed")
else:
    # Fallback: remove by line numbers approach
    lines = text.splitlines(keepends=True)
    new_lines = []
    skip_phrases = [
        "var cells = Array.from(row.querySelectorAll",
        "var hit = cells.some(function(td)",
        "return td.textContent.toLowerCase().indexOf(q) >= 0;",
        "row.style.display = hit ? ",
        "        }});\n",
    ]
    i = 0
    removed = 0
    while i < len(lines):
        line = lines[i]
        # Skip orphaned lines that appear AFTER the closing }} of filterPatients
        # but BEFORE refreshStats
        if any(p in line for p in skip_phrases) and "refreshStats" not in "".join(lines[max(0,i-5):i+5]):
            removed += 1
            i += 1
            continue
        new_lines.append(line)
        i += 1
    text = "".join(new_lines)
    print(f"✅  Removed {removed} orphaned lines via fallback")

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
