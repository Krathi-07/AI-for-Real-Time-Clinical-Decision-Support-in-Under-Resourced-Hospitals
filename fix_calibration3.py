from pathlib import Path

text = Path("src/models/early_warning.py").read_text(encoding="utf-8")

old = """        # Platt calibration on validation set
        # cv="prefit" means "the classifier is already trained, just fit the calibration layer"
        self._calibrated = CalibratedClassifierCV(self._xgb, method="sigmoid", cv=5)
        self._calibrated.fit(X_train, y_train)

        # SHAP explainer \xe2\x80\x94 TreeExplainer is exact (not approximate) for XGBoost
        self._explainer = shap.TreeExplainer(self._xgb.get_booster())

        # Evaluation
        train_proba = self._calibrated.predict_proba(X_train)[:, 1]
        val_proba   = self._calibrated.predict_proba(X_val)[:, 1]"""

new = """        # Use XGBoost's built-in probability output directly (no separate calibration)
        self._calibrated = self._xgb  # alias so rest of code works unchanged

        # SHAP explainer \xe2\x80\x94 TreeExplainer is exact (not approximate) for XGBoost
        self._explainer = shap.TreeExplainer(self._xgb.get_booster())

        # Evaluation
        train_proba = self._xgb.predict_proba(X_train)[:, 1]
        val_proba   = self._xgb.predict_proba(X_val)[:, 1]"""

if old in text:
    Path("src/models/early_warning.py").write_text(text.replace(old, new), encoding="utf-8")
    print("Patched OK")
else:
    print("ERROR: pattern not found - trying alternate")
    # Try finding just the calibration lines
    if "CalibratedClassifierCV" in text:
        print("CalibratedClassifierCV found in file")
    else:
        print("CalibratedClassifierCV NOT found")