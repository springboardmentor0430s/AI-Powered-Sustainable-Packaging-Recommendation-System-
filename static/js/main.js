/* ===============================
   EcoPackAI – Main JavaScript
   =============================== */

/* ---------- AUTH UTIL ---------- */
class Auth {
    static getToken() {
        return localStorage.getItem("token");
    }

    static setToken(token) {
        localStorage.setItem("token", token);
    }

    static logout() {
        localStorage.removeItem("token");
        window.location.href = "/login";
    }
}

/* ---------- API UTIL ---------- */
class API {
    static async request(url, options = {}) {
        const token = Auth.getToken();

        const headers = {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            Auth.logout();
            throw new Error("Unauthorized");
        }

        const text = await response.text();
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error("Server returned non-JSON response:", text);
            throw new Error(`Server Error: ${response.status}`);
        }
    }
}

/* ---------- PRODUCT ANALYSIS ---------- */
class ProductAnalyzer {
    static async analyze(formData) {
        return API.request("/api/recommendations/recommend", {
            method: "POST",
            body: JSON.stringify(formData)
        });
    }
}

/* ---------- ANALYTICS DASHBOARD ---------- */
class Dashboard {
    static async load() {
        try {
            const data = await API.request("/api/analytics/dashboard");

            if (!data || !data.metrics) return;

            this.updateStats(data.metrics);
            this.renderCharts(data.charts || {});
        } catch (err) {
            console.error("Dashboard load failed:", err);
        }
    }

    /* ---- METRICS ---- */
    static updateStats(metrics) {
        this.setText("avgCO2", (metrics.avg_co2_reduction || 0) + "%");
        this.setText("avgCost", (metrics.avg_cost_savings || 0) + "%");
        this.setText("totalRecs", metrics.total_recommendations || 0);
        this.setText("topMaterial", metrics.top_material || "—");
    }

    static setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    /* ---- CHARTS ---- */
    static renderCharts(charts) {
        if (charts.co2_trend && document.getElementById("co2Chart")) {
            Plotly.newPlot(
                "co2Chart",
                charts.co2_trend.data,
                charts.co2_trend.layout,
                { responsive: true }
            );
        }

        if (charts.material_usage && document.getElementById("materialChart")) {
            Plotly.newPlot(
                "materialChart",
                charts.material_usage.data,
                charts.material_usage.layout,
                { responsive: true }
            );
        }

        if (charts.cost_trend && document.getElementById("costChart")) {
            Plotly.newPlot(
                "costChart",
                charts.cost_trend.data,
                charts.cost_trend.layout,
                { responsive: true }
            );
        }
    }
}

/* ---------- MATERIAL INSIGHTS ---------- */
async function loadMaterialInsights() {
    try {
        const data = await API.request("/api/analytics/insights/materials");
        const container = document.getElementById("insightsContainer");

        if (!container) return;

        if (!data.insights || data.insights.length === 0) {
            container.innerHTML =
                `<p class="text-muted text-center">No insights available yet.</p>`;
            return;
        }

        container.innerHTML = data.insights.map(insight => `
            <div class="col-md-4">
                <div class="metric-card">
                    <h6 class="fw-bold">${insight.material}</h6>
                    <p class="mb-1">Avg CO₂ Reduction: ${insight.avg_co2_reduction}%</p>
                    <p class="mb-1">Avg Cost Savings: ${insight.avg_cost_savings}%</p>
                    <p class="mb-0">Avg Score: ${insight.avg_score}</p>
                </div>
            </div>
        `).join("");
    } catch (err) {
        console.error("Material insights error:", err);
    }
}

/* ---------- EXPORT ---------- */
async function exportData(format) {
    // Matches analytics.py routes: /export/csv, /export/excel, /export/pdf
    const endpoint = `/api/analytics/export/${format}`;

    try {
        const token = Auth.getToken();

        const response = await fetch(endpoint, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download =
            format === "csv" ? "EcoPackAI_Report.csv" :
            format === "excel" ? "EcoPackAI_Report.xlsx" :
            "EcoPackAI_Report.pdf";

        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Export failed:", err);
    }
}

/* ---------- INIT ---------- */
document.addEventListener("DOMContentLoaded", () => {
    // Load analytics dashboard if present
    if (document.getElementById("co2Chart")) {
        Dashboard.load();
        loadMaterialInsights();
    }
});

/* ---------- GLOBAL EXPORT ---------- */
window.EcoPackAI = {
    analyzeProduct: ProductAnalyzer.analyze,
    loadDashboard: Dashboard.load,
    loadMaterialInsights,
    exportData,
    logout: Auth.logout
};
