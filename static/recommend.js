let costChart = null;

/* ================= DARK MODE ================= */
function toggleDarkMode() {
  document.body.classList.toggle("dark");
  localStorage.setItem("darkMode", document.body.classList.contains("dark"));
}

window.addEventListener("load", () => {
  if (localStorage.getItem("darkMode") === "true") {
    document.body.classList.add("dark");
  }
});

/* ================= MAIN FUNCTION ================= */
function recommend() {

  // ===== INPUTS =====
  const material = document.getElementById("material").value;
  const shape = document.getElementById("shape").value;
  const strength = document.getElementById("strength").value;
  const food = document.getElementById("food").value;

  const qtyInput = document.getElementById("qty").value;
  const pkgwtInput = document.getElementById("pkgwt").value;
  const recycleInput = document.getElementById("recycle").value;

  // ===== VALIDATION =====
  if (!qtyInput || !pkgwtInput || !recycleInput) {
    document.getElementById("out").innerHTML = `
      <span style="color:red;font-weight:bold;">
        ⚠️ Please enter:
        ${!qtyInput ? " Product Quantity" : ""}
        ${!pkgwtInput ? " Package Weight" : ""}
        ${!recycleInput ? " Recyclability %" : ""}
      </span>
    `;
    return;
  }

  // ===== CONVERT =====
  const qty = Number(qtyInput);
  const pkgwt = Number(pkgwtInput);
  const recycle = Number(recycleInput);

  // ===== ML PREDICTION =====
  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ qty, pkgwt, recycle })
  })
  .then(res => res.json())
  .then(data => {

    const predictedCost = data.cost;
    const predictedCO2 = data.co2;

    // ===== SMART LOGIC =====
    let bestAlt = "";
    let altReason = "";

    if (qty < 500 && recycle >= 80) {
      bestAlt = "Molded Pulp";
      altReason = "Lightweight + highly recyclable → best for sustainability.";
    } else if (qty <= 1000) {
      bestAlt = "Paper-based Carton";
      altReason = "Balanced eco-friendly and cost efficient.";
    } else if (qty > 1000 && recycle >= 70) {
      bestAlt = "Corrugated Cardboard";
      altReason = "Best for heavy products.";
    } else if (recycle < 60) {
      bestAlt = "Recycled Cardboard";
      altReason = "Improves recyclability.";
    } else if (pkgwt > 80) {
      bestAlt = "Reinforced Cardboard";
      altReason = "Handles high weight.";
    } else {
      bestAlt = "Standard Cardboard";
      altReason = "Default sustainable choice.";
    }

    // ===== OUTPUT + AI PANEL =====
    document.getElementById("out").innerHTML = `
      <b>Material:</b> ${material}<br>
      <b>Shape:</b> ${shape}<br>
      <b>Strength:</b> ${strength}<br>
      <b>Food:</b> ${food}<br>
      <b>Qty:</b> ${qty} g<br>
      <b>Weight:</b> ${pkgwt} g<br>
      <b>Recycle:</b> ${recycle}%<br><br>

      <b>Cost:</b> ₹${predictedCost.toFixed(2)}<br>
      <b>CO₂:</b> ${predictedCO2.toFixed(2)}<br><br>

      <b>Best:</b> ${bestAlt}<br>

      <div style="margin-top:10px;padding:12px;background:#ecfdf5;border-radius:12px;">
        🤖 <b>AI Insight:</b><br>
        ${altReason}
        <br><br>
        This recommendation balances cost, weight, and sustainability.
      </div>
    `;

    // ===== KPI UPDATE =====
    let totalRec = Number(localStorage.getItem("totalRec")) || 0;
    let totalCostSaved = Number(localStorage.getItem("totalCostSaved")) || 0;
    let totalCO2Saved = Number(localStorage.getItem("totalCO2Saved")) || 0;

    totalRec++;

    const costSaved = predictedCost * 0.2;
    const co2Saved = predictedCO2 * 0.3;

    totalCostSaved += costSaved;
    totalCO2Saved += co2Saved;

    localStorage.setItem("totalRec", totalRec);
    localStorage.setItem("totalCostSaved", totalCostSaved);
    localStorage.setItem("totalCO2Saved", totalCO2Saved);

    // 🔥 LIVE UPDATE
    document.getElementById("k1").innerText = totalRec;
    document.getElementById("k2").innerText = "₹" + totalCostSaved.toFixed(2);
    document.getElementById("k3").innerText = totalCO2Saved.toFixed(2);

    // ===== SAVE LAST INPUT =====
    localStorage.setItem("lastInput", JSON.stringify({
      material, shape, strength, food, qty, pkgwt, recycle
    }));

    // ===== SAVE HISTORY =====
    const history = JSON.parse(localStorage.getItem("history")) || [];

    history.unshift({
      dateTime: new Date().toLocaleString(),
      material,
      shape,
      strength,
      food,
      qty,
      pkgwt,
      recycle,
      predictedCost,
      predictedCO2,
      bestAlt
    });

    localStorage.setItem("history", JSON.stringify(history));

    // ===== GRAPH =====
    const altCost = predictedCost * 0.8;

    if (!costChart) {
      costChart = new Chart(document.getElementById("costChart"), {
        type: "bar",
        data: {
          labels: ["Predicted", "Best Alternative"],
          datasets: [{
            data: [predictedCost, altCost],
            backgroundColor: ["#ef4444", "#10b981"]
          }]
        },
        options: {
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } }
        }
      });
    } else {
      costChart.data.datasets[0].data = [predictedCost, altCost];
      costChart.update();
    }

    // ===== CLEAR INPUTS =====
    document.getElementById("qty").value = "";
    document.getElementById("pkgwt").value = "";
    document.getElementById("recycle").value = "";

  }); // END FETCH
}

/* ================= DOWNLOAD CSV ================= */
function downloadCSV() {
  const history = JSON.parse(localStorage.getItem("history")) || [];

  if (history.length === 0) {
    alert("No data to download");
    return;
  }

  let csv = "Date,Material,Qty,Weight,Recycle,Cost,CO2,Best\n";

  history.forEach(h => {
    csv += `${h.dateTime},${h.material},${h.qty},${h.pkgwt},${h.recycle},${h.predictedCost},${h.predictedCO2},${h.bestAlt}\n`;
  });

  const blob = new Blob([csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "ecopack_data.csv";
  a.click();
}
