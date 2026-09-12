import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

const DEFAULT_REGISTRATION_ID = "SB-MGM-001";

const PERIOD_OPTIONS = [
  { label: "7 days", value: 7 },
  { label: "30 days", value: 30 },
  { label: "60 days", value: 60 },
  { label: "90 days", value: 90 },
];

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
  });
}

function formatDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("en-IN");
}

function trendLabel(trend) {
  switch (trend) {
    case "IMPROVING":
      return "↑ IMPROVING";

    case "DETERIORATING":
      return "↓ DETERIORATING";

    default:
      return "→ STABLE";
  }
}

function trendClass(trend) {
  switch (trend) {
    case "IMPROVING":
      return "audit-trend improving";

    case "DETERIORATING":
      return "audit-trend deteriorating";

    default:
      return "audit-trend stable";
  }
}

function numberValue(value) {
  return Number(value || 0);
}

function getPriorityLabel(score) {
  const value = numberValue(score);

  if (value >= 80) return "CRITICAL";
  if (value >= 60) return "HIGH";
  if (value >= 35) return "MEDIUM";
  return "LOW";
}

function priorityClass(priority) {
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

function scoreClass(score) {
  const value = numberValue(score);

  if (value < 50) {
    return {
      background: "#fdeceb",
      color: "#963d37",
    };
  }

  if (value < 65) {
    return {
      background: "#fff8e8",
      color: "#89611f",
    };
  }

  if (value < 80) {
    return {
      background: "#fff4df",
      color: "#95601d",
    };
  }

  return {
    background: "#e8f5eb",
    color: "#266437",
  };
}

export default function AuditHistory() {
  const [registrationId, setRegistrationId] = useState(
    DEFAULT_REGISTRATION_ID
  );

  const [days, setDays] = useState(30);

  const [history, setHistory] = useState(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  async function loadHistory(
    requestedId = registrationId,
    requestedDays = days
  ) {
    const cleanId = requestedId.trim();

    if (!cleanId) {
      setError("Enter an outlet registration ID.");
      setHistory(null);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await api.auditHistory(
        cleanId,
        requestedDays
      );

      setHistory(data);
    } catch (err) {
      setHistory(null);

      setError(
        err.message ||
          "Unable to load outlet audit history."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory(
      DEFAULT_REGISTRATION_ID,
      30
    );
  }, []);

  const chartData = useMemo(() => {
    if (!history?.history) {
      return [];
    }

    return history.history.map(
      (point) => ({
        label: formatDate(
          point.period_end
        ),

        score: numberValue(
          point.score
        ),

        priority: numberValue(
          point.inspection_priority_score
        ),

        alerts: numberValue(
          point.alerts
        ),

        red: numberValue(
          point.active_red
        ),

        orange: numberValue(
          point.active_orange
        ),

        investigations: numberValue(
          point.investigations
        ),

        ai: numberValue(
          point.ai_detections
        ),

        hygiene: numberValue(
          point.hygiene_ai_findings
        ),

        criticalAi: numberValue(
          point.critical_ai_findings
        ),

        citizen: numberValue(
          point.verified_citizen_reports
        ),
      })
    );
  }, [history]);

  const chartWidth = 780;
  const chartHeight = 300;

  const paddingLeft = 50;
  const paddingRight = 25;
  const paddingTop = 24;
  const paddingBottom = 50;

  const plotWidth =
    chartWidth -
    paddingLeft -
    paddingRight;

  const plotHeight =
    chartHeight -
    paddingTop -
    paddingBottom;

  const pointX = (index) => {
    if (chartData.length <= 1) {
      return (
        paddingLeft +
        plotWidth / 2
      );
    }

    return (
      paddingLeft +
      (
        index /
        (chartData.length - 1)
      ) *
        plotWidth
    );
  };

  const pointY = (score) => {
    return (
      paddingTop +
      (
        1 -
        Math.max(
          0,
          Math.min(
            100,
            score
          )
        ) /
          100
      ) *
        plotHeight
    );
  };

  const points = chartData.map(
    (point, index) => ({
      ...point,
      x: pointX(index),
      y: pointY(point.score),
    })
  );

  const polyline = points
    .map(
      (point) =>
        `${point.x},${point.y}`
    )
    .join(" ");

  const evidence =
    history?.current_evidence || {};

  const currentScore =
    numberValue(
      history?.current_score
    );

  const currentPriority =
    numberValue(
      history?.current_inspection_priority
    );

  const scoreStyle =
    scoreClass(
      currentScore
    );

  const priorityStyle =
    priorityClass(
      getPriorityLabel(
        currentPriority
      )
    );

  return (
    <div
      style={{
        display: "grid",
        gap: 20,
      }}
    >

      {/* ======================================================
          HEADER
          ====================================================== */}

      <div
        style={{
          display: "flex",
          justifyContent:
            "space-between",
          alignItems:
            "flex-end",
          gap: 20,
          flexWrap:
            "wrap",
        }}
      >

        <div>

          <div className="eyebrow">
            OUTLET INTELLIGENCE
          </div>

          <h2
            style={{
              margin:
                "4px 0",
            }}
          >
            Audit History
          </h2>

          <p
            style={{
              margin: 0,
              color: "#68716b",
            }}
          >
            Unified historical view of
            food-safety risk, investigations,
            AI evidence, and verified citizen reports.
          </p>

        </div>


        {/* ====================================================
            SEARCH CONTROLS
            ==================================================== */}

        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems:
              "center",
            flexWrap:
              "wrap",
          }}
        >

          <input
            value={registrationId}
            onChange={(event) =>
              setRegistrationId(
                event.target.value
              )
            }
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                loadHistory();
              }
            }}
            placeholder="Registration ID"
            style={{
              width: 180,
              padding:
                "11px 12px",
              border:
                "1px solid #cfd8d1",
              borderRadius: 10,
              font:
                "inherit",
            }}
          />


          <select
            value={days}
            onChange={(event) => {
              const selected =
                Number(
                  event.target.value
                );

              setDays(selected);

              loadHistory(
                registrationId,
                selected
              );
            }}
            style={{
              padding:
                "11px 12px",
              border:
                "1px solid #cfd8d1",
              borderRadius: 10,
              font:
                "inherit",
              background:
                "white",
            }}
          >
            {PERIOD_OPTIONS.map(
              (option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              )
            )}
          </select>


          <button
            className="primary-button"
            onClick={() =>
              loadHistory()
            }
            disabled={
              loading
            }
          >
            {loading
              ? "Loading..."
              : "View History"}
          </button>

        </div>

      </div>


      {/* ======================================================
          ERROR
          ====================================================== */}

      {error && (
        <div
          style={{
            padding:
              "14px 16px",
            borderRadius:
              11,
            background:
              "#fdeceb",
            border:
              "1px solid #e3b7b4",
            color:
              "#953d37",
          }}
        >
          {error}
        </div>
      )}


      {/* ======================================================
          LOADING
          ====================================================== */}

      {loading && !history && (
        <div
          style={{
            background:
              "white",
            border:
              "1px solid #dde5de",
            borderRadius:
              16,
            padding: 50,
            textAlign:
              "center",
            color:
              "#727b74",
          }}
        >
          Loading audit history...
        </div>
      )}


      {history && (
        <>

          {/* ==================================================
              OUTLET SUMMARY
              ================================================== */}

          <section
            style={{
              background:
                "white",
              border:
                "1px solid #dde5de",
              borderRadius:
                16,
              padding: 22,
            }}
          >

            <div
              style={{
                display:
                  "flex",
                justifyContent:
                  "space-between",
                alignItems:
                  "center",
                gap: 20,
                flexWrap:
                  "wrap",
              }}
            >

              <div>

                <div className="eyebrow">
                  REGISTERED OUTLET
                </div>

                <h3
                  style={{
                    margin:
                      "5px 0 3px",
                    fontSize:
                      25,
                  }}
                >
                  {
                    history.outlet?.name ||
                    "Unknown outlet"
                  }
                </h3>

                <p
                  style={{
                    margin: 0,
                    color:
                      "#68716b",
                  }}
                >
                  {
                    history.outlet?.registration_id
                  }
                  {" • "}
                  {
                    history.outlet?.region
                  }
                </p>

              </div>


              <div
                style={{
                  display:
                    "flex",
                  alignItems:
                    "center",
                  gap: 14,
                  flexWrap:
                    "wrap",
                }}
              >

                <div
                  style={{
                    textAlign:
                      "right",
                  }}
                >

                  <div
                    style={{
                      fontSize:
                        12,
                      color:
                        "#727b74",
                    }}
                  >
                    Compliance
                  </div>

                  <strong
                    style={{
                      display:
                        "block",
                      fontSize:
                        34,
                      lineHeight:
                        1.1,
                    }}
                  >
                    {currentScore}
                    <span
                      style={{
                        fontSize:
                          15,
                        color:
                          "#747d76",
                      }}
                    >
                      /100
                    </span>
                  </strong>

                </div>


                <div
                  style={{
                    display:
                      "grid",
                    gap: 6,
                  }}
                >

                  <span
                    style={{
                      display:
                        "inline-flex",
                      justifyContent:
                        "center",
                      padding:
                        "6px 10px",
                      borderRadius:
                        999,
                      background:
                        scoreStyle.background,
                      color:
                        scoreStyle.color,
                      fontSize:
                        10,
                      fontWeight:
                        800,
                    }}
                  >
                    CURRENT SCORE
                  </span>

                  <span
                    className={trendClass(
                      history.trend
                    )}
                  >
                    {trendLabel(
                      history.trend
                    )}
                  </span>

                </div>

              </div>

            </div>

          </section>


          {/* ==================================================
              CURRENT EVIDENCE
              ================================================== */}

          <section>

            <div
              style={{
                marginBottom:
                  12,
              }}
            >

              <div className="eyebrow">
                CURRENT EVIDENCE
              </div>

              <h3
                style={{
                  margin:
                    "4px 0",
                }}
              >
                What is driving the current risk?
              </h3>

              <p
                style={{
                  margin: 0,
                  color:
                    "#727b74",
                  fontSize:
                    13,
                }}
              >
                Evidence is shown by source so
                officers can distinguish automated
                signals from government-confirmed findings.
              </p>

            </div>


            <div
              style={{
                display:
                  "grid",
                gridTemplateColumns:
                  "repeat(5, minmax(0, 1fr))",
                gap: 12,
              }}
            >

              {/* ALERTS */}

              <div
                style={{
                  background:
                    "white",
                  border:
                    "1px solid #dde5de",
                  borderRadius:
                    14,
                  padding: 16,
                }}
              >
                <span
                  style={{
                    display:
                      "block",
                    fontSize:
                      11,
                    color:
                      "#727b74",
                  }}
                >
                  IoT / Alerts
                </span>

                <strong
                  style={{
                    display:
                      "block",
                    marginTop:
                      7,
                    fontSize:
                      28,
                  }}
                >
                  {evidence.alerts || 0}
                </strong>

                <small
                  style={{
                    display:
                      "block",
                    marginTop:
                      5,
                    color:
                      "#963d37",
                  }}
                >
                  RED: {evidence.active_red || 0}
                </small>
              </div>


              {/* INVESTIGATIONS */}

              <div
                style={{
                  background:
                    "white",
                  border:
                    "1px solid #dde5de",
                  borderRadius:
                    14,
                  padding: 16,
                }}
              >
                <span
                  style={{
                    display:
                      "block",
                    fontSize:
                      11,
                    color:
                      "#727b74",
                  }}
                >
                  Investigations
                </span>

                <strong
                  style={{
                    display:
                      "block",
                    marginTop:
                      7,
                    fontSize:
                      28,
                  }}
                >
                  {
                    evidence.investigations ||
                    0
                  }
                </strong>

                <small
                  style={{
                    display:
                      "block",
                    marginTop:
                      5,
                    color:
                      "#727b74",
                  }}
                >
                  Unresolved:{" "}
                  {
                    evidence.unresolved_investigations ||
                    0
                  }
                </small>
              </div>


              {/* AI */}

              <div
                style={{
                  background:
                    "white",
                  border:
                    "1px solid #dde5de",
                  borderRadius:
                    14,
                  padding: 16,
                }}
              >
                <span
                  style={{
                    display:
                      "block",
                    fontSize:
                      11,
                    color:
                      "#727b74",
                  }}
                >
                  Hygiene AI
                </span>

                <strong
                  style={{
                    display:
                      "block",
                    marginTop:
                      7,
                    fontSize:
                      28,
                  }}
                >
                  {
                    evidence.hygiene_ai_findings ||
                    0
                  }
                </strong>

                <small
                  style={{
                    display:
                      "block",
                    marginTop:
                      5,
                    color:
                      "#727b74",
                  }}
                >
                  Total AI detections:{" "}
                  {
                    evidence.ai_detections ||
                    0
                  }
                </small>
              </div>


              {/* CRITICAL AI */}

              <div
                style={{
                  background:
                    "white",
                  border:
                    "1px solid #dde5de",
                  borderRadius:
                    14,
                  padding: 16,
                }}
              >
                <span
                  style={{
                    display:
                      "block",
                    fontSize:
                      11,
                    color:
                      "#727b74",
                  }}
                >
                  Critical AI
                </span>

                <strong
                  style={{
                    display:
                      "block",
                    marginTop:
                      7,
                    fontSize:
                      28,
                  }}
                >
                  {
                    evidence.critical_ai_findings ||
                    0
                  }
                </strong>

                <small
                  style={{
                    display:
                      "block",
                    marginTop:
                      5,
                    color:
                      evidence.critical_ai_findings
                        ? "#963d37"
                        : "#266437",
                  }}
                >
                  {
                    evidence.critical_ai_findings
                      ? "Immediate attention"
                      : "No critical AI finding"
                  }
                </small>
              </div>


              {/* CITIZEN */}

              <div
                style={{
                  background:
                    "white",
                  border:
                    "1px solid #dde5de",
                  borderRadius:
                    14,
                  padding: 16,
                }}
              >
                <span
                  style={{
                    display:
                      "block",
                    fontSize:
                      11,
                    color:
                      "#727b74",
                  }}
                >
                  Verified citizen reports
                </span>

                <strong
                  style={{
                    display:
                      "block",
                    marginTop:
                      7,
                    fontSize:
                      28,
                  }}
                >
                  {
                    evidence.verified_citizen_reports ||
                    0
                  }
                </strong>

                <small
                  style={{
                    display:
                      "block",
                    marginTop:
                      5,
                    color:
                      "#266437",
                  }}
                >
                  Government-confirmed
                </small>
              </div>

            </div>

          </section>


          {/* ==================================================
              PRIORITY
              ================================================== */}

          <section
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "1fr 1fr",
              gap: 14,
            }}
          >

            <div
              style={{
                background:
                  "white",
                border:
                  "1px solid #dde5de",
                borderRadius:
                  14,
                padding: 20,
              }}
            >

              <span
                style={{
                  display:
                    "block",
                  color:
                    "#727b74",
                  fontSize:
                    12,
                }}
              >
                Inspection priority
              </span>

              <div
                style={{
                  display:
                    "flex",
                  alignItems:
                    "center",
                  gap: 12,
                  marginTop:
                    8,
                  flexWrap:
                    "wrap",
                }}
              >

                <strong
                  style={{
                    fontSize:
                      30,
                  }}
                >
                  {currentPriority}
                  /100
                </strong>

                <span
                  style={{
                    padding:
                      "6px 10px",
                    borderRadius:
                      999,
                    background:
                      priorityStyle.background,
                    color:
                      priorityStyle.color,
                    fontSize:
                      10,
                    fontWeight:
                      800,
                  }}
                >
                  {
                    getPriorityLabel(
                      currentPriority
                    )
                  }
                </span>

              </div>

            </div>


            <div
              style={{
                background:
                  "white",
                border:
                  "1px solid #dde5de",
                borderRadius:
                  14,
                padding: 20,
              }}
            >

              <span
                style={{
                  display:
                    "block",
                  color:
                    "#727b74",
                  fontSize:
                    12,
                }}
              >
                Score movement
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    8,
                  fontSize:
                    30,
                }}
              >
                {
                  history.score_change > 0
                    ? "+"
                    : ""
                }
                {
                  history.score_change
                }
              </strong>

              <small
                style={{
                  display:
                    "block",
                  marginTop:
                    3,
                  color:
                    "#727b74",
                }}
              >
                Across the selected{" "}
                {history.period_days}-
                day audit period
              </small>

            </div>

          </section>


          {/* ==================================================
              TREND CHART
              ================================================== */}

          <section
            style={{
              background:
                "white",
              border:
                "1px solid #dde5de",
              borderRadius:
                16,
              padding: 22,
            }}
          >

            <div
              style={{
                display:
                  "flex",
                justifyContent:
                  "space-between",
                alignItems:
                  "center",
                gap: 15,
                marginBottom:
                  15,
                flexWrap:
                  "wrap",
              }}
            >

              <div>

                <div className="eyebrow">
                  SCORE TREND
                </div>

                <h3
                  style={{
                    margin:
                      "4px 0",
                  }}
                >
                  Compliance trajectory
                </h3>

                <p
                  style={{
                    margin: 0,
                    color:
                      "#727b74",
                    fontSize:
                      13,
                  }}
                >
                  Higher score indicates stronger
                  recorded compliance.
                </p>

              </div>

              <span
                className={trendClass(
                  history.trend
                )}
              >
                {trendLabel(
                  history.trend
                )}
              </span>

            </div>


            {points.length > 0 ? (

              <div
                style={{
                  width:
                    "100%",
                  overflowX:
                    "auto",
                }}
              >

                <svg
                  viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                  width="100%"
                  height="310"
                  role="img"
                  aria-label="Compliance score trend"
                  style={{
                    minWidth:
                      "650px",
                  }}
                >

                  {/* GRID */}

                  {[0, 25, 50, 75, 100].map(
                    (value) => {

                      const y =
                        pointY(value);

                      return (
                        <g
                          key={value}
                        >

                          <line
                            x1={
                              paddingLeft
                            }
                            x2={
                              chartWidth -
                              paddingRight
                            }
                            y1={y}
                            y2={y}
                            stroke="#e7ece8"
                            strokeWidth="1"
                          />

                          <text
                            x="8"
                            y={
                              y + 4
                            }
                            fontSize="11"
                            fill="#7a837c"
                          >
                            {value}
                          </text>

                        </g>
                      );
                    }
                  )}


                  {/* SCORE LINE */}

                  <polyline
                    points={
                      polyline
                    }
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="4"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />


                  {/* SCORE POINTS */}

                  {points.map(
                    (
                      point,
                      index
                    ) => (

                      <g
                        key={`${point.label}-${index}`}
                      >

                        <circle
                          cx={
                            point.x
                          }
                          cy={
                            point.y
                          }
                          r="7"
                          fill="white"
                          stroke="currentColor"
                          strokeWidth="3"
                        />

                        <text
                          x={
                            point.x
                          }
                          y={
                            point.y -
                            14
                          }
                          textAnchor="middle"
                          fontSize="11"
                          fontWeight="700"
                          fill="currentColor"
                        >
                          {
                            point.score
                          }
                        </text>

                        <text
                          x={
                            point.x
                          }
                          y={
                            chartHeight -
                            16
                          }
                          textAnchor="middle"
                          fontSize="10"
                          fill="#7a837c"
                        >
                          {
                            point.label
                          }
                        </text>

                      </g>

                    )
                  )}

                </svg>

              </div>

            ) : (

              <div
                style={{
                  textAlign:
                    "center",
                  padding:
                    40,
                  color:
                    "#727b74",
                }}
              >
                No historical data available.
              </div>

            )}

          </section>


          {/* ==================================================
              PERIOD DETAILS
              ================================================== */}

          <section
            style={{
              background:
                "white",
              border:
                "1px solid #dde5de",
              borderRadius:
                16,
              padding: 22,
            }}
          >

            <div
              style={{
                marginBottom:
                  15,
              }}
            >

              <div className="eyebrow">
                EVIDENCE TIMELINE
              </div>

              <h3
                style={{
                  margin:
                    "4px 0",
                }}
              >
                Period-by-period evidence
              </h3>

            </div>


            <div
              style={{
                width:
                  "100%",
                overflowX:
                  "auto",
              }}
            >

              <table
                style={{
                  width:
                    "100%",
                  borderCollapse:
                    "collapse",
                  minWidth:
                    "900px",
                }}
              >

                <thead>

                  <tr>

                    {[
                      "Period",
                      "Score",
                      "Alerts",
                      "RED",
                      "Investigations",
                      "AI findings",
                      "Critical AI",
                      "Verified citizens",
                    ].map(
                      (heading) => (
                        <th
                          key={heading}
                          style={{
                            textAlign:
                              "left",
                            padding:
                              "11px 10px",
                            borderBottom:
                              "1px solid #e6ebe7",
                            fontSize:
                              10,
                            color:
                              "#717a73",
                            textTransform:
                              "uppercase",
                            letterSpacing:
                              "0.05em",
                          }}
                        >
                          {heading}
                        </th>
                      )
                    )}

                  </tr>

                </thead>


                <tbody>

                  {history.history.map(
                    (
                      point,
                      index
                    ) => (

                      <tr
                        key={`${point.period_start}-${index}`}
                      >

                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                            whiteSpace:
                              "nowrap",
                          }}
                        >
                          {
                            formatDate(
                              point.period_start
                            )
                          }
                          {" → "}
                          {
                            formatDate(
                              point.period_end
                            )
                          }
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                            fontWeight:
                              800,
                          }}
                        >
                          {point.score}
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {point.alerts}
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                            fontWeight:
                              point.active_red
                                ? 800
                                : 400,
                          }}
                        >
                          {point.active_red}
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {
                            point.investigations
                          }
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {
                            point.ai_detections
                          }
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                            fontWeight:
                              point.critical_ai_findings
                                ? 800
                                : 400,
                          }}
                        >
                          {
                            point.critical_ai_findings
                          }
                        </td>


                        <td
                          style={{
                            padding:
                              "12px 10px",
                            borderBottom:
                              "1px solid #eef1ee",
                            fontWeight:
                              point.verified_citizen_reports
                                ? 800
                                : 400,
                          }}
                        >
                          {
                            point.verified_citizen_reports
                          }
                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          </section>


          {/* ==================================================
              DATA SOURCES
              ================================================== */}

          <section
            style={{
              background:
                "white",
              border:
                "1px solid #dde5de",
              borderRadius:
                16,
              padding: 22,
            }}
          >

            <div className="eyebrow">
              DATA PROVENANCE
            </div>

            <h3
              style={{
                margin:
                  "4px 0 14px",
              }}
            >
              Evidence sources
            </h3>

            <div
              style={{
                display:
                  "grid",
                gridTemplateColumns:
                  "repeat(4, 1fr)",
                gap: 10,
              }}
            >

              {[
                [
                  "Government alerts",
                  history.data_sources?.government_alerts,
                ],
                [
                  "Investigations",
                  history.data_sources?.investigations,
                ],
                [
                  "Hygiene AI",
                  history.data_sources?.hygiene_ai,
                ],
                [
                  "Verified citizen reports",
                  history.data_sources?.verified_citizen_reports,
                ],
              ].map(
                ([label, enabled]) => (

                  <div
                    key={label}
                    style={{
                      padding:
                        14,
                      borderRadius:
                        11,
                      background:
                        enabled
                          ? "#f0f6f1"
                          : "#f5f6f5",
                      border:
                        "1px solid #e2e8e2",
                    }}
                  >

                    <span
                      style={{
                        display:
                          "block",
                        fontSize:
                          12,
                        color:
                          "#68716b",
                      }}
                    >
                      {label}
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          6,
                        color:
                          enabled
                            ? "#266437"
                            : "#777f79",
                      }}
                    >
                      {enabled
                        ? "ACTIVE"
                        : "NO DATA"}
                    </strong>

                  </div>

                )
              )}

            </div>

          </section>


          {/* ==================================================
              INTERPRETATION
              ================================================== */}

          <section
            style={{
              background:
                "white",
              border:
                "1px solid #dde5de",
              borderRadius:
                16,
              padding: 22,
            }}
          >

            <div className="eyebrow">
              AUDITOR INTERPRETATION
            </div>

            <h3
              style={{
                margin:
                  "5px 0 8px",
              }}
            >
              {history.trend ===
              "DETERIORATING"
                ? "Risk pressure is increasing"
                : history.trend ===
                    "IMPROVING"
                  ? "Compliance direction is improving"
                  : "Compliance is relatively stable"}
            </h3>

            <p
              style={{
                margin: 0,
                lineHeight:
                  1.6,
                color:
                  "#68716b",
              }}
            >
              {history.trend ===
              "DETERIORATING"
                ? `The outlet's compliance score changed by ${history.score_change} points during the selected period. Current indicators should be reviewed together with alerts, investigations, AI findings, and verified citizen evidence.`
                : history.trend ===
                    "IMPROVING"
                  ? `The outlet's compliance score improved by ${history.score_change} points during the selected period. Continue monitoring to confirm that the improvement is sustained.`
                  : "The recorded evidence has not changed enough to classify the outlet as clearly improving or deteriorating."
              }
            </p>

            <div
              style={{
                marginTop:
                  14,
                padding:
                  14,
                borderRadius:
                  10,
                background:
                  "#f5f7f5",
              }}
            >

              <strong
                style={{
                  display:
                    "block",
                  fontSize:
                    12,
                }}
              >
                System note
              </strong>

              <span
                style={{
                  display:
                    "block",
                  marginTop:
                    4,
                  fontSize:
                    12,
                  color:
                    "#727b74",
                }}
              >
                {
                  history.explanation ||
                  "Historical indicators are derived from recorded SafeBite evidence."
                }
              </span>

            </div>

          </section>


          {/* ==================================================
              GENERATED INFORMATION
              ================================================== */}

          <div
            style={{
              textAlign:
                "right",
              color:
                "#7a837c",
              fontSize:
                11,
            }}
          >
            Generated:{" "}
            {
              formatDateTime(
                history.generated_at
              )
            }
          </div>

        </>
      )}

    </div>
  );
}