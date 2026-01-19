let count = 0;
let costChart;

function recommend() {

    /* ===== 1. READ INPUTS ===== */
    const material = document.getElementById("material").value;
    const shape = document.getElementById("shape").value;
    const strength = document.getElementById("strength").value;
    const food = document.getElementById("food").value;
    const qty = document.getElementById("qty").value || 500;
    const pkgwt = document.getElementById("pkgwt").value || 25;
    const recycle = document.getElementById("recycle").value || 70;

    /* ===== 2. PREDICT VALUES (DEMO LOGIC) ===== */
    // SIMPLE DYNAMIC PREDICTION (UI-LEVEL)
const baseCost = 50;
const baseCO2 = 20;

const predictedCost =
  baseCost +
  qty * 0.08 +
  pkgwt * 0.5 -
  recycle * 0.2;

const predictedCO2 =
  baseCO2 +
  qty * 0.03 +
  pkgwt * 0.4 -
  recycle * 0.15;

  
    /* ===== 3. SMART UI LOGIC (NeoSmartUI) ===== */
     let bestAlt = "";
    let altReason = "";

    if (qty < 500 && recycle >= 80) {
    bestAlt = "Molded Pulp";
    altReason = "Lightweight product with high recyclability is best suited for molded pulp packaging.";
    }
    else if (qty >= 500 && qty <= 1000) {
    bestAlt = "Paper-based Carton";
    altReason = "Medium-weight products benefit from paper-based cartons due to balanced strength and sustainability.";
    }
    else if (qty > 1000 && recycle >= 70) {
    bestAlt = "Corrugated Cardboard";
    altReason = "Heavy products require corrugated cardboard for structural strength and recyclability.";
    }
    else if (recycle < 60) {
    bestAlt = "Recycled Cardboard";
    altReason = "Low recyclability inputs are improved using recycled cardboard alternatives.";
    }
    else if (pkgwt > 80) {
    bestAlt = "Reinforced Cardboard";
    altReason = "Higher package weight requires reinforced cardboard for durability.";
    }
    else {
    bestAlt = "Standard Cardboard";
    altReason = "Default sustainable option based on packaging constraints.";
    }

    /* ===== 4. OUTPUT UI ===== */
    document.getElementById("out").innerHTML = `
        <b>Material:</b> ${material}<br>
        <b>Shape:</b> ${shape}<br>
        <b>Strength:</b> ${strength}<br>
        <b>Food Group:</b> ${food}<br>
        <b>Product Qty:</b> ${qty} g<br>
        <b>Package Weight:</b> ${pkgwt} g<br>
        <b>Recycle %:</b> ${recycle}%<br>
        <b>Predicted Cost:</b> ₹${predictedCost}<br>
        <b>Predicted CO₂:</b> ${predictedCO2}<br><br>

        <b>Recommended Packaging Material:</b>
        <span class="badge">${bestAlt}</span><br>

        <small style="color:#047857;">
            Why? ${altReason}
        </small>
    `;

    /* ===== 5. KPI UPDATE ===== */
    count++;
    document.getElementById("k1").innerText = count;
    document.getElementById("k2").innerText = "₹" + (count * 300);
    document.getElementById("k3").innerText = count * 40;
    document.getElementById("k4").innerText = "95%";

    /* ===== 6. SAVE TO HISTORY ===== */
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

    /* ===== 7. COST GRAPH ===== */
    if (!costChart) {
        costChart = new Chart(document.getElementById("costChart"), {
            type: "bar",
            data: {
                labels: ["Predicted", "Best Alternative"],
                datasets: [{
                    data: [predictedCost, 120],
                    backgroundColor: ["#ef4444", "#10b981"],
                    barThickness: 40
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    } else {
        costChart.data.datasets[0].data = [predictedCost, 120];
        costChart.update();
    }
}
// ===== CO2 IMPACT GRAPH =====
const altCO2 = predictedCO2 * 0.7; // 30% reduction assumption

if (!window.co2Chart) {
    window.co2Chart = new Chart(
        document.getElementById("co2Chart"),
        {
            type: "bar",
            data: {
                labels: ["Predicted", "Best Alternative"],
                datasets: [{
                    label: "CO₂ Impact (kg)",
                    data: [predictedCO2, altCO2],
                    backgroundColor: ["#ef4444", "#10b981"],
                    barThickness: 40
                }]
            },
            options: {
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "CO₂ Impact (kg)"
                        }
                    }
                }
            }
        }
    );
} else {
    window.co2Chart.data.datasets[0].data = [predictedCO2, altCO2];
    window.co2Chart.update();
}

