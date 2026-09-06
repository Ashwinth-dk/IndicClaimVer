const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Verify a factual claim against the IndicClaimVer pipeline.
 * @param {string} claim - Factual claim string.
 * @returns {Promise<Object>} Verification response payload.
 */
export async function verifyClaim(claim) {
  if (!claim || !claim.trim()) {
    throw new Error('Please enter a valid claim text to verify.');
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000); // 90-second timeout for first-load / GPU-CPU processing

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
      const message = errorData.detail || `Server returned error (${response.status})`;
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Verification request timed out. The model or retrieval index may still be warming up.');
    }
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Could not connect to IndicClaimVer backend server. Please verify the backend is running on port 8000.');
    }
    throw error;
  }
}

/**
 * Check backend health status and loaded model info.
 * @returns {Promise<Object>} Health response payload.
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
