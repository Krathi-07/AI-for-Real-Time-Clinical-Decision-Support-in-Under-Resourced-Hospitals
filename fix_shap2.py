from pathlib import Path

text = Path("src/models/early_warning.py").read_text(encoding="utf-8")

old = "        shap_values = self._explainer.shap_values(x)[1][0]  # class-1 (sepsis) SHAP, first row"
new = "        sv = self._explainer.shap_values(x)\n        shap_values = sv[1][0] if isinstance(sv, list) else sv[0]  # handle both output formats"

if old in text:
    Path("src/models/early_warning.py").write_text(text.replace(old, new), encoding="utf-8")
    print("Patched OK")
else:
    print("ERROR: pattern not found")