import { useEffect, useState } from "react";
import { api } from "../api";

function noticeClass(type) {
  return String(type || "").toUpperCase() === "APPRECIATION"
    ? "badge neutral"
    : "badge warning";
}

export default function MonthlyNotices() {
  const currentMonth = new Date().toISOString().slice(0, 7);
  const [month, setMonth] = useState(currentMonth);
  const [data, setData] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await api.monthlyNotices(month));
    } catch (err) {
      setError(err.message || "Unable to load monthly notices.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [month]);

  async function generate() {
    setGenerating(true);
    setError("");
    try {
      await api.generateMonthlyNotices(month);
      await load();
    } catch (err) {
      setError(err.message || "Unable to generate monthly notices.");
    } finally {
      setGenerating(false);
    }
  }

  if (loading && !data) return <div className="loading">Loading monthly notices...</div>;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">MONTHLY AI AUDIT</div>
          <h2>Outlet notices</h2>
          <p className="muted">Review automated appreciation and warning notices generated from the monthly audit evidence.</p>
        </div>
        <button className="primary-button" onClick={generate} disabled={generating}>
          {generating ? "Generating..." : "Generate / refresh"}
        </button>
      </div>

      <section className="section-card">
        <label className="field">
          <span>Audit month</span>
          <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} />
        </label>
      </section>

      {error && <div className="error-box">{error}</div>}

      <section className="section-card">
        <div className="panel-header">
          <div>
            <h3>{data?.count ?? 0} notice(s)</h3>
            <span className="muted">{data?.audit_month || month}</span>
          </div>
        </div>

        {!data?.notices?.length ? (
          <div className="empty-state">No monthly notices yet. Generate the selected month.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Outlet</th>
                  <th>Type</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Delivery</th>
                  <th>Comment</th>
                </tr>
              </thead>
              <tbody>
                {data.notices.map((notice) => (
                  <tr key={notice.id}>
                    <td>
                      <strong>{notice.outlet?.name}</strong>
                      <small>{notice.outlet?.registration_id}</small>
                    </td>
                    <td><span className={noticeClass(notice.notice_type)}>{notice.notice_type}</span></td>
                    <td>{Number(notice.audit?.compliance_score ?? 0).toFixed(0)}/100</td>
                    <td>{notice.audit?.status || "—"}</td>
                    <td>{notice.delivery_status || "—"}</td>
                    <td>{notice.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
