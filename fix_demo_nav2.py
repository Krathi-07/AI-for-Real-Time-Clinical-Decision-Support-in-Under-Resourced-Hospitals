from pathlib import Path

text = Path("src/dashboard/demo.html").read_text(encoding="utf-8")

old = """<nav>
  <div class="nav-logo"><div class="dot"></div>Clinical AI \u00e2\u0080\u0093 Live Demo</div>
  <div class="nav-right">
    <a href="/dashboard" class="nav-back">Back to Dashboard</a>
    <a href="/logout" class="nav-logout">Logout</a>
  </div>
</nav>"""

new = """<nav>
  <div class="nav-logo"><div class="dot"></div>Clinical AI</div>
  <div class="nav-links">
    <a href="/about">Home</a>
    <a href="/about">About</a>
    <a href="/demo" style="color:var(--cyan)">Live Demo</a>
    <a href="/federated">Federated Learning</a>
    <a href="/audit-page">Audit Log</a>
  </div>
  <div class="nav-right">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()">&#9728; Light</button>
    <a href="/logout" class="nav-logout">Logout</a>
  </div>
</nav>"""

if old in text:
    text = text.replace(old, new)
    print("nav replaced OK")
else:
    print("trying line-based replace")
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if "<nav>" in line:
            start = i
        if "</nav>" in line and start is not None:
            lines[start:i+1] = new.split("\n")
            print(f"replaced lines {start} to {i}")
            break
    text = "\n".join(lines)

# Add nav-links style
if ".nav-links" not in text:
    style = """.nav-links { display:flex; gap:24px; }
.nav-links a { color:var(--muted); text-decoration:none; font-size:0.88rem; font-weight:500; transition:color 0.2s; }
.nav-links a:hover { color:var(--text); }
.theme-btn { background:transparent; border:1px solid var(--border); color:var(--text); padding:5px 14px; border-radius:999px; cursor:pointer; font-size:0.8rem; font-weight:600; font-family:"DM Sans",sans-serif; }
.theme-btn:hover { border-color:var(--cyan); color:var(--cyan); }"""
    text = text.replace("</style>", style + "\n</style>", 1)
    print("styles added")

# Add theme JS before </body>
if "toggleTheme" not in text:
    theme_js = """<script>
function toggleTheme(){
  var b=document.body,btn=document.getElementById("theme-btn");
  if(b.classList.contains("light")){b.classList.remove("light");localStorage.setItem("theme","dark");btn.textContent="\\u2600 Light";}
  else{b.classList.add("light");localStorage.setItem("theme","light");btn.textContent="\\U0001f319 Dark";}
}
(function(){if(localStorage.getItem("theme")==="light"){document.body.classList.add("light");var btn=document.getElementById("theme-btn");if(btn)btn.textContent="\\U0001f319 Dark";}})();
</script>"""
    text = text.replace("</body>", theme_js + "\n</body>")
    print("theme JS added")

Path("src/dashboard/demo.html").write_text(text, encoding="utf-8")
print("demo.html saved OK")