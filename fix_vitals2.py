from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

OLD = '''        # Convert vitals to plain dict (VitalMention objects are not JSON serializable)
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

NEW = '''        # Safely serialize all fields
        def to_str_list(x):
            if not x: return []
            return [str(i) for i in x]
        def safe_vitals(v):
            if not v: return {}
            if isinstance(v, dict):
                return {str(k): str(val) for k, val in v.items()}
            if isinstance(v, list):
                out = {}
                for item in v:
                    if hasattr(item, "__dict__"):
                        d = item.__dict__
                        key = str(d.get("name", d.get("type", str(item))))
                        val = str(d.get("value", d.get("raw", str(item))))
                        out[key] = val
                    elif hasattr(item, "name"):
                        out[str(item.name)] = str(getattr(item, "value", item))
                    else:
                        out[str(item)] = str(item)
                return out
            return {}
        return JSONResponse(content={
            "symptoms":  to_str_list(result.symptoms),
            "diseases":  to_str_list(result.diseases),
            "diagnoses": to_str_list(result.diagnoses),
            "medications": to_str_list(result.medications),
            "negated":   to_str_list(result.negated_entities),
            "vitals":    safe_vitals(result.vitals_mentioned),
            "confidence": str(result.confidence) if result.confidence else "n/a",
            "entity_count": int(result.entity_count or 0),
        })'''

if OLD in text:
    text = text.replace(OLD, NEW)
    print("✅  Fixed")
else:
    # Direct replacement of the vitals line only
    text = text.replace(
        '"vitals": {str(k): str(v) for k,v in (result.vitals_mentioned or {}).items()},',
        '"vitals": ({str(k):str(v) for k,v in result.vitals_mentioned.items()} if isinstance(result.vitals_mentioned,dict) else {str(getattr(i,"name",i)):str(getattr(i,"value",i)) for i in (result.vitals_mentioned or [])}),',
    )
    print("✅  Fixed via line replacement")

Path("src/api/main.py").write_text(text, encoding="utf-8")
print("Saved")
