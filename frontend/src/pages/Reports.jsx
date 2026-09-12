import { useEffect, useState } from "react";
import { api } from "../api";


function Stat({ label, value, hint }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}


function statusClass(status) {
  switch (
    String(status || "").toUpperCase()
  ) {
    case "VERIFIED":
      return "badge success";

    case "NEEDS_INVESTIGATION":
      return "badge warning";

    case "DISMISSED":
      return "badge neutral";

    case "SUBMITTED":
      return "badge amber";

    default:
      return "badge neutral";
  }
}


function severityClass(severity) {
  switch (
    String(severity || "").toUpperCase()
  ) {
    case "CRITICAL":
      return "badge danger";

    case "MODERATE":
      return "badge warning";

    case "LOW":
      return "badge amber";

    default:
      return "badge neutral";
  }
}


function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("en-IN");
}


function shortHash(value) {
  if (!value) {
    return "Unavailable";
  }

  if (value.length <= 22) {
    return value;
  }

  return `${value.slice(0, 16)}…`;
}


export default function Reports() {

  const [data, setData] =
    useState(null);

  const [selectedReport, setSelectedReport] =
    useState(null);

  const [evidenceUrl, setEvidenceUrl] =
    useState("");

  const [evidenceHash, setEvidenceHash] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [actionLoading, setActionLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");


  /* ==========================================================
     LOAD REPORTS
     ========================================================== */

  async function loadReports() {

    setRefreshing(true);
    setError("");

    try {

      const result =
        await api.citizenReports();

      setData(result);

    } catch (err) {

      setError(
        err.message ||
          "Unable to load citizen reports."
      );

    } finally {

      setLoading(false);
      setRefreshing(false);

    }
  }


  useEffect(() => {

    loadReports();

  }, []);


  /* ==========================================================
     OPEN REPORT
     ========================================================== */

  async function openReport(report) {

    setSelectedReport(
      report
    );

    setEvidenceUrl("");

    setEvidenceHash("");

    setMessage("");

    try {

      const result =
        await api.citizenReportMedia(
          report.id
        );

      const url =
        URL.createObjectURL(
          result.blob
        );

      setEvidenceUrl(
        url
      );

      setEvidenceHash(
        result.hash ||
          report.media_sha256 ||
          ""
      );

    } catch (err) {

      /*
       * Keep report details visible even if
       * the media itself cannot be loaded.
       */

      setError(
        err.message ||
          "Unable to load citizen evidence."
      );

    }
  }


  /* ==========================================================
     REVIEW REPORT
     ========================================================== */

  async function reviewReport(
    reportId,
    status
  ) {

    setActionLoading(
      true
    );

    setMessage("");

    setError("");

    try {

      const notes =
        status ===
        "VERIFIED"
          ? "Evidence reviewed and concern verified."
          : status ===
              "DISMISSED"
            ? "Evidence reviewed and report dismissed."
            : "Evidence requires official investigation.";

      await api.reviewCitizenReport(
        reportId,
        {
          status,
          notes,
        }
      );

      setMessage(
        `Report #${reportId} marked as ${status.replaceAll(
          "_",
          " "
        )}.`
      );

      await loadReports();

      /*
       * Refresh selected report after the review.
       */

      const refreshed =
        await api.citizenReports();

      const updated =
        refreshed.reports?.find(
          (item) =>
            item.id === reportId
        );

      if (updated) {

        setSelectedReport(
          updated
        );

      }

    } catch (err) {

      setError(
        err.message ||
          "Unable to review citizen report."
      );

    } finally {

      setActionLoading(
        false
      );

    }
  }


  /* ==========================================================
     CLEANUP MEDIA URL
     ========================================================== */

  useEffect(() => {

    return () => {

      if (evidenceUrl) {

        URL.revokeObjectURL(
          evidenceUrl
        );

      }

    };

  }, [evidenceUrl]);


  /* ==========================================================
     LOADING
     ========================================================== */

  if (
    loading &&
    !data
  ) {

    return (
      <div className="page">

        <div className="loading">
          Loading citizen reports…
        </div>

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
      <div className="page">

        <div className="error-box">

          {error}

          <button
            className="secondary-button"
            onClick={
              loadReports
            }
            style={{
              marginTop:
                "12px",
            }}
          >
            Retry
          </button>

        </div>

      </div>
    );

  }


  const reports =
    data?.reports || [];


  const verified =
    reports.filter(
      (report) =>
        String(
          report.status || ""
        ).toUpperCase()
        === "VERIFIED"
    ).length;


  const investigationRequired =
    reports.filter(
      (report) =>
        String(
          report.status || ""
        ).toUpperCase()
        === "NEEDS_INVESTIGATION"
    ).length;


  const pending =
    reports.filter(
      (report) => {

        const status =
          String(
            report.status || ""
          ).toUpperCase();

        return (
          status ===
            "SUBMITTED" ||
          status ===
            "UNDER_REVIEW"
        );

      }
    ).length;


  return (
    <div className="page">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <div className="page-head">

        <div>

          <div className="eyebrow">
            CITIZEN INTELLIGENCE
          </div>

          <h2>
            Food-safety reports
          </h2>

          <p
            style={{
              marginTop:
                "5px",
              color:
                "#68716b",
              fontSize:
                "13px",
            }}
          >
            Review citizen-submitted food-safety
            concerns, AI screening results and
            evidence integrity.
          </p>

        </div>


        <button
          className="secondary-button"
          onClick={
            loadReports
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


      {/* ======================================================
          MESSAGE
          ====================================================== */}

      {error && (

        <div
          className="error-box"
          style={{
            marginBottom:
              "14px",
          }}
        >
          {error}
        </div>

      )}


      {message && (

        <div
          className="success-box"
          style={{
            marginBottom:
              "14px",
          }}
        >
          {message}
        </div>

      )}


      {/* ======================================================
          SUMMARY
          ====================================================== */}

      <div className="stat-grid">

        <Stat
          label="Total reports"
          value={
            data?.count ??
            reports.length
          }
          hint="Citizen reports in your authorised region"
        />

        <Stat
          label="Pending review"
          value={pending}
          hint="Reports awaiting officer action"
        />

        <Stat
          label="Verified"
          value={verified}
          hint="Government-confirmed reports"
        />

        <Stat
          label="Needs investigation"
          value={investigationRequired}
          hint="Escalated for official investigation"
        />

      </div>


      {/* ======================================================
          REPORT QUEUE
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
              Citizen report queue
            </h3>

            <span>
              Select a report to review its evidence and
              AI screening.
            </span>

          </div>

        </div>


        <div className="table-wrap">

          {reports.length === 0 ? (

            <div
              style={{
                padding:
                  "45px",
                textAlign:
                  "center",
                color:
                  "#727b74",
              }}
            >
              No citizen reports available.
            </div>

          ) : (

            <table>

              <thead>

                <tr>

                  <th>
                    Report
                  </th>

                  <th>
                    Establishment
                  </th>

                  <th>
                    Concern
                  </th>

                  <th>
                    AI
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Submitted
                  </th>

                  <th>
                  </th>

                </tr>

              </thead>


              <tbody>

                {reports.map(
                  (report) => (

                    <tr
                      key={
                        report.id
                      }
                    >

                      <td>

                        <strong>
                          RPT-
                          {String(
                            report.id
                          ).padStart(
                            4,
                            "0"
                          )}
                        </strong>

                      </td>


                      <td>

                        <strong>
                          {
                            report.outlet
                              ?.name ||
                            "Unknown outlet"
                          }
                        </strong>

                        <small>
                          {
                            report.outlet
                              ?.registration_id ||
                            ""
                          }
                        </small>

                      </td>


                      <td>

                        <strong>
                          {
                            report.category ||
                            "Food-safety concern"
                          }
                        </strong>

                        <small>
                          {
                            report.description ||
                            "No description"
                          }
                        </small>

                      </td>


                      <td>

                        <span
                          className={
                            severityClass(
                              report.ai
                                ?.severity
                            )
                          }
                        >
                          {
                            report.ai
                              ?.severity ||
                            "UNKNOWN"
                          }
                        </span>

                        <small
                          style={{
                            display:
                              "block",
                            marginTop:
                              "4px",
                          }}
                        >
                          {
                            Math.round(
                              (
                                Number(
                                  report.ai
                                    ?.relevance
                                ) ||
                                0
                              ) *
                                100
                            )
                          }
                          % relevance
                        </small>

                      </td>


                      <td>

                        <span
                          className={
                            statusClass(
                              report.status
                            )
                          }
                        >
                          {String(
                            report.status ||
                              "UNKNOWN"
                          ).replaceAll(
                            "_",
                            " "
                          )}
                        </span>

                      </td>


                      <td>
                        {
                          formatDate(
                            report.submitted_at
                          )
                        }
                      </td>


                      <td>

                        <button
                          className="text-link"
                          onClick={() =>
                            openReport(
                              report
                            )
                          }
                        >
                          Review
                        </button>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          )}

        </div>

      </section>


      {/* ======================================================
          SELECTED REPORT
          ====================================================== */}

      {selectedReport && (

        <section
          className="section-card"
          style={{
            marginTop:
              "20px",
          }}
        >

          <div className="section-title">

            <div>

              <div className="eyebrow">
                REPORT #
                {selectedReport.id}
              </div>

              <h3>
                {
                  selectedReport.category ||
                  "Food-safety concern"
                }
              </h3>

              <span>
                {
                  selectedReport.outlet
                    ?.name ||
                  "Unknown outlet"
                }
                {" • "}
                {
                  selectedReport.outlet
                    ?.registration_id ||
                  ""
                }
              </span>

            </div>


            <button
              className="secondary-button"
              onClick={() =>
                setSelectedReport(
                  null
                )
              }
            >
              Close
            </button>

          </div>


          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "1fr 1fr",
              gap:
                "16px",
              marginTop:
                "16px",
            }}
          >

            {/* =================================================
                REPORT DETAILS
                ================================================= */}

            <div>

              <div
                style={{
                  padding:
                    "16px",
                  borderRadius:
                    "11px",
                  background:
                    "#f6f8f6",
                }}
              >

                <div
                  style={{
                    display:
                      "grid",
                    gap:
                      "10px",
                  }}
                >

                  <div>

                    <span>
                      Status
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          "4px",
                      }}
                    >
                      {
                        selectedReport.status
                          ?.replaceAll(
                            "_",
                            " "
                          )
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      Submitted
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          "4px",
                      }}
                    >
                      {
                        formatDate(
                          selectedReport.submitted_at
                        )
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      Citizen description
                    </span>

                    <p
                      className="muted"
                      style={{
                        margin:
                          "5px 0 0",
                        lineHeight:
                          1.5,
                      }}
                    >
                      {
                        selectedReport.description ||
                        "No description provided."
                      }
                    </p>

                  </div>

                </div>

              </div>


              {/* AI */}

              <div
                style={{
                  marginTop:
                    "14px",
                  padding:
                    "16px",
                  borderRadius:
                    "11px",
                  background:
                    "#f6f8f6",
                }}
              >

                <div className="eyebrow">
                  AI SCREENING
                </div>

                <div
                  style={{
                    display:
                      "grid",
                    gridTemplateColumns:
                      "1fr 1fr",
                    gap:
                      "10px",
                    marginTop:
                      "9px",
                  }}
                >

                  <div>

                    <span>
                      AI status
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          "4px",
                      }}
                    >
                      {
                        selectedReport
                          .ai
                          ?.status ||
                        "UNKNOWN"
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      Severity
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          "4px",
                      }}
                    >
                      {
                        selectedReport
                          .ai
                          ?.severity ||
                        "UNKNOWN"
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      Relevance
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          "4px",
                      }}
                    >
                      {
                        Math.round(
                          (
                            Number(
                              selectedReport
                                .ai
                                ?.relevance
                            ) ||
                            0
                          ) *
                            100
                        )
                      }
                      %
                    </strong>

                  </div>


                  <div>

                    <span>
                      Model
                    </span>

                    <strong
                      style={{
                        display:
                          "block",
                        marginTop:
                          "4px",
                        fontSize:
                          "12px",
                        wordBreak:
                          "break-all",
                      }}
                    >
                      {
                        selectedReport
                          .ai
                          ?.model ||
                        "Unavailable"
                      }
                    </strong>

                  </div>

                </div>


                <details
                  style={{
                    marginTop:
                      "14px",
                  }}
                >

                  <summary>
                    View AI detections
                  </summary>

                  <pre
                    style={{
                      marginTop:
                        "9px",
                      padding:
                        "10px",
                      background:
                        "white",
                      borderRadius:
                        "8px",
                      overflowX:
                        "auto",
                      fontSize:
                        "11px",
                    }}
                  >
                    {
                      JSON.stringify(
                        selectedReport
                          .ai
                          ?.findings ||
                        {},
                        null,
                        2
                      )
                    }
                  </pre>

                </details>

              </div>

            </div>


            {/* =================================================
                EVIDENCE
                ================================================= */}

            <div>

              <div className="eyebrow">
                CITIZEN EVIDENCE
              </div>

              <div
                style={{
                  marginTop:
                    "9px",
                  padding:
                    "14px",
                  borderRadius:
                    "11px",
                  background:
                    "#f6f8f6",
                }}
              >

                {evidenceUrl ? (

                  selectedReport
                    .original_filename
                    ?.match(
                      /\.(jpg|jpeg|png|webp|bmp)$/i
                    ) ? (

                    <img
                      src={
                        evidenceUrl
                      }
                      alt="Citizen evidence"
                      style={{
                        width:
                          "100%",
                        maxHeight:
                          "360px",
                        objectFit:
                          "contain",
                        borderRadius:
                          "8px",
                        background:
                          "#eef1ee",
                      }}
                    />

                  ) : (

                    <video
                      src={
                        evidenceUrl
                      }
                      controls
                      style={{
                        width:
                          "100%",
                        maxHeight:
                          "360px",
                        borderRadius:
                          "8px",
                        background:
                          "#111",
                      }}
                    />

                  )

                ) : (

                  <div
                    style={{
                      padding:
                        "35px 10px",
                      textAlign:
                        "center",
                      color:
                        "#727b74",
                    }}
                  >
                    Evidence not loaded.
                  </div>

                )}

              </div>


              {/* HASH */}

              <div
                style={{
                  marginTop:
                    "12px",
                  padding:
                    "13px",
                  borderRadius:
                    "10px",
                  background:
                    "#f6f8f6",
                }}
              >

                <span>
                  SHA-256 evidence hash
                </span>

                <code
                  style={{
                    display:
                      "block",
                    marginTop:
                      "6px",
                    wordBreak:
                      "break-all",
                    fontSize:
                      "11px",
                  }}
                >
                  {
                    evidenceHash ||
                    selectedReport.media_sha256 ||
                    "Unavailable"
                  }
                </code>

              </div>

            </div>

          </div>


          {/* =================================================
              REVIEW ACTIONS
              ================================================= */}

          <div
            style={{
              marginTop:
                "18px",
              paddingTop:
                "18px",
              borderTop:
                "1px solid #e1e7e2",
            }}
          >

            <div className="eyebrow">
              GOVERNMENT REVIEW
            </div>

            <p
              className="muted"
              style={{
                margin:
                  "5px 0 12px",
              }}
            >
              Citizen evidence and AI screening support
              the review. The authorised government officer
              makes the official determination.
            </p>


            <div
              style={{
                display:
                  "flex",
                gap:
                  "9px",
                flexWrap:
                  "wrap",
              }}
            >

              <button
                className="primary-button"
                disabled={
                  actionLoading ||
                  String(
                    selectedReport.status ||
                      ""
                  ).toUpperCase()
                  === "VERIFIED"
                }
                onClick={() =>
                  reviewReport(
                    selectedReport.id,
                    "VERIFIED"
                  )
                }
              >
                {actionLoading
                  ? "Saving..."
                  : "Verify report"}
              </button>


              <button
                className="secondary-button"
                disabled={
                  actionLoading ||
                  String(
                    selectedReport.status ||
                      ""
                  ).toUpperCase()
                  === "NEEDS_INVESTIGATION"
                }
                onClick={() =>
                  reviewReport(
                    selectedReport.id,
                    "NEEDS_INVESTIGATION"
                  )
                }
              >
                Send to investigation
              </button>


              <button
                className="secondary-button"
                disabled={
                  actionLoading ||
                  String(
                    selectedReport.status ||
                      ""
                  ).toUpperCase()
                  === "DISMISSED"
                }
                onClick={() =>
                  reviewReport(
                    selectedReport.id,
                    "DISMISSED"
                  )
                }
              >
                Dismiss
              </button>

            </div>

          </div>


          {/* =================================================
              REVIEW INFORMATION
              ================================================= */}

          {(selectedReport.reviewed_at ||
            selectedReport.review_notes) && (

            <div
              style={{
                marginTop:
                  "14px",
                padding:
                  "14px",
                borderRadius:
                  "10px",
                background:
                  "#f5f7f5",
              }}
            >

              <strong>
                Previous government review
              </strong>

              <p
                className="muted"
                style={{
                  margin:
                    "5px 0",
                }}
              >
                Reviewed:{" "}
                {
                  formatDate(
                    selectedReport.reviewed_at
                  )
                }
              </p>

              <p
                className="muted"
                style={{
                  margin:
                    0,
                }}
              >
                {
                  selectedReport.review_notes ||
                  "No review notes recorded."
                }
              </p>

            </div>

          )}

        </section>

      )}


      {/* ======================================================
          PRINCIPLE
          ====================================================== */}

      <section
        className="section-card compact"
        style={{
          marginTop:
            "20px",
        }}
      >

        <h3>
          Evidence principle
        </h3>

        <p className="muted">
          SafeBite treats citizen submissions as supporting
          evidence. AI screening assists prioritisation,
          while the authorised government officer makes the
          official determination.
        </p>

      </section>

    </div>
  );
}