import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Investigations() {
  const [data, setData] = useState(null);
  useEffect(() => { api.investigations().then(setData); }, []);
  if (!data) return <div className="panel">Loading investigations…</div>;
  return <section className="panel"><div className="eyebrow">CASE MANAGEMENT</div><h2>Investigations</h2><p className="muted">Track active cases, submitted findings, verification and closure.</p>{data.total === 0 ? <div className="empty">No investigations yet.</div> : <div className="table-wrap"><table><thead><tr><th>Case</th><th>Establishment</th><th>Alert</th><th>Officer</th><th>Status</th><th></th></tr></thead><tbody>{data.investigations.map(i => <tr key={i.id}><td>INV-{String(i.id).padStart(4,"0")}</td><td>{i.restaurant.name}</td><td>{i.alert.reason}</td><td>{i.officer}</td><td>{i.status.replaceAll("_", " ")}</td><td><Link className="text-link" to={`/investigations/${i.id}`}>Open</Link></td></tr>)}</tbody></table></div>}</section>;
}
