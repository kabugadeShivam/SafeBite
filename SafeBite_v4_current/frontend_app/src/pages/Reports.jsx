import { useEffect, useState } from "react";
import { api } from "../api";

export default function Reports() {
  const [data, setData] = useState(null);
  const [audit, setAudit] = useState(null);
  const [error, setError] = useState("");

  const load = () => api.report().then(setData).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);

  const verifyAudit = async () => {
    try {
      setAudit(await api.auditVerify());
    } catch (e) {
      setAudit({ verified: false, message: e.message });
    }
  };

  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="panel">Loading report…</div>;

  const sev = data.alerts.severity;

  return <div className="detail-stack">
    <section className="hero">
      <div>
        <div className="eyebrow">REGIONAL REPORTING</div>
        <h2>Monitoring summary</h2>
        <p className="muted">Operational statistics for {data.jurisdiction.region}, {data.jurisdiction.state}.</p>
      </div>
      <button className="secondary-button" onClick={load}>Refresh</button>
    </section>

    <div className="stat-grid">
      <div className="stat-card"><span>Establishments</span><strong>{data.establishments}</strong></div>
      <div className="stat-card"><span>Total alerts</span><strong>{data.alerts.total}</strong></div>
      <div className="stat-card"><span>Open investigations</span><strong>{data.investigations.open}</strong></div>
      <div className="stat-card"><span>Closed investigations</span><strong>{data.investigations.closed}</strong></div>
    </div>

    <div className="three-grid">
      <div className="panel"><h3>Severity distribution</h3><div className="report-lines"><span>Critical <strong>{sev.RED}</strong></span><span>High risk <strong>{sev.ORANGE}</strong></span><span>Warning <strong>{sev.AMBER}</strong></span><span>Normal <strong>{sev.GREEN}</strong></span></div></div>
      <div className="panel"><h3>Alert sources</h3><div className="report-lines"><span>IoT <strong>{data.alerts.source.IOT}</strong></span><span>AI <strong>{data.alerts.source.AI}</strong></span></div></div>
      <div className="panel"><h3>Audit integrity</h3><p className="muted">Verify the complete local tamper-evident audit chain.</p><button className="primary-button" onClick={verifyAudit}>Verify audit chain</button>{audit && <div className={`callout ${audit.verified ? "good" : "bad"}`}>{audit.verified ? "✓ Verified" : "⚠ Verification failed"}<br/>{audit.message}</div>}</div>
    </div>
  </div>;
}
