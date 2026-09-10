import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";


/* ============================================================
   STATUS HELPERS
   ============================================================ */

function statusLabel(status) {
  switch (status) {
    case "SUBMITTED":
      return "SUBMITTED";

    case "NEEDS_INVESTIGATION":
      return "UNDER GOVERNMENT REVIEW";

    case "VERIFIED":
      return "VERIFIED BY GOVERNMENT";

    case "DISMISSED":
      return "CLOSED";

    default:
      return status || "UNKNOWN";
  }
}


function statusClass(status) {
  switch (status) {
    case "VERIFIED":
      return "report-status verified";

    case "DISMISSED":
      return "report-status dismissed";

    case "NEEDS_INVESTIGATION":
      return "report-status investigation";

    case "SUBMITTED":
      return "report-status submitted";

    default:
      return "report-status";
  }
}


function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("en-IN");
}


function relevancePercent(value) {
  return `${Math.round(
    (Number(value) || 0) * 100
  )}%`;
}


/* ============================================================
   PAGE
   ============================================================ */

export default function PublicReportStatus() {
  const { reportId } = useParams();

  const [report, setReport] = useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /* ==========================================================
     LOAD REPORT
     ========================================================== */

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError("");
    setReport(null);

    api.citizenReportStatus(reportId)
      .then((data) => {
        if (active) {
          setReport(data);
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err.message ||
              "Unable to load this report."
          );
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [reportId]);


  /* ==========================================================
     LOADING
     ========================================================== */

  if (loading) {
    return (
      <div className="public-report-status-page">

        <header className="public-report-status-header">

          <div className="public-report-status-brand">

            <div className="public-report-status-logo">
              SB
            </div>

            <div>
              <strong>
                SafeBite
              </strong>

              <span>
                Government Food Safety Platform
              </span>
            </div>

          </div>

        </header>

        <main className="public-report-status-container">

          <section className="public-report-status-card">

            <div className="public-report-status-loading">
              Loading report status...
            </div>

          </section>

        </main>

      </div>
    );
  }


  /* ==========================================================
     ERROR
     ========================================================== */

  if (error || !report) {
    return (
      <div className="public-report-status-page">

        <header className="public-report-status-header">

          <div className="public-report-status-brand">

            <div className="public-report-status-logo">
              SB
            </div>

            <div>
              <strong>
                SafeBite
              </strong>

              <span>
                Government Food Safety Platform
              </span>
            </div>

          </div>

        </header>

        <main className="public-report-status-container">

          <section className="public-report-status-card public-report-status-error">

            <div className="public-report-status-icon">
              !
            </div>

            <div className="public-report-status-eyebrow">
              REPORT NOT FOUND
            </div>

            <h1>
              We couldn't find this report.
            </h1>

            <p>
              {error ||
                "Check the Report ID and try again."}
            </p>

            <Link
              to="/"
              className="public-report-status-secondary"
            >
              Return to SafeBite
            </Link>

          </section>

        </main>

      </div>
    );
  }


  /* ==========================================================
     SUCCESS
     ========================================================== */

  return (
    <div className="public-report-status-page">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <header className="public-report-status-header">

        <div className="public-report-status-brand">

          <div className="public-report-status-logo">
            SB
          </div>

          <div>

            <strong>
              SafeBite
            </strong>

            <span>
              Government Food Safety Platform
            </span>

          </div>

        </div>


        <div className="public-report-status-official">
          OFFICIAL REPORT TRACKING
        </div>

      </header>


      {/* ======================================================
          MAIN
          ====================================================== */}

      <main className="public-report-status-container">

        <section className="public-report-status-card">

          <div className="public-report-status-eyebrow">
            CITIZEN REPORT
          </div>

          <h1>
            Report #{report.report_id}
          </h1>

          <p className="public-report-status-subtitle">
            {report.outlet ||
              "Registered food outlet"}
          </p>


          {/* ==================================================
              STATUS
              ================================================== */}

          <div className="public-report-status-main">

            <span
              className={statusClass(
                report.status
              )}
            >
              {statusLabel(
                report.status
              )}
            </span>

          </div>


          {/* ==================================================
              TIMELINE
              ================================================== */}

          <div className="public-report-status-timeline">

            <div
              className={
                report.status
                  ? "report-timeline-step done"
                  : "report-timeline-step"
              }
            >
              <div className="report-timeline-dot">
                ✓
              </div>

              <div>
                <strong>
                  Report received
                </strong>

                <span>
                  {formatDate(
                    report.submitted_at
                  )}
                </span>
              </div>
            </div>


            <div
              className={
                report.status ===
                  "NEEDS_INVESTIGATION" ||
                report.status ===
                  "VERIFIED" ||
                report.status ===
                  "DISMISSED"
                  ? "report-timeline-step done"
                  : "report-timeline-step current"
              }
            >
              <div className="report-timeline-dot">
                2
              </div>

              <div>
                <strong>
                  Government review
                </strong>

                <span>
                  Evidence may be reviewed by
                  an authorized officer.
                </span>
              </div>
            </div>


            <div
              className={
                report.status === "VERIFIED" ||
                report.status === "DISMISSED"
                  ? "report-timeline-step done"
                  : "report-timeline-step"
              }
            >
              <div className="report-timeline-dot">
                3
              </div>

              <div>
                <strong>
                  Government decision
                </strong>

                <span>
                  Final status depends on
                  official review.
                </span>
              </div>
            </div>

          </div>


          {/* ==================================================
              REPORT DETAILS
              ================================================== */}

          <div className="public-report-status-grid">

            <div>
              <span>
                Registration ID
              </span>

              <strong>
                {report.registration_id ||
                  "Not available"}
              </strong>
            </div>


            <div>
              <span>
                AI screening
              </span>

              <strong>
                {report.ai_status ||
                  "Not available"}
              </strong>
            </div>


            <div>
              <span>
                AI relevance
              </span>

              <strong>
                {relevancePercent(
                  report.ai_relevance
                )}
              </strong>
            </div>


            <div>
              <span>
                AI severity
              </span>

              <strong>
                {report.ai_severity ||
                  "UNKNOWN"}
              </strong>
            </div>

          </div>


          {/* ==================================================
              INFORMATION NOTICE
              ================================================== */}

          <div className="public-report-status-notice">

            <strong>
              What this means
            </strong>

            <p>
              SafeBite uses AI as a screening and
              evidence-assistance tool. AI results and
              citizen reports do not by themselves establish
              an official food-safety violation.
            </p>

          </div>


          {/* ==================================================
              ACTIONS
              ================================================== */}

          <div className="public-report-status-actions">

            {report.registration_id && (

              <Link
                to={`/public/outlet/${encodeURIComponent(
                  report.registration_id
                )}`}
                className="public-report-status-primary"
              >
                View Official Outlet
              </Link>

            )}

          </div>

        </section>

      </main>


      <footer className="public-report-status-footer">
        SafeBite • Official public food-safety reporting platform
      </footer>

    </div>
  );
}
