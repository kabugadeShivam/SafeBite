const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://safebite-sje5.onrender.com";

/* ==========================================================
   GENERIC REQUEST HELPER
   ========================================================== */

async function request(path, options = {}) {
  const token = localStorage.getItem("safebite_token");
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data;
}

export const api = {
  login: (username, password) =>
    request("/government/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  me: () => request("/government/me"),
  dashboard: () => request("/government/dashboard"),
  alerts: (params = "") => request(`/government/alerts${params ? `?${params}` : ""}`),
  alert: (id) => request(`/government/alerts/${id}`),
  startInvestigation: (alertId) =>
    request(`/government/alerts/${alertId}/investigate`, { method: "POST" }),
  investigations: () => request("/government/investigations"),
  investigation: (id) => request(`/government/investigations/${id}`),
  updateInvestigation: (id, payload) =>
    request(`/government/investigations/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  uploadEvidence: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/government/investigations/${id}/evidence`, {
      method: "POST",
      body: form,
    });
  },

  verifyInvestigation: (id, payload) =>
    request(`/government/investigations/${id}/verify`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  audit: (id) => request(`/government/investigations/${id}/audit`),
  establishments: () => request("/government/establishments"),
  devices: () => request("/government/devices"),
  aiStatus: () => request("/ai/status"),

  analyzeHygiene: (file, investigationId = null) => {
    const form = new FormData();
    form.append("file", file);
    const query = investigationId !== null
      ? `?investigation_id=${encodeURIComponent(investigationId)}`
      : "";
    return request(`/ai/hygiene${query}`, { method: "POST", body: form });
  },

  analyzeExpiry: (file, investigationId = null) => {
    const form = new FormData();
    form.append("file", file);
    const query = investigationId !== null
      ? `?investigation_id=${encodeURIComponent(investigationId)}`
      : "";
    return request(`/ai/expiry${query}`, { method: "POST", body: form });
  },

  itemSafetyScan: (file, restaurantId = null, investigationId = null) => {
    const form = new FormData();
    form.append("file", file);
    if (restaurantId !== null) form.append("restaurant_id", String(restaurantId));
    if (investigationId !== null) form.append("investigation_id", String(investigationId));
    return request("/ai/item-safety", { method: "POST", body: form });
  },

  regionalAudit: (days = 30) =>
    request(`/government/auditor/regional?days=${encodeURIComponent(days)}`),
  auditHistory: (registrationId, days = 30) =>
    request(`/government/audit-history/outlets/${encodeURIComponent(registrationId)}?days=${encodeURIComponent(days)}`),
  commandCenter: () => request("/government/command-center"),
  actionQueue: () => request("/government/action-queue"),

  monthlyNotices: (auditMonth = "", noticeType = "") => {
    const params = new URLSearchParams();
    if (auditMonth) params.set("audit_month", auditMonth);
    if (noticeType) params.set("notice_type", noticeType);
    const query = params.toString();
    return request(`/government/monthly-notices${query ? `?${query}` : ""}`);
  },

  generateMonthlyNotices: (auditMonth) =>
    request(`/government/monthly-notices/generate?audit_month=${encodeURIComponent(auditMonth)}`, {
      method: "POST",
    }),
  monthlyNotice: (id) => request(`/government/monthly-notices/${id}`),

  outletContact: (restaurantId) => request(`/government/outlet-contacts/${restaurantId}`),
  saveOutletContact: (restaurantId, payload) =>
    request(`/government/outlet-contacts/${restaurantId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  publicOutlet: (registrationId) =>
    request(`/public/outlets/${encodeURIComponent(registrationId)}`),
  citizenReports: (status = "") =>
    request(`/government/citizen-reports${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  reviewCitizenReport: (id, payload) =>
    request(`/government/citizen-reports/${id}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  citizenReportMedia: async (id) => {
    const token = localStorage.getItem("safebite_token");
    const response = await fetch(`${API_BASE}/government/citizen-reports/${id}/media`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      const text = await response.text();
      let message = "Unable to load evidence.";
      try {
        const data = JSON.parse(text);
        message = data.detail || message;
      } catch {
        // Keep default message.
      }
      throw new Error(message);
    }
    return {
      blob: await response.blob(),
      contentType: response.headers.get("content-type") || "application/octet-stream",
      hash: response.headers.get("X-SafeBite-Evidence-Hash"),
    };
  },

  submitCitizenReport: ({ registrationId, concernCategory, description = "", isAnonymous = true, file }) => {
    const form = new FormData();
    form.append("registration_id", registrationId);
    form.append("concern_category", concernCategory);
    form.append("description", description);
    form.append("is_anonymous", String(isAnonymous));
    form.append("file", file);
    return request("/public/reports", { method: "POST", body: form });
  },

  citizenReportStatus: (reportId) =>
    request(`/public/reports/${encodeURIComponent(reportId)}`),
};
