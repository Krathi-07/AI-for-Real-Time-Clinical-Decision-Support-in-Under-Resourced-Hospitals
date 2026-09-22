import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# The analyseNote JS needs to be on the patient history page itself
# Find the body += notes card line and add the script inline

INLINE_JS = """
    <script>
    async function analyseNote() {{
        var note = document.getElementById('clinicalNote').value.trim();
        if (!note) {{ alert('Please enter a clinical note.'); return; }}
        var btn = document.querySelector('button[onclick="analyseNote()"]');
        if (btn) {{ btn.textContent = 'Analysing...'; btn.disabled = true; }}
        try {{
            var pid = window.location.pathname.split('/').pop();
            var r = await fetch('/analyse-note/' + pid, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{note: note}})
            }});
            var d = await r.json();
            if (d.error) {{
                document.getElementById('noteResults').innerHTML = '<p style="color:#ef4444">Error: ' + d.error + '</p>';
                document.getElementById('noteResults').style.display = 'block';
                return;
            }}
            function chips(arr, color) {{
                if (!arr || !arr.length) return '<span style="color:#94a3b8;font-size:.8rem">None detected</span>';
                return arr.map(function(x) {{ return '<span style="background:' + color + '20;color:' + color + ';padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block">' + x + '</span>'; }}).join('');
            }}
            var vitals = d.vitals && Object.keys(d.vitals).length
                ? Object.entries(d.vitals).map(function(kv) {{ return '<span style="background:#f0fdf420;color:#16a34a;padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block">' + kv[0] + ': ' + kv[1] + '</span>'; }}).join('')
                : '<span style="color:#94a3b8;font-size:.8rem">None detected</span>';
            document.getElementById('noteResults').innerHTML =
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:.5rem">' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">SYMPTOMS / DISEASES</p>' + chips((d.symptoms||[]).concat(d.diagnoses||[]), '#6c3fcf') + '</div>' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">MEDICATIONS</p>' + chips(d.medications||[], '#0ea5e9') + '</div>' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">VITALS</p>' + vitals + '</div>' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">NEGATED (ruled out)</p>' + chips(d.negated||[], '#94a3b8') + '</div>' +
                '</div><p style="font-size:.72rem;color:#64748b;margin-top:.5rem">Confidence: ' + (d.confidence||'n/a') + ' | Entities: ' + (d.entity_count||0) + '</p>';
            document.getElementById('noteResults').style.display = 'block';
        }} catch(e) {{
            document.getElementById('noteResults').innerHTML = '<p style="color:#ef4444">Error: ' + e + '</p>';
            document.getElementById('noteResults').style.display = 'block';
        }} finally {{
            if (btn) {{ btn.textContent = '\u26a1 Analyse Note'; btn.disabled = false; }}
        }}
    }}
    </script>
"""

# Add inline JS right after the notes card in body +=
TARGET = "    body += '''"
# Find the notes card body += and add script after the closing '''
old = "      <div id='noteResults' style='display:none;margin-top:1rem'></div>\n    </div>\n'''\n    return html"
new = "      <div id='noteResults' style='display:none;margin-top:1rem'></div>\n    </div>\n" + INLINE_JS + "'''\n    return html"

if old in text:
    text = text.replace(old, new)
    print("✅  Inline JS injected into patient history page")
else:
    print("❌  Pattern not found — trying alternate")
    # Find the body += block and append JS to it
    idx = text.find("body += '''")
    if idx != -1:
        close = text.find("'''", idx + 10)
        if close != -1:
            text = text[:close] + INLINE_JS + text[close:]
            print("✅  JS injected via alternate method")

MAIN.write_text(text, encoding="utf-8")
tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"❌  {e}")
finally:
    tmp.unlink(missing_ok=True)
