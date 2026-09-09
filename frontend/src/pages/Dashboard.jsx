import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const severityClass = s => s === "RED" ? "danger" : s === "ORANGE" ? "warning" : "amber";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api.dashboard().then(setData).catch(e => setError(e.message)); }, []);

  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="loading">Loading regional overview…</div>;

  const c = data.counts;

  return (
    <div className="page">
      <div className="page-head"><div><div className="eyebrow">LIVE OVERVIEW</div><h2>Safety control center</h2></div><span className="live-dot">● Live monitoring</span></div>
      <div className="stat-grid">
        <div className="stat-card"><span>Monitored establishments</span><strong>{c.establishments}</strong><small>Registered in scope</small></div>
        <div className="stat-card"><span>Online devices</span><strong>{c.online_devices}<em>/{c.devices}</em></strong><small>Device health</small></div>
        <div className="stat-card critical"><span>Critical alerts</span><strong>{c.critical_alerts}</strong><small>Immediate attention</small></div>
        <div className="stat-card"><span>Pending investigations</span><strong>{c.pending_investigations}</strong><small>Cases not closed</small></div>
      </div>

      <section className="section-card">
        <div className="section-title"><div><h3>Recent alerts</h3><span>Latest safety events from your authorised region</span></div><Link to="/alerts" className="text-link">View all →</Link></div>
        <div className="table-wrap">
          <table><thead><tr><th>Severity</th><th>Establishment</th><th>Issue</th><th>Risk</th><th>Status</th><th></th></tr></thead>
          <tbody>{data.latest_alerts.map(a => <tr key={a.id}><td><span className={`badge ${severityClass(a.severity)}`}>{a.severity}</span></td><td><strong>{a.restaurant.name}</strong><small>{a.restaurant.region}</small></td><td>{a.reason}</td><td><strong>{a.risk_score}</strong>/100</td><td>{a.status.replaceAll("_", " ")}</td><td><Link className="text-link" to={`/alerts/${a.id}`}>Open</Link></td></tr>)}</tbody></table>
        </div>
      </section>

      <div className="two-col">
        <section className="section-card compact"><h3>Operational principle</h3><p className="muted">SafeBite converts raw sensor observations into explainable risk signals. Government officers see actionable incidents rather than a stream of raw telemetry.</p></section>
        <section className="section-card compact"><h3>Investigation lifecycle</h3><div className="timeline-mini"><span>Alert</span><i>→</i><span>Investigation</span><i>→</i><span>Action</span><i>→</i><span>Verification</span><i>→</i><span>Audit</span></div></section>
      </div>
    </div>
  );
}
