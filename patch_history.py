import pathlib
import sys

path = pathlib.Path("src/api/write_main.py")
text = path.read_text(encoding="utf-8")

OLD = '''    <div class="card">
      <h2>Analysis History ({len(analyses)} records)</h2>
      <table>
        <thead><tr><th>Date</th><th>Condition</th><th>Risk</th><th>Actions</th></tr></thead>
        <tbody>
          {rows if rows else "<tr><td colspan='4' style='text-align:center;color:#475569;padding:2rem'>No analyses yet</td></tr>"}
        </tbody>
      </table>
    </div>"""
    return html(_base(patient["full_name"], body, doctor["full_name"]))'''

NEW = '''    <div class="card">
      <h2>Analysis History ({len(analyses)} records)</h2>
      <table>
        <thead><tr><th>Date</th><th>Condition</th><th>Risk</th><th>Actions</th></tr></thead>
        <tbody>
          {rows if rows else "<tr><td colspan='4' style='text-align:center;color:#475569;padding:2rem'>No analyses yet</td></tr>"}
        </tbody>
      </table>
    </div>
    <div class="card" style="margin-top:1.5rem">
      <h2>Risk Trend</h2>
      <div id="ai-summary" style="margin-bottom:1.2rem;padding:1rem;border-radius:8px;
           background:#1e293b;border-left:4px solid #3b82f6;
           color:#e2e8f0;font-size:0.95rem;min-height:2.5rem">
        Loading summary...
      </div>
      <canvas id="trendChart" height="110"></canvas>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
    <script>
    (function() {{
      var PATIENT_ID = "{patient_id}";
      var LEVEL_COLOR = {{
        CRITICAL: "rgba(220,38,38,1)",
        HIGH:     "rgba(234,88,12,1)",
        MEDIUM:   "rgba(234,179,8,1)",
        LOW:      "rgba(34,197,94,1)"
      }};

      function aiSummary(points) {{
        if (!points || points.length === 0) return "No analysis data available yet.";
        if (points.length === 1) {{
          return "First analysis recorded: " + points[0].risk_level + " (" + points[0].risk_score + "%). Monitor closely.";
        }}
        var first = points[0], last = points[points.length - 1];
        var d1 = new Date(first.timestamp), d2 = new Date(last.timestamp);
        var days = Math.round(Math.abs(d2 - d1) / 86400000);
        var dayStr = days === 0 ? "today" : (days === 1 ? "over 1 day" : "over " + days + " days");
        var diff = last.risk_score - first.risk_score;
        if (diff > 5) {{
          return "Risk has worsened from " + first.risk_level + " (" + first.risk_score + "%) to " +
                 last.risk_level + " (" + last.risk_score + "%) " + dayStr + " - immediate intervention recommended.";
        }} else if (diff < -5) {{
          return "Risk has improved from " + first.risk_level + " (" + first.risk_score + "%) to " +
                 last.risk_level + " (" + last.risk_score + "%) " + dayStr + ".";
        }} else {{
          return "Risk remains stable at approximately " + last.risk_score + "% (" + last.risk_level + ") " + dayStr + ".";
        }}
      }}

      fetch("/patient-trend/" + encodeURIComponent(PATIENT_ID))
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
          var points = data.points || [];
          document.getElementById("ai-summary").textContent = aiSummary(points);

          if (points.length === 0) return;

          var labels = points.map(function(p) {{
            var d = new Date(p.timestamp);
            return d.toLocaleDateString([], {{month:"short", day:"numeric"}}) + " " +
                   d.toLocaleTimeString([], {{hour:"2-digit", minute:"2-digit"}});
          }});
          var scores  = points.map(function(p) {{ return p.risk_score; }});
          var colors  = points.map(function(p) {{ return LEVEL_COLOR[p.risk_level] || "#3b82f6"; }});

          new Chart(document.getElementById("trendChart").getContext("2d"), {{
            type: "line",
            data: {{
              labels: labels,
              datasets: [{{
                label: "Risk Score (%)",
                data: scores,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.08)",
                pointBackgroundColor: colors,
                pointBorderColor: colors,
                pointRadius: 7,
                pointHoverRadius: 10,
                borderWidth: 2.5,
                tension: 0.3,
                fill: true
              }}]
            }},
            options: {{
              responsive: true,
              scales: {{
                y: {{
                  min: 0, max: 100,
                  title: {{ display: true, text: "Risk Score (%)", color: "#94a3b8" }},
                  ticks: {{ color: "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }},
                x: {{
                  title: {{ display: true, text: "Analysis Date", color: "#94a3b8" }},
                  ticks: {{ color: "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }}
              }},
              plugins: {{
                legend: {{ labels: {{ color: "#e2e8f0" }} }},
                tooltip: {{
                  callbacks: {{
                    afterLabel: function(ctx) {{
                      return "Level: " + data.points[ctx.dataIndex].risk_level;
                    }}
                  }}
                }}
              }}
            }}
          }});
        }})
        .catch(function() {{
          document.getElementById("ai-summary").textContent = "Could not load trend data.";
        }});
    }})();
    </script>"""
    return html(_base(patient["full_name"], body, doctor["full_name"]))'''

if OLD not in text:
    print("ERROR: target string not found - check indentation")
    sys.exit(1)

patched = text.replace(OLD, NEW, 1)
path.write_text(patched, encoding="utf-8")
print("Patched write_main.py successfully")
