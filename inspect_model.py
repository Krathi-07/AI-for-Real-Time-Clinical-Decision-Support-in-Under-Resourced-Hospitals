from src.models.early_warning import EarlyWarningSepsis
e = EarlyWarningSepsis()
e.train_on_synthetic_data()
print('Attributes:', [a for a in dir(e) if not a.startswith('__')])
