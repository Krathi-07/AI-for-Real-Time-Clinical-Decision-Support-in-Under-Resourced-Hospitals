from pathlib import Path

text = Path("src/models/early_warning.py").read_text(encoding="utf-8")

old = '        self._calibrated = CalibratedClassifierCV(self._xgb, method="sigmoid", cv="prefit")\n        self._calibrated.fit(X_val, y_val)'
new = '        self._calibrated = CalibratedClassifierCV(self._xgb, method="sigmoid", cv=5)\n        self._calibrated.fit(X_train, y_train)'

if old in text:
    Path("src/models/early_warning.py").write_text(text.replace(old, new), encoding="utf-8")
    print("Patched OK")
else:
    print("ERROR: pattern not found")