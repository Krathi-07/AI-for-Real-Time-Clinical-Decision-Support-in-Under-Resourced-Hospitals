from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

OLD = '''        return JSONResponse(content={
            "symptoms": result.symptoms,
            "diseases": result.diseases,
            "diagnoses": result.diagnoses,
            "medications": result.medications,
            "negated": result.negated_entities,
            "vitals": result.vitals_mentioned,
            "confidence": result.confidence,
            "entity_count": result.entity_count,
        })'''

NEW = '''        # Convert vitals to plain dict (VitalMention objects are not JSON serializable)
        vitals_dict = {}
        if result.vitals_mentioned:
            for k, v in result.vitals_mentioned.items():
                vitals_dict[str(k)] = str(v) if not isinstance(v, (str, int, float)) else v
        return JSONResponse(content={
            "symptoms": result.symptoms,
            "diseases": result.diseases,
            "diagnoses": result.diagnoses,
            "medications": result.medications,
            "negated": result.negated_entities,
            "vitals": vitals_dict,
            "confidence": str(result.confidence) if result.confidence else "n/a",
            "entity_count": result.entity_count or 0,
        })'''

if OLD in text:
    text = text.replace(OLD, NEW)
    print("✅  VitalMention serialization fixed")
else:
    print("❌  Pattern not found — trying simpler fix")
    text = text.replace(
        '"vitals": result.vitals_mentioned,',
        '"vitals": {str(k): str(v) for k,v in (result.vitals_mentioned or {}).items()},'
    )
    text = text.replace(
        '"confidence": result.confidence,',
        '"confidence": str(result.confidence) if result.confidence else "n/a",'
    )
    text = text.replace(
        '"entity_count": result.entity_count,',
        '"entity_count": result.entity_count or 0,'
    )
    print("✅  Fixed via line replacement")

Path("src/api/main.py").write_text(text, encoding="utf-8")
print("Done")
