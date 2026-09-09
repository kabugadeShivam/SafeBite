import { useEffect, useState } from "react";
import { api } from "../api";

export default function Establishments() {
  const [data, setData] = useState(null);
  useEffect(() => { api.establishments().then(setData); }, []);
  return <div className="page"><div className="page-head"><div><div className="eyebrow">REGIONAL REGISTER</div><h2>Establishments</h2></div></div><section className="section-card"><div className="table-wrap"><table><thead><tr><th>Establishment</th><th>Registration</th><th>Region</th><th>Devices</th><th>Active alerts</th><th>Critical</th><th>Status</th></tr></thead><tbody>{data?.establishments?.map(r => <tr key={r.id}><td><strong>{r.name}</strong><small>{r.location}</small></td><td>{r.registration_id}</td><td>{r.region}</td><td>{r.devices}</td><td>{r.active_alerts}</td><td><span className={r.critical_alerts ? "text-danger" : "text-safe"}>{r.critical_alerts}</span></td><td>{r.status}</td></tr>)}</tbody></table></div></section></div>;
}
