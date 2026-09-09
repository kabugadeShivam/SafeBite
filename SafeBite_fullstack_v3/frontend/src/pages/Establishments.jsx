import { useEffect, useState } from "react";
import { api } from "../api";

export default function Establishments() {
  const [data, setData] = useState(null);
  useEffect(() => { api.establishments().then(setData); }, []);
  if (!data) return <div className="panel">Loading establishments…</div>;
  return <section className="panel"><div className="eyebrow">REGISTERED FOOD ESTABLISHMENTS</div><h2>Establishments</h2><p className="muted">Current monitored establishments within the officer's jurisdiction.</p><div className="table-wrap"><table><thead><tr><th>Establishment</th><th>Registration</th><th>Location</th><th>Devices</th><th>Status</th></tr></thead><tbody>{data.establishments.map(r=><tr key={r.id}><td><strong>{r.name}</strong><small>{r.region}</small></td><td>{r.registration_id}</td><td>{r.location}</td><td>{r.devices.map(d=><div key={d.device_id}><strong>{d.device_id}</strong><small>{d.status}</small></div>)}</td><td>{r.status}</td></tr>)}</tbody></table></div></section>;
}
