import { useCallback, useEffect, useState } from "react";
import { api } from "../api";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString();
}

function statusClass(status) {
  return String(status || "").toUpperCase() === "ONLINE"
    ? "text-safe"
    : "text-danger";
}

function Metric({ label, value, unit }) {
  return (
    <div
      style={{
        padding: "14px",
        border: "1px solid #e2e8e2",
        borderRadius: "10px",
        background: "#f7f9f7",
      }}
    >
      <small className="muted">{label}</small>
      <div style={{ marginTop: "5px", fontSize: "22px", fontWeight: 700 }}>
        {value ?? "—"}
        {value !== null && value !== undefined && value !== "—" && unit ? ` ${unit}` : ""}
      </div>
    </div>
  );
}

export default function Sensors() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadSensors = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError("");

    try {
      const result = await api.devices();
      setData(result);
    } catch (err) {
      setError(err.message || "Unable to load sensor data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadSensors();

    const interval = setInterval(() => {
      loadSensors(true);
    }, 10000);

    return () => clearInterval(interval);
  }, [loadSensors]);

  const devices = data?.devices || [];
  const online = devices.filter(
    (device) => String(device.status).toUpperCase() === "ONLINE"
  ).length;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">LIVE IOT MONITORING</div>
          <h2>Sensors</h2>
          <p className="muted">
            Connected SafeBite devices and their latest sensor readings.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={() => loadSensors(true)}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="section-card" style={{ color: "#b42318", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="section-card">
          <p className="muted">Loading connected sensors...</p>
        </div>
      ) : (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
              gap: "16px",
              marginBottom: "18px",
            }}
          >
            <section className="section-card">
              <small className="muted">CONNECTED DEVICES</small>
              <h3 style={{ margin: "6px 0 0" }}>{devices.length}</h3>
            </section>
            <section className="section-card">
              <small className="muted">ONLINE</small>
              <h3 className="text-safe" style={{ margin: "6px 0 0" }}>{online}</h3>
            </section>
            <section className="section-card">
              <small className="muted">AUTO REFRESH</small>
              <h3 style={{ margin: "6px 0 0" }}>10 sec</h3>
            </section>
          </div>

          {devices.length === 0 ? (
            <section className="section-card">
              <h3>No sensors connected</h3>
              <p className="muted">
                SafeBite has not received any registered IoT device yet.
              </p>
            </section>
          ) : (
            <div style={{ display: "grid", gap: "18px" }}>
              {devices.map((device) => {
                const latest = device.latest_reading;
                const readings = device.recent_readings || [];

                return (
                  <section className="section-card" key={device.id}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "16px",
                        alignItems: "flex-start",
                        marginBottom: "16px",
                      }}
                    >
                      <div>
                        <div className="eyebrow">IOT DEVICE</div>
                        <h3 style={{ margin: "4px 0 5px" }}>{device.device_id}</h3>
                        <p className="muted" style={{ margin: 0 }}>
                          {device.restaurant} • {device.device_type || "Sensor gateway"}
                        </p>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <strong className={statusClass(device.status)}>
                          {device.status}
                        </strong>
                        <small className="muted" style={{ display: "block", marginTop: "4px" }}>
                          Last seen: {formatDate(device.last_seen_at)}
                        </small>
                      </div>
                    </div>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                        gap: "12px",
                        marginBottom: "18px",
                      }}
                    >
                      <Metric
                        label="Temperature"
                        value={latest?.temperature}
                        unit="°C"
                      />
                      <Metric
                        label="Humidity"
                        value={latest?.humidity}
                        unit="%"
                      />
                      <Metric
                        label="Door status"
                        value={latest ? (latest.door_open ? "OPEN" : "CLOSED") : "—"}
                      />
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                      <strong>Recent readings</strong>
                      <small className="muted">
                        Latest: {formatDate(latest?.timestamp)}
                      </small>
                    </div>

                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Time</th>
                            <th>Temperature</th>
                            <th>Humidity</th>
                            <th>Door</th>
                          </tr>
                        </thead>
                        <tbody>
                          {readings.length === 0 ? (
                            <tr>
                              <td colSpan="4" className="muted">
                                No sensor readings received yet.
                              </td>
                            </tr>
                          ) : (
                            readings.map((reading, index) => (
                              <tr key={`${device.id}-${reading.timestamp}-${index}`}>
                                <td>{formatDate(reading.timestamp)}</td>
                                <td>{reading.temperature ?? "—"} °C</td>
                                <td>{reading.humidity ?? "—"} %</td>
                                <td>{reading.door_open ? "OPEN" : "CLOSED"}</td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
