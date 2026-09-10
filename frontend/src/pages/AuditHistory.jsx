import { useEffect, useMemo, useState } from "react";
import { api } from "../api";


const DEFAULT_REGISTRATION_ID = "SB-MGM-001";


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


export default function AuditHistory() {
  const [registrationId, setRegistrationId] = useState(
    DEFAULT_REGISTRATION_ID
  );

  const [history, setHistory] = useState(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");


  // ==========================================================
  // LOAD HISTORY
  // ==========================================================

  async function loadHistory(id = registrationId) {
    const cleanId = id.trim();

    if (!cleanId) {
      setError("Enter an outlet registration ID.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await api.auditHistory(
        cleanId,
        30
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


  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {
    loadHistory(DEFAULT_REGISTRATION_ID);
  }, []);


  // ==========================================================
  // GRAPH DATA
  // ==========================================================

  const chartData = useMemo(() => {
    if (!history?.history) {
      return [];
    }

    return history.history.map(
      (point) => ({
        label: formatDate(
          point.period_end
        ),

        score: Number(
          point.score || 0
        ),
      })
    );
  }, [history]);


  const maxScore = 100;

  const chartWidth = 760;

  const chartHeight = 260;

  const paddingLeft = 48;

  const paddingRight = 20;

  const paddingTop = 24;

  const paddingBottom = 42;

  const plotWidth =
    chartWidth -
    paddingLeft -
    paddingRight;

  const plotHeight =
    chartHeight -
    paddingTop -
    paddingBottom;


  function pointX(index) {
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
  }


  function pointY(score) {
    return (
      paddingTop +
      (
        1 -
        score / maxScore
      ) *
        plotHeight
    );
  }


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
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: 20,
          flexWrap: "wrap",
        }}
      >

        <div>
          <div className="eyebrow">
            OUTLET INTELLIGENCE
          </div>

          <h2
            style={{
              margin: "4px 0",
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
            Review historical compliance performance
            and risk direction for an outlet.
          </p>
        </div>


        {/* ====================================================
            SEARCH
            ==================================================== */}

        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
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
              padding: "11px 12px",
              border:
                "1px solid #cfd8d1",
              borderRadius: 10,
              font: "inherit",
            }}
          />

          <button
            className="primary-button"
            onClick={() =>
              loadHistory()
            }
            disabled={loading}
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
            padding: "14px 16px",
            borderRadius: 11,
            background: "#fdeceb",
            border:
              "1px solid #e3b7b4",
            color: "#953d37",
          }}
        >
          {error}
        </div>
      )}


      {/* ======================================================
          EMPTY STATE
          ====================================================== */}

      {!history && !loading && !error && (
        <div
          className="content-card"
        >
          Enter an outlet registration ID
          to view historical audit performance.
        </div>
      )}


      {loading && !history && (
        <div
          className="content-card"
          style={{
            textAlign: "center",
            padding: 50,
          }}
        >
          Loading audit history...
        </div>
      )}


      {history && (

        <>

          {/* ==================================================
              OUTLET HEADER CARD
              ================================================== */}

          <section
            style={{
              background: "white",
              border:
                "1px solid #dde5de",
              borderRadius: 16,
              padding: 22,
            }}
          >

            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems:
                  "center",
                gap: 20,
                flexWrap: "wrap",
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
                    fontSize: 25,
                  }}
                >
                  {history.outlet?.name}
                </h3>

                <p
                  style={{
                    margin: 0,
                    color: "#68716b",
                  }}
                >
                  {history.outlet?.registration_id}
                  {" • "}
                  {history.outlet?.region}
                </p>

              </div>


              <div
                style={{
                  textAlign: "right",
                }}
              >

                <div
                  style={{
                    fontSize: 12,
                    color: "#727b74",
                  }}
                >
                  Current compliance
                </div>

                <strong
                  style={{
                    display: "block",
                    marginTop: 2,
                    fontSize: 36,
                  }}
                >
                  {history.current_score}
                  <span
                    style={{
                      fontSize: 16,
                      color: "#747d76",
                    }}
                  >
                    /100
                  </span>
                </strong>

                <span
                  className={trendClass(
                    history.trend
                  )}
                  style={{
                    marginTop: 6,
                    display:
                      "inline-flex",
                  }}
                >
                  {trendLabel(
                    history.trend
                  )}
                </span>

              </div>

            </div>

          </section>


          {/* ==================================================
              KPI CARDS
              ================================================== */}

          <section
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(3, 1fr)",
              gap: 14,
            }}
          >

            <div
              style={{
                background: "white",
                border:
                  "1px solid #dde5de",
                borderRadius: 14,
                padding: 18,
              }}
            >
              <span
                style={{
                  display: "block",
                  color: "#727b74",
                  fontSize: 12,
                }}
              >
                Current score
              </span>

              <strong
                style={{
                  display: "block",
                  marginTop: 7,
                  fontSize: 28,
                }}
              >
                {history.current_score}
                /100
              </strong>
            </div>


            <div
              style={{
                background: "white",
                border:
                  "1px solid #dde5de",
                borderRadius: 14,
                padding: 18,
              }}
            >
              <span
                style={{
                  display: "block",
                  color: "#727b74",
                  fontSize: 12,
                }}
              >
                Score change
              </span>

              <strong
                style={{
                  display: "block",
                  marginTop: 7,
                  fontSize: 28,
                }}
              >
                {history.score_change > 0
                  ? "+"
                  : ""}
                {history.score_change}
              </strong>
            </div>


            <div
              style={{
                background: "white",
                border:
                  "1px solid #dde5de",
                borderRadius: 14,
                padding: 18,
              }}
            >
              <span
                style={{
                  display: "block",
                  color: "#727b74",
                  fontSize: 12,
                }}
              >
                Audit period
              </span>

              <strong
                style={{
                  display: "block",
                  marginTop: 7,
                  fontSize: 28,
                }}
              >
                {history.period_days}
                <span
                  style={{
                    fontSize: 14,
                    color: "#727b74",
                  }}
                >
                  {" "}days
                </span>
              </strong>
            </div>

          </section>


          {/* ==================================================
              TREND CHART
              ================================================== */}

          <section
            style={{
              background: "white",
              border:
                "1px solid #dde5de",
              borderRadius: 16,
              padding: 22,
            }}
          >

            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems:
                  "center",
                gap: 15,
                marginBottom: 18,
              }}
            >

              <div>

                <h3
                  style={{
                    margin: 0,
                  }}
                >
                  Compliance trend
                </h3>

                <p
                  style={{
                    margin:
                      "5px 0 0",
                    color: "#727b74",
                    fontSize: 13,
                  }}
                >
                  Period-by-period compliance
                  score based on recorded alerts
                  and investigations.
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
                  width: "100%",
                  overflowX: "auto",
                }}
              >

                <svg
                  viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                  width="100%"
                  height="300"
                  role="img"
                  aria-label="Compliance score trend"
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
                            x="6"
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


                  {/* LINE */}

                  <polyline
                    points={polyline}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="4"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />


                  {/* POINTS */}

                  {points.map(
                    (point, index) => (

                      <g
                        key={`${point.label}-${index}`}
                      >

                        <circle
                          cx={point.x}
                          cy={point.y}
                          r="7"
                          fill="white"
                          stroke="currentColor"
                          strokeWidth="3"
                        />

                        <text
                          x={point.x}
                          y={
                            point.y - 14
                          }
                          textAnchor="middle"
                          fontSize="11"
                          fontWeight="700"
                          fill="currentColor"
                        >
                          {point.score}
                        </text>

                        <text
                          x={point.x}
                          y={
                            chartHeight -
                            14
                          }
                          textAnchor="middle"
                          fontSize="10"
                          fill="#7a837c"
                        >
                          {point.label}
                        </text>

                      </g>

                    )
                  )}

                </svg>

              </div>

            ) : (

              <div
                style={{
                  padding: 40,
                  textAlign: "center",
                  color: "#727b74",
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
              background: "white",
              border:
                "1px solid #dde5de",
              borderRadius: 16,
              padding: 22,
            }}
          >

            <h3
              style={{
                margin:
                  "0 0 16px",
              }}
            >
              Period details
            </h3>

            <div
              style={{
                overflowX:
                  "auto",
              }}
            >

              <table
                style={{
                  width: "100%",
                  borderCollapse:
                    "collapse",
                }}
              >

                <thead>

                  <tr>

                    <th
                      style={{
                        textAlign: "left",
                        padding: 11,
                        borderBottom:
                          "1px solid #e6ebe7",
                        fontSize: 11,
                        color: "#717a73",
                        textTransform:
                          "uppercase",
                      }}
                    >
                      Period
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: 11,
                        borderBottom:
                          "1px solid #e6ebe7",
                        fontSize: 11,
                        color: "#717a73",
                        textTransform:
                          "uppercase",
                      }}
                    >
                      Score
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: 11,
                        borderBottom:
                          "1px solid #e6ebe7",
                        fontSize: 11,
                        color: "#717a73",
                        textTransform:
                          "uppercase",
                      }}
                    >
                      Alerts
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: 11,
                        borderBottom:
                          "1px solid #e6ebe7",
                        fontSize: 11,
                        color: "#717a73",
                        textTransform:
                          "uppercase",
                      }}
                    >
                      RED
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: 11,
                        borderBottom:
                          "1px solid #e6ebe7",
                        fontSize: 11,
                        color: "#717a73",
                        textTransform:
                          "uppercase",
                      }}
                    >
                      Investigations
                    </th>

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
                            padding: 12,
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {formatDate(
                            point.period_start
                          )}
                          {" → "}
                          {formatDate(
                            point.period_end
                          )}
                        </td>

                        <td
                          style={{
                            padding: 12,
                            borderBottom:
                              "1px solid #eef1ee",
                            fontWeight: 800,
                          }}
                        >
                          {point.score}
                        </td>

                        <td
                          style={{
                            padding: 12,
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {point.alerts}
                        </td>

                        <td
                          style={{
                            padding: 12,
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {point.active_red}
                        </td>

                        <td
                          style={{
                            padding: 12,
                            borderBottom:
                              "1px solid #eef1ee",
                          }}
                        >
                          {point.investigations}
                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          </section>


          {/* ==================================================
              INTERPRETATION
              ================================================== */}

          <section
            style={{
              background: "white",
              border:
                "1px solid #dde5de",
              borderRadius: 16,
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
                lineHeight: 1.6,
                color: "#68716b",
              }}
            >
              {history.trend ===
              "DETERIORATING"
                ? `The outlet's compliance score has changed by ${history.score_change} points during the selected period. This should be considered together with current alerts, investigations, AI findings, and government review.`
                : history.trend ===
                    "IMPROVING"
                  ? `The outlet's compliance score has improved by ${history.score_change} points during the selected period. Continued monitoring is recommended to confirm that the improvement is sustained.`
                  : "The recorded compliance indicators have not changed enough to classify the outlet as clearly improving or deteriorating."
              }
            </p>

          </section>

        </>

      )}

    </div>
  );
}