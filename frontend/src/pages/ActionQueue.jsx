import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

function priorityClass(priority) {
  switch (String(priority || "").toUpperCase()) {
    case "CRITICAL":
      return "badge danger";
    case "HIGH":
      return "badge warning";
    default:
      return "badge amber";
  }
}

function actionLabel(action) {
  return String(action || "MONITOR").replaceAll("_", " ");
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("en-IN");
}

export default function ActionQueue() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      setError("");
      const result = await api.actionQueue();
      setData(result);
    } catch (err) {
      setError(err.message || "Unable to load officer action queue.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    load();
    const interval = window.setInterval(load, 10000);
    return () => window.clearInterval(interval);
  }, []);

  async function refreshNow() {
    setRefreshing(true);
    await load();
  }

  if (loading && !data) {
    return <div className="loading">Loading officer action queue...</div>;
  }

  if (error && !data) {
    return (
      <div className="page">
        <div className="error-box">
          {error}
          <button
            className="secondary-button"
            onClick={refreshNow}
            style={{ marginTop: "12px" }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const items = data?.items || [];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">OFFICER ACTION QUEUE</div>
          <h2>What needs attention now</h2>
          <p className="muted">
            AI and monitoring systems prepare the queue; the officer performs
            physical verification and makes the official decision.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={refreshNow}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="stat-grid">
        <div className="stat-card">
          <span>Critical</span>
          <strong>{data?.critical ?? 0}</strong>
          <small>Immediate officer attention</small>
        </div>
        <div className="stat-card">
          <span>High</span>
          <strong>{data?.high ?? 0}</strong>
          <small>Follow-up required</small>
        </div>
        <div className="stat-card">
          <span>Physical actions</span>
          <strong>{data?.requires_physical_action ?? 0}</strong>
          <small>Inspection or investigation work</small>
        </div>
      </div>

      <section className="section-card">
        <div className="panel-header">
          <div>
            <h3>Priority cases</h3>
            <span className="muted">
              Highest priority first; newest first within priority.
            </span>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="empty-state">
            No active cases require officer action.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Outlet</th>
                  <th>Source</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th>Time</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={`${item.kind}-${item.id}`}>
                    <td>
                      <span className={priorityClass(item.priority)}>
                        {item.priority}
                      </span>
                    </td>
                    <td>
                      <strong>{item.outlet?.name}</strong>
                      <small>{item.outlet?.registration_id}</small>
                    </td>
                    <td>{item.source}</td>
                    <td>{actionLabel(item.action)}</td>
                    <td>{String(item.status || "").replaceAll("_", " ")}</td>
                    <td>{item.reason}</td>
                    <td>{formatDate(item.timestamp)}</td>
                    <td>
                      {item.kind === "ALERT" ? (
                        <Link className="text-link" to={`/alerts/${item.id}`}>
                          Open
                        </Link>
                      ) : (
                        <Link className="text-link" to="/reports">
                          Review
                        </Link>
                      )}
                    </td>
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
