from pathlib import Path

content = Path('src/api/main.py').read_text(encoding='utf-8')
old = 'import logging'
new = 'import logging\nfrom pathlib import Path'

if old in content and 'from pathlib import Path' not in content:
    Path('src/api/main.py').write_text(content.replace(old, new, 1), encoding='utf-8')
    print('Fixed OK')
else:
    print('Already has Path or pattern not found')