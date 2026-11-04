// One place for talking to the Flask backend.
//
// The backend address comes from REACT_APP_API_URL when it's set (for the
// deployed app), and falls back to the local development server.
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

/**
 * Call a backend route and return its JSON.
 * Throws an Error with the backend's own message when the request fails,
 * so callers can show it directly.
 */
export async function apiRequest(path, { method = 'GET', body } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error('Could not reach the server. Make sure the backend is running.');
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}
