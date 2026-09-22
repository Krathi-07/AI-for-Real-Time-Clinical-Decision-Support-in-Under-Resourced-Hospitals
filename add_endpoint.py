import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

ENDPOINT = '''
@app.post("/analyse-note/{patient_id}")
async def analyse_note(patient_id: str, request: Request, session: str | None = Cookie(default=None)):
    require_doctor(session)
    data = await request.json()
    note_text = data.get("note", "").strip()
    if not note_text:
        return JSONResponse(content={"error": "No note provided"}, status_code=400)
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from src.note_parser import ClinicalNoteParser
        parser = ClinicalNoteParser()
        result = parser.parse(note_text)
        return JSONResponse(content={
            "symptoms": result.symptoms,
            "diseases": result.diseases,
            "diagnoses": result.diagnoses,
            "medications": result.medications,
            "negated": result.negated_entities,
            "vitals": result.vitals_mentioned,
            "confidence": result.confidence,
            "entity_count": result.entity_count,
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
'''

# Insert before /stats endpoint
target = '@app.get("/stats")'
if target in text:
    text = text.replace(target, ENDPOINT + "\n" + target)
    print("✅  /analyse-note endpoint added")
else:
    print("❌  Could not find /stats anchor")

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
