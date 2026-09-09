import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Alerts() {
  const [data, setData] = useState(null);
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const load = () => api.alerts(new URLSearchParams({ ...(severity && { severity }), ...(status && { status_filter: status }) }).toString()).then(d => { setData(d); return d; }).catch(() => { const d={ total: 0, alerts: [] }; setData(d); return d; });
  useEffect(() => {
    let active = true;
    const refresh = () => load().then(d => { if (active) setData(d); }).catch(() => {});
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => { active = false; clearInterval(timer); };
  }, [severity, status]);
  return <section className="panel"><div className="panel-header"><div><div className="eyebrow">INCIDENT MANAGEMENT</div><h2>Alerts</h2></div><div className="filters"><select value={severity} onChange={e => setSeverity(e.target.value)}><option value="">All severity</option><option value="RED">Critical</option><option value="ORANGE">High</option><option value="AMBER">Warning</option></select><select value={status} onChange={e => setStatus(e.target.value)}><option value="">All status</option><option value="OPEN">Open</option><option value="UNDER_INVESTIGATION">Investigating</option><option value="ACTION_REQUIRED">Action required</option><option value="CLOSED">Closed</option></select></div></div>
    {!data ? <div className="empty">Loading…</div> : data.total === 0 ? <div className="empty">No alerts match your filters.</div> : <div className="table-wrap"><table><thead><tr><th>Alert</th><th>Establishment</th><th>Risk</th><th>Reason</th><th>Status</th><th></th></tr></thead><tbody>{data.alerts.map(a => <tr key={a.id}><td>SB-{String(a.id).padStart(5,"0")}</td><td><strong>{a.restaurant.name}</strong><small>{a.restaurant.region}</small></td><td><span className={`severity ${a.severity.toLowerCase()}`}>{a.severity}</span> <strong>{a.risk_score}</strong></td><td>{a.reason}</td><td>{a.status.replaceAll("_", " ")}</td><td><Link className="text-link" to={`/alerts/${a.id}`}>Open</Link></td></tr>)}</tbody></table></div>}
  </section>;
}
