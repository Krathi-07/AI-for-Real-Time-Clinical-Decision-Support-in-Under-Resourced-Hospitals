from pathlib import Path

text = Path("src/models/early_warning.py").read_text(encoding="utf-8")

old = '        shap_values = self._explainer.shap_values(x)[0]  # shape: (N_FEATURES,)'
new = '        shap_values = self._explainer.shap_values(x)[1][0]  # class-1 (sepsis) SHAP, first row'

if old in text:
    Path("src/models/early_warning.py").write_text(text.replace(old, new), encoding="utf-8")
    print("early_warning.py patched OK")
else:
    print("ERROR: pattern not found")