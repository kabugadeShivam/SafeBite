import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

const FILTERS = [
  { label: "All Reports", value: "" },
  { label: "Submitted", value: "SUBMITTED" },
  {
    label: "Needs Investigation",
    value: "NEEDS_INVESTIGATION",
  },
  { label: "Verified", value: "VERIFIED" },
  { label: "Dismissed", value: "DISMISSED" },
];

function severityClass(severity) {
  switch (severity) {
    case "CRITICAL":
      return "citizen-badge critical";

    case "MODERATE":
      return "citizen-badge moderate";

    case "LOW":
      return "citizen-badge low";

    default:
      return "citizen-badge";
  }
}

function statusClass(status) {
  switch (status) {
    case "VERIFIED":
      return "citizen-badge verified";

    case "DISMISSED":
      return "citizen-badge dismissed";

    case "NEEDS_INVESTIGATION":
      return "citizen-badge investigation";

    case "SUBMITTED":
      return "citizen-badge submitted";

    default:
      return "citizen-badge";
  }
}

function relevancePercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("en-IN");
}

export default function CitizenReports() {
  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedReport, setSelectedReport] = useState(null);

  const [reviewStatus, setReviewStatus] = useState(
    "NEEDS_INVESTIGATION"
  );

  const [reviewNotes, setReviewNotes] = useState("");

  const [reviewing, setReviewing] = useState(false);

  // ==========================================================
  // LOAD REPORTS
  // ==========================================================

  async function loadReports() {
    setLoading(true);
    setError("");

    try {
      const data = await api.citizenReports(filter);

      setReports(data.reports || []);
    } catch (err) {
      setError(
        err.message ||
          "Failed to load citizen reports."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, [filter]);

  // ==========================================================
  // SUMMARY
  // ==========================================================

  const summary = useMemo(() => {
    const total = reports.length;

    const relevant = reports.filter(
      (report) =>
        Number(
          report.ai?.relevance || 0
        ) >= 0.5
    ).length;

    const verified = reports.filter(
      (report) =>
        report.status === "VERIFIED"
    ).length;

    const investigation = reports.filter(
      (report) =>
        report.status ===
        "NEEDS_INVESTIGATION"
    ).length;

    const critical = reports.filter(
      (report) =>
        report.ai?.severity === "CRITICAL"
    ).length;

    return {
      total,
      relevant,
      verified,
      investigation,
      critical,
    };
  }, [reports]);

  // ==========================================================
  // OPEN REVIEW
  // ==========================================================

  function openReview(report) {
    setSelectedReport(report);

    setReviewStatus(
      report.status === "SUBMITTED"
        ? "NEEDS_INVESTIGATION"
        : report.status
    );

    setReviewNotes("");
    setError("");
  }

  // ==========================================================
  // CLOSE REVIEW
  // ==========================================================

  function closeReview() {
    if (reviewing) return;

    setSelectedReport(null);
    setReviewNotes("");
  }

  // ==========================================================
  // SUBMIT REVIEW
  // ==========================================================

  async function submitReview() {
    if (!selectedReport) return;

    if (!reviewStatus) {
      setError(
        "Select a government decision first."
      );
      return;
    }

    setReviewing(true);
    setError("");

    try {
      await api.reviewCitizenReport(
        selectedReport.id,
        {
          status: reviewStatus,
          notes: reviewNotes,
        }
      );

      setSelectedReport(null);
      setReviewNotes("");

      await loadReports();
    } catch (err) {
      setError(
        err.message ||
          "Failed to submit government review."
      );
    } finally {
      setReviewing(false);
    }
  }

  return (
    <div className="citizen-page">

      {/* =======================================================
          PAGE HEADER
          ======================================================= */}

      <div className="citizen-header">

        <div>
          <div className="eyebrow">
            PUBLIC SIGNALS
          </div>

          <h2>
            Citizen Intelligence
          </h2>

          <p>
            Review customer-submitted food-safety
            concerns and determine whether further
            government action is required.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={loadReports}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>

      </div>

      {/* =======================================================
          ERROR
          ======================================================= */}

      {error && (
        <div className="citizen-error">
          {error}
        </div>
      )}

      {/* =======================================================
          SUMMARY CARDS
          ======================================================= */}

      <section className="citizen-stats">

        <div className="citizen-stat">
          <span>
            Total reports
          </span>

          <strong>
            {summary.total}
          </strong>
        </div>

        <div className="citizen-stat">
          <span>
            AI-relevant
          </span>

          <strong>
            {summary.relevant}
          </strong>
        </div>

        <div className="citizen-stat">
          <span>
            Needs investigation
          </span>

          <strong>
            {summary.investigation}
          </strong>
        </div>

        <div className="citizen-stat">
          <span>
            Government verified
          </span>

          <strong>
            {summary.verified}
          </strong>
        </div>

        <div className="citizen-stat">
          <span>
            Critical AI signals
          </span>

          <strong>
            {summary.critical}
          </strong>
        </div>

      </section>

      {/* =======================================================
          FILTERS
          ======================================================= */}

      <section className="citizen-card">

        <div className="citizen-filter-row">

          {FILTERS.map((item) => (
            <button
              key={item.value}
              className={
                filter === item.value
                  ? "citizen-filter active"
                  : "citizen-filter"
              }
              onClick={() =>
                setFilter(item.value)
              }
            >
              {item.label}
            </button>
          ))}

        </div>

      </section>

      {/* =======================================================
          REPORT LIST
          ======================================================= */}

      <section className="citizen-card">

        <div className="citizen-card-heading">

          <div>
            <h3>
              Incoming reports
            </h3>

            <p>
              AI results are preliminary.
              Government review determines
              the official status.
            </p>
          </div>

          <div className="citizen-source-note">
            AI-assisted triage
          </div>

        </div>

        {loading ? (
          <div className="citizen-empty">
            Loading citizen reports...
          </div>
        ) : reports.length === 0 ? (
          <div className="citizen-empty">
            No citizen reports match this filter.
          </div>
        ) : (
          <div className="citizen-table-wrap">

            <table className="citizen-table">

              <thead>
                <tr>
                  <th>
                    Outlet
                  </th>

                  <th>
                    Concern
                  </th>

                  <th>
                    AI relevance
                  </th>

                  <th>
                    Severity
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Submitted
                  </th>

                  <th>
                    Action
                  </th>
                </tr>
              </thead>

              <tbody>

                {reports.map((report) => (

                  <tr key={report.id}>

                    {/* OUTLET */}

                    <td>

                      <strong>
                        {report.outlet?.name ||
                          "Unknown outlet"}
                      </strong>

                      <span>
                        {report.outlet
                          ?.registration_id ||
                          "No registration ID"}
                      </span>

                    </td>

                    {/* CONCERN */}

                    <td>

                      <strong>
                        {report.category ||
                          "Unspecified concern"}
                      </strong>

                      <span className="citizen-description">
                        {report.description ||
                          "No description provided"}
                      </span>

                    </td>

                    {/* AI RELEVANCE */}

                    <td>

                      <strong>
                        {relevancePercent(
                          report.ai?.relevance
                        )}
                      </strong>

                    </td>

                    {/* SEVERITY */}

                    <td>

                      <span
                        className={severityClass(
                          report.ai?.severity
                        )}
                      >
                        {report.ai?.severity ||
                          "UNKNOWN"}
                      </span>

                    </td>

                    {/* STATUS */}

                    <td>

                      <span
                        className={statusClass(
                          report.status
                        )}
                      >
                        {report.status ||
                          "UNKNOWN"}
                      </span>

                    </td>

                    {/* DATE */}

                    <td>
                      {formatDate(
                        report.submitted_at
                      )}
                    </td>

                    {/* ACTION */}

                    <td>

                      <button
                        className="citizen-review-button"
                        onClick={() =>
                          openReview(report)
                        }
                      >
                        Review
                      </button>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>
        )}

      </section>

      {/* =======================================================
          GOVERNMENT REVIEW MODAL
          ======================================================= */}

      {selectedReport && (

        <div className="citizen-modal-backdrop">

          <div className="citizen-modal">

            <div className="citizen-modal-header">

              <div>

                <div className="eyebrow">
                  GOVERNMENT REVIEW
                </div>

                <h3>
                  Report #{selectedReport.id}
                </h3>

                <p>
                  {selectedReport.outlet?.name ||
                    "Unknown outlet"}
                </p>

              </div>

              <button
                className="citizen-close"
                onClick={closeReview}
                disabled={reviewing}
                aria-label="Close"
              >
                ×
              </button>

            </div>

            {/* =================================================
                REPORT SUMMARY
                ================================================= */}

            <div className="citizen-review-grid">

              <div>
                <span>
                  Concern
                </span>

                <strong>
                  {selectedReport.category ||
                    "Unspecified"}
                </strong>
              </div>

              <div>
                <span>
                  AI relevance
                </span>

                <strong>
                  {relevancePercent(
                    selectedReport.ai?.relevance
                  )}
                </strong>
              </div>

              <div>
                <span>
                  AI severity
                </span>

                <strong>
                  {selectedReport.ai?.severity ||
                    "UNKNOWN"}
                </strong>
              </div>

              <div>
                <span>
                  Current status
                </span>

                <strong>
                  {selectedReport.status ||
                    "UNKNOWN"}
                </strong>
              </div>

            </div>

            {/* =================================================
                CUSTOMER DESCRIPTION
                ================================================= */}

            <div className="citizen-detail-block">

              <span>
                Customer description
              </span>

              <p>
                {selectedReport.description ||
                  "No description supplied."}
              </p>

            </div>

            {/* =================================================
                AI FINDINGS
                ================================================= */}

            <div className="citizen-detail-block">

              <span>
                AI preliminary findings
              </span>

              <pre>
                {JSON.stringify(
                  selectedReport.ai?.findings ||
                    {},
                  null,
                  2
                )}
              </pre>

            </div>

            {/* =================================================
                MEDIA HASH
                ================================================= */}

            <div className="citizen-detail-block">

              <span>
                Evidence integrity
              </span>

              <code>
                {selectedReport.media_sha256 ||
                  "Hash unavailable"}
              </code>

            </div>

            {/* =================================================
                AI STATUS
                ================================================= */}

            <div className="citizen-detail-block">

              <span>
                AI screening status
              </span>

              <p>
                {selectedReport.ai?.status ||
                  "Unknown"}
              </p>

            </div>

            {/* =================================================
                GOVERNMENT DECISION
                ================================================= */}

            <div className="citizen-detail-block">

              <label htmlFor="citizen-review-status">
                Government decision
              </label>

              <select
                id="citizen-review-status"
                value={reviewStatus}
                onChange={(event) =>
                  setReviewStatus(
                    event.target.value
                  )
                }
                disabled={reviewing}
              >

                <option value="NEEDS_INVESTIGATION">
                  Needs Investigation
                </option>

                <option value="VERIFIED">
                  Verified
                </option>

                <option value="DISMISSED">
                  Dismissed
                </option>

              </select>

            </div>

            {/* =================================================
                OFFICER NOTES
                ================================================= */}

            <div className="citizen-detail-block">

              <label htmlFor="citizen-review-notes">
                Officer notes
              </label>

              <textarea
                id="citizen-review-notes"
                rows="4"
                value={reviewNotes}
                onChange={(event) =>
                  setReviewNotes(
                    event.target.value
                  )
                }
                disabled={reviewing}
                placeholder="Record the reasoning for your decision..."
              />

            </div>

            {/* =================================================
                ACTIONS
                ================================================= */}

            <div className="citizen-modal-actions">

              <button
                className="secondary-button"
                onClick={closeReview}
                disabled={reviewing}
              >
                Cancel
              </button>

              <button
                className="primary-button"
                onClick={submitReview}
                disabled={reviewing}
              >
                {reviewing
                  ? "Submitting..."
                  : "Submit Government Review"}
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}