import py_compile
import re
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# Add dark mode button back to navbar if missing
if "themeBtn" not in text:
    # Find the nav links block and insert button before doctor name or first <a>
    BTN = """<button id="themeBtn" onclick="toggleTheme()" style="background:var(--navy-800,#1e1b4b);border:1px solid var(--border,#c4b5fd);color:var(--text,#1e1b4b);padding:.3rem .9rem;border-radius:20px;cursor:pointer;font-size:.82rem;font-weight:600;font-family:Inter,sans-serif">&#9790; Dark</button>"""
    # Insert before the first nav link after the brand
    text = re.sub(r'(<div[^>]*display:flex[^>]*gap[^>]*>)\s*', r'\1' + BTN + '\n    ', text, count=1)
    print("✅  themeBtn re-added")
else:
    print("ℹ️  themeBtn already present")

# Make sure toggleTheme JS exists (it was in the original _base)
if "toggleTheme" not in text:
    TOGGLE_JS = """
        <script>
        (function(){{
          var t=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
          document.documentElement.setAttribute('data-theme',t);
          document.addEventListener('DOMContentLoaded',function(){{
            var btn=document.getElementById('themeBtn');
            if(btn) btn.textContent=t==='dark'?'\\u2600 Light':'\\u263e Dark';
          }});
        }})();
        function toggleTheme(){{
          var cur=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
          document.documentElement.setAttribute('data-theme',cur);
          localStorage.setItem('theme',cur);
          var btn=document.getElementById('themeBtn');
          if(btn) btn.textContent=cur==='dark'?'\\u2600 Light':'\\u263e Dark';
        }}
        </script>
"""
    pos = text.rfind("</body>")
    if pos == -1: pos = text.rfind("</html>")
    if pos != -1:
        text = text[:pos] + TOGGLE_JS + text[pos:]
        print("✅  toggleTheme JS injected")
else:
    # Just fix the label text
    text = re.sub(
        r"btn\.textContent\s*=\s*t\s*===\s*['\"]dark['\"]\s*\?\s*['\"][^'\"]+['\"]\s*:\s*['\"][^'\"]+['\"]",
        "btn.textContent=t==='dark'?'\\u2600 Light':'\\u263e Dark'",
        text
    )
    print("✅  toggleTheme labels updated to ☾/☀")

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
