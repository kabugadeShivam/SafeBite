import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Investigations() {
  const [data, setData] = useState(null);
  useEffect(() => { api.investigations().then(setData); }, []);
  return <div className="page"><div className="page-head"><div><div className="eyebrow">CASE MANAGEMENT</div><h2>Investigations</h2></div></div><section className="section-card"><div className="table-wrap"><table><thead><tr><th>Case</th><th>Establishment</th><th>Alert</th><th>Officer</th><th>Status</th><th>Started</th><th></th></tr></thead><tbody>{data?.investigations?.map(i => <tr key={i.id}><td><strong>INV-{String(i.id).padStart(4,"0")}</strong></td><td>{i.restaurant.name}</td><td>{i.alert.reason}</td><td>{i.officer}</td><td><span className="badge neutral">{i.status.replaceAll("_", " ")}</span></td><td>{new Date(i.started_at).toLocaleString()}</td><td><Link className="text-link" to={`/investigations/${i.id}`}>Open</Link></td></tr>)}</tbody></table></div></section></div>;
}
