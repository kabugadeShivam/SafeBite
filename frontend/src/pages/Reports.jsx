import { useEffect, useState } from "react";
import { api } from "../api";

function Stat({ label, value, hint }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

export default function Reports() {
  const [report, setReport] = useState(null);
  const [audit, setAudit] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([api.report(), api.auditVerify()])
      .then(([reportData, auditData]) => {
        if (!active) return;
        setReport(reportData);
        setAudit(auditData);
        setError("");
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  if (loading) return <div className="panel">Loading regional report…</div>;
  if (error) return <div className="error-box">{error}</div>;
  if (!report) return <div className="panel">No report data available.</div>;

  const severity = report.alerts?.severity || {};
  const source = report.alerts?.source || {};
  const investigations = report.investigations || {};

  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">REGIONAL PERFORMANCE REPORT</div>
          <h2>Food-safety activity summary</h2>
          <p className="muted">
            {report.jurisdiction?.region === "ALL"
              ? `${report.jurisdiction.state} • Central / statewide view`
              : `${report.jurisdiction?.region}, ${report.jurisdiction?.state}`}
          </p>
        </div>
        <div className={audit?.verified ? "status-chip" : "status-chip danger"}>
          {audit?.verified ? "● AUDIT CHAIN VERIFIED" : "● AUDIT REVIEW REQUIRED"}
        </div>
      </section>

      <div className="stat-grid">
        <Stat label="Establishments" value={report.establishments} hint="Currently in scope" />
        <Stat label="Total alerts" value={report.alerts?.total ?? 0} hint="All recorded alerts" />
        <Stat label="Open investigations" value={investigations.open ?? 0} hint="Require follow-up" />
        <Stat label="Closed investigations" value={investigations.closed ?? 0} hint="Verified and closed" />
      </div>

      <div className="content-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Alert severity</h3>
              <span className="muted">Distribution across the authorised jurisdiction</span>
            </div>
          </div>
          <div className="info-stack">
            <div><strong>{severity.RED ?? 0}</strong><p className="muted">Critical / RED</p></div>
            <div><strong>{severity.ORANGE ?? 0}</strong><p className="muted">High risk / ORANGE</p></div>
            <div><strong>{severity.AMBER ?? 0}</strong><p className="muted">Warning / AMBER</p></div>
            <div><strong>{severity.GREEN ?? 0}</strong><p className="muted">Informational / GREEN</p></div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Alert sources</h3>
              <span className="muted">Where monitoring signals originated</span>
            </div>
          </div>
          <div className="info-stack">
            <div><strong>{source.IOT ?? 0}</strong><p className="muted">IoT monitoring alerts</p></div>
            <div><strong>{source.AI ?? 0}</strong><p className="muted">AI / vision alerts</p></div>
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Audit integrity</h3>
            <span className="muted">Tamper-evident record status for investigation actions</span>
          </div>
        </div>
        <div className="list-row">
          <div>
            <strong>{audit?.verified ? "Audit chain valid" : "Audit chain requires review"}</strong>
            <span>{audit?.message || "No audit verification result returned."}</span>
          </div>
          <div className="row-right">
            <span className={`severity ${audit?.verified ? "green" : "red"}`}>
              {audit?.verified ? "VERIFIED" : "CHECK"}
            </span>
            <strong>{audit?.total_records ?? 0}</strong>
          </div>
        </div>
      </section>
    </>
  );
}
