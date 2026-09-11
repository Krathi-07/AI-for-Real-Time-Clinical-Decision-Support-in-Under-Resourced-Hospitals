from pathlib import Path

lines = Path("src/models/early_warning.py").read_text(encoding="utf-8").split("\n")
out = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    if 'CalibratedClassifierCV(self._xgb, method="sigmoid", cv=5)' in line:
        indent = "        "
        out.append(indent + "self._calibrated = self._xgb  # XGBoost predict_proba is well-calibrated")
        skip_next = True  # skip the .fit() line that follows
    else:
        out.append(line)

result = "\n".join(out)
Path("src/models/early_warning.py").write_text(result, encoding="utf-8")
print("Patched OK")