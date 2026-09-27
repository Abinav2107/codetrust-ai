/**
 * API base URL resolution:
 *
 * - In production builds: VITE_API_URL must be set at build time (e.g. https://api.example.com).
 *   Requests will be sent directly to that origin.
 *
 * - In local development (npm run dev): VITE_API_URL can be left unset.
 *   The Vite dev server proxy forwards /api/* to http://127.0.0.1:8000 automatically,
 *   so an empty base URL (i.e. same-origin requests) works out of the box.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const API_ENDPOINTS = {
  analyze: `${API_BASE_URL}/api/v1/analyze`,
  health: `${API_BASE_URL}/api/v1/health`,
  history: `${API_BASE_URL}/api/v1/history`,
}

export default API_BASE_URL
