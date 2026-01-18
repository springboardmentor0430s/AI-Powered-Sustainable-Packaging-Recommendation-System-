function resolveApiBaseUrl() {
  // Priority: <meta name="api-base-url" content="...">, then window.ECOPACKAI_API_BASE_URL, then localhost.
  const meta = document.querySelector('meta[name="api-base-url"]');
  const metaUrl = meta && meta.content ? meta.content.trim() : '';
  const winUrl = (window.ECOPACKAI_API_BASE_URL || '').toString().trim();
  const url = metaUrl || winUrl || (window.location && window.location.origin ? window.location.origin : 'http://127.0.0.1:8000');
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

export const API_BASE_URL = resolveApiBaseUrl();


// -------------------- Storage keys --------------------
const TOKEN_KEY = 'token';
const PROFILE_KEY = 'ecopackai-profile';

// -------------------- Token helpers --------------------
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(PROFILE_KEY);
}

// -------------------- Profile helpers --------------------
export function setProfile(profile) {
  // profile should look like: { email, companyName }
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile || {}));
  } catch {
    // ignore storage errors
  }
}

export function getProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

// -------------------- Auth gate --------------------
export function requireAuthOrRedirect() {
  const token = getToken();
  if (!token) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

// -------------------- Internal helpers --------------------
function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  let body;
  try {
    body = isJson ? await response.json() : await response.text();
  } catch {
    body = isJson ? {} : '';
  }

  if (!response.ok) {
    const msg =
      (isJson && body && (body.detail || body.message)) ||
      (typeof body === 'string' ? body : '') ||
      `Server responded with ${response.status}`;
    throw new Error(msg);
  }

  return body;
}

// -------------------- Navbar UI helpers --------------------
export function mountNavbarProfileChip() {
  const navList = document.querySelector('.navbar-nav');
  if (!navList) return;

  // avoid duplicates
  if (document.getElementById('profileChip')) return;

  const profile = getProfile();
  if (!profile?.email) return;

  const li = document.createElement('li');
  li.className = 'nav-item d-flex align-items-center ms-lg-2';

  const chip = document.createElement('div');
  chip.id = 'profileChip';
  chip.className = 'profile-chip';
  chip.setAttribute('role', 'status');
  chip.setAttribute('aria-label', 'Logged in user');

  const icon = document.createElement('i');
  icon.className = 'bi bi-person-circle';
  icon.setAttribute('aria-hidden', 'true');

  const textWrap = document.createElement('div');
  textWrap.className = 'profile-chip-text';

  const line1 = document.createElement('div');
  line1.className = 'profile-chip-email';
  line1.textContent = profile.email;

  textWrap.appendChild(line1);

  if (profile.companyName) {
    const line2 = document.createElement('div');
    line2.className = 'profile-chip-company';
    line2.textContent = profile.companyName;
    textWrap.appendChild(line2);
  }

  chip.append(icon, textWrap);
  li.appendChild(chip);
  navList.appendChild(li);
}

export function mountLogoutButton() {
  const navList = document.querySelector('.navbar-nav');
  if (!navList) return;

  // avoid duplicates
  if (document.getElementById('logoutBtn')) return;

  const li = document.createElement('li');
  li.className = 'nav-item ms-lg-2';

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.id = 'logoutBtn';
  btn.className = 'btn btn-sm btn-outline-danger';
  btn.innerHTML = '<i class="bi bi-box-arrow-right me-1" aria-hidden="true"></i>Logout';
  btn.setAttribute('aria-label', 'Logout');

  btn.addEventListener('click', () => {
    logout();
    window.location.href = 'login.html';
  });

  li.appendChild(btn);
  navList.appendChild(li);
}

// -------------------- Auth calls --------------------
export async function signup(email, password, companyName) {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, companyName }),
  });

  const data = await parseResponse(response);

  if (data?.access_token) setToken(data.access_token);
  setProfile({ email: data.email, companyName: data.companyName });

  return data;
}

export async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await parseResponse(response);

  if (data?.access_token) setToken(data.access_token);
  setProfile({ email: data.email, companyName: data.companyName });

  return data;
}

// -------------------- Recommendation --------------------
export async function fetchRecommendations(productData) {
  const response = await fetch(`${API_BASE_URL}/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(productData),
  });

  return await parseResponse(response);
}

// -------------------- Dashboard data --------------------
export async function fetchDashboardData() {
  const response = await fetch(`${API_BASE_URL}/dashboard-data`, {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  });

  return await parseResponse(response);
}

// -------------------- Trend Data --------------------
export async function fetchTrendData() {
  const response = await fetch(`${API_BASE_URL}/trend-data`, {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  });
  return await parseResponse(response);
}

// -------------------- Recommendation History --------------------
/**
 * Fetch a list of recent recommendation runs for the logged in user.  The
 * returned history includes the parameters entered on each run along with
 * the top recommended material.  Runs are returned in descending order
 * (most recent first).  The optional `limit` parameter controls how
 * many records are returned.
 *
 * @param {number} limit The maximum number of runs to return (default 20)
 * @returns {Promise<{history: Array}>} An object containing a `history` array
 */
export async function fetchRecommendationHistory(limit = 20) {
  const url = new URL(`${API_BASE_URL}/recommend/history`);
  // enforce integer limit within allowed range
  if (typeof limit === 'number' && !Number.isNaN(limit)) {
    url.searchParams.set('limit', Math.max(1, Math.min(limit, 500)));
  }
  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  });
  return await parseResponse(response);
}

// -------------------- Sustainability Score --------------------
export async function fetchSustainabilityScore() {
  const response = await fetch(`${API_BASE_URL}/sustainability-score`, {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  });
  return await parseResponse(response);
}

// -------------------- Preferences --------------------
export async function updateUserPreferences(preferences) {
  const response = await fetch(`${API_BASE_URL}/user/preferences`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(preferences),
  });
  return await parseResponse(response);
}

// -------------------- Feedback --------------------
export async function submitFeedback(feedbackData) {
  const response = await fetch(`${API_BASE_URL}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(feedbackData),
  });
  return await parseResponse(response);
}

// -------------------- Reports --------------------
export async function downloadReport(format) {
  const response = await fetch(`${API_BASE_URL}/report?format=${encodeURIComponent(format)}`, {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Server responded with ${response.status}`);
  }

  return await response.blob();
}

// -------------------- Email Report --------------------
/**
 * Request the server to email a report to the logged-in user.
 *
 * @param {string} format - Either 'pdf' or 'excel'.
 * @returns {Promise<object>} Response message
 */
export async function emailReport(format = 'pdf') {
  const response = await fetch(`${API_BASE_URL}/report/email`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ format }),
  });
  return await parseResponse(response);
}

// -------------------- Chat --------------------
export async function sendChatMessage(question, history = []) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ question, history }),
  });

  return await parseResponse(response);
}

// -------------------- Materials & Comparison --------------------
/**
 * Fetch the list of available material names from the backend.  These
 * names correspond to the materials present in the training dataset and
 * will populate the material selection dropdowns in the compare page.
 *
 * @returns {Promise<object>} An object with a `materials` array
 */
export async function fetchMaterials() {
  const response = await fetch(`${API_BASE_URL}/materials-names`, {
    method: 'GET',
    headers: {
      ...authHeaders(),
    },
  });
  return await parseResponse(response);
}

/**
 * Submit a material comparison request.  The payload must include all
 * product parameters used for recommendation along with a list of
 * material names to compare.  Unknown materials trigger a call to the
 * OpenAI API on the server.
 *
 * Example payload:
 * {
 *   productName: "Snack Box",
 *   category: "Bakery & Snacks",
 *   weightKg: 0.5,
 *   fragility: 5,
 *   maxBudget: 0.4,
 *   shippingDistance: 500,
 *   moistureReq: 5,
 *   oxygenSensitivity: 5,
 *   preferredBiodegradable: 1,
 *   preferredRecyclable: 0,
 *   materials: ["Glass", "Aluminium"]
 * }
 *
 * @param {object} payload
 * @returns {Promise<object>} Response containing a `results` array
 */
export async function compareMaterials(payload) {
  const response = await fetch(`${API_BASE_URL}/compare-materials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });
  return await parseResponse(response);
}

/**
 * Forecast future totals using the /forecast endpoint.
 *
 * payload example:
 * {
 *   plannedVolumes: [{ period: "2026-02", volumeTons: 1.2 }, ...],
 *   simulations: 600
 * }
 */
export async function fetchForecast(payload) {
  const response = await fetch(`${API_BASE_URL}/forecast`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(payload || {}),
  });
  return await parseResponse(response);
}
