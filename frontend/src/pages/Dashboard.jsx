import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";


/* ============================================================
   HELPERS
   ============================================================ */

const severityClass = (severity) =>
  severity === "RED"
    ? "danger"
    : severity === "ORANGE"
      ? "warning"
      : "amber";


function priorityStyle(priority) {
  switch (priority) {
    case "CRITICAL":
      return {
        background: "#fdeceb",
        color: "#963d37",
      };

    case "HIGH":
      return {
        background: "#fff1e4",
        color: "#925f1b",
      };

    case "MEDIUM":
      return {
        background: "#fff8e8",
        color: "#89611f",
      };

    default:
      return {
        background: "#e8f5eb",
        color: "#266437",
      };
  }
}


/* ============================================================
   DASHBOARD
   ============================================================ */

export default function Dashboard() {

  const [data, setData] =
    useState(null);

  const [command, setCommand] =
    useState(null);

  const [error, setError] =
    useState("");

  const [refreshing, setRefreshing] =
    useState(false);


  /* ==========================================================
     LOAD DASHBOARD + COMMAND CENTER
     ========================================================== */

  async function loadDashboard() {

    setRefreshing(true);
    setError("");

    try {

      const [dashboardResult, commandResult] =
        await Promise.all([
          api.dashboard(),
          api.commandCenter(),
        ]);

      setData(
        dashboardResult
      );

      setCommand(
        commandResult
      );

    } catch (err) {

      setError(
        err.message ||
          "Unable to load the government dashboard."
      );

    } finally {

      setRefreshing(false);

    }
  }


  useEffect(() => {

    loadDashboard();

  }, []);


  /* ==========================================================
     ERROR
     ========================================================== */

  if (error) {

    return (
      <div className="error-box">

        <div>
          {error}
        </div>

        <button
          className="secondary-button"
          onClick={loadDashboard}
          style={{
            marginTop: "12px",
          }}
        >
          Retry
        </button>

      </div>
    );

  }


  /* ==========================================================
     LOADING
     ========================================================== */

  if (!data) {

    return (
      <div className="loading">
        Loading regional overview…
      </div>
    );

  }


  /* ==========================================================
     DATA
     ========================================================== */

  const c =
    data.counts || {};

  const summary =
    command?.summary || {};

  const topRiskOutlets =
    command?.top_risk_outlets || [];

  const priority =
    command?.priority || "LOW";

  const priorityColors =
    priorityStyle(priority);


  /* ==========================================================
     SAFE VALUES
     ========================================================== */

  const establishments =
    c.establishments ?? 0;

  const onlineDevices =
    c.online_devices ?? 0;

  const devices =
    c.devices ?? 0;

  const criticalAlerts =
    c.critical_alerts ??
    summary.active_red_alerts ??
    0;

  const pendingInvestigations =
    c.pending_investigations ??
    summary.unresolved_investigations ??
    0;

  const citizenReports =
    summary.citizen_reports_30d ?? 0;

  const verifiedCitizenReports =
    summary.verified_citizen_reports_30d ?? 0;

  const aiFindings =
    summary.ai_hygiene_findings_30d ?? 0;

  const criticalAiFindings =
    summary.critical_ai_findings_30d ?? 0;

  const activeOrange =
    summary.active_orange_alerts ?? 0;

  const alertsLast24h =
    summary.alerts_last_24h ?? 0;

  const blockchainAudits =
    summary.blockchain_anchored_audits_30d ?? 0;


  return (
    <div className="page">

      {/* ======================================================
          PAGE HEADER
          ====================================================== */}

      <div className="page-head">

        <div>

          <div className="eyebrow">
            LIVE OVERVIEW
          </div>

          <h2>
            Safety control center
          </h2>

          <p
            style={{
              marginTop: "5px",
              color: "#68716b",
              fontSize: "13px",
            }}
          >
            Unified view of regional food-safety
            alerts, investigations, AI findings,
            citizen reports, and audit integrity.
          </p>

        </div>


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >

          <span className="live-dot">
            ● Live monitoring
          </span>

          <button
            className="secondary-button"
            onClick={loadDashboard}
            disabled={refreshing}
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </div>

      </div>


      {/* ======================================================
          CORE OPERATIONAL METRICS
          ====================================================== */}

      <div className="stat-grid">

        <div className="stat-card">

          <span>
            Monitored establishments
          </span>

          <strong>
            {establishments}
          </strong>

          <small>
            Registered in scope
          </small>

        </div>


        <div className="stat-card">

          <span>
            Online devices
          </span>

          <strong>

            {onlineDevices}

            <em>
              /{devices}
            </em>

          </strong>

          <small>
            Device health
          </small>

        </div>


        <div className="stat-card critical">

          <span>
            Critical alerts
          </span>

          <strong>
            {criticalAlerts}
          </strong>

          <small>
            Immediate attention
          </small>

        </div>


        <div className="stat-card">

          <span>
            Pending investigations
          </span>

          <strong>
            {pendingInvestigations}
          </strong>

          <small>
            Cases not closed
          </small>

        </div>

      </div>


      {/* ======================================================
          UNIFIED SIGNALS
          ====================================================== */}

      <section
        className="section-card"
        style={{
          marginTop: "20px",
        }}
      >

        <div className="section-title">

          <div>

            <h3>
              Unified safety signals
            </h3>

            <span>
              Signals collected across the SafeBite
              evidence ecosystem
            </span>

          </div>


          <Link
            to="/command-center"
            className="text-link"
          >
            Command Center →
          </Link>

        </div>


        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(4, minmax(0, 1fr))",
            gap: "12px",
            marginTop: "16px",
          }}
        >

          {/* CITIZEN */}

          <div
            style={{
              padding: "16px",
              borderRadius: "12px",
              background: "#f5f7f5",
              border:
                "1px solid #e1e7e2",
            }}
          >

            <span
              style={{
                display: "block",
                fontSize: "11px",
                color: "#727b74",
              }}
            >
              Citizen reports · 30 days
            </span>

            <strong
              style={{
                display: "block",
                marginTop: "7px",
                fontSize: "27px",
              }}
            >
              {citizenReports}
            </strong>

            <small
              style={{
                color: "#266437",
              }}
            >
              Verified: {verifiedCitizenReports}
            </small>

          </div>


          {/* AI */}

          <div
            style={{
              padding: "16px",
              borderRadius: "12px",
              background: "#f5f7f5",
              border:
                "1px solid #e1e7e2",
            }}
          >

            <span
              style={{
                display: "block",
                fontSize: "11px",
                color: "#727b74",
              }}
            >
              Hygiene AI findings
            </span>

            <strong
              style={{
                display: "block",
                marginTop: "7px",
                fontSize: "27px",
              }}
            >
              {aiFindings}
            </strong>

            <small
              style={{
                color:
                  criticalAiFindings > 0
                    ? "#963d37"
                    : "#266437",
              }}
            >
              Critical: {criticalAiFindings}
            </small>

          </div>


          {/* RECENT ALERT PRESSURE */}

          <div
            style={{
              padding: "16px",
              borderRadius: "12px",
              background: "#f5f7f5",
              border:
                "1px solid #e1e7e2",
            }}
          >

            <span
              style={{
                display: "block",
                fontSize: "11px",
                color: "#727b74",
              }}
            >
              Alerts · last 24 hours
            </span>

            <strong
              style={{
                display: "block",
                marginTop: "7px",
                fontSize: "27px",
              }}
            >
              {alertsLast24h}
            </strong>

            <small>
              ORANGE active: {activeOrange}
            </small>

          </div>


          {/* BLOCKCHAIN */}

          <div
            style={{
              padding: "16px",
              borderRadius: "12px",
              background: "#f5f7f5",
              border:
                "1px solid #e1e7e2",
            }}
          >

            <span
              style={{
                display: "block",
                fontSize: "11px",
                color: "#727b74",
              }}
            >
              Blockchain audits · 30 days
            </span>

            <strong
              style={{
                display: "block",
                marginTop: "7px",
                fontSize: "27px",
              }}
            >
              {blockchainAudits}
            </strong>

            <small>
              Anchored records
            </small>

          </div>

        </div>

      </section>


      {/* ======================================================
          PRIORITY + RISK DISTRIBUTION
          ====================================================== */}

      <div
        className="two-col"
        style={{
          marginTop: "20px",
        }}
      >

        {/* COMMAND PRIORITY */}

        <section className="section-card compact">

          <div className="section-title">

            <div>

              <h3>
                Regional priority
              </h3>

              <span>
                Current operational pressure
              </span>

            </div>

            <Link
              to="/command-center"
              className="text-link"
            >
              Open →
            </Link>

          </div>


          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "14px",
              marginTop: "18px",
            }}
          >

            <div
              style={{
                width: "72px",
                height: "72px",
                display: "grid",
                placeItems: "center",
                borderRadius: "50%",
                background:
                  priorityColors.background,
                color:
                  priorityColors.color,
                fontSize: "11px",
                fontWeight: 800,
              }}
            >
              {priority}
            </div>


            <div>

              <strong
                style={{
                  display: "block",
                  fontSize: "24px",
                }}
              >
                {summary.unresolved_investigations ??
                  0}
              </strong>

              <small>
                unresolved investigations
              </small>

              <p
                style={{
                  margin:
                    "6px 0 0",
                  color:
                    "#68716b",
                  fontSize:
                    "12px",
                }}
              >
                RED alerts:{" "}
                {summary.active_red_alerts ?? 0}
                {" • "}
                Citizen reports:{" "}
                {citizenReports}
              </p>

            </div>

          </div>

        </section>


        {/* RISK DISTRIBUTION */}

        <section className="section-card compact">

          <div className="section-title">

            <div>

              <h3>
                Outlet risk distribution
              </h3>

              <span>
                Current regional classification
              </span>

            </div>

            <Link
              to="/command-center"
              className="text-link"
            >
              Details →
            </Link>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(4, 1fr)",
              gap: "8px",
              marginTop: "18px",
            }}
          >

            {[
              [
                "Critical",
                command?.risk_distribution?.critical ??
                  0,
                "#963d37",
              ],
              [
                "High",
                command?.risk_distribution?.high ??
                  0,
                "#925f1b",
              ],
              [
                "Medium",
                command?.risk_distribution?.medium ??
                  0,
                "#89611f",
              ],
              [
                "Low",
                command?.risk_distribution?.low ??
                  0,
                "#266437",
              ],
            ].map(
              ([label, value, color]) => (

                <div
                  key={label}
                  style={{
                    padding:
                      "12px 9px",
                    borderRadius:
                      "9px",
                    background:
                      "#f5f7f5",
                  }}
                >

                  <span
                    style={{
                      display: "block",
                      fontSize: "10px",
                      color: "#727b74",
                    }}
                  >
                    {label}
                  </span>

                  <strong
                    style={{
                      display: "block",
                      marginTop: "5px",
                      fontSize: "23px",
                      color,
                    }}
                  >
                    {value}
                  </strong>

                </div>

              )
            )}

          </div>

        </section>

      </div>


      {/* ======================================================
          RECENT ALERTS
          ====================================================== */}

      <section className="section-card">

        <div className="section-title">

          <div>

            <h3>
              Recent alerts
            </h3>

            <span>
              Latest safety events from your authorised region
            </span>

          </div>

          <Link
            to="/alerts"
            className="text-link"
          >
            View all →
          </Link>

        </div>


        <div className="table-wrap">

          <table>

            <thead>

              <tr>

                <th>
                  Severity
                </th>

                <th>
                  Establishment
                </th>

                <th>
                  Issue
                </th>

                <th>
                  Risk
                </th>

                <th>
                  Status
                </th>

                <th>
                </th>

              </tr>

            </thead>


            <tbody>

              {(data.latest_alerts || [])
                .map(
                  (alert) => (

                    <tr
                      key={alert.id}
                    >

                      <td>

                        <span
                          className={`badge ${severityClass(
                            alert.severity
                          )}`}
                        >
                          {alert.severity}
                        </span>

                      </td>


                      <td>

                        <strong>
                          {
                            alert.restaurant
                              ?.name ||
                            "Unknown"
                          }
                        </strong>

                        <small>
                          {
                            alert.restaurant
                              ?.region ||
                            ""
                          }
                        </small>

                      </td>


                      <td>
                        {alert.reason}
                      </td>


                      <td>

                        <strong>
                          {alert.risk_score}
                        </strong>

                        /100

                      </td>


                      <td>
                        {String(
                          alert.status ||
                            ""
                        ).replaceAll(
                          "_",
                          " "
                        )}
                      </td>


                      <td>

                        <Link
                          className="text-link"
                          to={`/alerts/${alert.id}`}
                        >
                          Open
                        </Link>

                      </td>

                    </tr>

                  )
                )}


              {(!data.latest_alerts ||
                data.latest_alerts.length === 0) && (

                <tr>

                  <td
                    colSpan="6"
                    style={{
                      textAlign:
                        "center",
                      padding:
                        "35px",
                      color:
                        "#727b74",
                    }}
                  >
                    No recent alerts.
                  </td>

                </tr>

              )}

            </tbody>

          </table>

        </div>

      </section>


      {/* ======================================================
          HIGHEST RISK OUTLETS
          ====================================================== */}

      <section className="section-card">

        <div className="section-title">

          <div>

            <h3>
              Highest-risk outlets
            </h3>

            <span>
              Outlets requiring the most attention
            </span>

          </div>

          <Link
            to="/audit-history"
            className="text-link"
          >
            Audit History →
          </Link>

        </div>


        {topRiskOutlets.length === 0 ? (

          <div
            style={{
              padding:
                "30px",
              textAlign:
                "center",
              color:
                "#727b74",
            }}
          >
            No outlet risk data available.
          </div>

        ) : (

          <div
            style={{
              display:
                "grid",
              gap:
                "8px",
              marginTop:
                "15px",
            }}
          >

            {topRiskOutlets.map(
              (outlet, index) => {

                const level =
                  outlet.risk_score >= 80
                    ? "CRITICAL"
                    : outlet.risk_score >= 45
                      ? "HIGH"
                      : outlet.risk_score >= 20
                        ? "MEDIUM"
                        : "LOW";

                const colors =
                  priorityStyle(
                    level
                  );

                return (

                  <div
                    key={
                      outlet.id
                    }
                    style={{
                      display:
                        "grid",
                      gridTemplateColumns:
                        "42px 1fr auto",
                      gap:
                        "12px",
                      alignItems:
                        "center",
                      padding:
                        "13px",
                      borderRadius:
                        "10px",
                      background:
                        "#f7f9f7",
                    }}
                  >

                    <strong
                      style={{
                        color:
                          "#7a837c",
                      }}
                    >
                      #{index + 1}
                    </strong>


                    <div>

                      <strong>
                        {
                          outlet.name
                        }
                      </strong>

                      <small
                        style={{
                          display:
                            "block",
                          marginTop:
                            "3px",
                          color:
                            "#727b74",
                        }}
                      >
                        {
                          outlet.registration_id
                        }
                        {" • "}
                        RED:{" "}
                        {
                          outlet.red_alerts
                        }
                        {" • "}
                        Investigations:{" "}
                        {
                          outlet.unresolved_investigations
                        }
                        {" • "}
                        Verified citizens:{" "}
                        {
                          outlet.verified_citizen_reports
                        }
                      </small>

                    </div>


                    <div
                      style={{
                        textAlign:
                          "right",
                      }}
                    >

                      <strong
                        style={{
                          display:
                            "block",
                          fontSize:
                            "19px",
                        }}
                      >
                        {
                          outlet.risk_score
                        }
                      </strong>

                      <span
                        style={{
                          display:
                            "inline-flex",
                          marginTop:
                            "4px",
                          padding:
                            "4px 8px",
                          borderRadius:
                            "999px",
                          background:
                            colors.background,
                          color:
                            colors.color,
                          fontSize:
                            "9px",
                          fontWeight:
                            800,
                        }}
                      >
                        {level}
                      </span>

                    </div>

                  </div>

                );
              }
            )}

          </div>

        )}

      </section>


      {/* ======================================================
          EXISTING PROJECT PRINCIPLES
          ====================================================== */}

      <div className="two-col">

        <section className="section-card compact">

          <h3>
            Operational principle
          </h3>

          <p className="muted">
            SafeBite converts raw sensor observations,
            AI findings and citizen evidence into
            explainable risk signals. Government officers
            see actionable incidents rather than a stream
            of raw telemetry.
          </p>

        </section>


        <section className="section-card compact">

          <h3>
            Investigation lifecycle
          </h3>

          <div className="timeline-mini">

            <span>
              Alert
            </span>

            <i>
              →
            </i>

            <span>
              Investigation
            </span>

            <i>
              →
            </i>

            <span>
              Action
            </span>

            <i>
              →
            </i>

            <span>
              Verification
            </span>

            <i>
              →
            </i>

            <span>
              Audit
            </span>

          </div>

        </section>

      </div>


      {/* ======================================================
          QUICK LINKS
          ====================================================== */}

      <section
        className="section-card"
        style={{
          marginTop:
            "20px",
        }}
      >

        <div className="section-title">

          <div>

            <h3>
              Investigation tools
            </h3>

            <span>
              Move from regional monitoring to evidence review.
            </span>

          </div>

        </div>


        <div
          style={{
            display:
              "flex",
            gap:
              "10px",
            flexWrap:
              "wrap",
            marginTop:
              "14px",
          }}
        >

          <Link
            to="/command-center"
            className="primary-button"
          >
            Command Center
          </Link>

          <Link
            to="/reports"
            className="secondary-button"
          >
            Citizen Reports
          </Link>

          <Link
            to="/audit-history"
            className="secondary-button"
          >
            Audit History
          </Link>

          <Link
            to="/investigations"
            className="secondary-button"
          >
            Investigations
          </Link>

        </div>

      </section>

    </div>
  );
}