const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:18081").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the fallback message.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  baseUrl: API_BASE_URL,
  listSources: () => request("/api/v1/sources"),
  getSourceDetail: (sourceId, logTail = 100) =>
    request(`/api/v1/sources/${sourceId}?log_tail=${logTail}`),
  createSource: (payload) =>
    request("/api/v1/sources", { method: "POST", body: JSON.stringify(payload) }),
  updateSource: (sourceId, payload) =>
    request(`/api/v1/sources/${sourceId}`, { method: "PUT", body: JSON.stringify(payload) }),
  listTargets: () => request("/api/v1/targets"),
  createTarget: (payload) =>
    request("/api/v1/targets", { method: "POST", body: JSON.stringify(payload) }),
  updateTarget: (targetId, payload) =>
    request(`/api/v1/targets/${targetId}`, { method: "PUT", body: JSON.stringify(payload) }),
  getSettings: () => request("/api/v1/settings"),
  updateSettings: (payload) =>
    request("/api/v1/settings", { method: "PUT", body: JSON.stringify(payload) }),
  getJobStatus: (sourceId) => request(`/api/v1/jobs/${sourceId}/status`),
  startJob: (sourceId) => request(`/api/v1/jobs/${sourceId}/start`, { method: "POST" }),
  stopJob: (sourceId) => request(`/api/v1/jobs/${sourceId}/stop`, { method: "POST" }),
  restartJob: (sourceId) => request(`/api/v1/jobs/${sourceId}/restart`, { method: "POST" }),
  getJobLogs: (sourceId, tail = 100) =>
    request(`/api/v1/jobs/${sourceId}/logs?tail=${tail}`),
};
