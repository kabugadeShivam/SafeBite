import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

export default function InvestigationDetails() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [audit, setAudit] = useState(null);
  const [findings, setFindings] = useState("");
  const [actionTaken, setActionTaken] = useState("");
  const [correctiveAction, setCorrectiveAction] = useState("");
  const [status, setStatus] = useState("PENDING_VERIFICATION");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const officer = useMemo(() => {
    try { return JSON.parse(localStorage.getItem("safebite_officer") || "{}"); } catch { return {}; }
  }, []);

  const canVerify = officer.role === "SUPERVISOR" || officer.role === "CENTRAL_ADMIN";

  const load = async () => {
    const d = await api.investigation(id);
    setData(d);
    setFindings(d.findings || "");
    setActionTaken(d.action_taken || "");
    setCorrectiveAction(d.corrective_action || "");
    setStatus(d.status === "CLOSED" ? "CLOSED" : d.status || "IN_PROGRESS");
  };

  useEffect(() => { load().catch(e => setMessage(e.message)); }, [id]);

  if (!data) return <div className="panel">{message || "Loading case…"}</div>;

  const save = async () => {
    try {
      setBusy(true);
      const r = await api.updateInvestigation(id, { findings, action_taken: actionTaken, corrective_action: correctiveAction, status });
      setMessage(r.message);
      await load();
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  };

  const upload = async e => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setBusy(true);
      const r = await api.uploadEvidence(id, file);
      setMessage(`Evidence uploaded. SHA-256: ${r.sha256}`);
      await load();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  };

  const verify = async decision => {
    try {
      setBusy(true);
      const r = await api.verifyInvestigation(id, {
        decision,
        remarks: decision === "APPROVE" ? "Verified by supervisor" : "Returned for correction",
      });
      setMessage(r.message);
      await load();
    } catch (e) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  };

  const loadAudit = async () => {
    try { setAudit(await api.audit(id)); }
    catch (e) { setAudit({ chain_verified: false, chain_message: e.message, records: [] }); }
  };

  const isClosed = data.status === "CLOSED";

  return <div className="detail-stack">
    <section className="panel">
      <div className="eyebrow">INVESTIGATION #{String(id).padStart(4, "0")}</div>
      <h2>{data.alert.restaurant.name}</h2>
      <p className="muted">{data.alert.restaurant.location} · {data.alert.restaurant.region}</p>
      <div className="three-grid">
        <div className="mini-card"><span>Alert</span><strong>{data.alert.severity} · {data.alert.risk_score}</strong><small>{data.alert.reason}</small></div>
        <div className="mini-card"><span>Officer</span><strong>{data.officer}</strong><small>{data.status.replaceAll("_", " ")}</small></div>
        <div className="mini-card"><span>Started</span><strong>{new Date(data.started_at).toLocaleDateString()}</strong><small>{data.verified_at ? `Verified ${new Date(data.verified_at).toLocaleDateString()}` : "Verification pending"}</small></div>
      </div>
    </section>

    {!isClosed && <section className="panel">
      <div className="panel-header"><div><h3>Official findings</h3><span className="muted">Record inspection findings and the corrective action taken.</span></div></div>
      <div className="form-grid">
        <label>Findings<textarea value={findings} onChange={e => setFindings(e.target.value)} /></label>
        <label>Action taken<textarea value={actionTaken} onChange={e => setActionTaken(e.target.value)} /></label>
        <label>Corrective action<textarea value={correctiveAction} onChange={e => setCorrectiveAction(e.target.value)} /></label>
        <label>Status<select value={status} onChange={e => setStatus(e.target.value)}><option>IN_PROGRESS</option><option>ACTION_REQUIRED</option><option>PENDING_VERIFICATION</option></select></label>
      </div>
      <button className="primary-button" onClick={save} disabled={busy}>Submit findings</button>
    </section>}

    <section className="panel">
      <div className="panel-header"><div><h3>Evidence</h3><span className="muted">Each uploaded file receives a SHA-256 integrity hash.</span></div>{!isClosed && <label className="secondary-button upload-button">Upload evidence<input type="file" onChange={upload} hidden /></label>}</div>
      {data.evidence.length === 0 ? <div className="empty">No evidence uploaded.</div> : <div className="list">{data.evidence.map(e => <div className="list-row" key={e.id}><div><strong>{e.filename}</strong><span>{new Date(e.uploaded_at).toLocaleString()}</span></div><code>{e.sha256}</code></div>)}</div>}
    </section>

    {canVerify && !isClosed && <section className="panel">
      <div className="panel-header"><div><h3>Supervisor verification</h3><span className="muted">Approve only after findings and corrective action have been submitted.</span></div><div className="button-row"><button className="secondary-button" onClick={() => verify("RETURN")} disabled={busy}>Return for correction</button><button className="primary-button" onClick={() => verify("APPROVE")} disabled={busy}>Approve & close</button></div></div>
    </section>}

    <section className="panel">
      <div className="panel-header"><div><h3>Audit trail</h3><span className="muted">Tamper-evident record chain for this case.</span></div><button className="secondary-button" onClick={loadAudit}>Verify audit</button></div>
      {audit && <><div className={`callout ${audit.chain_verified ? "good" : "bad"}`}>{audit.chain_verified ? "✓ Chain verified" : "⚠ Chain verification failed"} — {audit.chain_message}</div><div className="list">{audit.records.map(r => <div className="list-row" key={r.id}><div><strong>{r.record_type}</strong><span>{new Date(r.timestamp).toLocaleString()}</span></div><code>{r.record_hash}</code></div>)}</div></>}
    </section>

    {message && <div className="toast">{message}</div>}
  </div>;
}
