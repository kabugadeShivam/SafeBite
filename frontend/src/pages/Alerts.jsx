import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Alerts() {
  const [data, setData] = useState(null);
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");

  const load = () => {
    const p = new URLSearchParams();
    if (severity) p.set("severity", severity);
    if (status) p.set("status_filter", status);
    api.alerts(p.toString()).then(setData);
  };

  useEffect(load, [severity, status]);

  return <div className="page">
    <div className="page-head"><div><div className="eyebrow">INCIDENT CENTER</div><h2>Alerts</h2></div></div>
    <div className="filters"><select value={severity} onChange={e => setSeverity(e.target.value)}><option value="">All severity</option><option value="RED">Critical</option><option value="ORANGE">High</option><option value="AMBER">Warning</option></select><select value={status} onChange={e => setStatus(e.target.value)}><option value="">All status</option><option value="OPEN">Open</option><option value="UNDER_INVESTIGATION">Under investigation</option><option value="ACTION_REQUIRED">Action required</option><option value="CLOSED">Closed</option></select></div>
    <section className="section-card"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Establishment</th><th>Reason</th><th>Risk</th><th>Status</th><th>Time</th><th></th></tr></thead><tbody>{data?.alerts?.map(a => <tr key={a.id}><td>#{a.id}</td><td><span className={`badge ${a.severity === "RED" ? "danger" : a.severity === "ORANGE" ? "warning" : "amber"}`}>{a.severity}</span></td><td><strong>{a.restaurant.name}</strong><small>{a.restaurant.registration_id}</small></td><td>{a.reason}</td><td><strong>{a.risk_score}</strong>/100</td><td>{a.status.replaceAll("_", " ")}</td><td>{new Date(a.timestamp).toLocaleString()}</td><td><Link className="text-link" to={`/alerts/${a.id}`}>Details</Link></td></tr>)}</tbody></table></div></section>
  </div>;
}
