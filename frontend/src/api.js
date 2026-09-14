const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


/* ==========================================================
   GENERIC REQUEST HELPER
   ========================================================== */

async function request(path, options = {}) {
  const token =
    localStorage.getItem("safebite_token");

  const headers = new Headers(
    options.headers || {}
  );

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  if (!(options.body instanceof FormData)) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  const response = await fetch(
    `${API_BASE}${path}`,
    {
      ...options,
      headers,
    }
  );

  const data = await response
    .json()
    .catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Request failed"
    );
  }

  return data;
}


/* ==========================================================
   API
   ========================================================== */

export const api = {

  /* ========================================================
     AUTHENTICATION
     ======================================================== */

  login: (
    username,
    password
  ) =>
    request(
      "/government/login",
      {
        method: "POST",

        body: JSON.stringify({
          username,
          password,
        }),
      }
    ),

  me: () =>
    request(
      "/government/me"
    ),


  /* ========================================================
     GOVERNMENT DASHBOARD
     ======================================================== */

  dashboard: () =>
    request(
      "/government/dashboard"
    ),


  /* ========================================================
     ALERTS
     ======================================================== */

  alerts: (
    params = ""
  ) =>
    request(
      `/government/alerts${
        params
          ? `?${params}`
          : ""
      }`
    ),

  alert: (
    id
  ) =>
    request(
      `/government/alerts/${id}`
    ),


  /* ========================================================
     INVESTIGATIONS
     ======================================================== */

  startInvestigation: (
    alertId
  ) =>
    request(
      `/government/alerts/${alertId}/investigate`,
      {
        method: "POST",
      }
    ),

  investigations: () =>
    request(
      "/government/investigations"
    ),

  investigation: (
    id
  ) =>
    request(
      `/government/investigations/${id}`
    ),

  updateInvestigation: (
    id,
    payload
  ) =>
    request(
      `/government/investigations/${id}`,
      {
        method: "PUT",

        body: JSON.stringify(
          payload
        ),
      }
    ),


  /* ========================================================
     INVESTIGATION EVIDENCE
     ======================================================== */

  uploadEvidence: (
    id,
    file
  ) => {

    const form =
      new FormData();

    form.append(
      "file",
      file
    );

    return request(
      `/government/investigations/${id}/evidence`,
      {
        method: "POST",
        body: form,
      }
    );
  },


  /* ========================================================
     INVESTIGATION VERIFICATION
     ======================================================== */

  verifyInvestigation: (
    id,
    payload
  ) =>
    request(
      `/government/investigations/${id}/verify`,
      {
        method: "POST",

        body: JSON.stringify(
          payload
        ),
      }
    ),


  /* ========================================================
     INVESTIGATION AUDIT
     ======================================================== */

  audit: (
    id
  ) =>
    request(
      `/government/investigations/${id}/audit`
    ),


  /* ========================================================
     ESTABLISHMENTS
     ======================================================== */

  establishments: () =>
    request(
      "/government/establishments"
    ),


  /* ========================================================
     DEVICES
     ======================================================== */

  devices: () =>
    request(
      "/government/devices"
    ),


  /* ========================================================
     AI STATUS
     ======================================================== */

  aiStatus: () =>
    request(
      "/ai/status"
    ),


  /* ========================================================
     AI HYGIENE
     ======================================================== */

  analyzeHygiene: (
    file,
    investigationId = null
  ) => {

    const form =
      new FormData();

    form.append(
      "file",
      file
    );

    const query =
      investigationId !== null
        ? `?investigation_id=${encodeURIComponent(
            investigationId
          )}`
        : "";

    return request(
      `/ai/hygiene${query}`,
      {
        method: "POST",
        body: form,
      }
    );
  },


  /* ========================================================
     AI EXPIRY
     ======================================================== */

  analyzeExpiry: (
    file,
    investigationId = null
  ) => {

    const form =
      new FormData();

    form.append(
      "file",
      file
    );

    const query =
      investigationId !== null
        ? `?investigation_id=${encodeURIComponent(
            investigationId
          )}`
        : "";

    return request(
      `/ai/expiry${query}`,
      {
        method: "POST",
        body: form,
      }
    );
  },


  /* ========================================================
     ITEM SAFETY
     ========================================================
     */

  itemSafetyScan: (
    file,
    restaurantId = null,
    investigationId = null
  ) => {

    const form =
      new FormData();

    form.append(
      "file",
      file
    );

    if (restaurantId !== null) {
      form.append(
        "restaurant_id",
        String(restaurantId)
      );
    }

    if (investigationId !== null) {
      form.append(
        "investigation_id",
        String(investigationId)
      );
    }

    return request(
      "/ai/item-safety",
      {
        method: "POST",
        body: form,
      }
    );
  },


  /* ========================================================
     REGIONAL AUDITOR
     ======================================================== */

  regionalAudit: (
    days = 30
  ) =>
    request(
      `/government/auditor/regional?days=${encodeURIComponent(
        days
      )}`
    ),


  /* ========================================================
     OUTLET AUDIT HISTORY
     ======================================================== */

  auditHistory: (
    registrationId,
    days = 30
  ) =>
    request(
      `/government/audit-history/outlets/${encodeURIComponent(
        registrationId
      )}?days=${encodeURIComponent(
        days
      )}`
    ),


  /* ========================================================
     COMMAND CENTER
     ======================================================== */

  commandCenter: () =>
    request(
      "/government/command-center"
    ),


  /* ========================================================
     OFFICER ACTION QUEUE
     ======================================================== */

  actionQueue: () =>
    request(
      "/government/action-queue"
    ),


  /* ========================================================
     MONTHLY AI AUDIT
     ======================================================== */

  monthlyNotices: (
    auditMonth = "",
    noticeType = ""
  ) => {
    const params = new URLSearchParams();

    if (auditMonth) {
      params.set(
        "audit_month",
        auditMonth
      );
    }

    if (noticeType) {
      params.set(
        "notice_type",
        noticeType
      );
    }

    const query =
      params.toString();

    return request(
      `/government/monthly-notices${
        query
          ? `?${query}`
          : ""
      }`
    );
  },

  generateMonthlyNotices: (
    auditMonth
  ) =>
    request(
      `/government/monthly-notices/generate?audit_month=${encodeURIComponent(
        auditMonth
      )}`,
      {
        method: "POST",
      }
    ),

  monthlyNotice: (
    id
  ) =>
    request(
      `/government/monthly-notices/${id}`
    ),


  /* ========================================================
     OUTLET OFFICIAL CONTACT
     ======================================================== */

  outletContact: (
    restaurantId
  ) =>
    request(
      `/government/outlet-contacts/${restaurantId}`
    ),

  saveOutletContact: (
    restaurantId,
    payload
  ) =>
    request(
      `/government/outlet-contacts/${restaurantId}`,
      {
        method: "PUT",
        body: JSON.stringify(
          payload
        ),
      }
    ),


  /* ========================================================
     PUBLIC OUTLET
     ======================================================== */

  publicOutlet: (
    registrationId
  ) =>
    request(
      `/public/outlets/${encodeURIComponent(
        registrationId
      )}`
    ),


  /* ========================================================
     GOVERNMENT CITIZEN REPORTS
     ======================================================== */

  citizenReports: (
    status = ""
  ) =>
    request(
      `/government/citizen-reports${
        status
          ? `?status=${encodeURIComponent(
              status
            )}`
          : ""
      }`
    ),


  /* ========================================================
     REVIEW CITIZEN REPORT
     ======================================================== */

  reviewCitizenReport: (
    id,
    payload
  ) =>
    request(
      `/government/citizen-reports/${id}/review`,
      {
        method: "POST",

        body: JSON.stringify(
          payload
        ),
      }
    ),


  /* ========================================================
     SECURE CITIZEN MEDIA
     ======================================================== */

  citizenReportMedia: async (
    id
  ) => {

    const token =
      localStorage.getItem(
        "safebite_token"
      );

    const response = await fetch(
      `${API_BASE}/government/citizen-reports/${id}/media`,
      {
        headers: token
          ? {
              Authorization:
                `Bearer ${token}`,
            }
          : {},
      }
    );

    if (!response.ok) {

      const text =
        await response.text();

      let message =
        "Unable to load evidence.";

      try {

        const data =
          JSON.parse(text);

        message =
          data.detail ||
          message;

      } catch {
        // Keep default message.
      }

      throw new Error(
        message
      );
    }

    return {
      blob:
        await response.blob(),

      contentType:
        response.headers.get(
          "content-type"
        ) ||
        "application/octet-stream",

      hash:
        response.headers.get(
          "X-SafeBite-Evidence-Hash"
        ),
    };
  },


  /* ========================================================
     PUBLIC CITIZEN REPORT SUBMISSION
     ========================================================
     */

  submitCitizenReport: ({
    registrationId,
    concernCategory,
    description = "",
    isAnonymous = true,
    file,
  }) => {

    const form =
      new FormData();

    form.append(
      "registration_id",
      registrationId
    );

    form.append(
      "concern_category",
      concernCategory
    );

    form.append(
      "description",
      description
    );

    form.append(
      "is_anonymous",
      String(
        isAnonymous
      )
    );

    form.append(
      "file",
      file
    );

    return request(
      "/public/reports",
      {
        method: "POST",
        body: form,
      }
    );
  },


  /* ========================================================
     PUBLIC CITIZEN REPORT TRACKING
     ======================================================== */

  citizenReportStatus: (
    reportId
  ) =>
    request(
      `/public/reports/${encodeURIComponent(
        reportId
      )}`
    ),
};
