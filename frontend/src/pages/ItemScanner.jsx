import { useEffect, useState } from "react";
import { api } from "../api";

function statusClass(status) {
  switch (String(status || "").toUpperCase()) {
    case "UNSAFE":
      return "badge danger";
    case "CHECK":
      return "badge warning";
    default:
      return "badge neutral";
  }
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("en-IN");
}

export default function ItemScanner() {
  const [outlets, setOutlets] = useState([]);
  const [restaurantId, setRestaurantId] = useState("");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.establishments()
      .then((data) => {
        const rows = data.establishments || [];
        setOutlets(rows);
        if (rows.length && !restaurantId) setRestaurantId(String(rows[0].id));
      })
      .catch((err) => setError(err.message || "Unable to load outlets."))
      .finally(() => setLoading(false));
  }, []);

  async function scan() {
    if (!file) {
      setError("Select a product image first.");
      return;
    }

    setScanning(true);
    setError("");
    setResult(null);

    try {
      const data = await api.itemSafetyScan(
        file,
        restaurantId ? Number(restaurantId) : null,
      );
      setResult(data);
    } catch (err) {
      setError(err.message || "Item scan failed.");
    } finally {
      setScanning(false);
    }
  }

  if (loading) return <div className="loading">Loading item scanner...</div>;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">ITEM SAFETY CHECK</div>
          <h2>Scan one food item</h2>
          <p className="muted">
            Check the printed expiry date and available visual/storage evidence before an officer makes a final decision.
          </p>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      <section className="section-card">
        <div className="form-grid">
          <label className="field">
            <span>Outlet</span>
            <select value={restaurantId} onChange={(event) => setRestaurantId(event.target.value)}>
              <option value="">No outlet selected</option>
              {outlets.map((outlet) => (
                <option key={outlet.id} value={outlet.id}>
                  {outlet.name} — {outlet.registration_id}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Product image</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/bmp"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
        </div>

        <button className="primary-button" onClick={scan} disabled={scanning}>
          {scanning ? "Scanning..." : "Scan item"}
        </button>
      </section>

      {result && (
        <section className="section-card">
          <div className="panel-header">
            <div>
              <div className="eyebrow">RESULT</div>
              <h3>Item assessment</h3>
            </div>
            <span className={statusClass(result.assessment?.status)}>
              {result.assessment?.status || "CHECK"}
            </span>
          </div>

          <div className="stat-grid">
            <div className="stat-card">
              <span>Expiry</span>
              <strong>{result.expiry?.status || "NOT_FOUND"}</strong>
              <small>{result.expiry?.expiry_date || "Date not verified"}</small>
            </div>
            <div className="stat-card">
              <span>Vision</span>
              <strong>{result.vision?.risk_score ?? "—"}</strong>
              <small>{result.vision?.status || "Not available"}</small>
            </div>
            <div className="stat-card">
              <span>Storage</span>
              <strong>{result.storage?.temperature != null ? `${result.storage.temperature}°C` : "—"}</strong>
              <small>{result.storage?.available ? `Humidity ${result.storage.humidity}%` : "No sensor reading"}</small>
            </div>
          </div>

          <div className="notice-card">
            <strong>Why this result?</strong>
            {(result.assessment?.reasons || []).length ? (
              <ul>
                {result.assessment.reasons.map((reason, index) => <li key={index}>{reason}</li>)}
              </ul>
            ) : (
              <p className="muted">No risk reason recorded.</p>
            )}
            <small className="muted">
              Latest storage reading: {formatDate(result.storage?.timestamp)}
            </small>
          </div>
        </section>
      )}
    </div>
  );
}
