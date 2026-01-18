import {
  fetchTrendData,
  fetchSustainabilityScore,
  updateUserPreferences,
  downloadReport,
  emailReport,
  requireAuthOrRedirect,
  logout,
  mountNavbarProfileChip,
  mountLogoutButton,
} from './api.js';

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
});

const toNumber = (value) => {
  const cast = Number(value);
  return Number.isFinite(cast) ? cast : 0;
};

const formatPercent = (value) => `${percentFormatter.format(toNumber(value))}%`;

/**
 * Populate a data table with the provided labels and values.
 */
function populateDataTable({ tableId, labels, values, formatter, emptyMessage }) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const tbody = table.querySelector('tbody');
  if (!tbody) return;

  tbody.innerHTML = '';
  const rows = Math.min(labels.length, values.length);

  if (!rows) {
    const messageRow = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = table.querySelectorAll('thead th').length || 2;
    cell.className = 'text-muted';
    cell.textContent = emptyMessage || 'No data available.';
    messageRow.appendChild(cell);
    tbody.appendChild(messageRow);
    return;
  }

  for (let index = 0; index < rows; index += 1) {
    const tr = document.createElement('tr');

    const th = document.createElement('th');
    th.scope = 'row';
    th.textContent = labels[index];

    const td = document.createElement('td');
    const rawValue = values[index];
    td.textContent = formatter ? formatter(rawValue, index) : rawValue;

    tr.append(th, td);
    tbody.appendChild(tr);
  }
}

function updateAccessibleTables({ co2Data, costData, usageData }) {
  populateDataTable({
    tableId: 'co2DataTable',
    labels: co2Data.labels || [],
    values: co2Data.values || [],
    formatter: (value) => formatPercent(value),
    emptyMessage: 'CO₂ reduction data is unavailable.',
  });

  populateDataTable({
    tableId: 'costDataTable',
    labels: costData.labels || [],
    values: costData.values || [],
    formatter: (value) => currencyFormatter.format(toNumber(value)),
    emptyMessage: 'Cost savings data is unavailable.',
  });

  populateDataTable({
    tableId: 'usageDataTable',
    labels: usageData.labels || [],
    values: usageData.values || [],
    formatter: (value) => formatPercent(value),
    emptyMessage: 'Material usage data is unavailable.',
  });
}

/**
 * Populate the category summary table.  The summary contains parallel
 * arrays: categories, runs, avgCost and avgCO2.  If no data is
 * available, a placeholder row is inserted.
 *
 * @param {{categories: Array<string>, runs: Array<number>, avgCost: Array<number>, avgCO2: Array<number>}} summary
 */
function populateCategorySummaryTable(summary) {
  const table = document.getElementById('categorySummaryTable');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const cats = summary?.categories || [];
  const runs = summary?.runs || [];
  const costs = summary?.avgCost || [];
  const co2s = summary?.avgCO2 || [];
  const rows = Math.min(cats.length, runs.length, costs.length, co2s.length);
  if (!rows) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 4;
    td.className = 'text-muted';
    td.textContent = 'No category data available.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  for (let i = 0; i < rows; i += 1) {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    th.scope = 'row';
    th.textContent = cats[i];
    const tdRuns = document.createElement('td');
    tdRuns.textContent = String(runs[i]);
    const tdCost = document.createElement('td');
    tdCost.textContent = currencyFormatter.format(Number(costs[i] || 0));
    const tdCO2 = document.createElement('td');
    tdCO2.textContent = Number(co2s[i] || 0).toFixed(2);
    tr.append(th, tdRuns, tdCost, tdCO2);
    tbody.appendChild(tr);
  }
}

/**
 * Populate the preference summary table.  Takes an object with
 * biodegradable and recyclable percentages.  Missing values are
 * represented as 'N/A'.
 *
 * @param {{biodegradable: number|null, recyclable: number|null}} prefs
 */
function populatePreferenceSummaryTable(prefs) {
  const table = document.getElementById('preferenceSummaryTable');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const rows = [
    { label: 'Biodegradable', value: prefs?.biodegradable },
    { label: 'Recyclable', value: prefs?.recyclable },
  ];
  rows.forEach(({ label, value }) => {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    th.scope = 'row';
    th.textContent = label;
    const td = document.createElement('td');
    if (typeof value === 'number') {
      td.textContent = percentFormatter.format(value);
    } else {
      td.textContent = 'N/A';
    }
    tr.append(th, td);
    tbody.appendChild(tr);
  });
}

function renderPlotlyCharts({ co2Data, costData, usageData }) {
  const plotly = window.Plotly;
  if (!plotly) throw new Error('Plotly library did not load.');

  const co2Values = (co2Data.values || []).map((value) => toNumber(value));
  const costValues = (costData.values || []).map((value) => toNumber(value));
  const usageValues = (usageData.values || []).map((value) => toNumber(value));

  const sharedConfig = { displayModeBar: false, responsive: true };

  plotly.newPlot(
    'co2Chart',
    [
      {
        x: co2Data.labels,
        y: co2Values,
        type: 'scatter',
        mode: 'lines+markers',
        line: { shape: 'spline', width: 3 },
        marker: { size: 8 },
        hovertemplate: '%{x}<br>CO₂ reduction: %{y:.1f}%<extra></extra>',
      },
    ],
    {
      margin: { t: 30, r: 15, b: 50, l: 60 },
      yaxis: { title: 'Reduction (%)', ticksuffix: '%', rangemode: 'tozero' },
      xaxis: { title: 'Period', showgrid: false },
      hovermode: 'x unified',
    },
    sharedConfig,
  );

  plotly.newPlot(
    'costChart',
    [
      {
        x: costData.labels,
        y: costValues,
        type: 'bar',
        hovertemplate: '%{x}<br>Cost savings: $%{y:,.0f} per ton<extra></extra>',
      },
    ],
    {
      margin: { t: 30, r: 15, b: 50, l: 60 },
      yaxis: { title: 'Savings (USD per metric ton)', tickprefix: '$', rangemode: 'tozero' },
      xaxis: { title: 'Period', showgrid: false },
    },
    sharedConfig,
  );

  plotly.newPlot(
    'usageChart',
    [
      {
        labels: usageData.labels,
        values: usageValues,
        type: 'pie',
        hole: 0.45,
        hovertemplate: '%{label}: %{percent}<extra></extra>',
      },
    ],
    {
      margin: { t: 20, r: 20, b: 20, l: 20 },
      showlegend: true,
      legend: { orientation: 'h' },
    },
    sharedConfig,
  );
}

function showChartError(message) {
  document.querySelectorAll('.plotly-chart').forEach((container) => {
    container.innerHTML = `<p class="text-danger small mb-0">${message}</p>`;
  });
}

async function downloadAndSave(format, filename) {
  try {
    const blob = await downloadReport(format);
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
  } catch (error) {
    const msg = String(error?.message || error);

    if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
      alert('Your session expired. Please log in again.');
      logout();
      window.location.href = 'login.html';
      return;
    }

    alert(`Failed to download ${format.toUpperCase()} report. Please try again later.`);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  // Enforce auth
  if (!requireAuthOrRedirect()) return;

  // profile chip + logout button
  mountNavbarProfileChip();
  mountLogoutButton();

  try {
    // Fetch trend data instead of generic dashboard data
    const trend = await fetchTrendData();
    const co2Data = trend.co2Trend || { labels: [], values: [] };
    const costData = trend.costTrend || { labels: [], values: [] };
    const usageData = trend.usageTrend || { labels: [], values: [] };
    updateAccessibleTables({ co2Data, costData, usageData });
    renderPlotlyCharts({ co2Data, costData, usageData });
    // Populate additional tables for category and preference summaries
    if (trend && typeof trend === 'object') {
      populateCategorySummaryTable(trend.categorySummary || {});
      populatePreferenceSummaryTable(trend.preferences || {});
      // Update KPI tiles from summary if available
      const summary = trend.summary || {};
      const totalRunsElem = document.getElementById('kpiTotalRuns');
      const avgCostElem = document.getElementById('kpiAvgCost');
      const avgCO2Elem = document.getElementById('kpiAvgCO2');
      if (totalRunsElem) {
        const val = summary.totalRuns;
        totalRunsElem.textContent = (typeof val === 'number' && val >= 0) ? String(val) : '--';
      }
      if (avgCostElem) {
        const val = summary.avgCost;
        avgCostElem.textContent = (typeof val === 'number') ? currencyFormatter.format(val) : '--';
      }
      if (avgCO2Elem) {
        const val = summary.avgCO2;
        avgCO2Elem.textContent = (typeof val === 'number') ? Number(val).toFixed(2) : '--';
      }
    }

    // Fetch sustainability score
    const sustainability = await fetchSustainabilityScore();
    const scoreElem = document.getElementById('sustainabilityScoreValue');
    if (scoreElem && sustainability && typeof sustainability.score === 'number') {
      scoreElem.textContent = `${Number(sustainability.score).toFixed(1)}%`;
    }
  } catch (error) {
    const msg = String(error?.message || error);
    console.error('Error rendering dashboard:', error);
    showChartError('Unable to load chart data.');
    updateAccessibleTables({
      co2Data: { labels: [], values: [] },
      costData: { labels: [], values: [] },
      usageData: { labels: [], values: [] },
    });
    // Handle expired session
    if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
      logout();
      window.location.href = 'login.html';
      return;
    }
  }

  // Bind report download buttons
  const pdfBtn = document.getElementById('downloadPdf');
  const excelBtn = document.getElementById('downloadExcel');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', async () => {
      await downloadAndSave('pdf', 'ecopackai_sustainability_report.pdf');
    });
  }
  if (excelBtn) {
    excelBtn.addEventListener('click', async () => {
      await downloadAndSave('excel', 'ecopackai_sustainability_report.xlsx');
    });
  }

  // Bind email report button
  const emailBtn = document.getElementById('emailReport');
  if (emailBtn) {
    emailBtn.addEventListener('click', async () => {
      const statusElem = document.getElementById('emailStatus');
      if (statusElem) statusElem.textContent = 'Sending email...';
      try {
        const resp = await emailReport('pdf');
        if (statusElem) statusElem.textContent = 'Report emailed successfully.';
      } catch (err) {
        const msg = String(err?.message || err);
        if (statusElem) statusElem.textContent = `Failed to email report: ${msg}`;
        if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
          logout();
          window.location.href = 'login.html';
        }
      }
    });
  }

  // Handle preferences form submission
  const prefForm = document.getElementById('preferencesForm');
  if (prefForm) {
    prefForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const co2Input = document.getElementById('co2Weight');
      const costInput = document.getElementById('costWeight');
      const statusElem = document.getElementById('prefStatus');
      const prefs = {};
      const co2Val = parseFloat(co2Input?.value);
      const costVal = parseFloat(costInput?.value);
      if (!isNaN(co2Val)) prefs.co2Weight = co2Val;
      if (!isNaN(costVal)) prefs.costWeight = costVal;
      try {
        const resp = await updateUserPreferences(prefs);
        if (statusElem) statusElem.textContent = 'Preferences saved successfully.';
      } catch (err) {
        const msg = String(err?.message || err);
        if (statusElem) statusElem.textContent = 'Failed to save preferences: ' + msg;
        if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
          logout();
          window.location.href = 'login.html';
        }
      }
    });
  }
});
