import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const riskClass = (value) =>
  value === "RED" || value === "CRITICAL" ? "danger" : value === "ORANGE" || value === "HIGH" ? "warning" : "safe";

export default function DashboardNew() {
  const [data, setData] = useState(null);
  const [command, setCommand] = useState(null);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    setRefreshing(true);
    setError("");
    try {
      const [dashboard, center] = await Promise.all([api.dashboard(), api.commandCenter()]);
      setData(dashboard);
      setCommand(center);
    } catch (err) {
      setError(err.message || "Unable to load dashboard.");
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (error) {
    return <div className="page"><div className="error-box">{error}<button className="secondary-button" onClick={load}>Retry</button></div></div>;
  }
  if (!data) return <div className="loading">Loading overview…</div>;

  const c = data.counts || {};
  const s = command?.summary || {};
  const alerts = data.latest_alerts || [];
  const distribution = command?.risk_distribution || {};
  const priority = command?.priority || "LOW";

  return (
    <div className="page dashboard-clean">
      <div className="page-head clean-head">
        <div>
          <div className="eyebrow">LIVE OVERVIEW</div>
          <h2>Safety control center</h2>
          <p className="muted">Monitor risk, act on alerts, and verify compliance.</p>
        </div>
        <div className="head-actions">
          <span className="live-dot">● Live</span>
          <button className="secondary-button" onClick={load} disabled={refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button>
        </div>
      </div>

      <div className="stat-grid dashboard-stats">
        <div className="stat-card"><span>Establishments</span><strong>{c.establishments ?? 0}</strong><small>In authorised region</small></div>
        <div className="stat-card"><span>Devices online</span><strong>{c.online_devices ?? 0}<em>/{c.devices ?? 0}</em></strong><small>IoT health</small></div>
        <div className={`stat-card ${c.critical_alerts ? "critical" : ""}`}><span>Critical alerts</span><strong>{c.critical_alerts ?? 0}</strong><small>Immediate attention</small></div>
        <div className="stat-card"><span>Investigations</span><strong>{c.pending_investigations ?? 0}</strong><small>Pending closure</small></div>
      </div>

      <div className="dashboard-main-grid">
        <section className="section-card priority-card">
          <div className="section-title"><div><h3>Current priority</h3><span>Regional operational pressure</span></div><Link to="/command-center" className="text-link">Open →</Link></div>
          <div className={`priority-value ${riskClass(priority)}`}>{priority}</div>
          <div className="priority-details">
            <div><strong>{s.active_red_alerts ?? 0}</strong><span>RED alerts</span></div>
            <div><strong>{s.active_orange_alerts ?? 0}</strong><span>ORANGE alerts</span></div>
            <div><strong>{s.unresolved_investigations ?? 0}</strong><span>Investigations</span></div>
          </div>
        </section>

        <section className="section-card">
          <div className="section-title"><div><h3>Risk distribution</h3><span>Current outlet classification</span></div><Link to="/command-center" className="text-link">Details →</Link></div>
          <div className="risk-grid">
            {[["Critical", distribution.critical ?? 0, "danger"],["High", distribution.high ?? 0, "warning"],["Medium", distribution.medium ?? 0, "amber"],["Low", distribution.low ?? 0, "safe"]].map(([label, value, cls]) => (
              <div className="risk-item" key={label}><span>{label}</span><strong className={cls}>{value}</strong></div>
            ))}
          </div>
        </section>
      </div>

      <section className="section-card">
        <div className="section-title"><div><h3>Recent alerts</h3><span>Latest events requiring attention</span></div><Link to="/alerts" className="text-link">View all →</Link></div>
        {alerts.length === 0 ? <p className="muted">No alerts recorded.</p> : (
          <div className="alert-list">
            {alerts.slice(0, 5).map((alert) => (
              <Link className="alert-row" to={`/alerts/${alert.id}`} key={alert.id}>
                <div><strong>{alert.restaurant?.name || "Unknown establishment"}</strong><small>{alert.reason || "Risk condition detected"}</small></div>
                <div className="alert-meta"><span className={`badge ${alert.severity === "RED" ? "danger" : "warning"}`}>{alert.severity}</span><small>{alert.status}</small></div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <div className="dashboard-signal-grid">
        <section className="section-card compact"><div className="section-title"><div><h3>Safety signals</h3><span>Last 30 days</span></div><Link to="/command-center" className="text-link">Details →</Link></div><div className="signal-list"><div><span>Citizen reports</span><strong>{s.citizen_reports_30d ?? 0}</strong></div><div><span>Verified reports</span><strong>{s.verified_citizen_reports_30d ?? 0}</strong></div><div><span>AI hygiene findings</span><strong>{s.ai_hygiene_findings_30d ?? 0}</strong></div></div></section>
        <section className="section-card compact"><div className="section-title"><div><h3>System integrity</h3><span>Recent activity</span></div><Link to="/audit-history" className="text-link">Audit history →</Link></div><div className="signal-list"><div><span>Alerts · 24h</span><strong>{s.alerts_last_24h ?? 0}</strong></div><div><span>Blockchain audits · 30d</span><strong>{s.blockchain_anchored_audits_30d ?? 0}</strong></div><div><span>Critical AI findings</span><strong>{s.critical_ai_findings_30d ?? 0}</strong></div></div></section>
      </div>
    </div>
  );
}
