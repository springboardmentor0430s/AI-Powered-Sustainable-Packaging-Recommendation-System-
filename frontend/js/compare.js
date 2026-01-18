import {
  requireAuthOrRedirect,
  fetchMaterials,
  compareMaterials,
  mountNavbarProfileChip,
  mountLogoutButton,
  logout,
  fetchRecommendationHistory,
} from './api.js';

/*
 * Material Comparison page logic.
 *
 * This script drives the interactive comparison page where users can enter
 * product parameters, select how many materials to compare, choose the
 * specific materials (with an option to type a custom name), and view
 * the predicted cost and CO₂ impact side‑by‑side in a table and bar charts.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Enforce authentication
  if (!requireAuthOrRedirect()) return;
  // Mount profile chip and logout button
  mountNavbarProfileChip();
  mountLogoutButton();
  // Populate number of materials select (1–10)
  const numSelect = document.getElementById('numMaterials');
  if (numSelect) {
    for (let i = 1; i <= 10; i += 1) {
      const opt = document.createElement('option');
      opt.value = String(i);
      opt.textContent = String(i);
      numSelect.appendChild(opt);
    }
  }
  // Fetch list of available material names
  let materials = [];
  try {
    const res = await fetchMaterials();
    if (res && Array.isArray(res.materials)) {
      materials = res.materials;
    }
  } catch (err) {
    console.warn('Failed to fetch materials list:', err);
    materials = [];
  }
  const materialsContainer = document.getElementById('materialsContainer');
  function renderMaterialSelectors(n) {
    if (!materialsContainer) return;
    materialsContainer.innerHTML = '';
    const count = Number(n) || 0;
    for (let i = 0; i < count; i += 1) {
      const group = document.createElement('div');
      group.className = 'mb-3';
      const label = document.createElement('label');
      label.className = 'form-label';
      label.setAttribute('for', `materialSelect${i}`);
      label.textContent = `Material ${i + 1}`;
      const select = document.createElement('select');
      select.className = 'form-select';
      select.id = `materialSelect${i}`;
      select.setAttribute('data-index', String(i));
      select.required = true;
      // default empty option
      const emptyOpt = document.createElement('option');
      emptyOpt.value = '';
      emptyOpt.disabled = true;
      emptyOpt.selected = true;
      emptyOpt.textContent = 'Select a material';
      select.appendChild(emptyOpt);
      // populate names
      materials.forEach((name) => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        select.appendChild(opt);
      });
      // other option
      const otherOpt = document.createElement('option');
      otherOpt.value = '_other';
      otherOpt.textContent = 'Other';
      select.appendChild(otherOpt);
      // Hidden text input for custom material
      const otherInput = document.createElement('input');
      otherInput.type = 'text';
      otherInput.className = 'form-control mt-2 d-none';
      otherInput.id = `materialOther${i}`;
      otherInput.placeholder = 'Enter material name';
      otherInput.setAttribute('aria-label', `Custom material name ${i + 1}`);
      // Change handler: reveal/hide custom input
      select.addEventListener('change', (event) => {
        const val = event.target.value;
        if (val === '_other') {
          otherInput.classList.remove('d-none');
          otherInput.required = true;
        } else {
          otherInput.classList.add('d-none');
          otherInput.required = false;
          otherInput.value = '';
        }
      });
      group.appendChild(label);
      group.appendChild(select);
      group.appendChild(otherInput);
      materialsContainer.appendChild(group);
    }
  }
  // Update material selectors when number changes
  if (numSelect) {
    numSelect.addEventListener('change', (e) => {
      const value = e.target.value;
      renderMaterialSelectors(value);
    });
  }
  // Form submission: compare materials
  const form = document.getElementById('compareForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      // Validate form
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      // Show loading indicator
      const loadingEl = document.getElementById('compareLoading');
      const compareBtn = document.getElementById('compareBtn');
      if (loadingEl) loadingEl.style.display = 'block';
      if (compareBtn) compareBtn.disabled = true;
      // Collect form data
      const data = {
        productName: document.getElementById('cmpProductName').value.trim() || 'Generic Product',
        category: document.getElementById('cmpCategory').value,
        weightKg: parseFloat(document.getElementById('cmpWeightKg').value) || 0,
        fragility: parseInt(document.getElementById('cmpFragility').value) || 1,
        maxBudget: parseFloat(document.getElementById('cmpMaxBudget').value) || 0,
        shippingDistance: parseFloat(document.getElementById('cmpShippingDistance').value) || 0,
        moistureReq: parseInt(document.getElementById('cmpMoistureReq').value) || 0,
        oxygenSensitivity: parseInt(document.getElementById('cmpOxygenSensitivity').value) || 0,
        preferredBiodegradable: parseInt(document.querySelector('input[name="cmpPreferredBiodegradable"]:checked').value) || 0,
        preferredRecyclable: parseInt(document.querySelector('input[name="cmpPreferredRecyclable"]:checked').value) || 0,
        materials: [],
      };
      const nVal = parseInt(document.getElementById('numMaterials').value) || 0;
      for (let i = 0; i < nVal; i += 1) {
        const selectEl = document.getElementById(`materialSelect${i}`);
        if (!selectEl) continue;
        let name = selectEl.value;
        if (name === '_other') {
          const customInput = document.getElementById(`materialOther${i}`);
          name = customInput ? customInput.value.trim() : '';
        }
        if (name) data.materials.push(name);
      }
      try {
        const resp = await compareMaterials(data);
        const results = resp?.results || [];
        renderResults(results);
      } catch (err) {
        console.error('Compare materials error:', err);
        alert('Failed to compare materials. Please try again later.');
      } finally {
        if (loadingEl) loadingEl.style.display = 'none';
        if (compareBtn) compareBtn.disabled = false;
      }
    });
  }
  /**
   * Render the comparison table and update the charts.
   *
   * @param {Array<{material: string, predictedCost: number|null, predictedCO2: number|null, alternativeMaterial: string|null}>} results
   */
  function renderResults(results) {
    const resultsSection = document.getElementById('comparisonResults');
    const tbody = document.querySelector('#compareResultsTable tbody');
    if (!tbody || !resultsSection) return;
    tbody.innerHTML = '';
    const names = [];
    const costs = [];
    const co2s = [];
    if (!results || !results.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 4;
      td.className = 'text-muted';
      td.textContent = 'No comparison data available.';
      tr.appendChild(td);
      tbody.appendChild(tr);
      resultsSection.style.display = 'block';
      renderCharts(names, costs, co2s);
      return;
    }
    results.forEach((item) => {
      const tr = document.createElement('tr');
      const nameCell = document.createElement('th');
      nameCell.scope = 'row';
      nameCell.textContent = item.material || '';
      const costCell = document.createElement('td');
      const costVal = item.predictedCost;
      costCell.textContent = typeof costVal === 'number' ? costVal.toFixed(3) : '—';
      const co2Cell = document.createElement('td');
      const co2Val = item.predictedCO2;
      co2Cell.textContent = typeof co2Val === 'number' ? co2Val.toFixed(3) : '—';
      const altCell = document.createElement('td');
      altCell.textContent = item.alternativeMaterial || '—';
      tr.append(nameCell, costCell, co2Cell, altCell);
      tbody.appendChild(tr);
      names.push(item.material || '');
      costs.push(typeof costVal === 'number' ? costVal : 0);
      co2s.push(typeof co2Val === 'number' ? co2Val : 0);
    });
    resultsSection.style.display = 'block';
    renderCharts(names, costs, co2s);
  }
  /**
   * Draw cost and CO₂ bar charts using Plotly.
   *
   * @param {string[]} names
   * @param {number[]} costs
   * @param {number[]} co2s
   */
  function renderCharts(names, costs, co2s) {
    const Plotly = window.Plotly;
    const sharedConfig = { displayModeBar: false, responsive: true };
    // Cost bar chart
    Plotly.newPlot(
      'costHistogram',
      [
        {
          x: names,
          y: costs,
          type: 'bar',
          hovertemplate: '%{x}<br>Cost: $%{y:,.3f}<extra></extra>',
        },
      ],
      {
        margin: { t: 30, r: 15, b: 60, l: 60 },
        yaxis: { title: 'Cost (USD/unit)', rangemode: 'tozero' },
        xaxis: { title: 'Material', tickangle: -45 },
      },
      sharedConfig,
    );
    // CO₂ bar chart
    Plotly.newPlot(
      'co2Histogram',
      [
        {
          x: names,
          y: co2s,
          type: 'bar',
          hovertemplate: '%{x}<br>CO₂: %{y:,.3f} kg<extra></extra>',
        },
      ],
      {
        margin: { t: 30, r: 15, b: 60, l: 60 },
        yaxis: { title: 'CO₂ (kg/unit)', rangemode: 'tozero' },
        xaxis: { title: 'Material', tickangle: -45 },
      },
      sharedConfig,
    );
  }
  // ----------------------- PREFILL FROM PAST RUNS -----------------------
  // Attempt to load recommendation history and populate the prefill selector.  When a run
  // is selected, its product parameters will be used to prefill the form fields.
  const prefillSelect = document.getElementById('prefillRunSelect');
  if (prefillSelect) {
    let runs = [];
    try {
      const res = await fetchRecommendationHistory();
      runs = Array.isArray(res?.history) ? res.history : [];
    } catch (err) {
      console.warn('Unable to fetch recommendation history:', err);
      runs = [];
    }

    // Helper to format run label for display
    function formatRunLabel(run) {
      const dateStr = run.createdAt ? new Date(run.createdAt).toLocaleString() : 'Unknown date';
      const product = run.productName || 'Unnamed product';
      const category = run.category || 'Uncategorised';
      return `${product} – ${category} (${dateStr})`;
    }

    // Populate options
    prefillSelect.innerHTML = '';
    if (runs.length > 0) {
      // Optional: manual entry option if user wants to clear prefill
      const manualOpt = document.createElement('option');
      manualOpt.value = '';
      manualOpt.textContent = 'Enter parameters manually';
      prefillSelect.appendChild(manualOpt);
      // Add each run as an option
      runs.forEach((run, index) => {
        const opt = document.createElement('option');
        opt.value = String(run.id);
        opt.textContent = formatRunLabel(run);
        prefillSelect.appendChild(opt);
      });
      // Select the most recent run by default (index 0).  If manual entry is first, select second.
      // Preselect the first run in list (most recent) unless manual entry is desired.
      if (prefillSelect.options.length > 1) {
        prefillSelect.selectedIndex = 1; // skip manual entry option
        prefillFormWithRun(runs[0]);
      }
    } else {
      // If no runs exist, provide a disabled option
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'No previous runs available';
      opt.disabled = true;
      prefillSelect.appendChild(opt);
    }
    // Event listener to prefill form when run is selected
    prefillSelect.addEventListener('change', (e) => {
      const selectedValue = e.target.value;
      if (!selectedValue) {
        // Manual entry selected; do not change current values
        return;
      }
      const run = runs.find((r) => String(r.id) === String(selectedValue));
      if (run) prefillFormWithRun(run);
    });
    /**
     * Prefill the product input fields with values from a previous run.  The function safely
     * assigns values to each form input.  If a category in the run is not present in the
     * predefined select options, it will be appended as a temporary option so that it can be
     * selected.  Users can still modify any field after prefill.
     *
     * @param {Object} run A recommendation history record containing product parameters
     */
    function prefillFormWithRun(run) {
      // Product name
      const productNameEl = document.getElementById('cmpProductName');
      if (productNameEl && run.productName) productNameEl.value = run.productName;
      // Category
      const categoryEl = document.getElementById('cmpCategory');
      if (categoryEl) {
        const value = run.category || '';
        let found = false;
        Array.from(categoryEl.options).forEach((opt) => {
          if (String(opt.value) === String(value)) {
            opt.selected = true;
            found = true;
          } else {
            opt.selected = false;
          }
        });
        // If not found, add temporary option and select it
        if (!found && value) {
          const tempOpt = document.createElement('option');
          tempOpt.value = value;
          tempOpt.textContent = value;
          tempOpt.selected = true;
          categoryEl.appendChild(tempOpt);
        }
      }
      // Numeric fields
      const weightEl = document.getElementById('cmpWeightKg');
      if (weightEl && Number.isFinite(run.weightKg)) weightEl.value = String(run.weightKg);
      const fragEl = document.getElementById('cmpFragility');
      if (fragEl && Number.isFinite(run.fragility)) fragEl.value = String(run.fragility);
      const budgetEl = document.getElementById('cmpMaxBudget');
      if (budgetEl && Number.isFinite(run.maxBudget)) budgetEl.value = String(run.maxBudget);
      const distEl = document.getElementById('cmpShippingDistance');
      if (distEl && Number.isFinite(run.shippingDistance)) distEl.value = String(run.shippingDistance);
      const moistureEl = document.getElementById('cmpMoistureReq');
      if (moistureEl && Number.isFinite(run.moistureReq)) moistureEl.value = String(run.moistureReq);
      const oxygenEl = document.getElementById('cmpOxygenSensitivity');
      if (oxygenEl && Number.isFinite(run.oxygenSensitivity)) oxygenEl.value = String(run.oxygenSensitivity);
      // Preferences (radio buttons)
      const bioYes = document.getElementById('cmpBioYes');
      const bioNo = document.getElementById('cmpBioNo');
      if (bioYes && bioNo && typeof run.preferredBiodegradable !== 'undefined') {
        if (String(run.preferredBiodegradable) === '1') {
          bioYes.checked = true;
        } else {
          bioNo.checked = true;
        }
      }
      const recYes = document.getElementById('cmpRecYes');
      const recNo = document.getElementById('cmpRecNo');
      if (recYes && recNo && typeof run.preferredRecyclable !== 'undefined') {
        if (String(run.preferredRecyclable) === '1') {
          recYes.checked = true;
        } else {
          recNo.checked = true;
        }
      }
      // We intentionally do not prefill the number of materials or materials list; these
      // remain user-driven choices on the comparison page.
    }
  }
});