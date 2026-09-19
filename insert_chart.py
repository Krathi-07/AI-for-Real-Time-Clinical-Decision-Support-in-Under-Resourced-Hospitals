# insert_chart.py
MARKER = "<footer>"

CHART_HTML = """
<section id="risk-trend" style="padding:40px 20px;max-width:900px;margin:0 auto;">
  <h2 style="text-align:center;margin-bottom:6px;">📈 Patient Risk Trend</h2>
  <p style="text-align:center;color:var(--text-muted);margin-bottom:20px;font-size:0.9rem;">
    Track how a patient's sepsis risk score changes across visits
  </p>

  <div style="display:flex;gap:10px;justify-content:center;margin-bottom:24px;">
    <input
      id="trend-patient-id"
      type="text"
      placeholder="Enter Patient ID e.g. P001"
      style="padding:10px 14px;border-radius:8px;border:1px solid var(--border);
             background:var(--card-bg);color:var(--text);font-size:0.95rem;width:260px;"
    />
    <button
      onclick="loadTrend()"
      style="padding:10px 22px;border-radius:8px;border:none;
             background:var(--accent);color:#fff;font-weight:700;
             cursor:pointer;font-size:0.95rem;">
      Load Trend
    </button>
  </div>

  <div id="trend-status" style="text-align:center;color:var(--text-muted);
       font-size:0.88rem;margin-bottom:12px;min-height:20px;"></div>

  <div style="background:var(--card-bg);border-radius:12px;
              border:1px solid var(--border);padding:24px;">
    <canvas id="trendChart" height="100"></canvas>
  </div>
</section>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
var trendChartInstance = null;

async function loadTrend() {
  var pid = document.getElementById("trend-patient-id").value.trim();
  var status = document.getElementById("trend-status");

  if (!pid) {
    status.textContent = "⚠️ Please enter a Patient ID.";
    return;
  }

  status.textContent = "⏳ Loading...";

  try {
    var res = await fetch("/patient-trend/" + encodeURIComponent(pid));
    if (!res.ok) {
      status.textContent = "❌ Error: " + res.status;
      return;
    }
    var data = await res.json();

    if (!data.points || data.points.length === 0) {
      status.textContent = "No trend data found for patient " + pid + ". Run an analysis first.";
      return;
    }

    status.textContent = "✅ " + data.points.length + " data point(s) loaded for " + pid;

    var labels = data.points.map(function(p) {
      var d = new Date(p.timestamp);
      return d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
    });

    var scores = data.points.map(function(p) { return p.risk_score; });

    var colors = data.points.map(function(p) {
      if (p.risk_level === "CRITICAL") return "rgba(220,38,38,1)";
      if (p.risk_level === "HIGH")     return "rgba(234,88,12,1)";
      if (p.risk_level === "MEDIUM")   return "rgba(234,179,8,1)";
      return "rgba(34,197,94,1)";
    });

    if (trendChartInstance) {
      trendChartInstance.destroy();
    }

    var ctx = document.getElementById("trendChart").getContext("2d");
    trendChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Sepsis Risk Score (%)",
          data: scores,
          borderColor: "rgba(99,102,241,1)",
          backgroundColor: "rgba(99,102,241,0.1)",
          pointBackgroundColor: colors,
          pointBorderColor: colors,
          pointRadius: 7,
          pointHoverRadius: 9,
          borderWidth: 2.5,
          tension: 0.3,
          fill: true,
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            min: 0,
            max: 100,
            title: { display: true, text: "Risk Score (%)" },
            grid: { color: "rgba(128,128,128,0.15)" }
          },
          x: {
            title: { display: true, text: "Analysis Time" },
            grid: { color: "rgba(128,128,128,0.15)" }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              afterLabel: function(ctx) {
                return "Level: " + data.points[ctx.dataIndex].risk_level;
              }
            }
          }
        }
      }
    });

  } catch(e) {
    status.textContent = "❌ Failed to load trend: " + e.message;
  }
}
</script>

"""

with open("src/dashboard/index.html", "r", encoding="utf-8") as f:
    content = f.read()

if MARKER not in content:
    print("ERROR: Could not find <footer> tag in index.html")
else:
    new_content = content.replace(MARKER, CHART_HTML + MARKER, 1)
    with open("src/dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: Chart section inserted before <footer>")
    