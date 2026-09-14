import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

function statusClass(status) {
  switch (String(status || "").toUpperCase()) {
    case "EXCELLENT":
      return "public-status excellent";
    case "GOOD":
      return "public-status compliant";
    case "WATCH":
      return "public-status watchlist";
    case "POOR":
      return "public-status warning";
    case "CRITICAL":
      return "public-status critical";
    default:
      return "public-status";
  }
}

function statusLabel(status) {
  const value = String(status || "").toUpperCase();
  return ["EXCELLENT", "GOOD", "WATCH", "POOR", "CRITICAL"].includes(value)
    ? value
    : "STATUS UNAVAILABLE";
}

function formatDate(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("en-IN");
}

function decisionLabel(decision) {
  switch (String(decision || "").toUpperCase()) {
    case "APPROVE":
    case "VERIFIED":
      return "VERIFIED";
    case "REJECT":
      return "NOT VERIFIED";
    case "DISMISSED":
      return "DISMISSED";
    default:
      return String(decision || "NOT AVAILABLE").replaceAll("_", " ");
  }
}

export default function PublicOutlet() {
  const { registrationId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setData(null);

    api.publicOutlet(registrationId)
      .then((response) => {
        if (active) setData(response);
      })
      .catch((err) => {
        if (active) {
          setError(err.message || "Unable to load official outlet information.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [registrationId]);

  if (loading) {
    return (
      <div className="public-page">
        <div className="public-card public-loading">
          <div className="public-logo">SB</div>
          <h1>SafeBite</h1>
          <p>Loading official government status...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="public-page">
        <div className="public-card public-error-card">
          <div className="public-logo">SB</div>
          <h1>SafeBite</h1>
          <p>{error || "Official outlet information is unavailable."}</p>
          <small>Please check the registration ID or try again later.</small>
        </div>
      </div>
    );
  }

  const outlet = data.outlet || {};
  const officialStatus = data.official_status || {};
  const summary = data.public_summary || {};
  const verifiedOutcome =
    data.latest_verified_outcome || officialStatus.latest_verified_outcome || null;
  const strengths = Array.isArray(summary.strengths) ? summary.strengths : [];
  const concerns = Array.isArray(summary.concerns) ? summary.concerns : [];
  const score = Number(officialStatus.compliance_score ?? 0);
  const status = officialStatus.status || "UNKNOWN";
  const auditMonth = officialStatus.audit_month;

  const hasVerifiedOutcome = Boolean(
    verifiedOutcome &&
      (verifiedOutcome.decision ||
        verifiedOutcome.status ||
        verifiedOutcome.verified_at ||
        verifiedOutcome.remarks)
  );

  return (
    <div className="public-page">
      <header className="public-header">
        <div className="public-brand">
          <div className="public-logo">SB</div>
          <div>
            <strong>SafeBite</strong>
            <span>Government Food Safety Platform</span>
          </div>
        </div>
        <div className="government-badge">GOVERNMENT VERIFIED</div>
      </header>

      <main className="public-container">
        <section className="public-card public-hero">
          <div className="public-eyebrow">MONTHLY FOOD-SAFETY PERFORMANCE</div>
          <h1>{outlet.name || "Registered Food Outlet"}</h1>
          <p className="public-location">
            {outlet.location || outlet.region || "Registered establishment"}
          </p>

          <div className={statusClass(status)}>
            <div className="public-score">
              {Math.round(score)}
              <span>/100</span>
            </div>
            <div>
              <strong>{statusLabel(status)}</strong>
              <small>
                {auditMonth
                  ? `AI monthly assessment • ${auditMonth}`
                  : "Official food-safety monitoring status"}
              </small>
            </div>
          </div>

          <div className="public-government-note" style={{ marginTop: "15px" }}>
            <strong>
              {officialStatus.public_comment ||
                "Monthly food-safety performance is being monitored."}
            </strong>
          </div>

          <div className="public-government-note">
            This information is published by the SafeBite government platform.
            The public score is generated from official SafeBite audit data and
            AI-assisted monthly analysis. Government officers remain responsible
            for official decisions.
          </div>
        </section>

        {hasVerifiedOutcome && (
          <section className="public-card">
            <div className="public-eyebrow">OFFICIAL INVESTIGATION OUTCOME</div>
            <h2>Government verification</h2>

            <div className="public-list" style={{ marginTop: "15px" }}>
              {verifiedOutcome.decision && (
                <div>
                  <span>Decision</span>
                  <strong>{decisionLabel(verifiedOutcome.decision)}</strong>
                </div>
              )}
              {verifiedOutcome.status && (
                <div>
                  <span>Investigation status</span>
                  <strong>{String(verifiedOutcome.status).replaceAll("_", " ")}</strong>
                </div>
              )}
              {verifiedOutcome.verified_at && (
                <div>
                  <span>Verified at</span>
                  <strong>{formatDate(verifiedOutcome.verified_at)}</strong>
                </div>
              )}
            </div>

            {verifiedOutcome.remarks && (
              <div className="public-government-note" style={{ marginTop: "15px" }}>
                <strong>Government remarks</strong>
                <br />
                {verifiedOutcome.remarks}
              </div>
            )}

            <p className="public-muted" style={{ marginTop: "14px" }}>
              This outcome reflects an authorised government investigation and is
              separate from preliminary AI screening.
            </p>
          </section>
        )}

        <section className="public-grid">
          <div className="public-card">
            <h2>Safety overview</h2>
            <div className="public-list">
              <div>
                <span>Public status</span>
                <strong>{statusLabel(status)}</strong>
              </div>
              <div>
                <span>Monthly score</span>
                <strong>{Math.round(score)} / 100</strong>
              </div>
              <div>
                <span>Assessment month</span>
                <strong>{auditMonth || "Not available"}</strong>
              </div>
              <div>
                <span>Registration ID</span>
                <strong>{outlet.registration_id || registrationId}</strong>
              </div>
              <div>
                <span>Assessment updated</span>
                <strong>
                  {formatDate(
                    officialStatus.assessment_at || officialStatus.generated_at
                  )}
                </strong>
              </div>
            </div>
          </div>

          <div className="public-card">
            <h2>Government observations</h2>

            {strengths.length > 0 && (
              <>
                <h3 className="public-subheading positive">Positive findings</h3>
                <ul className="public-bullets">
                  {strengths.map((item, index) => (
                    <li key={`strength-${index}`}>✓ {item}</li>
                  ))}
                </ul>
              </>
            )}

            {concerns.length > 0 && (
              <>
                <h3 className="public-subheading concern">Areas requiring attention</h3>
                <ul className="public-bullets">
                  {concerns.map((item, index) => (
                    <li key={`concern-${index}`}>⚠ {item}</li>
                  ))}
                </ul>
              </>
            )}

            {strengths.length === 0 && concerns.length === 0 && (
              <p className="public-muted">No additional public observations are available.</p>
            )}
          </div>
        </section>

        <section className="public-card public-recommendation">
          <div>
            <div className="public-eyebrow">GOVERNMENT RECOMMENDATION</div>
            <p>
              {summary.recommendation ||
                "Continue monitoring official food-safety status."}
            </p>
          </div>
          <Link
            className="public-report-button"
            to={`/public/outlet/${encodeURIComponent(registrationId)}/report`}
          >
            🚨 Report a Food-Safety Concern
          </Link>
        </section>

        <section className="public-card public-verification">
          <div>
            <span>Official source</span>
            <strong>{data.source || "SafeBite Government Platform"}</strong>
          </div>
          <div>
            <span>Outlet registration</span>
            <strong>{outlet.registration_id || registrationId}</strong>
          </div>
          <div className="public-readonly">✓ Government-controlled information</div>
        </section>

        <section className="public-card">
          <div className="public-eyebrow">CITIZEN SAFETY REPORTING</div>
          <h2>See something unsafe?</h2>
          <p className="public-government-note">
            Customers can submit a photo or video describing a food-safety concern.
            SafeBite may use AI to screen the evidence before a government officer
            reviews it.
          </p>
          <div style={{ marginTop: "18px" }}>
            <Link
              className="public-report-button"
              to={`/public/outlet/${encodeURIComponent(registrationId)}/report`}
            >
              Submit a Concern
            </Link>
          </div>
        </section>
      </main>

      <footer className="public-footer">
        SafeBite • Official public food-safety information
      </footer>
    </div>
  );
}
