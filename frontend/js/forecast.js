import {
  requireAuthOrRedirect,
  mountNavbarProfileChip,
  mountLogoutButton,
  fetchForecast,
} from './api.js';

const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const PERIOD_RE = /^\d{4}-\d{2}$/;

function parseFloatSafe(value) {
  const n = Number.parseFloat(String(value ?? '').trim());
  return Number.isFinite(n) ? n : NaN;
}

function monthKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  return `${y}-${m}`;
}

function nextMonths(n, startDate = new Date()) {
  const out = [];
  const d = new Date(startDate.getFullYear(), startDate.getMonth(), 1);
  for (let i = 0; i < n; i++) {
    out.push(monthKey(new Date(d.getFullYear(), d.getMonth() + i, 1)));
  }
  return out;
}

function setStatus(el, message, variant = 'info') {
  el.className = `alert alert-${variant}`;
  el.textContent = message;
}

function downloadText(filename, content, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function planToCsv(plan) {
  const lines = ['period,volumeTons'];
  for (const row of plan) {
    lines.push(`${row.period},${row.volumeTons}`);
  }
  return lines.join('\n');
}

function parsePlanCsv(text) {
  const lines = String(text || '')
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);

  if (!lines.length) return [];

  let start = 0;
  const header = lines[0].toLowerCase();
  if (header.includes('period') && header.includes('vol')) start = 1;

  const rows = [];
  for (let i = start; i < lines.length; i++) {
    const parts = lines[i].split(',').map((p) => p.trim());
    if (parts.length < 2) continue;
    rows.push({ period: parts[0], volumeTons: parseFloatSafe(parts[1]) });
  }
  return rows;
}

function normalizePlan(rows) {
  const cleaned = [];
  const seen = new Set();
  for (const row of rows || []) {
    const period = String(row?.period ?? '').trim();
    const vol = parseFloatSafe(row?.volumeTons);
    if (!PERIOD_RE.test(period)) continue;
    if (!Number.isFinite(vol) || vol < 0) continue;
    if (seen.has(period)) continue;
    seen.add(period);
    cleaned.push({ period, volumeTons: vol });
  }
  cleaned.sort((a, b) => a.period.localeCompare(b.period));
  return cleaned;
}

function sum(arr) {
  return (arr || []).reduce((acc, v) => acc + (Number.isFinite(v) ? v : 0), 0);
}

function getForecastSeries(forecast, path) {
  // path: e.g. ['totals','total_cost_usd']
  const node = path.reduce((acc, k) => (acc && acc[k] != null ? acc[k] : null), forecast);
  const mean = node?.mean || [];
  const bands = node?.bands || {};
  return {
    mean,
    p10: bands.p10 || [],
    p90: bands.p90 || [],
  };
}

function buildBandChartTraces({ labels, mean, p10, p90, nameMean, nameBand }) {
  // Band: p10..p90
  const tP10 = {
    x: labels,
    y: p10,
    mode: 'lines',
    line: { width: 0 },
    name: 'P10',
    hoverinfo: 'skip',
    showlegend: false,
  };
  const tP90 = {
    x: labels,
    y: p90,
    mode: 'lines',
    fill: 'tonexty',
    fillcolor: 'rgba(0,0,0,0.10)',
    line: { width: 0 },
    name: nameBand,
    hovertemplate: '%{x}<br>' + nameBand + ': %{y:.2f}<extra></extra>',
  };
  const tMean = {
    x: labels,
    y: mean,
    mode: 'lines+markers',
    name: nameMean,
    hovertemplate: '%{x}<br>' + nameMean + ': %{y:.2f}<extra></extra>',
  };
  return [tP10, tP90, tMean];
}

function plotBandChart(divId, labels, series, yTitle, valueFormatter) {
  const div = document.getElementById(divId);
  if (!div) return;

  const traces = buildBandChartTraces({
    labels,
    mean: series.mean,
    p10: series.p10,
    p90: series.p90,
    nameMean: 'Mean',
    nameBand: 'P10–P90',
  });

  const layout = {
    margin: { l: 50, r: 20, t: 10, b: 40 },
    xaxis: { title: 'Period' },
    yaxis: { title: yTitle, tickformat: valueFormatter || undefined },
    legend: { orientation: 'h' },
  };

  Plotly.newPlot(div, traces, layout, { responsive: true, displayModeBar: false });
}

function plotDiffChart(divId, labels, diffCost, diffCo2) {
  const div = document.getElementById(divId);
  if (!div) return;

  const traces = [
    {
      x: labels,
      y: diffCost,
      type: 'bar',
      name: 'Δ cost (USD)',
      hovertemplate: '%{x}<br>Δ cost: %{y:.0f} USD<extra></extra>',
      yaxis: 'y1',
    },
    {
      x: labels,
      y: diffCo2,
      type: 'bar',
      name: 'Δ CO₂ (kg)',
      hovertemplate: '%{x}<br>Δ CO₂: %{y:.2f} kg<extra></extra>',
      yaxis: 'y2',
    },
  ];

  const layout = {
    barmode: 'group',
    margin: { l: 50, r: 50, t: 10, b: 40 },
    xaxis: { title: 'Period' },
    yaxis: { title: 'Δ Cost (USD)', side: 'left' },
    yaxis2: { title: 'Δ CO₂ (kg)', overlaying: 'y', side: 'right' },
    legend: { orientation: 'h' },
  };

  Plotly.newPlot(div, traces, layout, { responsive: true, displayModeBar: false });
}

function createPlanEditor(prefix, state) {
  const tbody = document.getElementById(`planTableBody${prefix}`);
  const addRowBtn = document.getElementById(`addRowBtn${prefix}`);
  const nextSixBtn = document.getElementById(`nextSixBtn${prefix}`);
  const clearBtn = document.getElementById(`clearPlanBtn${prefix}`);
  const quickTotalTons = document.getElementById(`quickTotalTons${prefix}`);
  const quickMonths = document.getElementById(`quickMonths${prefix}`);
  const quickBuildBtn = document.getElementById(`quickBuildBtn${prefix}`);
  const planCsvFile = document.getElementById(`planCsvFile${prefix}`);
  const templateBtn = document.getElementById(`downloadPlanTemplateBtn${prefix}`);
  const planStatus = document.getElementById(`planStatus${prefix}`);

  if (!tbody) throw new Error(`Missing plan table body for ${prefix}`);

  function render() {
    tbody.innerHTML = '';

    if (!state.plan.length) {
      // Render a gentle empty state row
      const tr = document.createElement('tr');
      tr.innerHTML = `<td colspan="3" class="text-muted">No rows yet. Use “Next 6 months” or “Fill evenly across months”.</td>`;
      tbody.appendChild(tr);
      return;
    }

    state.plan.forEach((row, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="min-width: 160px;">
          <input class="form-control" inputmode="numeric" pattern="\\d{4}-\\d{2}" aria-label="Period YYYY-MM"
                 value="${row.period ?? ''}" data-field="period" data-index="${idx}" />
        </td>
        <td style="min-width: 160px;">
          <input class="form-control text-end" type="number" min="0" step="0.1" aria-label="Volume in tons"
                 value="${Number.isFinite(row.volumeTons) ? row.volumeTons : ''}" data-field="volumeTons" data-index="${idx}" />
        </td>
        <td class="text-end" style="min-width: 140px;">
          <button type="button" class="btn btn-sm btn-outline-danger" data-action="remove" data-index="${idx}">
            Remove
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function pullFromUi() {
    const rows = [];
    const inputs = tbody.querySelectorAll('input[data-index]');
    const byIdx = new Map();
    inputs.forEach((el) => {
      const idx = Number(el.getAttribute('data-index'));
      const field = el.getAttribute('data-field');
      const v = el.value;
      if (!byIdx.has(idx)) byIdx.set(idx, {});
      byIdx.get(idx)[field] = v;
    });
    for (const [, obj] of byIdx.entries()) {
      rows.push({
        period: String(obj.period ?? '').trim(),
        volumeTons: parseFloatSafe(obj.volumeTons),
      });
    }
    state.plan = normalizePlan(rows);
    render();
    return state.plan;
  }

  function setPlan(plan) {
    state.plan = normalizePlan(plan);
    render();
  }

  tbody.addEventListener('click', (e) => {
    const btn = e.target?.closest('button[data-action="remove"]');
    if (!btn) return;
    const idx = Number(btn.getAttribute('data-index'));
    state.plan.splice(idx, 1);
    state.plan = normalizePlan(state.plan);
    render();
    setStatus(planStatus, `Removed row ${idx + 1}.`, 'info');
  });

  tbody.addEventListener('change', () => {
    pullFromUi();
  });

  addRowBtn?.addEventListener('click', () => {
    pullFromUi();
    state.plan.push({ period: '', volumeTons: 0 });
    render();
    setStatus(planStatus, 'Added an empty row. Enter a period like 2026-02 and a non-negative ton value.', 'info');
  });

  nextSixBtn?.addEventListener('click', () => {
    const months = nextMonths(6);
    setPlan(months.map((m) => ({ period: m, volumeTons: 1 })));
    setStatus(planStatus, 'Filled the next 6 months with 1 ton each. Adjust any month as needed.', 'success');
  });

  clearBtn?.addEventListener('click', () => {
    state.plan = [];
    render();
    setStatus(planStatus, 'Cleared the plan.', 'warning');
  });

  quickBuildBtn?.addEventListener('click', () => {
    const total = parseFloatSafe(quickTotalTons?.value);
    const nMonths = Number.parseInt(String(quickMonths?.value ?? '6'), 10);
    if (!Number.isFinite(total) || total < 0) {
      setStatus(planStatus, 'Total tons must be a non-negative number.', 'danger');
      return;
    }
    if (!Number.isFinite(nMonths) || nMonths <= 0) {
      setStatus(planStatus, 'Months must be a positive number.', 'danger');
      return;
    }
    const per = total / nMonths;
    const months = nextMonths(nMonths);
    setPlan(months.map((m) => ({ period: m, volumeTons: Number(per.toFixed(3)) })));
    setStatus(planStatus, `Filled ${nMonths} month(s) evenly (~${per.toFixed(2)} tons/month).`, 'success');
  });

  templateBtn?.addEventListener('click', () => {
    const csv = planToCsv(nextMonths(6).map((m) => ({ period: m, volumeTons: 1 })));
    downloadText(`ecopackai_plan_template_${prefix}.csv`, csv, 'text/csv');
  });

  planCsvFile?.addEventListener('change', async () => {
    const file = planCsvFile.files?.[0];
    if (!file) return;
    const text = await file.text();
    const rows = normalizePlan(parsePlanCsv(text));
    if (!rows.length) {
      setStatus(planStatus, 'Could not find valid rows in the CSV. Expected: period,volumeTons.', 'danger');
      planCsvFile.value = '';
      return;
    }
    setPlan(rows);
    setStatus(planStatus, `Imported ${rows.length} row(s) from CSV.`, 'success');
    planCsvFile.value = '';
  });

  // initial render
  render();

  return {
    getPlan: pullFromUi,
    setPlan,
  };
}

function alignLabels(fA, fB) {
  const labels = new Set();
  (fA?.labels || []).forEach((l) => labels.add(l));
  (fB?.labels || []).forEach((l) => labels.add(l));
  return Array.from(labels).sort((a, b) => String(a).localeCompare(String(b)));
}

function mapSeriesByLabel(labels, forecast, path) {
  const series = getForecastSeries(forecast, path);
  const labelToIdx = new Map((forecast?.labels || []).map((l, i) => [l, i]));
  const out = { mean: [], p10: [], p90: [] };
  for (const l of labels) {
    const i = labelToIdx.get(l);
    out.mean.push(i == null ? 0 : (series.mean[i] ?? 0));
    out.p10.push(i == null ? 0 : (series.p10[i] ?? 0));
    out.p90.push(i == null ? 0 : (series.p90[i] ?? 0));
  }
  return out;
}

function mapPlanVolumeByLabel(labels, plan) {
  const m = new Map((plan || []).map((r) => [r.period, r.volumeTons]));
  return labels.map((l) => m.get(l) ?? 0);
}

function safeCurrency(n) {
  return currencyFormatter.format(Number.isFinite(n) ? n : 0);
}

function safeNumber(n, unit = '') {
  const v = Number.isFinite(n) ? n : 0;
  return `${numberFormatter.format(v)}${unit}`;
}

function buildResultsTable(labels, planA, planB, fA, fB) {
  const body = document.getElementById('resultsTableBody');
  if (!body) return;
  body.innerHTML = '';

  const aCost = mapSeriesByLabel(labels, fA, ['totals', 'total_cost_usd']);
  const aCo2 = mapSeriesByLabel(labels, fA, ['totals', 'total_co2_kg']);
  const bCost = mapSeriesByLabel(labels, fB, ['totals', 'total_cost_usd']);
  const bCo2 = mapSeriesByLabel(labels, fB, ['totals', 'total_co2_kg']);

  const volA = mapPlanVolumeByLabel(labels, planA);
  const volB = mapPlanVolumeByLabel(labels, planB);

  labels.forEach((label, i) => {
    const dCost = (bCost.mean[i] ?? 0) - (aCost.mean[i] ?? 0);
    const dCo2 = (bCo2.mean[i] ?? 0) - (aCo2.mean[i] ?? 0);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <th scope="row">${label}</th>
      <td class="text-end">${safeNumber(volA[i], '')}</td>
      <td class="text-end">${safeCurrency(aCost.mean[i] ?? 0)}</td>
      <td class="text-end">${safeNumber(aCo2.mean[i] ?? 0, ' kg')}</td>
      <td class="text-end">${safeNumber(volB[i], '')}</td>
      <td class="text-end">${safeCurrency(bCost.mean[i] ?? 0)}</td>
      <td class="text-end">${safeNumber(bCo2.mean[i] ?? 0, ' kg')}</td>
      <td class="text-end">${safeCurrency(dCost)}</td>
      <td class="text-end">${safeNumber(dCo2, ' kg')}</td>
    `;
    body.appendChild(tr);
  });
}

function buildExportCsv(labels, planA, planB, fA, fB) {
  const aCost = mapSeriesByLabel(labels, fA, ['totals', 'total_cost_usd']);
  const aCo2 = mapSeriesByLabel(labels, fA, ['totals', 'total_co2_kg']);
  const bCost = mapSeriesByLabel(labels, fB, ['totals', 'total_cost_usd']);
  const bCo2 = mapSeriesByLabel(labels, fB, ['totals', 'total_co2_kg']);

  const volA = mapPlanVolumeByLabel(labels, planA);
  const volB = mapPlanVolumeByLabel(labels, planB);

  const lines = [
    'period,planA_volume_tons,planA_cost_usd,planA_co2_kg,planB_volume_tons,planB_cost_usd,planB_co2_kg,diff_cost_usd_B_minus_A,diff_co2_kg_B_minus_A',
  ];
  labels.forEach((label, i) => {
    const dCost = (bCost.mean[i] ?? 0) - (aCost.mean[i] ?? 0);
    const dCo2 = (bCo2.mean[i] ?? 0) - (aCo2.mean[i] ?? 0);
    lines.push(
      [
        label,
        volA[i] ?? 0,
        aCost.mean[i] ?? 0,
        aCo2.mean[i] ?? 0,
        volB[i] ?? 0,
        bCost.mean[i] ?? 0,
        bCo2.mean[i] ?? 0,
        dCost,
        dCo2,
      ].join(',')
    );
  });
  return lines.join('\n');
}

document.addEventListener('DOMContentLoaded', () => {
  requireAuthOrRedirect();
  mountNavbarProfileChip('profileChip');
  mountLogoutButton('logoutBtn');

  const statusEl = document.getElementById('status');
  const simSelect = document.getElementById('simulations');

  const totalsAEl = document.getElementById('totalsA');
  const totalsBEl = document.getElementById('totalsB');
  const totalsDiffEl = document.getElementById('totalsDiff');
  const volAEl = document.getElementById('volA');
  const volBEl = document.getElementById('volB');
  const diffHintEl = document.getElementById('diffHint');

  const exportBtn = document.getElementById('exportCsvBtn');

  const costNote = document.getElementById('costChartNote');
  const co2Note = document.getElementById('co2ChartNote');
  const diffNote = document.getElementById('diffChartNote');

  const stateA = { plan: [] };
  const stateB = { plan: [] };

  const editorA = createPlanEditor('A', stateA);
  const editorB = createPlanEditor('B', stateB);

  const copyAToBBtn = document.getElementById('copyAToBBtn');
  const copyBToABtn = document.getElementById('copyBToABtn');

  copyAToBBtn?.addEventListener('click', () => {
    editorA.getPlan();
    editorB.setPlan(stateA.plan);
    setStatus(document.getElementById('planStatusB'), 'Copied Plan A into Plan B.', 'success');
  });

  copyBToABtn?.addEventListener('click', () => {
    editorB.getPlan();
    editorA.setPlan(stateB.plan);
    setStatus(document.getElementById('planStatusA'), 'Copied Plan B into Plan A.', 'success');
  });

  let lastA = null;
  let lastB = null;

  function setExportEnabled(enabled) {
    if (!exportBtn) return;
    exportBtn.disabled = !enabled;
  }

  function updateTotals() {
    // totals and volumes (mean)
    if (lastA) {
      const aCost = getForecastSeries(lastA, ['totals', 'total_cost_usd']).mean;
      const aCo2 = getForecastSeries(lastA, ['totals', 'total_co2_kg']).mean;
      totalsAEl.textContent = `${safeCurrency(sum(aCost))} • ${safeNumber(sum(aCo2), ' kg CO₂')}`;
      volAEl.textContent = `Planned volume: ${safeNumber(sum(stateA.plan.map((r) => r.volumeTons)), ' tons')}`;
    } else {
      totalsAEl.textContent = '—';
      volAEl.textContent = '—';
    }

    if (lastB) {
      const bCost = getForecastSeries(lastB, ['totals', 'total_cost_usd']).mean;
      const bCo2 = getForecastSeries(lastB, ['totals', 'total_co2_kg']).mean;
      totalsBEl.textContent = `${safeCurrency(sum(bCost))} • ${safeNumber(sum(bCo2), ' kg CO₂')}`;
      volBEl.textContent = `Planned volume: ${safeNumber(sum(stateB.plan.map((r) => r.volumeTons)), ' tons')}`;
    } else {
      totalsBEl.textContent = '—';
      volBEl.textContent = '—';
    }

    if (lastA && lastB) {
      const aCost = sum(getForecastSeries(lastA, ['totals', 'total_cost_usd']).mean);
      const aCo2 = sum(getForecastSeries(lastA, ['totals', 'total_co2_kg']).mean);
      const bCost = sum(getForecastSeries(lastB, ['totals', 'total_cost_usd']).mean);
      const bCo2 = sum(getForecastSeries(lastB, ['totals', 'total_co2_kg']).mean);
      totalsDiffEl.textContent = `${safeCurrency(bCost - aCost)} • ${safeNumber(bCo2 - aCo2, ' kg CO₂')}`;
      diffHintEl.textContent = 'Positive means Plan B has higher impact than Plan A.';
    } else {
      totalsDiffEl.textContent = '—';
      diffHintEl.textContent = 'Run Compare to see differences.';
    }
  }

  function renderChartsAndTable() {
    const labels = alignLabels(lastA, lastB);

    // Charts: show A by default; if only one plan exists, chart that plan.
    const base = lastA || lastB;
    if (!base) return;

    const chartLabels = base.labels || labels;

    const costSeries = getForecastSeries(base, ['totals', 'total_cost_usd']);
    const co2Series = getForecastSeries(base, ['totals', 'total_co2_kg']);

    plotBandChart('costChart', chartLabels, costSeries, 'Total cost (USD)', undefined);
    plotBandChart('co2Chart', chartLabels, co2Series, 'Total CO₂ (kg)', undefined);

    if (costNote) {
      costNote.textContent = 'Band = 10th–90th percentile across simulations. Mean is the expected total cost each month.';
    }
    if (co2Note) {
      co2Note.textContent = 'Band = 10th–90th percentile across simulations. Mean is the expected total CO₂ each month.';
    }

    // Diff chart requires both
    if (lastA && lastB) {
      const allLabels = alignLabels(lastA, lastB);

      const aCost = mapSeriesByLabel(allLabels, lastA, ['totals', 'total_cost_usd']).mean;
      const aCo2 = mapSeriesByLabel(allLabels, lastA, ['totals', 'total_co2_kg']).mean;
      const bCost = mapSeriesByLabel(allLabels, lastB, ['totals', 'total_cost_usd']).mean;
      const bCo2 = mapSeriesByLabel(allLabels, lastB, ['totals', 'total_co2_kg']).mean;

      const dCost = allLabels.map((_, i) => (bCost[i] ?? 0) - (aCost[i] ?? 0));
      const dCo2 = allLabels.map((_, i) => (bCo2[i] ?? 0) - (aCo2[i] ?? 0));

      plotDiffChart('diffChart', allLabels, dCost, dCo2);
      if (diffNote) diffNote.textContent = 'Bars show the change if you switch from Plan A to Plan B (B − A).';

      buildResultsTable(allLabels, stateA.plan, stateB.plan, lastA, lastB);
      setExportEnabled(true);
    } else {
      const diffDiv=document.getElementById('diffChart'); if(diffDiv) Plotly.purge(diffDiv);
      if (diffNote) diffNote.textContent = 'Run both plans to see the scenario difference.';
      document.getElementById('resultsTableBody').innerHTML = '';
      setExportEnabled(false);
    }
  }

  async function runPlan(prefix) {
    const plan = prefix === 'A' ? editorA.getPlan() : editorB.getPlan();
    const planStatus = document.getElementById(`planStatus${prefix}`);

    if (!plan.length) {
      setStatus(planStatus, `Add at least one valid row (YYYY-MM and non-negative tons) for Plan ${prefix}.`, 'danger');
      return null;
    }

    const simulations = Number.parseInt(String(simSelect?.value ?? '500'), 10) || 500;

    try {
      setStatus(statusEl, `Running forecast for Plan ${prefix}...`, 'info');
      const result = await fetchForecast({ plannedVolumes: plan, simulations });

      if (prefix === 'A') lastA = result;
      else lastB = result;

      setStatus(planStatus, `Forecast ready for Plan ${prefix}.`, 'success');
      setStatus(statusEl, `Forecast complete for Plan ${prefix}.`, 'success');

      updateTotals();
      renderChartsAndTable();
      return result;
    } catch (e) {
      setStatus(planStatus, `Forecast failed for Plan ${prefix}. Check login and backend.`, 'danger');
      setStatus(statusEl, `Forecast failed for Plan ${prefix}.`, 'danger');
      return null;
    }
  }

  const runA = document.getElementById('runPlanABtn');
  const runB = document.getElementById('runPlanBBtn');
  const compareBtn = document.getElementById('comparePlansBtn');

  runA?.addEventListener('click', () => runPlan('A'));
  runB?.addEventListener('click', () => runPlan('B'));
  compareBtn?.addEventListener('click', async () => {
    await runPlan('A');
    await runPlan('B');
    if (lastA && lastB) {
      setStatus(statusEl, 'Comparison ready. Scroll to “Scenario difference”.', 'success');
    }
  });

  exportBtn?.addEventListener('click', () => {
    if (!lastA || !lastB) return;
    const labels = alignLabels(lastA, lastB);
    const csv = buildExportCsv(labels, stateA.plan, stateB.plan, lastA, lastB);
    const todayStr = new Date().toISOString().slice(0, 10);
    downloadText(`ecopackai_forecast_compare_${todayStr}.csv`, csv, 'text/csv');
  });

  // Give users a helpful starting point
  editorA.setPlan(nextMonths(6).map((m) => ({ period: m, volumeTons: 1 })));
  editorB.setPlan(nextMonths(6).map((m) => ({ period: m, volumeTons: 1 })));
});
