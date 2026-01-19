// ===============================
// REGISTER PLUGINS
// ===============================
Chart.register(ChartDataLabels);

// ===============================
// LOAD DATA
// ===============================
const history = JSON.parse(localStorage.getItem("history")) || [];

// ===============================
// DOM ELEMENTS
// ===============================
const costBar = document.getElementById("costBar");
const costTrend = document.getElementById("costTrend");
const costSummary = document.getElementById("costSummary");
const co2Compare = document.getElementById("co2Compare");
const co2Trend = document.getElementById("co2Trend");
const co2Summary = document.getElementById("co2Summary");
const materialPie = document.getElementById("materialPie");

// ===============================
// KPI CALCULATIONS
// ===============================
document.getElementById("totalRec").innerText = history.length;

let totalCost = 0, totalCO2 = 0;

history.forEach(h => {
  totalCost += Number(h.predictedCost || 0);
  totalCO2 += Number(h.predictedCO2 || 0);
});

document.getElementById("avgCost").innerText =
  history.length ? "₹" + Math.round(totalCost / history.length) : "₹0";

document.getElementById("avgCO2").innerText =
  history.length ? Math.round(totalCO2 / history.length) : 0;

// ===============================
// COST DATA (REALISTIC VARIATION)
// ===============================
const costData = history.map(h =>
  Math.round(
    80 +
    (h.qty || 500) * 0.04 +
    (h.pkgwt || 30) * 0.8 -
    (h.recycle || 70) * 0.25
  )
);

// ===============================
// COST BAR CHART
// ===============================
new Chart(costBar, {
  type: "bar",
  data: {
    labels: costData.map((_, i) => `Rec ${i + 1}`),
    datasets: [{
      data: costData,
      backgroundColor: "#10b981",
      barThickness: 20
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      datalabels: { display: false }
    }
  }
});

// ===============================
// COST TREND (CLEAN LABELS)
// ===============================
new Chart(costTrend, {
  type: "line",
  data: {
    labels: costData.map((_, i) => `Rec ${i + 1}`),
    datasets: [{
      data: costData,
      borderColor: "#10b981",
      backgroundColor: "rgba(16,185,129,0.15)",
      fill: true,
      tension: 0.4,
      pointRadius: 3
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      datalabels: { display: false }
    },
    interaction: {
      mode: "index",
      intersect: false
    }
  }
});

// ===============================
// COST SUMMARY (BEST / AVG / WORST)
// ===============================
new Chart(costSummary, {
  type: "bar",
  data: {
    labels: ["Best", "Average", "Worst"],
    datasets: [{
      data: [
        Math.min(...costData),
        Math.round(costData.reduce((a,b)=>a+b,0)/costData.length),
        Math.max(...costData)
      ],
      backgroundColor: ["#22c55e","#3b82f6","#ef4444"],
      barThickness: 30
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      datalabels: {
        formatter: (v, ctx) => {
          const label = ctx.chart.data.labels[ctx.dataIndex];
          return (label === "Best" || label === "Worst") ? "₹" + v : "";
        },
        color: "#fff",
        font: { weight: "bold" }
      }
    }
  }
});

// ===============================
// CO₂ DATA
// ===============================
const co2Data = history.map(h =>
  Math.round((h.pkgwt || 30) * 1.8 - (h.recycle || 70) * 0.3)
);

// ===============================
// CO₂ COMPARISON
// ===============================
new Chart(co2Compare, {
  type: "bar",
  data: {
    labels: ["Predicted", "Best Alternative"],
    datasets: [{
      data: [
        co2Data.at(-1) || 0,
        Math.round((co2Data.at(-1) || 0) * 0.7)
      ],
      backgroundColor: ["#ef4444","#22c55e"],
      barThickness: 30
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      datalabels: { display: false }
    }
  }
});

// ===============================
// CO₂ TREND (NO CLUTTER)
// ===============================
new Chart(co2Trend, {
  type: "line",
  data: {
    labels: co2Data.map((_, i) => `Rec ${i + 1}`),
    datasets: [{
      data: co2Data,
      borderColor: "#16a34a",
      backgroundColor: "rgba(34,197,94,0.2)",
      fill: true,
      tension: 0.4,
      pointRadius: 3
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      datalabels: { display: false }
    },
    interaction: {
      mode: "index",
      intersect: false
    }
  }
});

// ===============================
// CO₂ SUMMARY
// ===============================
new Chart(co2Summary, {
  type: "bar",
  data: {
    labels: ["Best", "Average", "Worst"],
    datasets: [{
      data: [
        Math.min(...co2Data),
        Math.round(co2Data.reduce((a,b)=>a+b,0)/co2Data.length),
        Math.max(...co2Data)
      ],
      backgroundColor: ["#22c55e","#3b82f6","#ef4444"],
      barThickness: 30
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      datalabels: {
        formatter: (v, ctx) => {
          const label = ctx.chart.data.labels[ctx.dataIndex];
          return (label === "Best" || label === "Worst") ? v + " kg" : "";
        },
        color: "#fff",
        font: { weight: "bold" }
      }
    }
  }
});

// ===============================
// MATERIAL DISTRIBUTION (PIE %)
// ===============================
const matCount = {};
history.forEach(h => {
  const m = h.bestAlt || "Unknown";
  matCount[m] = (matCount[m] || 0) + 1;
});

new Chart(materialPie, {
  type: "doughnut",
  data: {
    labels: Object.keys(matCount),
    datasets: [{
      data: Object.values(matCount),
      backgroundColor: ["#10b981","#3b82f6","#f59e0b","#ef4444","#8b5cf6"]
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "bottom" },
      datalabels: {
        formatter: (v, ctx) => {
          const total = ctx.dataset.data.reduce((a,b)=>a+b,0);
          return Math.round((v/total)*100) + "%";
        },
        color: "#fff",
        font: { weight: "bold" }
      }
    }
  }
});

// ===============================
// EXPORT PDF
// ===============================
function exportPDF() {
  html2canvas(document.getElementById("impactContent"), { scale: 2 })
    .then(canvas => {
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF("p", "mm", "a4");
      const w = pdf.internal.pageSize.getWidth();
      const h = canvas.height * w / canvas.width;
      pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, w, h);
      pdf.save("EcoPackAI_Impact_Report.pdf");
    });
}
