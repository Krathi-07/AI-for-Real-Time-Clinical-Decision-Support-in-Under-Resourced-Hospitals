with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = '''                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                   grid:  {{ color: "rgba(148,163,184,0.1)" }}
                 }},
                 x: {{
                   title: {{ display: true, text: "Analysis Date", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                   ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                   grid:  {{ color: "rgba(148,163,184,0.1)" }}'''

new = '''                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},
                   grid:  {{ color: "rgba(255,255,255,0.1)" }}
                 }},
                 x: {{
                   title: {{ display: true, text: "Analysis Date", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},
                   ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},
                   grid:  {{ color: "rgba(255,255,255,0.1)" }}'''

if old in code:
    code = code.replace(old, new)
    print("✅ Chart ticks fixed to white in dark mode")
else:
    print("❌ Pattern not found")

# Fix legend and y-axis title too
old2 = '''                  title: {{ display: true, text: "Risk Score (%)", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},'''
new2 = '''                  title: {{ display: true, text: "Risk Score (%)", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }},'''

if old2 in code:
    code = code.replace(old2, new2)
    print("✅ Y-axis title fixed")
else:
    print("❌ Y-axis title not found")

old3 = '''                legend: {{ labels: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#e2e8f0" }} }},'''
new3 = '''                legend: {{ labels: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#ffffff" }} }},'''

if old3 in code:
    code = code.replace(old3, new3)
    print("✅ Legend fixed")
else:
    print("❌ Legend not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
