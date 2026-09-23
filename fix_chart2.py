with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = '                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},\n                   grid:  {{ color: "rgba(148,163,184,0.1)" }}\n                 }},\n                 x: {{\n                   title: {{ display: true, text: "Analysis Date", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},\n                   ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},\n                   grid:  {{ color: "rgba(148,163,184,0.1)" }}'

new = '                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},\n                   grid:  {{ color: "rgba(255,255,255,0.1)" }}\n                 }},\n                 x: {{\n                   title: {{ display: true, text: "Analysis Date", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},\n                   ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},\n                   grid:  {{ color: "rgba(255,255,255,0.1)" }}'

if old in code:
    code = code.replace(old, new)
    print("✅ Chart ticks fixed")
else:
    print("❌ Still not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
