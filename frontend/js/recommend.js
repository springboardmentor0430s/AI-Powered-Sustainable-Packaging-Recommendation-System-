import {
  fetchRecommendations,
  submitFeedback,
  requireAuthOrRedirect,
  logout,
  mountNavbarProfileChip,
  mountLogoutButton,
  fetchRecommendationHistory,
} from './api.js';

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
});

const decimalFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

const wholeNumberFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const toNumber = (value) => {
  const cast = Number(value);
  return Number.isFinite(cast) ? cast : 0;
};

// ----------------------- SMART AUTOFILL CONFIG -----------------------
// Mapping of known product names to suggested categories and default values.
// These suggestions are heuristics to streamline data entry for users.  When
// the user selects or types a product name matching a key in this object,
// the corresponding category and weight (and optionally fragility) fields
// will be prefilled automatically.  Extend or adjust these entries to
// support additional products.
const AUTO_FILL_MAP = {
  'Milk Bottle': { category: 'Milk & Dairy', weightKg: 1.0, fragility: 2 },
  'Snack Box': { category: 'Bakery & Snacks', weightKg: 0.5, fragility: 3 },
  'Cereal Box': { category: 'Grains & Staples', weightKg: 0.7, fragility: 2 },
  'Chocolate Bar': { category: 'Confectionery', weightKg: 0.1, fragility: 1 },
  'Chips Packet': { category: 'Snacks & Nuts', weightKg: 0.2, fragility: 1 },
  'Sauce Bottle': { category: 'Condiments & Sauces', weightKg: 0.5, fragility: 3 },
  'Fresh Produce Bag': { category: 'Fresh Produce', weightKg: 1.0, fragility: 1 },
};

// Backend returns per-unit predictions.
const formatCost = (value) => (Number.isFinite(value) ? `${currencyFormatter.format(value)} / unit` : 'N/A');
const formatCO2 = (value) => (Number.isFinite(value) ? `${decimalFormatter.format(value)} kg / unit` : 'N/A');
const formatScore = (value) => (Number.isFinite(value) ? `${wholeNumberFormatter.format(value)} / 100` : 'N/A');

// Key used to track runs that the user has hidden from the UI.  Deleted runs
// remain in the database but will no longer appear in the history table.  We
// persist this list in localStorage so the UI remains consistent across
// sessions.
const DELETED_RUNS_KEY = 'ecopackai_deleted_runs';

function loadDeletedRuns() {
  try {
    const raw = localStorage.getItem(DELETED_RUNS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.warn('Unable to load deleted runs:', err);
    return [];
  }
}

function saveDeletedRuns(list) {
  try {
    localStorage.setItem(DELETED_RUNS_KEY, JSON.stringify(list || []));
  } catch (err) {
    console.warn('Unable to save deleted runs:', err);
  }
}

// ---------------- NEW: shimmer placeholders ----------------
function showShimmer() {
  const cards = document.getElementById('recommendationCards');
  const tbody = document.getElementById('rankingTableBody');
  const results = document.getElementById('resultsSection');
  const badge = document.getElementById('resultsCountBadge');

  if (!cards || !tbody || !results || !badge) return;

  results.style.display = 'block';
  badge.textContent = 'Evaluating materials…';

  cards.innerHTML = '';
  for (let i = 0; i < 3; i += 1) {
    const col = document.createElement('div');
    col.className = 'col-md-4';
    col.innerHTML = `
      <div class="shimmer shimmer-block h-100" aria-label="Loading recommendation">
        <div class="shimmer-line w-40"></div>
        <div class="shimmer-line w-70"></div>
        <div class="shimmer-line w-85"></div>
        <div class="shimmer-line w-55"></div>
      </div>
    `;
    cards.appendChild(col);
  }

  tbody.innerHTML = `
    <tr>
      <td colspan="6">
        <div class="shimmer shimmer-block" aria-label="Loading ranking table">
          <div class="shimmer-line w-85"></div>
          <div class="shimmer-line w-70"></div>
          <div class="shimmer-line w-55"></div>
        </div>
      </td>
    </tr>
  `;
}
// -----------------------------------------------------------

// Convert backend record -> UI record (aligned to patched backend prediction.py)
function normalizeRecommendation(rec) {
  // Prefer explicit material name fields from backend.  Avoid falling back to
  // MaterialType when the name is missing because that can produce generic
  // values like "Material" which are confusing for users.  If nothing
  // sensible is available, provide a clear placeholder.
  let materialName = rec.materialName || rec.MaterialName;
  if (!materialName || typeof materialName !== 'string' || !materialName.trim()) {
    // Only use MaterialType if it appears to contain a descriptive phrase (e.g.
    // "Paper/Cardboard"), otherwise ignore it.  Some malformed results had
    // plain values like "Material" which should not be shown to users.
    const candidate = rec.MaterialType || rec.materialType;
    if (candidate && typeof candidate === 'string' && candidate.trim().length > 1 && candidate.toLowerCase() !== 'material') {
      materialName = candidate.trim();
    } else {
      materialName = 'Unknown material';
    }
  }

  // Patched backend: predictedCost, predictedCO2
  const predictedCost = toNumber(rec.predictedCost ?? rec.predictedCostUSD ?? rec.predicted_cost_unit_usd);
  const predictedCO2 = toNumber(rec.predictedCO2 ?? rec.predictedCO2KG ?? rec.predicted_co2_unit_kg);

  // Patched backend: suitabilityScore and rankingScore are already 0..100
  const suitability = toNumber(rec.suitabilityScore ?? rec.suitability_score);
  const ranking = toNumber(rec.rankingScore ?? rec.ranking_score);

  // Prefer suitabilityScore if present; else fall back to rankingScore.
  const suitabilityScore = Math.max(0, Math.min(100, Math.round(suitability || ranking)));

  const recommendationReason =
    rec.reason ||
    rec.recommendationReason ||
    rec.recommendation_reason ||
    'Optimised for sustainability and cost.';

  // Extract detailed explanation and confidence score if provided by the backend
  const explanation = rec.explanation || rec.detailedExplanation || rec.detailed_explanation || {};
  const confidence = toNumber(rec.confidenceScore ?? rec.confidence_score);

  return {
    materialName,
    predictedCost,
    predictedCO2,
    suitabilityScore,
    recommendationReason,
    explanation,
    confidenceScore: Number.isFinite(confidence) && confidence >= 0 ? confidence : null,
  };
}

const extractReason = (rec) => rec.recommendationReason || rec.recommendationReason === ''
  ? rec.recommendationReason
  : 'Optimised for sustainability and cost.';

const updateSummaryCards = (recs) => {
  const metricTopScore = document.getElementById('metricTopScore');
  const metricTopMaterial = document.getElementById('metricTopMaterial');
  const metricCost = document.getElementById('metricCost');
  const metricCO2 = document.getElementById('metricCO2');

  if (!metricTopScore || !metricTopMaterial || !metricCost || !metricCO2) return;

  if (!recs.length) {
    metricTopScore.textContent = '—';
    metricTopMaterial.textContent = 'Awaiting results';
    metricCost.textContent = '—';
    metricCO2.textContent = '—';
    return;
  }

  const byScore = [...recs].sort((a, b) => (b.suitabilityScore ?? 0) - (a.suitabilityScore ?? 0));
  const topScore = byScore[0];

  metricTopScore.textContent = formatScore(topScore.suitabilityScore);
  metricTopMaterial.textContent = topScore.materialName || 'Top material';

  const sortedByCost = [...recs].sort((a, b) => (a.predictedCost ?? Infinity) - (b.predictedCost ?? Infinity));
  metricCost.textContent = formatCost(sortedByCost[0]?.predictedCost);

  const sortedByCo2 = [...recs].sort((a, b) => (a.predictedCO2 ?? Infinity) - (b.predictedCO2 ?? Infinity));
  metricCO2.textContent = formatCO2(sortedByCo2[0]?.predictedCO2);
};

const renderRecommendationCards = (recs) => {
  const container = document.getElementById('recommendationCards');
  if (!container) return;

  container.innerHTML = '';
  if (!recs.length) {
    const placeholder = document.createElement('p');
    placeholder.className = 'text-muted mb-0';
    placeholder.textContent = 'No recommendations available yet.';
    container.appendChild(placeholder);
    return;
  }

  recs.slice(0, 3).forEach((rec, index) => {
    const col = document.createElement('div');
    col.className = 'col-md-4';

    const card = document.createElement('div');
    card.className = 'material-card h-100 shadow-sm';

    const badge = document.createElement('span');
    badge.className = 'material-pill align-self-start';
    badge.innerHTML = `<i class="bi bi-award me-1" aria-hidden="true"></i>Rank ${index + 1}`;

    const title = document.createElement('h4');
    title.className = 'h5 mb-1';
    title.textContent = rec.materialName;

    const reason = document.createElement('p');
    reason.className = 'text-muted small mb-2';
    reason.textContent = extractReason(rec);

    const metricsList = document.createElement('ul');
    metricsList.className = 'list-unstyled mb-0';

    const costItem = document.createElement('li');
    costItem.innerHTML = `<span class="metric-label"><i class="bi bi-currency-dollar me-1" aria-hidden="true"></i>Predicted cost</span>
      <div class="metric-value">${formatCost(rec.predictedCost)}</div>`;

    const co2Item = document.createElement('li');
    co2Item.className = 'mt-2';
    co2Item.innerHTML = `<span class="metric-label"><i class="bi bi-cloud me-1" aria-hidden="true"></i>Predicted CO₂</span>
      <div class="metric-value">${formatCO2(rec.predictedCO2)}</div>`;

    const scoreItem = document.createElement('li');
    scoreItem.className = 'mt-2';
    scoreItem.innerHTML = `<span class="metric-label"><i class="bi bi-speedometer2 me-1" aria-hidden="true"></i>Suitability</span>
      <div class="metric-value">${formatScore(rec.suitabilityScore)}</div>`;

    // Confidence item
    const confItem = document.createElement('li');
    confItem.className = 'mt-2';
    if (Number.isFinite(rec.confidenceScore)) {
      confItem.innerHTML = `<span class="metric-label"><i class="bi bi-shield-check me-1" aria-hidden="true"></i>Confidence</span>
        <div class="metric-value">${Number(rec.confidenceScore).toFixed(1)}%</div>`;
    }

    metricsList.append(costItem, co2Item, scoreItem);
    if (confItem.innerHTML) {
      metricsList.append(confItem);
    }

    // Prepare detailed explanation as a collapsible <details> element for accessibility.
    let detailsEl = null;
    if (rec.explanation && typeof rec.explanation === 'object' && Object.keys(rec.explanation).length > 0) {
      const details = document.createElement('details');
      details.className = 'mt-3';
      const summary = document.createElement('summary');
      summary.textContent = 'Why this material?';
      summary.className = 'fw-semibold';
      details.appendChild(summary);
      const explList = document.createElement('ul');
      explList.className = 'list-unstyled mb-0';
      Object.entries(rec.explanation).forEach(([key, text]) => {
        const li = document.createElement('li');
        li.className = 'small';
        li.textContent = text;
        explList.appendChild(li);
      });
      details.appendChild(explList);
      detailsEl = details;
    }

    // Append elements in order: badge, title, reason, metrics, (optional) details
    card.append(badge, title, reason, metricsList);
    if (detailsEl) {
      card.append(detailsEl);
    }
    col.appendChild(card);
    container.appendChild(col);
  });
};

const renderRankingTable = (recs) => {
  const tbody = document.getElementById('rankingTableBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (!recs.length) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 6;
    cell.className = 'text-center text-muted';
    cell.textContent = 'No suitable materials found. Adjust your constraints and try again.';
    row.appendChild(cell);
    tbody.appendChild(row);
    return;
  }

  const sorted = [...recs].sort((a, b) => (b.suitabilityScore ?? 0) - (a.suitabilityScore ?? 0));

  sorted.forEach((rec, index) => {
    const row = document.createElement('tr');

    const rankCell = document.createElement('th');
    rankCell.scope = 'row';
    rankCell.textContent = index + 1;

    const nameCell = document.createElement('td');
    nameCell.textContent = rec.materialName;

    const costCell = document.createElement('td');
    costCell.textContent = Number.isFinite(rec.predictedCost) ? currencyFormatter.format(rec.predictedCost) : 'N/A';

    const co2Cell = document.createElement('td');
    co2Cell.textContent = Number.isFinite(rec.predictedCO2) ? decimalFormatter.format(rec.predictedCO2) : 'N/A';

    const scoreCell = document.createElement('td');
    scoreCell.textContent = Number.isFinite(rec.suitabilityScore)
      ? `${wholeNumberFormatter.format(rec.suitabilityScore)}`
      : 'N/A';

    const highlightCell = document.createElement('td');
    // Show the concise reason and confidence if available
    const reasonText = extractReason(rec);
    const conf = rec.confidenceScore;
    if (typeof conf === 'number' && !Number.isNaN(conf)) {
      highlightCell.innerHTML = `${reasonText}<br><span class="text-muted small">Confidence: ${Number(conf).toFixed(1)}%</span>`;
    } else {
      highlightCell.textContent = reasonText;
    }

    row.append(rankCell, nameCell, costCell, co2Cell, scoreCell, highlightCell);
    tbody.appendChild(row);
  });
};

// ------------------- History rendering -------------------
/**
 * Format an ISO timestamp into a human-friendly date/time string.  If the
 * input is invalid or empty, returns an em dash.
 *
 * @param {string} iso ISO timestamp
 * @returns {string}
 */
function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  // Use locale-sensitive formatting; includes date and time for clarity
  return d.toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/**
 * Render the history table with a list of past recommendation runs.  If no
 * history is available, the empty message is shown instead.  Assumes
 * descending order (most recent first).
 *
 * @param {Array<object>} history List of run objects from the API
 */
function renderHistoryTable(history) {
  const tbody = document.getElementById('historyTableBody');
  const emptyMsg = document.getElementById('historyEmptyMessage');
  if (!tbody || !emptyMsg) return;
  tbody.innerHTML = '';
  if (!history || !history.length) {
    emptyMsg.style.display = 'block';
    return;
  }
  emptyMsg.style.display = 'none';
  // Filter out any runs that the user has chosen to hide.  This ensures
  // the delete button only affects the UI while the underlying data remains
  // intact in the database.
  const deletedRuns = loadDeletedRuns();
  const visibleHistory = history.filter((r) => !deletedRuns.includes(String(r.id)));
  visibleHistory.forEach((run, idx) => {
    const row = document.createElement('tr');
    // Run number
    const runCell = document.createElement('th');
    runCell.scope = 'row';
    runCell.textContent = idx + 1;
    // Date/time
    const dateCell = document.createElement('td');
    dateCell.textContent = formatDateTime(run.createdAt);
    // Product name (with category)
    const productCell = document.createElement('td');
    const name = run.productName || '—';
    const cat = run.category || '';
    productCell.textContent = cat ? `${name} (${cat})` : name;
    // Parameters: build descriptive string
    const paramsCell = document.createElement('td');
    paramsCell.className = 'small';
    const parts = [];
    if (Number.isFinite(run.weightKg)) parts.push(`Weight: ${Number(run.weightKg).toFixed(2)}kg`);
    if (Number.isFinite(run.fragility)) parts.push(`Fragility: ${run.fragility}`);
    if (Number.isFinite(run.maxBudget)) parts.push(`Budget: $${Number(run.maxBudget).toFixed(2)}`);
    if (Number.isFinite(run.shippingDistance)) parts.push(`Distance: ${Number(run.shippingDistance).toFixed(0)}km`);
    if (Number.isFinite(run.moistureReq)) parts.push(`Moisture: ${run.moistureReq}`);
    if (Number.isFinite(run.oxygenSensitivity)) parts.push(`O₂: ${run.oxygenSensitivity}`);
    if (run.preferredBiodegradable !== undefined && run.preferredBiodegradable !== null) parts.push(`Bio: ${run.preferredBiodegradable ? 'Yes' : 'No'}`);
    if (run.preferredRecyclable !== undefined && run.preferredRecyclable !== null) parts.push(`Recyclable: ${run.preferredRecyclable ? 'Yes' : 'No'}`);
    paramsCell.textContent = parts.join('; ');
    // Top material
    const topCell = document.createElement('td');
    topCell.textContent = run.topMaterialName || '—';
    // Score
    const scoreCell = document.createElement('td');
    if (Number.isFinite(run.topScore)) {
      scoreCell.textContent = Math.round(Number(run.topScore)).toString();
    } else {
      scoreCell.textContent = '—';
    }
    // Action cell with load and delete buttons
    const actionCell = document.createElement('td');
    actionCell.className = 'd-flex gap-1';
    // Load button to prefill the form
    const loadBtn = document.createElement('button');
    loadBtn.type = 'button';
    loadBtn.className = 'btn btn-sm btn-outline-primary';
    loadBtn.textContent = 'Load';
    loadBtn.setAttribute('aria-label', 'Load parameters into form');
    loadBtn.addEventListener('click', () => {
      prefillProductForm(run);
      const formEl = document.getElementById('productForm');
      if (formEl) formEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    // Delete button to hide this run from the table
    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'btn btn-sm btn-link text-danger';
    delBtn.setAttribute('aria-label', 'Hide this run from history');
    delBtn.innerHTML = '<i class="bi bi-x-circle" aria-hidden="true"></i>';
    delBtn.addEventListener('click', () => {
      const list = loadDeletedRuns();
      list.push(String(run.id));
      saveDeletedRuns(list);
      // Remove the row visually
      row.remove();
      // If after removal the table is empty, show the empty message
      if (!tbody.querySelector('tr')) {
        emptyMsg.style.display = 'block';
      }
    });
    actionCell.appendChild(loadBtn);
    actionCell.appendChild(delBtn);
    row.append(runCell, dateCell, productCell, paramsCell, topCell, scoreCell, actionCell);
    tbody.appendChild(row);
  });
}

/**
 * Fetch history from the backend and update the table.  Swallows errors
 * silently to avoid interrupting the main flow.
 */
// Maintain a copy of the full history to enable client‑side filtering by category.
let historyData = [];

async function loadAndRenderHistory() {
  try {
    const data = await fetchRecommendationHistory(20);
    const history = Array.isArray(data?.history) ? data.history : [];
    historyData = history;
    filterAndRenderHistory();
  } catch (err) {
    console.error('Failed to load history', err);
    historyData = [];
    filterAndRenderHistory();
  }
}

// Populate the category filter select with the same options as the main category select.
function populateHistoryCategoryFilter() {
  const filterEl = document.getElementById('historyCategoryFilter');
  const categorySelect = document.getElementById('category');
  if (!filterEl || !categorySelect) return;
  // Remove any existing options except the first (All categories)
  while (filterEl.options.length > 1) {
    filterEl.remove(1);
  }
  // Copy options from the main category select
  const opts = categorySelect.querySelectorAll('option');
  opts.forEach((opt) => {
    const value = opt.value;
    const text = opt.textContent;
    if (value && !opt.disabled) {
      const newOpt = document.createElement('option');
      newOpt.value = value;
      newOpt.textContent = text;
      filterEl.appendChild(newOpt);
    }
  });
}

// Render the history table using the currently selected category filter.  If
// 'All categories' is selected (empty value), the full historyData is used.
function filterAndRenderHistory() {
  const filterEl = document.getElementById('historyCategoryFilter');
  let filtered = historyData || [];
  if (filterEl && filterEl.value) {
    const cat = filterEl.value;
    filtered = (historyData || []).filter((r) => String(r.category || '') === String(cat));
  }
  renderHistoryTable(filtered);
}

/**
 * Prefill the product input form using values from a previous run.  This helper
 * allows analysts to quickly reproduce or tweak past runs.  Only existing
 * input fields are updated; missing values are ignored.  Radio buttons for
 * preferences are set appropriately.
 *
 * @param {object} run A run record from the history API
 */
function prefillProductForm(run) {
  if (!run) return;
  const nameEl = document.getElementById('productName');
  if (nameEl && run.productName) nameEl.value = run.productName;
  const categoryEl = document.getElementById('category');
  if (categoryEl && run.category) categoryEl.value = run.category;
  const weightEl = document.getElementById('weightKg');
  if (weightEl && Number.isFinite(run.weightKg)) weightEl.value = Number(run.weightKg).toFixed(2);
  const fragilityEl = document.getElementById('fragility');
  if (fragilityEl && Number.isFinite(run.fragility)) fragilityEl.value = run.fragility;
  const budgetEl = document.getElementById('maxBudget');
  if (budgetEl && Number.isFinite(run.maxBudget)) budgetEl.value = Number(run.maxBudget).toFixed(2);
  const distanceEl = document.getElementById('shippingDistance');
  if (distanceEl && Number.isFinite(run.shippingDistance)) distanceEl.value = Number(run.shippingDistance).toFixed(0);
  const moistureEl = document.getElementById('moistureReq');
  if (moistureEl && Number.isFinite(run.moistureReq)) moistureEl.value = run.moistureReq;
  const oxygenEl = document.getElementById('oxygenSensitivity');
  if (oxygenEl && Number.isFinite(run.oxygenSensitivity)) oxygenEl.value = run.oxygenSensitivity;
  // Radio buttons for biodegradability preference
  if (run.preferredBiodegradable !== undefined && run.preferredBiodegradable !== null) {
    const bioYes = document.getElementById('bioYes');
    const bioNo = document.getElementById('bioNo');
    if (bioYes && bioNo) {
      if (parseInt(run.preferredBiodegradable, 10) === 1) {
        bioYes.checked = true;
      } else {
        bioNo.checked = true;
      }
    }
  }
  // Radio buttons for recyclability preference
  if (run.preferredRecyclable !== undefined && run.preferredRecyclable !== null) {
    const recYes = document.getElementById('recYes');
    const recNo = document.getElementById('recNo');
    if (recYes && recNo) {
      if (parseInt(run.preferredRecyclable, 10) === 1) {
        recYes.checked = true;
      } else {
        recNo.checked = true;
      }
    }
  }
  // Reset form validation state so the user can submit again
  const form = document.getElementById('productForm');
  if (form) form.classList.remove('was-validated');
}

const resetResults = () => {
  const resultsSection = document.getElementById('resultsSection');
  const recommendationCards = document.getElementById('recommendationCards');
  const rankingTableBody = document.getElementById('rankingTableBody');
  const resultsCountBadge = document.getElementById('resultsCountBadge');

  if (!resultsSection || !recommendationCards || !rankingTableBody || !resultsCountBadge) return;

  resultsSection.style.display = 'none';
  recommendationCards.innerHTML = '';
  rankingTableBody.innerHTML = '';
  resultsCountBadge.textContent = '0 materials evaluated';
  updateSummaryCards([]);
};

// Store the last submitted product data for what-if recalculation
let lastProductData = null;
let lastRunId = null;

document.addEventListener('DOMContentLoaded', () => {
  // Enforce auth
  if (!requireAuthOrRedirect()) return;

  // profile chip + logout
  mountNavbarProfileChip();
  mountLogoutButton();

  // Populate the category filter with the same options as the main category select.
  populateHistoryCategoryFilter();
  const filterEl = document.getElementById('historyCategoryFilter');
  if (filterEl) {
    filterEl.addEventListener('change', () => {
      filterAndRenderHistory();
    });
  }

  // Load and render the history table on initial page load
  loadAndRenderHistory();

  // ----------------------- SMART AUTOFILL ON PRODUCT NAME -----------------------
  // When the product name changes, attempt to auto-fill category, weight and
  // fragility based on predefined suggestions.  This enhances usability by
  // reducing the amount of manual input required for common products.
  const productNameInput = document.getElementById('productName');
  if (productNameInput) {
    productNameInput.addEventListener('change', () => {
      const name = productNameInput.value ? productNameInput.value.trim() : '';
      if (!name) return;
      const suggestion = AUTO_FILL_MAP[name];
      if (suggestion) {
        // Auto-select the appropriate category option
        const categorySelect = document.getElementById('category');
        if (categorySelect && suggestion.category) {
          Array.from(categorySelect.options).forEach((opt) => {
            opt.selected = String(opt.value) === String(suggestion.category);
          });
        }
        // Prefill weight value
        const weightInput = document.getElementById('weightKg');
        if (weightInput && suggestion.weightKg) {
          weightInput.value = suggestion.weightKg;
        }
        // Prefill fragility
        const fragilityInput = document.getElementById('fragility');
        if (fragilityInput && typeof suggestion.fragility === 'number') {
          fragilityInput.value = suggestion.fragility;
        }
      }
    });
  }

  const form = document.getElementById('productForm');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const resultsSection = document.getElementById('resultsSection');
  const resultsCountBadge = document.getElementById('resultsCountBadge');

  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (!form.checkValidity()) {
      form.classList.add('was-validated');
      return;
    }

    resetResults();

    // ✅ NEW: oxygenSensitivity added (0..10)
    const oxygenEl = document.getElementById('oxygenSensitivity');
    const oxygenSensitivity = oxygenEl ? parseInt(oxygenEl.value, 10) : 5;

    const data = {
      productName: document.getElementById('productName').value.trim(),
      category: document.getElementById('category').value,
      weightKg: parseFloat(document.getElementById('weightKg').value),
      fragility: parseInt(document.getElementById('fragility').value, 10),
      preferredBiodegradable: parseInt(form.elements.preferredBiodegradable.value, 10),
      preferredRecyclable: parseInt(form.elements.preferredRecyclable.value, 10),
      shippingDistance: parseFloat(document.getElementById('shippingDistance').value),
      moistureReq: parseInt(document.getElementById('moistureReq').value, 10),
      oxygenSensitivity, // ✅ NEW FIELD SENT TO BACKEND
      maxBudget: parseFloat(document.getElementById('maxBudget').value),
    };

    // show shimmer immediately
    showShimmer();

    if (loadingIndicator) loadingIndicator.style.display = 'block';

    try {
      const response = await fetchRecommendations(data);
      const rawRecs = response.recommendations || [];
      lastRunId = response.runId || null;
      const recs = rawRecs.map(normalizeRecommendation);

      // Save data for what-if scenario
      lastProductData = { ...data };

      if (resultsCountBadge) {
        resultsCountBadge.textContent = `${recs.length} material${recs.length === 1 ? '' : 's'} evaluated`;
      }

      updateSummaryCards(recs);
      renderRecommendationCards(recs);
      renderRankingTable(recs);

      if (resultsSection) resultsSection.style.display = 'block';

      // Show feedback section since we have a run ID
      const feedbackSection = document.getElementById('feedbackSection');
      if (feedbackSection && lastRunId) {
        feedbackSection.style.display = 'block';
        const status = document.getElementById('feedbackStatus');
        if (status) status.textContent = '';
      }

      // Show and reset what-if section when results are available
      const whatIfSection = document.getElementById('whatIfSection');
      if (whatIfSection) {
        whatIfSection.style.display = 'block';
        const budgetSlider = document.getElementById('budgetMultiplier');
        const shipSlider = document.getElementById('shippingMultiplier');
        const budgetVal = document.getElementById('budgetMultiplierValue');
        const shipVal = document.getElementById('shippingMultiplierValue');
        if (budgetSlider) budgetSlider.value = 0;
        if (shipSlider) shipSlider.value = 0;
        if (budgetVal) budgetVal.textContent = '0%';
        if (shipVal) shipVal.textContent = '0%';
        const status = document.getElementById('whatIfStatus');
        if (status) status.textContent = '';
      }

      // Refresh history after a successful run
      loadAndRenderHistory();
    } catch (error) {
      const msg = String(error?.message || error);
      console.error('Recommendation error:', error);

      // If token expired/invalid, force login
      if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
        logout();
        window.location.href = 'login.html';
        return;
      }

      const tbody = document.getElementById('rankingTableBody');
      if (tbody) {
        tbody.innerHTML = '';
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 6;
        cell.className = 'text-danger text-center';
        cell.textContent = 'An error occurred while fetching recommendations. Please try again later.';
        row.appendChild(cell);
        tbody.appendChild(row);
      }

      if (resultsSection) resultsSection.style.display = 'block';
    } finally {
      if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
  });

  // --- What-if scenario controls ---
  const budgetSlider = document.getElementById('budgetMultiplier');
  const shipSlider = document.getElementById('shippingMultiplier');
  const budgetVal = document.getElementById('budgetMultiplierValue');
  const shipVal = document.getElementById('shippingMultiplierValue');
  if (budgetSlider && budgetVal) {
    budgetSlider.addEventListener('input', () => {
      budgetVal.textContent = `${budgetSlider.value}%`;
    });
  }
  if (shipSlider && shipVal) {
    shipSlider.addEventListener('input', () => {
      shipVal.textContent = `${shipSlider.value}%`;
    });
  }
  const applyBtn = document.getElementById('applyWhatIf');
  if (applyBtn) {
    applyBtn.addEventListener('click', async () => {
      // Ensure we have a baseline product
      if (!lastProductData) return;
      const statusElem = document.getElementById('whatIfStatus');
      const bPct = budgetSlider ? parseFloat(budgetSlider.value) : 0;
      const sPct = shipSlider ? parseFloat(shipSlider.value) : 0;
      // Build new data adjusting maxBudget and shippingDistance
      const newData = { ...lastProductData };
      if (!Number.isNaN(bPct)) {
        newData.maxBudget = parseFloat((lastProductData.maxBudget * (1 + bPct / 100)).toFixed(2));
      }
      if (!Number.isNaN(sPct)) {
        newData.shippingDistance = parseFloat((lastProductData.shippingDistance * (1 + sPct / 100)).toFixed(2));
      }
      // Indicate loading
      if (statusElem) statusElem.textContent = 'Recalculating recommendations…';
      showShimmer();
      try {
        const response = await fetchRecommendations(newData);
        const rawRecs = response.recommendations || [];
        const recs = rawRecs.map(normalizeRecommendation);
        lastRunId = response.runId || lastRunId;
        // Update original results section
        updateSummaryCards(recs);
        renderRecommendationCards(recs);
        renderRankingTable(recs);
        const resultsCountBadge = document.getElementById('resultsCountBadge');
        if (resultsCountBadge) {
          resultsCountBadge.textContent = `${recs.length} material${recs.length === 1 ? '' : 's'} evaluated`;
        }
        if (statusElem) statusElem.textContent = 'Updated results.';

        // Refresh history after recomputing recommendations
        loadAndRenderHistory();
      } catch (err) {
        const msg = String(err?.message || err);
        if (statusElem) statusElem.textContent = 'Error recalculating: ' + msg;
        if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
          logout();
          window.location.href = 'login.html';
        }
      }
    });
  }

  // Handle feedback submission
  const feedbackBtn = document.getElementById('submitFeedback');
  if (feedbackBtn) {
    feedbackBtn.addEventListener('click', async () => {
      const statusElem = document.getElementById('feedbackStatus');
      if (!lastRunId) {
        if (statusElem) statusElem.textContent = 'No recommendation to rate yet.';
        return;
      }
      // Determine selected rating
      let selectedRating = null;
      const radios = document.querySelectorAll('input[name="rating"]');
      radios.forEach((rad) => {
        if (rad.checked) selectedRating = parseInt(rad.value, 10);
      });
      if (!selectedRating) {
        if (statusElem) statusElem.textContent = 'Please select a rating.';
        return;
      }
      try {
        await submitFeedback({ runId: lastRunId, rating: selectedRating });
        if (statusElem) statusElem.textContent = 'Thank you for your feedback!';
        feedbackBtn.disabled = true;
      } catch (err) {
        const msg = String(err?.message || err);
        if (statusElem) statusElem.textContent = 'Error submitting feedback: ' + msg;
        if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
          logout();
          window.location.href = 'login.html';
        }
      }
    });
  }
});
