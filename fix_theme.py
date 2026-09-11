from pathlib import Path

# ── Fix index.html ──────────────────────────────────────────────────────────
text = Path("src/dashboard/index.html").read_text(encoding="utf-8", errors="replace")

# Fix encoding artifacts
text = text.replace("ΓÇö", "→")
text = text.replace("\x00", "")

# Add theme toggle script + styles in <head> after <meta charset>
theme_css = """
<style id="theme-vars">
  :root { --bg:#0a0d14; --card:#111827; --card2:#1a2035; --border:#1f2937; --text:#e2e8f0; --muted:#64748b; }
  body.light-theme { --bg:#f0f4f8; --card:#ffffff; --card2:#f8fafc; --border:#e2e8f0; --text:#0f172a; --muted:#64748b; }
  .theme-toggle-btn {
    position:fixed; bottom:24px; right:24px; z-index:9999;
    background:var(--card); border:1px solid var(--border);
    color:var(--text); padding:10px 18px; border-radius:999px;
    cursor:pointer; font-size:0.85rem; font-weight:600;
    box-shadow:0 4px 12px rgba(0,0,0,0.3); transition:all 0.2s;
    font-family:inherit;
  }
  .theme-toggle-btn:hover { border-color:#06b6d4; color:#06b6d4; }
</style>
<script>
  (function(){
    var t = localStorage.getItem("theme") || "dark";
    if(t === "light") document.documentElement.classList.add("light-theme-pre");
  })();
</script>
"""

theme_js = """
<button class="theme-toggle-btn" onclick="toggleTheme()" id="theme-btn">☀ Light Mode</button>
<script>
function toggleTheme() {
  var body = document.body;
  var btn = document.getElementById("theme-btn");
  if(body.classList.contains("light-theme")) {
    body.classList.remove("light-theme");
    localStorage.setItem("theme","dark");
    btn.textContent = "☀ Light Mode";
  } else {
    body.classList.add("light-theme");
    localStorage.setItem("theme","light");
    btn.textContent = "🌙 Dark Mode";
  }
}
// Apply saved theme on load
(function(){
  var t = localStorage.getItem("theme") || "dark";
  if(t === "light") {
    document.body.classList.add("light-theme");
    var btn = document.getElementById("theme-btn");
    if(btn) btn.textContent = "🌙 Dark Mode";
  }
})();
</script>
"""

# Inject CSS before </head>
if "</head>" in text:
    text = text.replace("</head>", theme_css + "</head>", 1)

# Inject JS button before </body>
if "</body>" in text:
    text = text.replace("</body>", theme_js + "</body>", 1)

Path("src/dashboard/index.html").write_text(text, encoding="utf-8")
print("index.html fixed OK")

# ── Fix demo.html ───────────────────────────────────────────────────────────
demo = Path("src/dashboard/demo.html").read_text(encoding="utf-8", errors="replace")

demo_theme_js = """
<button class="theme-toggle-btn" onclick="toggleTheme()" id="theme-btn">☀ Light Mode</button>
<script>
function toggleTheme() {
  var body = document.body;
  var btn = document.getElementById("theme-btn");
  if(body.classList.contains("light-theme")) {
    body.classList.remove("light-theme");
    localStorage.setItem("theme","dark");
    btn.textContent = "☀ Light Mode";
  } else {
    body.classList.add("light-theme");
    localStorage.setItem("theme","light");
    btn.textContent = "🌙 Dark Mode";
  }
}
(function(){
  var t = localStorage.getItem("theme") || "dark";
  if(t === "light") {
    document.body.classList.add("light-theme");
    var btn = document.getElementById("theme-btn");
    if(btn) btn.textContent = "🌙 Dark Mode";
  }
})();
</script>
"""

demo_theme_css = """
<style id="theme-vars">
  body.light-theme { --bg:#f0f4f8; --card:#ffffff; --card2:#f8fafc; --border:#e2e8f0; --text:#0f172a; --muted:#64748b; }
  .theme-toggle-btn {
    position:fixed; bottom:24px; right:24px; z-index:9999;
    background:var(--card); border:1px solid var(--border);
    color:var(--text); padding:10px 18px; border-radius:999px;
    cursor:pointer; font-size:0.85rem; font-weight:600;
    box-shadow:0 4px 12px rgba(0,0,0,0.3); transition:all 0.2s;
    font-family:"DM Sans",sans-serif;
  }
  .theme-toggle-btn:hover { border-color:#06b6d4; color:#06b6d4; }
</style>
"""

if "</head>" in demo:
    demo = demo.replace("</head>", demo_theme_css + "</head>", 1)
if "</body>" in demo:
    demo = demo.replace("</body>", demo_theme_js + "</body>", 1)

Path("src/dashboard/demo.html").write_text(demo, encoding="utf-8")
print("demo.html fixed OK")