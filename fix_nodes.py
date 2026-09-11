from pathlib import Path

text = Path("src/agent/nodes.py").read_text(encoding="utf-8")

old = "    model = _get_warning_model()\n    prediction = model.predict(features)"
new = """    model = _get_warning_model()
    # Derive pulse_pressure (systolic - diastolic) — required 12th feature
    sbp = features.get("systolic_bp", -1.0)
    dbp = features.get("diastolic_bp", -1.0)
    if sbp > 0 and dbp > 0:
        features = dict(features, pulse_pressure=sbp - dbp)
    prediction = model.predict(features)"""

if old in text:
    Path("src/agent/nodes.py").write_text(text.replace(old, new), encoding="utf-8")
    print("nodes.py patched OK")
else:
    print("ERROR: pattern not found - paste nodes.py content")