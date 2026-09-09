import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

export default function AlertDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.alert(id).then(setData).catch(e => setError(e.message)); }, [id]);
  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="panel">Loading alert…</div>;
  const a = data.alert;
  const start = async () => { const r = await api.startInvestigation(id); navigate(`/investigations/${r.investigation_id}`); };
  return <div className="detail-stack"><Link to="/alerts" className="text-link">← Alerts</Link><section className="panel"><div className="detail-head"><div><div className="eyebrow">ALERT #{String(a.id).padStart(5,"0")}</div><h2>{a.restaurant.name}</h2><p className="muted">{a.restaurant.location} · {a.restaurant.region}</p></div><div className={`risk-badge ${a.severity.toLowerCase()}`}><span>{a.risk_score}</span><small>{a.severity}</small></div></div><div className="callout"><strong>{a.alert_type.replaceAll("_"," ")}</strong><p>{a.reason}</p></div>
    <div className="three-grid"><div className="mini-card"><span>Device</span><strong>{a.device?.device_id || "—"}</strong><small>{a.device?.status || "Unknown"}</small></div><div className="mini-card"><span>Source</span><strong>{a.source}</strong><small>{new Date(a.timestamp).toLocaleString()}</small></div><div className="mini-card"><span>Status</span><strong>{a.status.replaceAll("_"," ")}</strong><small>Regional access enforced</small></div></div>
  </section><section className="panel"><div className="panel-header"><div><h3>Sensor evidence</h3><span className="muted">Latest readings from the triggering device</span></div></div>{data.sensor_evidence.length === 0 ? <div className="empty">No sensor evidence available.</div> : <div className="table-wrap"><table><thead><tr><th>Time</th><th>Temperature</th><th>Humidity</th><th>Door</th></tr></thead><tbody>{data.sensor_evidence.map((r,i)=><tr key={i}><td>{new Date(r.timestamp).toLocaleString()}</td><td>{r.temperature}°C</td><td>{r.humidity}%</td><td>{r.door_open ? "OPEN" : "CLOSED"}</td></tr>)}</tbody></table></div>}</section><section className="panel action-panel"><div><h3>{data.investigation ? "Investigation already opened" : "Government action"}</h3><p className="muted">Review the evidence before creating or continuing the official case.</p></div>{data.investigation ? <Link className="primary-button" to={`/investigations/${data.investigation.id}`}>Open investigation</Link> : <button className="primary-button" onClick={start}>Start investigation</button>}</section></div>;
}
