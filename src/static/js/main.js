// Toggle Sidebar
document.getElementById("menu-toggle").addEventListener("click", function (e) {
    e.preventDefault();
    document.body.classList.toggle("sb-sidenav-toggled");
});

// Section Navigation
function showSection(sectionId) {
    // Hide all
    document.getElementById('section-recommend').classList.add('d-none');
    document.getElementById('section-analytics').classList.add('d-none');
    document.getElementById('section-history').classList.add('d-none');

    // Deactivate navs
    document.getElementById('nav-recommend').classList.remove('active');
    document.getElementById('nav-analytics').classList.remove('active');
    document.getElementById('nav-history').classList.remove('active');

    // Show selected
    document.getElementById('section-' + sectionId).classList.remove('d-none');
    document.getElementById('nav-' + sectionId).classList.add('active');
}

// Global charts
let costChart = null;
let co2Chart = null;

// Handle Recommendation Form
document.getElementById('recommendForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const btn = this.querySelector('button[type="submit"]');
    const spinner = btn.querySelector('.spinner-border');

    btn.disabled = true;
    spinner.classList.remove('d-none');

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const results = await response.json();

        if (response.ok) {
            displayResults(results);
            updateAnalytics(results);
        } else {
            alert('Error: ' + (results.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to fetch recommendations.');
    } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
    }
});

function displayResults(results) {
    const topPick = results[0];
    document.getElementById('topMaterial').innerText = topPick.material;
    document.getElementById('topCost').innerText = '$' + topPick.cost;
    document.getElementById('topBio').innerText = topPick.details.bio + '/100';

    document.getElementById('resultsArea').classList.remove('d-none');

    const tbody = document.getElementById('comparisonTable').querySelector('tbody');
    tbody.innerHTML = '';

    results.forEach(item => {
        let badgeClass = 'badge-consider';
        if (item.recommendation === 'Highly Recommended') badgeClass = 'badge-highly-recommended';
        if (item.recommendation === 'Avoid') badgeClass = 'badge-avoid';

        const row = `
            <tr>
                <td class="fw-bold">${item.material}</td>
                <td>${item.cost}</td>
                <td>${item.co2}</td>
                <td>
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar bg-success" role="progressbar" style="width: ${item.details.bio}%"></div>
                    </div>
                    <small>${item.details.bio}%</small>
                </td>
                <td>
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar bg-info" role="progressbar" style="width: ${item.details.recycle}%"></div>
                    </div>
                    <small>${item.details.recycle}%</small>
                </td>
                <td><span class="badge ${badgeClass} p-2">${item.recommendation}</span></td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// Baseline Analytics on Load
document.addEventListener('DOMContentLoaded', function () {
    loadBaselineAnalytics();
    loadHistory(); // Also load history
});

async function loadBaselineAnalytics() {
    // API call with 'Standard' params to get baseline comparison
    const payload = {
        tensile_strength: 10,
        weight_capacity: 1,
        moisture_barrier: 5,
        product_name: "Baseline",
        category: "Standard"
    };

    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const results = await response.json();
        updateAnalytics(results);
    } catch (e) {
        console.log("Analytics load error", e);
    }
}

function updateAnalytics(results) {
    // Show analytics tab (optional, or just update charts essentially)
    // We update charts in background so they are ready when user clicks Analytics

    // Sort for better visualization (Cost ascending? or just keep default recommendation order)
    // Image shows Recycled Cardboard, Molded Pulp, Bio-Plastic, Standard, Styrofoam
    // Let's filter to top 5 prominent ones for cleaner chart if too many, or show all.

    const labels = results.map(r => r.material);
    const costs = results.map(r => r.cost);
    const co2s = results.map(r => r.co2);

    // Generate colors based on material type
    const bgColors = results.map(r => getMaterialColor(r.material, r.recommendation));

    updateChart('costChart', 'bar', labels, costs, 'Cost per Unit ($)', bgColors);
    updateChart('co2Chart', 'doughnut', labels, co2s, 'CO2 Emission', bgColors);
}

function getMaterialColor(material, recommendation) {
    // Logic: 
    // Highly Recommended / High Bio -> Green
    // Avoid -> Red
    // Standard -> Grey

    if (recommendation === 'Highly Recommended') return '#2ecc71'; // Bright Green
    if (recommendation === 'Avoid') return '#e74c3c'; // Red
    if (material.includes('Plastic') && !material.includes('Bio')) return '#95a5a6'; // Grey for standard plastic
    if (material.includes('Styrofoam')) return '#e74c3c';
    if (material.includes('Aluminium')) return '#95a5a6';

    return '#f1c40f'; // Yellow/Orange for "Consider"
}

function updateChart(canvasId, type, labels, data, label, colors) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Quick hack for demo:
    const chartVar = canvasId === 'costChart' ? window.costChart : window.co2Chart;
    if (chartVar) chartVar.destroy();

    const newChart = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    display: type === 'doughnut' // Hide legend for bar char
                }
            }
        }
    });

    if (canvasId === 'costChart') window.costChart = newChart;
    else window.co2Chart = newChart;
}

// Load Analytics Matrix
async function loadAnalyticsMatrix() {
    try {
        const response = await fetch('/api/materials');
        const materials = await response.json();

        const tbody = document.getElementById('analyticsTable').querySelector('tbody');
        tbody.innerHTML = '';

        materials.sort((a, b) => b.bio - a.bio); // Sort by sustainability

        materials.forEach(mat => {
            const row = `
                <tr>
                    <td class="fw-bold">${mat.name}</td>
                    <td>
                        <div class="progress" style="height: 15px;">
                            <div class="progress-bar bg-success" role="progressbar" style="width: ${mat.bio}%">${mat.bio}</div>
                        </div>
                    </td>
                    <td>
                        <div class="progress" style="height: 15px;">
                            <div class="progress-bar bg-info" role="progressbar" style="width: ${mat.recycle}%">${mat.recycle}</div>
                        </div>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (e) {
        console.error("Failed to load analytics matrix", e);
    }
}

// Hook showSection to load analytics matrix if needed
const originalShowSection = showSection;
showSection = function (sectionId) {
    originalShowSection(sectionId);
    if (sectionId === 'analytics') {
        loadAnalyticsMatrix();
    }
}

async function loadHistory() {
    showSection('history');
    const tbody = document.getElementById('historyTable').querySelector('tbody');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

    try {
        const response = await fetch('/history');
        const data = await response.json();

        tbody.innerHTML = '';
        // We attach data to the row button so we can reconstruct it
        window.historyData = data;

        data.forEach((item, index) => {
            const row = `
                <tr>
                    <td>${item.date}</td>
                    <td>${item.product_name} (${item.category})</td>
                    <td class="fw-bold text-success">${item.material}</td>
                    <td>$${item.cost}</td>
                    <td>${item.co2}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewHistoryMatrix(${index})">
                            View Matrix
                        </button>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load history</td></tr>';
    }
}

async function viewHistoryMatrix(index) {
    const item = window.historyData[index];
    const dateSpan = document.getElementById('matrixDate');
    dateSpan.innerText = item.date;

    // We need to re-run the recommendation engine with saved inputs.
    // NOTE: item from /history endpoint needs to include the inputs!
    // Currently, /history in app.py only returns outputs (product_name, material, co2, etc.)
    // We need to update app.py /history to return params too. Assuming it does now or we update it.
    // If not, we can't reconstruct accurately. Let's assume we update app.py to return them.
    // Actually, looking at app.py code I wrote, /history endpoint returns: 
    // product_name, category, material, co2, cost, recommendation, date.
    // IT DOES NOT RETURN tensile, weight, etc. 
    // I MUST UPDATE app.py TO RETURN THESE INPUTS first.

    // For now, let's implement the logic assuming the data is there. I will fix app.py next.

    // Construct payload for /api/recommend
    // Note: The history item structure mimics the API response, but for reconstruction
    // we need the INPUTS (tensile, weight, moisture) which are in ScanHistory model 
    // but were not serialized in the /history response in my previous turn.

    // Just in case I can't update app.py easily in this turn (I can), 
    // I'll assume item has them.

    const payload = {
        tensile_strength: item.tensile_strength,
        weight_capacity: item.weight_capacity,
        moisture_barrier: item.moisture_barrier,
        product_name: item.product_name,
        category: item.category
    };

    // Fetch fresh matrix
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const results = await response.json();

        // Populate Modal Table
        const tbody = document.getElementById('historyMatrixTable').querySelector('tbody');
        tbody.innerHTML = '';

        results.forEach(res => {
            let badgeClass = 'badge-consider';
            if (res.recommendation === 'Highly Recommended') badgeClass = 'badge-highly-recommended';
            if (res.recommendation === 'Avoid') badgeClass = 'badge-avoid';

            const row = `
                <tr>
                    <td class="fw-bold">${res.material}</td>
                    <td>${res.cost}</td>
                    <td>${res.co2}</td>
                    <td>${res.details.bio}%</td>
                    <td>${res.details.recycle}%</td>
                    <td><span class="badge ${badgeClass}">${res.recommendation}</span></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });

        // Show Modal
        const modal = new bootstrap.Modal(document.getElementById('matrixModal'));
        modal.show();

    } catch (e) {
        alert('Failed to reconstruct matrix.');
    }
}
