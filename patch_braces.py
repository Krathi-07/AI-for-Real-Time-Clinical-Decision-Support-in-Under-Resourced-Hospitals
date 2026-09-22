with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = """        async function dischargePatient(pid) {
            if (!confirm('Discharge patient ' + pid + '? They will be hidden from active list.')) return;
            var r = await fetch('/discharge/' + pid, {method:'POST'});
            if (r.ok) { location.reload(); }
            else { alert('Could not discharge patient.'); }
        }"""

new = """        async function dischargePatient(pid) {{
            if (!confirm('Discharge patient ' + pid + '? They will be hidden from active list.')) return;
            var r = await fetch('/discharge/' + pid, {{method:'POST'}});
            if (r.ok) {{ location.reload(); }}
            else {{ alert('Could not discharge patient.'); }}
        }}"""

if old in code:
    code = code.replace(old, new)
    print("✅ Fixed JS braces")
else:
    print("❌ Pattern not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
