document.addEventListener("DOMContentLoaded", function () {

  Chart.register(ChartDataLabels);

  const history = JSON.parse(localStorage.getItem("history")) || [];

  // ===== NO DATA =====
  if (history.length === 0) {
    document.getElementById("impactContent").innerHTML = `
      <div style="text-align:center; margin-top:100px;">
        <h2>⚠️ No Data Yet</h2>
        <p>Please go to Dashboard and click "Get Recommendation"</p>
      </div>
    `;
    return;
  }

  // ===== CANVAS ELEMENTS =====
  const costBar = document.getElementById("costBar");
  const costTrend = document.getElementById("costTrend");
  const costSummary = document.getElementById("costSummary");
  const co2Compare = document.getElementById("co2Compare");
  const co2Trend = document.getElementById("co2Trend");
  const co2Summary = document.getElementById("co2Summary");
  const materialPie = document.getElementById("materialPie");

  // ================= KPI =================
  document.getElementById("totalRec").innerText = history.length;

  let totalCost = 0;
  let totalCO2 = 0;

  history.forEach(h => {
    totalCost += Number(h.predictedCost || 0);
    totalCO2 += Number(h.predictedCO2 || 0);
  });

  document.getElementById("avgCost").innerText =
    "₹" + (totalCost / history.length).toFixed(2);

  document.getElementById("avgCO2").innerText =
    (totalCO2 / history.length).toFixed(2);

  // ================= DATA =================
  const recent = history.slice(0, 8).reverse(); // last 8 only

  const costData = recent.map(h => Number(h.predictedCost || 0));
  const co2Data = recent.map(h => Number(h.predictedCO2 || 0));
  const labels = recent.map((_, i) => `Rec ${i + 1}`);

  const format = arr => arr.map(v => Number(v.toFixed(2)));

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => ctx.raw.toFixed(2)
        }
      },
      datalabels: { display: false }
    },
    scales: {
      y: {
        ticks: {
          callback: v => Number(v).toFixed(2)
        }
      }
    }
  };

  // ================= SAFE VALUES =================
  const safeCostMin = costData.length ? Math.min(...costData) : 0;
  const safeCostMax = costData.length ? Math.max(...costData) : 0;
  const safeCostAvg = costData.length
    ? costData.reduce((a,b)=>a+b,0)/costData.length
    : 0;

  const safeCO2Min = co2Data.length ? Math.min(...co2Data) : 0;
  const safeCO2Max = co2Data.length ? Math.max(...co2Data) : 0;
  const safeCO2Avg = co2Data.length
    ? co2Data.reduce((a,b)=>a+b,0)/co2Data.length
    : 0;

  const lastCO2 = co2Data.length ? co2Data[co2Data.length - 1] : 0;

  // ================= COST IMPACT =================
  new Chart(costBar, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: format(costData),
        backgroundColor: "#10b981"
      }]
    },
    options
  });

  // ================= COST TREND =================
  new Chart(costTrend, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: format(costData),
        borderColor: "#10b981",
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 5
      }]
    },
    options
  });

  // ================= COST SUMMARY =================
  new Chart(costSummary, {
    type: "bar",
    data: {
      labels: ["Best","Average","Worst"],
      datasets: [{
        data: [
          safeCostMin,
          safeCostAvg,
          safeCostMax
        ].map(v => Number(v.toFixed(2))),
        backgroundColor: ["#22c55e","#3b82f6","#ef4444"]
      }]
    },
    options
  });

  // ================= CO2 COMPARISON =================
  new Chart(co2Compare, {
    type: "bar",
    data: {
      labels: ["Predicted","Best Alternative"],
      datasets: [{
        data: [
          lastCO2,
          lastCO2 * 0.7
        ].map(v => Number(v.toFixed(2))),
        backgroundColor: ["#ef4444","#22c55e"]
      }]
    },
    options
  });

  // ================= CO2 TREND =================
  new Chart(co2Trend, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: format(co2Data),
        borderColor: "#16a34a",
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 5
      }]
    },
    options
  });

  // ================= CO2 SUMMARY =================
  new Chart(co2Summary, {
    type: "bar",
    data: {
      labels: ["Best","Average","Worst"],
      datasets: [{
        data: [
          safeCO2Min,
          safeCO2Avg,
          safeCO2Max
        ].map(v => Number(v.toFixed(2))),
        backgroundColor: ["#22c55e","#3b82f6","#ef4444"]
      }]
    },
    options
  });

  // ================= MATERIAL PIE =================
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
        backgroundColor: [
          "#10b981","#3b82f6","#f59e0b","#ef4444","#8b5cf6"
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
  function exportPDF() {
  const element = document.getElementById("impactContent");

  html2canvas(element, { scale: 2 }).then(canvas => {
    const imgData = canvas.toDataURL("image/png");

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF("p", "mm", "a4");

    const width = pdf.internal.pageSize.getWidth();
    const height = canvas.height * width / canvas.width;

    pdf.addImage(imgData, "PNG", 0, 0, width, height);
    pdf.save("EcoPackAI_Report.pdf");
  });
}

});
