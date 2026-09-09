import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

export default function InvestigationDetails() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [audit, setAudit] = useState(null);
  const [findings, setFindings] = useState("");
  const [action, setAction] = useState("");
  const [corrective, setCorrective] = useState("");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const load = () => api.investigation(id).then(d => { setData(d); setFindings(d.findings || ""); setAction(d.action_taken || ""); setCorrective(d.corrective_action || ""); });
  useEffect(load, [id]);

  const save = async () => {
    await api.updateInvestigation(id, { findings, action_taken: action, corrective_action: corrective, status: "PENDING_VERIFICATION" });
    setMessage("Findings submitted for verification.");
    load();
  };

  const upload = async () => { if (!file) return; await api.uploadEvidence(id, file); setMessage("Evidence uploaded and hashed."); setFile(null); load(); };
  const verify = async () => { await api.verifyInvestigation(id, { decision: "APPROVE", remarks: "Verified from portal." }); setMessage("Investigation verified and closed."); load(); };
  const loadAudit = async () => setAudit(await api.audit(id));

  if (!data) return <div className="loading">Loading case…</div>;

  return <div className="page">
    <Link to="/investigations" className="back-link">← Back to investigations</Link>
    <div className="detail-head"><div><div className="eyebrow">INVESTIGATION #{id}</div><h2>{data.alert.restaurant.name}</h2><p className="muted">Alert #{data.alert.id} · {data.alert.severity} · Risk {data.alert.risk_score}/100</p></div><span className="badge neutral large">{data.status.replaceAll("_", " ")}</span></div>
    <div className="two-col">
      <section className="section-card"><h3>Findings & action</h3><label>Inspection findings<textarea rows="5" value={findings} onChange={e => setFindings(e.target.value)} /></label><label>Action taken<textarea rows="4" value={action} onChange={e => setAction(e.target.value)} /></label><label>Corrective action / follow-up<textarea rows="4" value={corrective} onChange={e => setCorrective(e.target.value)} /></label><button className="primary-button" onClick={save}>Submit for verification</button>{message && <div className="success-box">{message}</div>}</section>
      <section className="section-card"><h3>Evidence</h3><div className="upload-box"><input type="file" onChange={e => setFile(e.target.files?.[0] || null)} /><button className="secondary-button" onClick={upload}>Upload evidence</button></div>{data.evidence.map(e => <div className="evidence-row" key={e.id}><strong>{e.filename}</strong><span>{e.sha256.slice(0, 18)}…</span></div>)}<div className="divider" /><h3>Verification</h3><p className="muted">Supervisor approval closes the case and records the verification event in the audit chain.</p><button className="primary-button" disabled={data.status !== "PENDING_VERIFICATION"} onClick={verify}>Verify & close case</button></section>
    </div>
    <section className="section-card"><div className="section-title"><div><h3>Audit / blockchain layer</h3><span>Every investigation event is chained with the previous record hash.</span></div><button className="secondary-button" onClick={loadAudit}>Load audit</button></div>{audit && <><div className={audit.chain_verified ? "success-box" : "error-box"}>{audit.chain_message}</div><div className="audit-list">{audit.records.map(r => <div className="audit-item" key={r.id}><div><strong>{r.record_type.replaceAll("_", " ")}</strong><span>{new Date(r.timestamp).toLocaleString()}</span></div><code>{r.record_hash}</code></div>)}</div></>}</section>
  </div>;
}
