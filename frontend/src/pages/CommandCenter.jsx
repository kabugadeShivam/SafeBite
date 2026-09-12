import { useEffect, useState } from "react";
import { api } from "../api";


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


function riskLevel(score) {
  if (score >= 80) {
    return "CRITICAL";
  }

  if (score >= 45) {
    return "HIGH";
  }

  if (score >= 20) {
    return "MEDIUM";
  }

  return "LOW";
}


export default function CommandCenter() {

  const [data, setData] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");


  /* ==========================================================
     LOAD COMMAND CENTER
     ========================================================== */

  async function load() {

    setError("");

    try {

      const result =
        await api.commandCenter();

      setData(result);

    } catch (err) {

      setError(
        err.message ||
          "Unable to load Command Center."
      );

    } finally {

      setLoading(false);
      setRefreshing(false);

    }
  }


  /* ==========================================================
     INITIAL LOAD + REAL-TIME POLLING
     ========================================================== */

  useEffect(() => {

    load();

    const interval =
      window.setInterval(
        () => {
          load();
        },
        10000
      );

    return () => {
      window.clearInterval(
        interval
      );
    };

  }, []);


  /* ==========================================================
     MANUAL REFRESH
     ========================================================== */

  async function refreshNow() {

    setRefreshing(true);

    await load();

  }


  /* ==========================================================
     LOADING
     ========================================================== */

  if (
    loading &&
    !data
  ) {

    return (
      <div
        style={{
          padding: "40px",
          textAlign: "center",
          color: "#68716b",
        }}
      >
        Loading Command Center...
      </div>
    );

  }


  /* ==========================================================
     ERROR
     ========================================================== */

  if (
    error &&
    !data
  ) {

    return (
      <div
        style={{
          padding: "18px",
          borderRadius: "12px",
          background: "#fdeceb",
          color: "#963d37",
        }}
      >

        {error}

        <button
          className="secondary-button"
          onClick={
            refreshNow
          }
          style={{
            marginLeft: "12px",
          }}
        >
          Retry
        </button>

      </div>
    );

  }


  const summary =
    data?.summary || {};

  const priority =
    data?.priority || "LOW";

  const priorityColors =
    priorityStyle(
      priority
    );

  const topOutlets =
    data?.top_risk_outlets || [];

  const distribution =
    data?.risk_distribution || {};

  const sources =
    data?.data_sources || {};


  return (
    <div
      style={{
        display: "grid",
        gap: "20px",
      }}
    >

      {/* ======================================================
          HEADER
          ====================================================== */}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: "15px",
          flexWrap: "wrap",
        }}
      >

        <div>

          <div className="eyebrow">
            NATIONAL FOOD SAFETY OPERATIONS
          </div>

          <h2
            style={{
              margin: "4px 0",
            }}
          >
            Command Center
          </h2>

          <p
            style={{
              margin: 0,
              color: "#68716b",
            }}
          >
            {data?.region?.region || "Regional"}
            {", "}
            {data?.region?.state || "India"}
            {" • "}
            Live operational overview
          </p>

        </div>


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >

          <span
            style={{
              padding:
                "7px 11px",
              borderRadius:
                "999px",
              background:
                "#e8f5eb",
              color:
                "#266437",
              fontSize:
                "10px",
              fontWeight:
                800,
            }}
          >
            ● AUTO-REFRESH 10s
          </span>


          <button
            className="secondary-button"
            onClick={
              refreshNow
            }
            disabled={
              refreshing
            }
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </div>

      </div>


      {/* ======================================================
          BACKGROUND ERROR
          ====================================================== */}

      {error && (

        <div
          style={{
            padding:
              "11px 13px",
            borderRadius:
              "10px",
            background:
              "#fdeceb",
            color:
              "#963d37",
            fontSize:
              "12px",
          }}
        >
          {error}
        </div>

      )}


      {/* ======================================================
          CORE METRICS
          ====================================================== */}

      <section
        style={{
          display:
            "grid",
          gridTemplateColumns:
            "repeat(4, minmax(0, 1fr))",
          gap:
            "14px",
        }}
      >

        <div className="content-card">

          <span>
            Outlets
          </span>

          <strong
            style={{
              display:
                "block",
              marginTop:
                "8px",
              fontSize:
                "32px",
            }}
          >
            {summary.outlets || 0}
          </strong>

        </div>


        <div className="content-card">

          <span>
            Active RED alerts
          </span>

          <strong
            style={{
              display:
                "block",
              marginTop:
                "8px",
              fontSize:
                "32px",
              color:
                "#963d37",
            }}
          >
            {
              summary.active_red_alerts ||
              0
            }
          </strong>

        </div>


        <div className="content-card">

          <span>
            Active ORANGE alerts
          </span>

          <strong
            style={{
              display:
                "block",
              marginTop:
                "8px",
              fontSize:
                "32px",
              color:
                "#925f1b",
            }}
          >
            {
              summary.active_orange_alerts ||
              0
            }
          </strong>

        </div>


        <div className="content-card">

          <span>
            Unresolved investigations
          </span>

          <strong
            style={{
              display:
                "block",
              marginTop:
                "8px",
              fontSize:
                "32px",
            }}
          >
            {
              summary.unresolved_investigations ||
              0
            }
          </strong>

        </div>

      </section>


      {/* ======================================================
          UNIFIED EVIDENCE
          ====================================================== */}

      <section
        className="content-card"
      >

        <div className="eyebrow">
          UNIFIED EVIDENCE
        </div>

        <h3
          style={{
            margin:
              "4px 0 15px",
          }}
        >
          Current safety signals
        </h3>


        <div
          style={{
            display:
              "grid",
            gridTemplateColumns:
              "repeat(4, minmax(0, 1fr))",
            gap:
              "12px",
          }}
        >

          <div
            style={{
              padding:
                "15px",
              borderRadius:
                "11px",
              background:
                "#f5f7f5",
            }}
          >

            <span>
              Citizen reports · 30 days
            </span>

            <strong
              style={{
                display:
                  "block",
                marginTop:
                  "6px",
                fontSize:
                  "27px",
              }}
            >
              {
                summary.citizen_reports_30d ||
                0
              }
            </strong>

            <small>
              Verified:{" "}
              {
                summary.verified_citizen_reports_30d ||
                0
              }
            </small>

          </div>


          <div
            style={{
              padding:
                "15px",
              borderRadius:
                "11px",
              background:
                "#f5f7f5",
            }}
          >

            <span>
              Hygiene AI findings
            </span>

            <strong
              style={{
                display:
                  "block",
                marginTop:
                  "6px",
                fontSize:
                  "27px",
              }}
            >
              {
                summary.ai_hygiene_findings_30d ||
                0
              }
            </strong>

            <small>
              Critical:{" "}
              {
                summary.critical_ai_findings_30d ||
                0
              }
            </small>

          </div>


          <div
            style={{
              padding:
                "15px",
              borderRadius:
                "11px",
              background:
                "#f5f7f5",
            }}
          >

            <span>
              Alerts · last 24 hours
            </span>

            <strong
              style={{
                display:
                  "block",
                marginTop:
                  "6px",
                fontSize:
                  "27px",
              }}
            >
              {
                summary.alerts_last_24h ||
                0
              }
            </strong>

            <small>
              Current activity
            </small>

          </div>


          <div
            style={{
              padding:
                "15px",
              borderRadius:
                "11px",
              background:
                "#f5f7f5",
            }}
          >

            <span>
              Blockchain audits
            </span>

            <strong
              style={{
                display:
                  "block",
                marginTop:
                  "6px",
                fontSize:
                  "27px",
              }}
            >
              {
                summary.blockchain_anchored_audits_30d ||
                0
              }
            </strong>

            <small>
              Anchored records
            </small>

          </div>

        </div>

      </section>


      {/* ======================================================
          REGIONAL PRIORITY
          ====================================================== */}

      <section
        style={{
          display:
            "grid",
          gridTemplateColumns:
            "1fr 1fr",
          gap:
            "14px",
        }}
      >

        <div className="content-card">

          <div className="eyebrow">
            GOVERNMENT PRIORITY
          </div>

          <h3
            style={{
              margin:
                "4px 0 15px",
            }}
          >
            Current regional priority
          </h3>


          <div
            style={{
              display:
                "flex",
              alignItems:
                "center",
              gap:
                "15px",
            }}
          >

            <div
              style={{
                minWidth:
                  "76px",
                height:
                  "76px",
                borderRadius:
                  "50%",
                display:
                  "grid",
                placeItems:
                  "center",
                background:
                  priorityColors.background,
                color:
                  priorityColors.color,
                fontWeight:
                  800,
                fontSize:
                  "11px",
              }}
            >
              {priority}
            </div>


            <div>

              <strong
                style={{
                  display:
                    "block",
                  fontSize:
                    "24px",
                }}
              >
                {
                  summary.unresolved_investigations ||
                  0
                }
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
                RED:{" "}
                {
                  summary.active_red_alerts ||
                  0
                }
                {" • "}
                ORANGE:{" "}
                {
                  summary.active_orange_alerts ||
                  0
                }
              </p>

            </div>

          </div>

        </div>


        {/* ====================================================
            RISK DISTRIBUTION
            ==================================================== */}

        <div className="content-card">

          <div className="eyebrow">
            OUTLET RISK
          </div>

          <h3
            style={{
              margin:
                "4px 0 15px",
            }}
          >
            Risk distribution
          </h3>


          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "repeat(4, 1fr)",
              gap:
                "8px",
            }}
          >

            {[
              [
                "Critical",
                distribution.critical || 0,
                "#963d37",
              ],
              [
                "High",
                distribution.high || 0,
                "#925f1b",
              ],
              [
                "Medium",
                distribution.medium || 0,
                "#89611f",
              ],
              [
                "Low",
                distribution.low || 0,
                "#266437",
              ],
            ].map(
              ([label, value, color]) => (

                <div
                  key={label}
                  style={{
                    padding:
                      "12px 8px",
                    borderRadius:
                      "9px",
                    background:
                      "#f5f7f5",
                  }}
                >

                  <span
                    style={{
                      display:
                        "block",
                      fontSize:
                        "10px",
                      color:
                        "#727b74",
                    }}
                  >
                    {label}
                  </span>

                  <strong
                    style={{
                      display:
                        "block",
                      marginTop:
                        "5px",
                      color,
                      fontSize:
                        "22px",
                    }}
                  >
                    {value}
                  </strong>

                </div>

              )
            )}

          </div>

        </div>

      </section>


      {/* ======================================================
          TOP RISK OUTLETS
          ====================================================== */}

      <section className="content-card">

        <div className="section-title">

          <div>

            <div className="eyebrow">
              INSPECTION FOCUS
            </div>

            <h3
              style={{
                margin:
                  "4px 0",
              }}
            >
              Highest-risk outlets
            </h3>

            <span>
              Automatically refreshed from the current
              regional evidence state.
            </span>

          </div>

        </div>


        {topOutlets.length === 0 ? (

          <div
            style={{
              marginTop:
                "16px",
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

            {topOutlets.map(
              (outlet, index) => {

                const level =
                  riskLevel(
                    outlet.risk_score || 0
                  );

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
                        "40px 1fr auto",
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
                          "#737c75",
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
                            "#737b74",
                        }}
                      >
                        {
                          outlet.registration_id
                        }
                        {" • RED: "}
                        {
                          outlet.red_alerts ||
                          0
                        }
                        {" • Investigations: "}
                        {
                          outlet.unresolved_investigations ||
                          0
                        }
                        {" • Verified citizens: "}
                        {
                          outlet.verified_citizen_reports ||
                          0
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
                          outlet.risk_score ||
                          0
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
          DATA SOURCES
          ====================================================== */}

      <section className="content-card">

        <div className="eyebrow">
          DATA SOURCES
        </div>

        <h3
          style={{
            margin:
              "4px 0 15px",
          }}
        >
          Active evidence systems
        </h3>


        <div
          style={{
            display:
              "grid",
            gridTemplateColumns:
              "repeat(5, 1fr)",
            gap:
              "9px",
          }}
        >

          {[
            [
              "IoT alerts",
              sources.iot_alerts,
            ],
            [
              "Investigations",
              sources.investigations,
            ],
            [
              "Hygiene AI",
              sources.hygiene_ai,
            ],
            [
              "Citizen reports",
              sources.citizen_reports,
            ],
            [
              "Blockchain",
              sources.blockchain,
            ],
          ].map(
            ([name, active]) => (

              <div
                key={name}
                style={{
                  padding:
                    "11px",
                  borderRadius:
                    "9px",
                  background:
                    "#f5f7f5",
                }}
              >

                <span
                  style={{
                    display:
                      "block",
                    fontSize:
                      "11px",
                  }}
                >
                  {name}
                </span>

                <strong
                  style={{
                    display:
                      "block",
                    marginTop:
                      "4px",
                    color:
                      active
                        ? "#266437"
                        : "#727b74",
                    fontSize:
                      "10px",
                  }}
                >
                  {active
                    ? "ACTIVE"
                    : "NO DATA"}
                </strong>

              </div>

            )
          )}

        </div>

      </section>


      {/* ======================================================
          SYSTEM MESSAGE
          ====================================================== */}

      <div
        style={{
          padding:
            "13px",
          borderRadius:
            "10px",
          background:
            "#f3f6f3",
          color:
            "#68716b",
          fontSize:
            "12px",
        }}
      >
        {data?.system_message ||
          "SafeBite Command Center is monitoring the current regional evidence state."}
      </div>

    </div>
  );
}