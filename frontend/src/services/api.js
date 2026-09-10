const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const ADMIN_STORAGE_KEY = 'indicclaim_admin_auth_key';

// ============================================================================
// DEVELOPER / ADMIN AUTHENTICATION HELPERS
// ============================================================================

export function getAdminKey() {
  try {
    return localStorage.getItem(ADMIN_STORAGE_KEY) || '';
  } catch (e) {
    return '';
  }
}

export function setAdminKey(key) {
  try {
    if (key) {
      localStorage.setItem(ADMIN_STORAGE_KEY, key.trim());
    } else {
      localStorage.removeItem(ADMIN_STORAGE_KEY);
    }
  } catch (e) {
    console.warn('LocalStorage access failed', e);
  }
}

export function clearAdminKey() {
  try {
    localStorage.removeItem(ADMIN_STORAGE_KEY);
  } catch (e) {}
}

export function isAdminAuthenticated() {
  return Boolean(getAdminKey());
}

/**
 * Verify key with backend auth endpoint.
 */
export async function verifyAdminKey(key) {
  if (!key || !key.trim()) {
    throw new Error('Please enter a developer key');
  }

  const response = await fetch(`${API_BASE_URL}/api/auth/verify-admin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key: key.trim() }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Invalid developer access key');
  }

  const data = await response.json();
  setAdminKey(key.trim());
  return data;
}

function getAuthHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  const key = getAdminKey();
  if (key) {
    headers['X-Admin-Key'] = key;
  }
  return headers;
}

// ============================================================================
// NORMAL USER APIS (Public)
// ============================================================================

/**
 * Verify a factual claim against the IndicClaim pipeline.
 * @param {string} claim - Factual claim string.
 * @returns {Promise<Object>} Verification response payload.
 */
export async function verifyClaim(claim) {
  if (!claim || !claim.trim()) {
    throw new Error('Please enter a claim to verify.');
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000);

  try {
    const response = await fetch(`${API_BASE_URL}/api/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ claim: claim.trim() }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `Verification failed (${response.status})`;
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Verification request timed out. Please try again.');
    }
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Could not connect to IndicClaim service. Please ensure the backend is running.');
    }
    throw error;
  }
}

/**
 * Check backend health status and active model connectivity.
 * @returns {Promise<Object>}
 */
export async function getHealthStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!response.ok) return { status: 'error', connected: false };
    const data = await response.json();
    return { ...data, connected: true };
  } catch (err) {
    return { status: 'disconnected', connected: false, error: err.message };
  }
}

// ============================================================================
// DEVELOPER / ADMIN APIS (Protected by X-Admin-Key)
// ============================================================================

/**
 * Start the automated Crawl -> Extract -> Validate -> Train -> Activate pipeline.
 */
export async function startCrawlPipeline(payload) {
  const response = await fetch(`${API_BASE_URL}/api/crawl/start`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to start pipeline (${response.status})`);
  }
  return await response.json();
}

/**
 * Get current pipeline status, stage, progress, and telemetry.
 */
export async function getCrawlStatus(jobId) {
  const endpoint = jobId ? `${API_BASE_URL}/api/crawl/status/${jobId}` : `${API_BASE_URL}/api/crawl/status`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch pipeline status (${response.status})`);
  }
  return await response.json();
}

/**
 * Stop running pipeline.
 */
export async function stopCrawlPipeline() {
  const response = await fetch(`${API_BASE_URL}/api/crawl/stop`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) {
    throw new Error(`Failed to stop pipeline (${response.status})`);
  }
  return await response.json();
}

/**
 * Get past pipeline run history.
 */
export async function getCrawlHistory() {
  const response = await fetch(`${API_BASE_URL}/api/crawl/history`, {
    method: 'GET',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) return [];
  return await response.json();
}

/**
 * Get active MuRIL model metadata.
 */
export async function getActiveModelInfo() {
  const response = await fetch(`${API_BASE_URL}/api/crawl/active-model`, {
    method: 'GET',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) return null;
  return await response.json();
}

/**
 * Get list of all model checkpoints (active & archived).
 */
export async function getModelsList() {
  const response = await fetch(`${API_BASE_URL}/api/models`, {
    method: 'GET',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) return { models: [], total: 0 };
  return await response.json();
}

/**
 * Get dataset and evidence pool overall statistics.
 */
export async function getDatasetStats() {
  const response = await fetch(`${API_BASE_URL}/api/stats`, {
    method: 'GET',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) return null;
  return await response.json();
}

/**
 * Query training dataset items.
 */
export async function getDatasetItems(params = {}) {
  const q = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/dataset?${q}`, {
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Dataset query failed (${response.status})`);
  return await response.json();
}

/**
 * Query evidence pool items.
 */
export async function getEvidenceItems(params = {}) {
  const q = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/evidence?${q}`, {
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Evidence query failed (${response.status})`);
  return await response.json();
}

/**
 * Query rejected review queue items.
 */
export async function getReviewItems(params = {}) {
  const q = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/review?${q}`, {
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Review query failed (${response.status})`);
  return await response.json();
}

/**
 * Perform action on review item (approve, delete, edit_and_approve).
 */
export async function handleReviewAction(payload) {
  const response = await fetch(`${API_BASE_URL}/api/review/action`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Review action failed (${response.status})`);
  return await response.json();
}

/**
 * Query sources registry.
 */
export async function getSources() {
  const response = await fetch(`${API_BASE_URL}/api/sources`, {
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Sources query failed (${response.status})`);
  return await response.json();
}

/**
 * Toggle source enabled status.
 */
export async function toggleSource(sourceId, enabled) {
  const response = await fetch(`${API_BASE_URL}/api/sources/${sourceId}/toggle?enabled=${enabled}`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Toggle source failed (${response.status})`);
  return await response.json();
}

/**
 * Get automated training trigger status, counter, threshold, and metrics.
 */
export async function getTrainingStatus() {
  const response = await fetch(`${API_BASE_URL}/api/training/status`, {
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Failed to fetch training status (${response.status})`);
  return await response.json();
}

/**
 * Developer manual override to trigger training immediately.
 */
export async function triggerManualTraining(payload = {}) {
  const response = await fetch(`${API_BASE_URL}/api/training/trigger`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to trigger training (${response.status})`);
  }
  return await response.json();
}

/**
 * Pause automated retraining trigger.
 */
export async function pauseAutoTraining() {
  const response = await fetch(`${API_BASE_URL}/api/training/pause`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Failed to pause training (${response.status})`);
  return await response.json();
}

/**
 * Resume automated retraining trigger.
 */
export async function resumeAutoTraining() {
  const response = await fetch(`${API_BASE_URL}/api/training/resume`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) throw new Error(`Failed to resume training (${response.status})`);
  return await response.json();
}

/**
 * Update the minimum new examples retrain threshold.
 */
export async function updateRetrainThreshold(threshold) {
  const response = await fetch(`${API_BASE_URL}/api/training/threshold`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ threshold: parseInt(threshold, 10) }),
  });
  if (!response.ok) throw new Error(`Failed to update threshold (${response.status})`);
  return await response.json();
}

/**
 * Activate a specific model version.
 */
export async function activateModelVersion(version) {
  const response = await fetch(`${API_BASE_URL}/api/models/${version}/activate`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to activate model (${response.status})`);
  }
  return await response.json();
}

/**
 * Rollback active model to a previous version.
 */
export async function rollbackModelVersion(version) {
  const response = await fetch(`${API_BASE_URL}/api/models/${version}/rollback`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Accept': 'application/json' }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to rollback model (${response.status})`);
  }
  return await response.json();
}

