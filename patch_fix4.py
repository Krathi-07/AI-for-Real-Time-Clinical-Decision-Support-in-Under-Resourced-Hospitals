with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = """        refreshStats();
        setInterval(refreshStats, 30000);"""

new = """        async function dischargePatient(pid) {
            if (!confirm('Discharge patient ' + pid + '? They will be hidden from active list.')) return;
            var r = await fetch('/discharge/' + pid, {method:'POST'});
            if (r.ok) { location.reload(); }
            else { alert('Could not discharge patient.'); }
        }
        refreshStats();
        setInterval(refreshStats, 30000);"""

if old in code:
    code = code.replace(old, new, 1)
    # Also update refreshStats to show discharged count
    code = code.replace(
        "                if (el) el.textContent = d[k];\n                });\n            } catch(e) { console.log('stats err',e); }",
        "                if (el) el.textContent = d[k];\n                });\n                var disc = document.getElementById('sc-disc-val');\n                if (disc && d.discharged_count !== undefined) disc.textContent = d.discharged_count;\n            } catch(e) { console.log('stats err',e); }"
    )
    print("✅ Fix 4: Discharge JS added")
else:
    print("❌ Pattern not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
