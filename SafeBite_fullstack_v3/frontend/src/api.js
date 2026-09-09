const API_BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const token = localStorage.getItem("safebite_token");
  const headers = new Headers(options.headers || {});

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData) && options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  login: (username, password) => request("/government/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  me: () => request("/government/me"),
  dashboard: () => request("/government/dashboard"),
  alerts: (query = "") => request(`/government/alerts${query ? `?${query}` : ""}`),
  alert: (id) => request(`/government/alerts/${id}`),
  startInvestigation: (id) => request(`/government/alerts/${id}/investigate`, { method: "POST" }),
  investigations: () => request("/government/investigations"),
  investigation: (id) => request(`/government/investigations/${id}`),
  updateInvestigation: (id, payload) => request(`/government/investigations/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  uploadEvidence: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/government/investigations/${id}/evidence`, { method: "POST", body: form });
  },
  verifyInvestigation: (id, payload) => request(`/government/investigations/${id}/verify`, { method: "POST", body: JSON.stringify(payload) }),
  audit: (id) => request(`/government/investigations/${id}/audit`),
  establishments: () => request("/government/establishments"),
  devices: () => request("/government/devices"),
};
