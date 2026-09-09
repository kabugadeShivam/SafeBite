import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = () => api.dashboard().then(d => { if (active) setData(d); }).catch(e => { if (active) setError(e.message); });
    load();
    const timer = setInterval(load, 5000);
    return () => { active = false; clearInterval(timer); };
  }, []);
  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="panel">Loading dashboard…</div>;

  const c = data.counts;
  return <>
    <section className="hero"><div><div className="eyebrow">REGIONAL COMMAND CENTER</div><h2>Food-safety overview</h2><p className="muted">Real-time monitoring and investigation status for your authorised jurisdiction.</p></div><div className="status-chip">● SYSTEM ONLINE</div></section>
    <div className="stat-grid">
      <div className="stat-card"><span>Monitored establishments</span><strong>{c.establishments}</strong></div>
      <div className="stat-card"><span>Online IoT devices</span><strong>{c.online_devices}/{c.devices}</strong></div>
      <div className="stat-card danger"><span>Critical alerts</span><strong>{c.critical_alerts}</strong></div>
      <div className="stat-card warn"><span>Pending investigations</span><strong>{c.pending_investigations}</strong></div>
    </div>
    <div className="content-grid">
      <section className="panel"><div className="panel-header"><div><h3>Latest alerts</h3><span className="muted">Most recent incidents in this jurisdiction</span></div><Link to="/alerts" className="text-link">View all →</Link></div>
        {data.latest_alerts.length === 0 ? <div className="empty">No alerts yet. Start the IoT simulator to generate monitoring events.</div> : <div className="list">{data.latest_alerts.map(a => <Link key={a.id} to={`/alerts/${a.id}`} className="list-row"><div><strong>{a.restaurant.name}</strong><span>{a.reason}</span></div><div className="row-right"><span className={`severity ${a.severity.toLowerCase()}`}>{a.severity}</span><strong>{a.risk_score}</strong></div></Link>)}</div>}
      </section>
      <section className="panel"><h3>System interpretation</h3><div className="info-stack"><div><strong>Risk signals</strong><p className="muted">Sensor readings are converted into explainable risk scores before becoming government incidents.</p></div><div><strong>Investigation</strong><p className="muted">Officers can submit findings and corrective actions for audit.</p></div><div><strong>Audit</strong><p className="muted">Critical case actions are linked through a tamper-evident hash chain.</p></div></div></section>
    </div>
  </>;
}
