import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const riskClass = (value) =>
  value === "RED" || value === "CRITICAL" ? "danger" : value === "ORANGE" || value === "HIGH" ? "warning" : "safe";

const TEMP_ALERT = 35;
const HUMIDITY_ALERT = 70;

function formatTime(value) {
  if (!value) return "Waiting for first reading";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Reading received" : date.toLocaleTimeString();
}

export default function DashboardNew() {
  const [data, setData] = useState(null);
  const [command, setCommand] = useState(null);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [sensorDevice, setSensorDevice] = useState(null);
  const [sensorError, setSensorError] = useState("");
  const [demoAlert, setDemoAlert] = useState(false);
  const alarmRef = useRef(null);

  async function load() {
    setRefreshing(true);
    setError("");
    try {
      const [dashboard, center] = await Promise.all([api.dashboard(), api.commandCenter()]);
      setData(dashboard);
      setCommand(center);
    } catch (err) {
      setError(err.message || "Unable to load dashboard.");
    } finally {
      setRefreshing(false);
    }
  }

  function stopAlarmSound() {
    const alarm = alarmRef.current;
    if (!alarm) return;
    window.clearInterval(alarm.timer);
    try {
      alarm.oscillator.stop();
      alarm.context.close();
    } catch {
      // The audio context may already be closed.
    }
    alarmRef.current = null;
  }

  function startAlarmSound() {
    if (alarmRef.current) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      const context = new AudioContextClass();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "square";
      oscillator.frequency.value = 880;
      gain.gain.value = 0.025;
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start();
      let high = true;
      const timer = window.setInterval(() => {
        high = !high;
        oscillator.frequency.setTargetAtTime(high ? 880 : 520, context.currentTime, 0.02);
        gain.gain.setTargetAtTime(high ? 0.08 : 0.015, context.currentTime, 0.02);
      }, 220);
      alarmRef.current = { context, oscillator, timer };
    } catch (err) {
      console.warn("Browser alarm audio is unavailable", err);
    }
  }

  function simulateAlert() {
    setDemoAlert(true);
    startAlarmSound();
  }

  function acknowledgeAlert() {
    setDemoAlert(false);
    stopAlarmSound();
  }

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 15000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let active = true;
    async function loadTelemetry() {
      try {
        const result = await api.devices();
        if (!active) return;
        const devices = result.devices || [];
        const target = devices.find((device) => device.device_id === "SB-MGM-ESP32-001") || devices[0] || null;
        setSensorDevice(target);
        setSensorError("");
      } catch (err) {
        if (active) setSensorError(err.message || "Live sensor data is temporarily unavailable.");
      }
    }
    loadTelemetry();
    const timer = window.setInterval(loadTelemetry, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => () => stopAlarmSound(), []);

  if (error) {
    return <div className="page"><div className="error-box">{error}<button className="secondary-button" onClick={load}>Retry</button></div></div>;
  }
  if (!data) return <div className="loading">Loading overview…</div>;

  const c = data.counts || {};
  const s = command?.summary || {};
  const alerts = data.latest_alerts || [];
  const distribution = command?.risk_distribution || {};
  const priority = command?.priority || "LOW";
  const latest = sensorDevice?.latest_reading;
  const temperature = latest?.temperature == null ? null : Number(latest.temperature);
  const humidity = latest?.humidity == null ? null : Number(latest.humidity);
  const sensorThresholdAlert =
    (temperature !== null && Number.isFinite(temperature) && temperature > TEMP_ALERT) ||
    (humidity !== null && Number.isFinite(humidity) && humidity > HUMIDITY_ALERT);
  const alarmActive = demoAlert || sensorThresholdAlert;
  const alertReasons = [
    temperature !== null && temperature > TEMP_ALERT ? `Temperature above ${TEMP_ALERT}°C` : "",
    humidity !== null && humidity > HUMIDITY_ALERT ? `Humidity above ${HUMIDITY_ALERT}%` : "",
  ].filter(Boolean);

  return (
    <div className={`page dashboard-clean ${alarmActive ? "dashboard-alarm-active" : ""}`}>
      <div className="page-head clean-head">
        <div>
          <div className="eyebrow">LIVE OVERVIEW</div>
          <h2>Safety control center</h2>
          <p className="muted">Monitor risk, act on alerts, and verify compliance.</p>
        </div>
        <div className="head-actions">
          <span className={alarmActive ? "live-dot alarm-live-dot" : "live-dot"}>{alarmActive ? "● ALERT ACTIVE" : "● Live"}</span>
          <button className="secondary-button" onClick={load} disabled={refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button>
        </div>
      </div>

      <section className={`section-card iot-telemetry ${alarmActive ? "iot-telemetry-alert" : ""}`}>
        <div className="section-title telemetry-heading">
          <div>
            <div className="eyebrow">ESP32 · DHT22</div>
            <h3>Live cold-chain telemetry</h3>
            <span>
              {sensorDevice ? `${sensorDevice.device_id} · ${sensorDevice.status || "Status unknown"}` : "Waiting for connected device"}
              {" · "}Refreshes every 5 seconds
            </span>
          </div>
          <div className={alarmActive ? "telemetry-status telemetry-status-alert" : "telemetry-status"}>
            <span className="telemetry-status-dot" />
            {alarmActive ? "SAFETY ALERT" : "SYSTEM NORMAL"}
          </div>
        </div>

        {sensorError && <p className="muted telemetry-error">{sensorError}</p>}

        <div className="telemetry-metrics">
          <div className={temperature !== null && temperature > TEMP_ALERT ? "telemetry-metric metric-alert" : "telemetry-metric"}>
            <span>Temperature</span>
            <strong>{temperature !== null && Number.isFinite(temperature) ? temperature.toFixed(1) : "—"}<small>°C</small></strong>
            <div className="telemetry-meter"><span style={{ width: `${Math.min(100, Math.max(0, (temperature || 0) / 50 * 100))}%` }} /></div>
            <small>Alert threshold: &gt; {TEMP_ALERT}°C</small>
          </div>
          <div className={humidity !== null && humidity > HUMIDITY_ALERT ? "telemetry-metric metric-alert" : "telemetry-metric"}>
            <span>Relative humidity</span>
            <strong>{humidity !== null && Number.isFinite(humidity) ? humidity.toFixed(1) : "—"}<small>%</small></strong>
            <div className="telemetry-meter humidity-meter"><span style={{ width: `${Math.min(100, Math.max(0, humidity || 0))}%` }} /></div>
            <small>Alert threshold: &gt; {HUMIDITY_ALERT}%</small>
          </div>
          <div className="telemetry-metric telemetry-device">
            <span>Device status</span>
            <strong className={String(sensorDevice?.status || "").toUpperCase() === "ONLINE" ? "safe" : "warning"}>
              {sensorDevice?.status || "WAITING"}
            </strong>
            <small>Last reading: {formatTime(latest?.timestamp)}</small>
            <small>Data source: registered ESP32</small>
          </div>
        </div>

        {alarmActive && (
          <div className="critical-alert-banner" role="alert">
            <div className="critical-alert-icon">!</div>
            <div>
              <strong>{demoAlert ? "SIMULATED EMERGENCY — DEMO MODE" : "FOOD SAFETY THRESHOLD BREACHED"}</strong>
              <p>{demoAlert ? "Operator-triggered alarm simulation is active." : alertReasons.join(" · ")}</p>
            </div>
            <span className="critical-alert-pulse">ACTION REQUIRED</span>
          </div>
        )}

        <div className="telemetry-actions">
          <div className="muted telemetry-note">Demo control triggers a flashing dashboard alert and audible browser alarm. The physical ESP32 buzzer/LED continue to follow the firmware thresholds.</div>
          {demoAlert ? (
            <button className="alarm-stop-button" onClick={acknowledgeAlert}>Acknowledge / Stop demo alarm</button>
          ) : (
            <button className="alarm-trigger-button" onClick={simulateAlert}>⚠ Simulate emergency alert</button>
          )}
        </div>
      </section>

      <div className="stat-grid dashboard-stats">
        <div className="stat-card"><span>Establishments</span><strong>{c.establishments ?? 0}</strong><small>In authorised region</small></div>
        <div className="stat-card"><span>Devices online</span><strong>{c.online_devices ?? 0}<em>/{c.devices ?? 0}</em></strong><small>IoT health</small></div>
        <div className={`stat-card ${c.critical_alerts || alarmActive ? "critical" : ""}`}><span>Critical alerts</span><strong>{(c.critical_alerts ?? 0) + (demoAlert ? 1 : 0)}</strong><small>{demoAlert ? "Includes demo simulation" : "Immediate attention"}</small></div>
        <div className="stat-card"><span>Investigations</span><strong>{c.pending_investigations ?? 0}</strong><small>Pending closure</small></div>
      </div>

      <div className="dashboard-main-grid">
        <section className="section-card priority-card">
          <div className="section-title"><div><h3>Current priority</h3><span>Regional operational pressure</span></div><Link to="/command-center" className="text-link">Open →</Link></div>
          <div className={`priority-value ${riskClass(priority)}`}>{priority}</div>
          <div className="priority-details">
            <div><strong>{s.active_red_alerts ?? 0}</strong><span>RED alerts</span></div>
            <div><strong>{s.active_orange_alerts ?? 0}</strong><span>ORANGE alerts</span></div>
            <div><strong>{s.unresolved_investigations ?? 0}</strong><span>Investigations</span></div>
          </div>
        </section>

        <section className="section-card">
          <div className="section-title"><div><h3>Risk distribution</h3><span>Current outlet classification</span></div><Link to="/command-center" className="text-link">Details →</Link></div>
          <div className="risk-grid">
            {[[ "Critical", distribution.critical ?? 0, "danger" ],[ "High", distribution.high ?? 0, "warning" ],[ "Medium", distribution.medium ?? 0, "amber" ],[ "Low", distribution.low ?? 0, "safe" ]].map(([label, value, cls]) => (
              <div className="risk-item" key={label}><span>{label}</span><strong className={cls}>{value}</strong></div>
            ))}
          </div>
        </section>
      </div>

      <section className="section-card">
        <div className="section-title"><div><h3>Recent alerts</h3><span>Latest events requiring attention</span></div><Link to="/alerts" className="text-link">View all →</Link></div>
        {alerts.length === 0 ? <p className="muted">No alerts recorded.</p> : (
          <div className="alert-list">
            {alerts.slice(0, 5).map((alert) => (
              <Link className="alert-row" to={`/alerts/${alert.id}`} key={alert.id}>
                <div><strong>{alert.restaurant?.name || "Unknown establishment"}</strong><small>{alert.reason || "Risk condition detected"}</small></div>
                <div className="alert-meta"><span className={`badge ${alert.severity === "RED" ? "danger" : "warning"}`}>{alert.severity}</span><small>{alert.status}</small></div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <div className="dashboard-signal-grid">
        <section className="section-card compact"><div className="section-title"><div><h3>Safety signals</h3><span>Last 30 days</span></div><Link to="/command-center" className="text-link">Details →</Link></div><div className="signal-list"><div><span>Citizen reports</span><strong>{s.citizen_reports_30d ?? 0}</strong></div><div><span>Verified reports</span><strong>{s.verified_citizen_reports_30d ?? 0}</strong></div><div><span>AI hygiene findings</span><strong>{s.ai_hygiene_findings_30d ?? 0}</strong></div></div></section>
        <section className="section-card compact"><div className="section-title"><div><h3>System integrity</h3><span>Recent activity</span></div><Link to="/audit-history" className="text-link">Audit history →</Link></div><div className="signal-list"><div><span>Alerts · 24h</span><strong>{s.alerts_last_24h ?? 0}</strong></div><div><span>Blockchain audits · 30d</span><strong>{s.blockchain_anchored_audits_30d ?? 0}</strong></div><div><span>Critical AI findings</span><strong>{s.critical_ai_findings_30d ?? 0}</strong></div></div></section>
      </div>
    </div>
  );
}
