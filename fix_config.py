import pathlib

f = pathlib.Path(r'C:\Projects\clinical-ai\.venv\Lib\site-packages\en_ner_bc5cdr_md\en_ner_bc5cdr_md-0.5.4\config.cfg')
text = f.read_text(encoding='utf-8')
text = text.replace('include_static_vectors = "True"', 'include_static_vectors = true')
text = text.replace('include_static_vectors = "False"', 'include_static_vectors = false')
f.write_text(text, encoding='utf-8')
print('Done')
for line in f.read_text().splitlines():
    if 'include_static' in line:
        print(repr(line))
