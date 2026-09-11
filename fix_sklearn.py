from pathlib import Path

content = Path('src/models/early_warning.py').read_text(encoding='utf-8')
old = 'from sklearn.calibration import CalibratedClassifierCV, IsotonicCalibration'
new = 'from sklearn.calibration import CalibratedClassifierCV'

if old in content:
    Path('src/models/early_warning.py').write_text(content.replace(old, new), encoding='utf-8')
    print('Fixed OK')
else:
    print('ERROR: pattern not found')