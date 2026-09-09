import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

export default function AlertDetails() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const load = () => api.alert(id).then(setData);
  useEffect(load, [id]);

  const investigate = async () => {
    setBusy(true);
    try {
      const result = await api.startInvestigation(id);
      navigate(`/investigations/${result.investigation_id}`);
    } finally { setBusy(false); }
  };

  if (!data) return <div className="loading">Loading alert evidence…</div>;
  const a = data.alert;

  return <div className="page">
    <Link to="/alerts" className="back-link">← Back to alerts</Link>
    <div className="detail-head"><div><div className="eyebrow">ALERT #{a.id}</div><h2>{a.restaurant.name}</h2><p className="muted">{a.restaurant.registration_id} · {a.restaurant.region}</p></div><div className={`risk-ring ${a.severity === "RED" ? "danger" : "warning"}`}><strong>{a.risk_score}</strong><span>/100</span><small>{a.severity}</small></div></div>
    <div className="two-col">
      <section className="section-card"><h3>Why was this alert raised?</h3><div className="reason-box">{a.reason}</div><dl className="detail-list"><div><dt>Status</dt><dd>{a.status.replaceAll("_", " ")}</dd></div><div><dt>Source</dt><dd>{a.source}</dd></div><div><dt>Detected</dt><dd>{new Date(a.timestamp).toLocaleString()}</dd></div><div><dt>Device</dt><dd>{data.alert.device?.device_id || "—"}</dd></div></dl>{!data.investigation && <button className="primary-button" onClick={investigate} disabled={busy}>{busy ? "Opening case…" : "Start investigation"}</button>}</section>
      <section className="section-card"><h3>Establishment</h3><dl className="detail-list"><div><dt>Name</dt><dd>{a.restaurant.name}</dd></div><div><dt>Registration</dt><dd>{a.restaurant.registration_id}</dd></div><div><dt>Location</dt><dd>{a.restaurant.location}</dd></div><div><dt>Region</dt><dd>{a.restaurant.region}, {a.restaurant.state}</dd></div></dl><h3 className="subhead">Device health</h3><dl className="detail-list"><div><dt>Status</dt><dd>{a.device?.status || "—"}</dd></div><div><dt>Last seen</dt><dd>{a.device?.last_seen_at ? new Date(a.device.last_seen_at).toLocaleString() : "—"}</dd></div></dl></section>
    </div>

    <section className="section-card"><div className="section-title"><div><h3>Sensor evidence</h3><span>Latest readings associated with the detected device</span></div></div><div className="table-wrap"><table><thead><tr><th>Time</th><th>Temperature</th><th>Humidity</th><th>Door</th></tr></thead><tbody>{data.sensor_evidence.map((r, i) => <tr key={i}><td>{new Date(r.timestamp).toLocaleString()}</td><td>{r.temperature} °C</td><td>{r.humidity} %</td><td>{r.door_open ? "OPEN" : "CLOSED"}</td></tr>)}</tbody></table></div></section>
  </div>;
}
