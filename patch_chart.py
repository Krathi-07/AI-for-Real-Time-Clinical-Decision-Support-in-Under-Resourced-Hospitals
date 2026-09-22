with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fix chart axis text color for light mode
old_chart = '''                  ticks: {{ color: "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }},
                x: {{
                  title: {{ display: true, text: "Analysis Date", color: "#94a3b8" }},
                  ticks: {{ color: "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}'''

new_chart = '''                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }},
                x: {{
                  title: {{ display: true, text: "Analysis Date", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}'''

old_legend = '''              plugins: {{
                legend: {{ labels: {{ color: "#e2e8f0" }} }},'''

new_legend = '''              plugins: {{
                legend: {{ labels: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#e2e8f0" }} }},'''

old_ytitle = '''                  title: {{ display: true, text: "Risk Score (%)", color: "#94a3b8" }},'''
new_ytitle = '''                  title: {{ display: true, text: "Risk Score (%)", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},'''

count = 0
for old, new in [(old_chart, new_chart), (old_legend, new_legend), (old_ytitle, new_ytitle)]:
    if old in code:
        code = code.replace(old, new)
        count += 1

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
print(f"✅ Chart colors fixed ({count}/3 patches applied)")
