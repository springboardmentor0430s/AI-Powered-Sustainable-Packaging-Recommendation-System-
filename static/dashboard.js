
document.addEventListener('DOMContentLoaded', function () {

    // --- TAB SWITCHING LOGIC ---
    const navRecommendations = document.getElementById('nav-recommendations');
    const navAnalytics = document.getElementById('nav-analytics');
    const navHistory = document.getElementById('nav-history');

    const viewRecommendations = document.getElementById('view-recommendations');
    const viewAnalytics = document.getElementById('view-analytics');
    const viewHistory = document.getElementById('view-history');

    // Helper to switch tabs
    function switchTab(activeNav, activeView) {
        // Reset all with checks
        if (navRecommendations) navRecommendations.classList.remove('active');
        if (navAnalytics) navAnalytics.classList.remove('active');
        if (navHistory) navHistory.classList.remove('active');

        if (viewRecommendations) viewRecommendations.classList.add('hidden');
        if (viewAnalytics) viewAnalytics.classList.add('hidden');
        if (viewHistory) viewHistory.classList.add('hidden');

        // Activate target
        if (activeNav) activeNav.classList.add('active');
        if (activeView) activeView.classList.remove('hidden');
    }

    if (navRecommendations && viewRecommendations) {
        navRecommendations.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab(navRecommendations, viewRecommendations);
        });
    }

    if (navAnalytics && viewAnalytics) {
        navAnalytics.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab(navAnalytics, viewAnalytics);
            renderCharts(); // Render/Update charts when tab is visible
        });
    }

    if (navHistory && viewHistory) {
        navHistory.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab(navHistory, viewHistory);
        });
    }


    // --- CHARTS LOGIC ---
    let costChartInstance = null;
    let co2ChartInstance = null;

    async function renderCharts() {
        if (costChartInstance) {
            // If already rendered, we might want to update it? For now, just return.
            // Or better: destroy and re-render to get fresh data
            costChartInstance.destroy();
            costChartInstance = null;
        }
        if (co2ChartInstance) {
            co2ChartInstance.destroy();
            co2ChartInstance = null;
        }

        try {
            const response = await fetch('/api/analytics');
            const data = await response.json();

            if (data.error) {
                console.error("Analytics error:", data.error);
                // Display error in table if possible
                const tableBody = document.querySelector('.comparison-table tbody');
                if (tableBody) {
                    tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-red-500 py-4">Error loading comparison data: ${data.error}</td></tr>`;
                }
                return;
            }

            // MATRIX TABLE & CHART DATA PREP
            const tableBody = document.querySelector('.comparison-table tbody');

            // Arrays for Charts (Grouped by Material now)
            let matLabels = [];
            let matCosts = [];
            let matCo2 = [];
            let matColors = ['#059669', '#10b981', '#34d399', '#6b7280', '#ef4444', '#f59e0b']; // Expanded palette

            if (tableBody) {
                tableBody.innerHTML = ''; // Clear existing

                if (data.matrix && data.matrix.length > 0) {
                    data.matrix.forEach((row, index) => {
                        // Populate Chart Data
                        matLabels.push(row.material);
                        matCosts.push(row.avg_pred_cost);
                        matCo2.push(row.est_co2);

                        const tr = document.createElement('tr');

                        // Sustainability Badge Logic
                        let badgeClass = 'badge-low';
                        let badgeText = 'Low';

                        if (row.avg_score >= 70) {
                            badgeClass = 'badge-high';
                            badgeText = 'High';
                        } else if (row.avg_score >= 40) {
                            badgeClass = 'badge-medium';
                            badgeText = 'Medium';
                        }

                        tr.innerHTML = `
                            <td>${row.material}</td>
                            <td>${row.avg_pred_cost}</td>
                            <td>${row.est_co2}</td>
                            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                            <td>${row.strength}</td>
                        `;
                        tableBody.appendChild(tr);
                    });
                } else {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td colspan="5" class="text-center text-gray-500 py-4">No comparison data available.</td>`;
                    tableBody.appendChild(tr);
                }
            }

            // Fallback if no matrix data (shouldn't happen if seeded)
            if (matLabels.length === 0) {
                matLabels = ['No Data'];
                matCosts = [0];
                matCo2 = [0];
            }

            // COST CHART (Bar)
            const ctxCostEl = document.getElementById('costChart');
            if (ctxCostEl) {
                const ctxCost = ctxCostEl.getContext('2d');
                costChartInstance = new Chart(ctxCost, {
                    type: 'bar',
                    data: {
                        labels: matLabels,
                        datasets: [{
                            label: 'Cost per Unit ($)',
                            data: matCosts,
                            backgroundColor: '#059669', // Or use matColors for multicolor bars
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { color: '#94a3b8' },
                                grid: { color: '#334155' }
                            },
                            x: {
                                ticks: { color: '#94a3b8' },
                                grid: { display: false }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: { color: '#f8fafc' } // White text
                            }
                        }
                    }
                });
            }

            // CO2 IMPACT CHART (Doughnut)
            const ctxCo2El = document.getElementById('co2Chart');
            if (ctxCo2El) {
                const ctxCo2 = ctxCo2El.getContext('2d');
                co2ChartInstance = new Chart(ctxCo2, {
                    type: 'doughnut',
                    data: {
                        labels: matLabels,
                        datasets: [{
                            label: 'CO2 Emission (kg)',
                            data: matCo2,
                            backgroundColor: matColors.slice(0, matLabels.length),
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { color: '#f8fafc' }
                            }
                        }
                    }
                });
            }

        } catch (err) {
            console.error("Failed to fetch analytics:", err);
            // Also display error in table if fetch fails
            const tableBody = document.querySelector('.comparison-table tbody');
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-red-500 py-4">Failed to load analytics data. Please try again.</td></tr>`;
            }
        }
    }

    // --- SIDEBAR TOGGLE ---
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function toggleSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.toggle('active');
            sidebarOverlay.classList.toggle('hidden');
        }
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', (e) => {
            e.preventDefault();
            toggleSidebar();
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            // Close when clicking overlay
            toggleSidebar();
        });
    }

});
