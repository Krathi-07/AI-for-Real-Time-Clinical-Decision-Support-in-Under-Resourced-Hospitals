import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# The patient_history body ends just before line 849
# Find the return statement and inject notes card into body before it
NOTES_CARD = """
    <div class='card' style='margin-top:1.5rem'>
      <h3 style='font-size:1rem;font-weight:700;margin-bottom:.75rem'>&#129302; AI Clinical Note Analysis</h3>
      <p style='font-size:.82rem;color:var(--text-muted);margin-bottom:.75rem'>
        Type free-text clinical notes. AI will extract symptoms, diagnoses, medications and vitals automatically.
      </p>
      <textarea id='clinicalNote' rows='4'
        placeholder='e.g. 65F with fever, tachycardia. Suspect sepsis. No chest pain. BP 90/60. Started piperacillin-tazobactam.'
        style='width:100%;padding:.75rem;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:.88rem;font-family:Inter,sans-serif;resize:vertical;box-sizing:border-box'
      ></textarea>
      <button onclick='analyseNote()'
        style='margin-top:.75rem;background:#6c3fcf;color:#fff;border:none;padding:.55rem 1.5rem;border-radius:8px;cursor:pointer;font-size:.9rem;font-weight:600'>
        &#9889; Analyse Note
      </button>
      <div id='noteResults' style='display:none;margin-top:1rem'></div>
    </div>
"""

# Find the exact return line for patient_history
TARGET = "    return html(_base(patient[\"full_name\"], body, doctor[\"full_name\"]))"
if TARGET not in text:
    TARGET = "    return html(_base(patient['full_name'], body, doctor['full_name']))"

if TARGET in text:
    # Insert notes card into body just before the return
    # Find where body is last assigned/concatenated before this return
    # Simplest: add to body just before return
    text = text.replace(
        TARGET,
        "    body += '''" + NOTES_CARD + "'''\n" + TARGET
    )
    print("✅  Notes card injected into patient_history body")
else:
    print("❌  Target return not found — trying line number approach")
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if 'return html(_base(patient' in line and 'full_name' in line and i > 690:
            lines.insert(i, "    body += '''" + NOTES_CARD + "'''\n")
            print(f"✅  Notes card inserted before line {i+1}")
            break
    text = "".join(lines)

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
