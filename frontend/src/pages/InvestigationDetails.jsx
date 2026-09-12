import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";


function formatStatus(status) {
  return String(
    status || "UNKNOWN"
  ).replaceAll(
    "_",
    " "
  );
}


function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString(
    "en-IN"
  );
}


function severityClass(severity) {
  switch (
    String(
      severity || ""
    ).toUpperCase()
  ) {
    case "RED":
      return "badge danger";

    case "ORANGE":
      return "badge warning";

    default:
      return "badge amber";
  }
}


function sourceClass(source) {
  switch (
    String(
      source || ""
    ).toUpperCase()
  ) {
    case "CITIZEN":
      return "badge warning";

    case "IOT":
      return "badge neutral";

    default:
      return "badge amber";
  }
}


function expiryStatusClass(status) {
  switch (
    String(
      status || ""
    ).toUpperCase()
  ) {
    case "EXPIRED":
      return "badge danger";

    case "EXPIRES_TODAY":
      return "badge warning";

    case "VALID":
      return "badge success";

    default:
      return "badge neutral";
  }
}


export default function InvestigationDetails() {

  const { id } = useParams();

  const [data, setData] =
    useState(null);

  const [citizenContext, setCitizenContext] =
    useState(null);

  const [citizenContextLoading, setCitizenContextLoading] =
    useState(false);

  const [audit, setAudit] =
    useState(null);

  const [findings, setFindings] =
    useState("");

  const [action, setAction] =
    useState("");

  const [corrective, setCorrective] =
    useState("");

  const [file, setFile] =
    useState(null);

  const [expiryFile, setExpiryFile] =
    useState(null);

  const [expiryResult, setExpiryResult] =
    useState(null);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [saving, setSaving] =
    useState(false);

  const [uploading, setUploading] =
    useState(false);

  const [analyzingExpiry, setAnalyzingExpiry] =
    useState(false);

  const [verifying, setVerifying] =
    useState(false);

  const [loadingAudit, setLoadingAudit] =
    useState(false);


  /* ==========================================================
     LOAD INVESTIGATION
     ========================================================== */

  async function load() {

    setError("");

    try {

      const result =
        await api.investigation(
          id
        );

      setData(result);

      setFindings(
        result.findings || ""
      );

      setAction(
        result.action_taken || ""
      );

      setCorrective(
        result.corrective_action || ""
      );

    } catch (err) {

      setError(
        err.message ||
          "Unable to load investigation."
      );

    }
  }


  useEffect(() => {

    load();

  }, [id]);


  /* ==========================================================
     LOAD CITIZEN CONTEXT
     ========================================================== */

  async function loadCitizenContext() {

    setCitizenContextLoading(
      true
    );

    try {

      const result =
        await api.investigationCitizenContext(
          id
        );

      setCitizenContext(
        result
      );

    } catch (err) {

      setCitizenContext({
        linked: false,

        message:
          err.message ||
          "Citizen context unavailable.",
      });

    } finally {

      setCitizenContextLoading(
        false
      );

    }
  }


  useEffect(() => {

    if (data) {
      loadCitizenContext();
    }

  }, [id, data?.id]);


  /* ==========================================================
     SAVE FINDINGS
     ========================================================== */

  async function save() {

    setSaving(true);
    setMessage("");
    setError("");

    try {

      await api.updateInvestigation(
        id,
        {
          findings,
          action_taken:
            action,
          corrective_action:
            corrective,
          status:
            "PENDING_VERIFICATION",
        }
      );

      setMessage(
        "Findings submitted for verification."
      );

      await load();

    } catch (err) {

      setError(
        err.message ||
          "Unable to save findings."
      );

    } finally {

      setSaving(false);

    }
  }


  /* ==========================================================
     UPLOAD INVESTIGATION EVIDENCE
     ========================================================== */

  async function upload() {

    if (!file) {

      setError(
        "Select an evidence file first."
      );

      return;
    }

    setUploading(true);
    setMessage("");
    setError("");

    try {

      await api.uploadEvidence(
        id,
        file
      );

      setMessage(
        "Evidence uploaded and hashed."
      );

      setFile(null);

      const input =
        document.getElementById(
          "investigation-evidence-file"
        );

      if (input) {
        input.value = "";
      }

      await load();

    } catch (err) {

      setError(
        err.message ||
          "Unable to upload evidence."
      );

    } finally {

      setUploading(false);

    }
  }


  /* ==========================================================
     EXPIRY OCR
     ========================================================== */

  async function analyzeExpiry() {

    if (!expiryFile) {

      setError(
        "Select a product-label image first."
      );

      return;
    }

    setAnalyzingExpiry(
      true
    );

    setMessage("");
    setError("");
    setExpiryResult(null);

    try {

      const response =
        await api.analyzeExpiry(
          expiryFile,
          id
        );

      setExpiryResult(
        response
      );

      const result =
        response?.result || {};

      const status =
        result.status ||
        "NOT_FOUND";

      if (
        status ===
        "EXPIRED"
      ) {

        setMessage(
          "Expiry OCR completed: product is expired."
        );

      } else if (
        status ===
        "EXPIRES_TODAY"
      ) {

        setMessage(
          "Expiry OCR completed: product expires today."
        );

      } else if (
        status ===
        "VALID"
      ) {

        setMessage(
          "Expiry OCR completed: product is currently valid."
        );

      } else {

        setMessage(
          "Expiry OCR completed, but no valid expiry date was detected."
        );

      }

      setExpiryFile(
        null
      );

      const input =
        document.getElementById(
          "expiry-ocr-file"
        );

      if (input) {
        input.value = "";
      }

    } catch (err) {

      setError(
        err.message ||
          "Unable to analyze product expiry."
      );

    } finally {

      setAnalyzingExpiry(
        false
      );

    }
  }


  /* ==========================================================
     VERIFY
     ========================================================== */

  async function verify() {

    setVerifying(true);
    setMessage("");
    setError("");

    try {

      await api.verifyInvestigation(
        id,
        {
          decision:
            "APPROVE",

          remarks:
            "Verified from SafeBite government portal.",
        }
      );

      setMessage(
        "Investigation verified and closed."
      );

      await load();

    } catch (err) {

      setError(
        err.message ||
          "Unable to verify investigation."
      );

    } finally {

      setVerifying(false);

    }
  }


  /* ==========================================================
     AUDIT
     ========================================================== */

  async function loadAudit() {

    setLoadingAudit(
      true
    );

    setError("");

    try {

      const result =
        await api.audit(
          id
        );

      setAudit(
        result
      );

    } catch (err) {

      setError(
        err.message ||
          "Unable to load audit information."
      );

    } finally {

      setLoadingAudit(
        false
      );

    }
  }


  /* ==========================================================
     LOADING
     ========================================================== */

  if (!data && !error) {

    return (
      <div className="loading">
        Loading case…
      </div>
    );

  }


  if (!data && error) {

    return (
      <div className="page">

        <div className="error-box">

          {error}

          <button
            className="secondary-button"
            onClick={
              load
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


  /* ==========================================================
     DATA
     ========================================================== */

  const alert =
    data.alert || {};

  const restaurant =
    alert.restaurant ||
    data.restaurant ||
    {};

  const evidence =
    Array.isArray(
      data.evidence
    )
      ? data.evidence
      : [];

  const investigationStatus =
    String(
      data.status ||
        ""
    ).toUpperCase();

  const source =
    alert.source ||
    citizenContext?.source ||
    "UNKNOWN";

  const canVerify =
    investigationStatus ===
    "PENDING_VERIFICATION";

  const expiry =
    expiryResult?.result ||
    null;


  return (
    <div className="page">

      {/* ======================================================
          BACK
          ====================================================== */}

      <Link
        to="/investigations"
        className="back-link"
      >
        ← Back to investigations
      </Link>


      {/* ======================================================
          HEADER
          ====================================================== */}

      <div className="detail-head">

        <div>

          <div className="eyebrow">
            INVESTIGATION #
            {String(id).padStart(
              4,
              "0"
            )}
          </div>

          <h2>
            {
              restaurant.name ||
              "Unknown establishment"
            }
          </h2>

          <p className="muted">
            Alert #
            {alert.id || "—"}
            {" • "}
            {alert.severity || "—"}
            {" • Risk "}
            {alert.risk_score ?? "—"}
            /100
          </p>

        </div>


        <div
          style={{
            display:
              "flex",
            gap:
              "8px",
            flexWrap:
              "wrap",
          }}
        >

          <span
            className={
              sourceClass(
                source
              )
            }
          >
            {source}
          </span>

          <span
            className={
              severityClass(
                alert.severity
              )
            }
          >
            {
              alert.severity ||
              "UNKNOWN"
            }
          </span>

          <span
            className="badge neutral large"
          >
            {formatStatus(
              data.status
            )}
          </span>

        </div>

      </div>


      {/* ======================================================
          MESSAGES
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
          CITIZEN REPORT LINK
          ====================================================== */}

      {citizenContext?.linked && (

        <section
          className="section-card"
          style={{
            marginBottom:
              "20px",
          }}
        >

          <div className="section-title">

            <div>

              <div className="eyebrow">
                CITIZEN-ORIGINATED CASE
              </div>

              <h3>
                Citizen Report #
                {
                  citizenContext
                    .citizen_report
                    ?.id
                }
              </h3>

              <span>
                This investigation was created from
                a government-reviewed citizen report.
              </span>

            </div>

            <Link
              to="/reports"
              className="text-link"
            >
              Open Citizen Reports →
            </Link>

          </div>


          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "repeat(4, 1fr)",
              gap:
                "12px",
              marginTop:
                "15px",
            }}
          >

            <div
              style={{
                padding:
                  "14px",
                background:
                  "#f5f7f5",
                borderRadius:
                  "10px",
              }}
            >

              <span>
                Concern
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "5px",
                }}
              >
                {
                  citizenContext
                    .citizen_report
                    ?.category ||
                  "—"
                }
              </strong>

            </div>


            <div
              style={{
                padding:
                  "14px",
                background:
                  "#f5f7f5",
                borderRadius:
                  "10px",
              }}
            >

              <span>
                Citizen status
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "5px",
                }}
              >
                {
                  citizenContext
                    .citizen_report
                    ?.status ||
                  "—"
                }
              </strong>

            </div>


            <div
              style={{
                padding:
                  "14px",
                background:
                  "#f5f7f5",
                borderRadius:
                  "10px",
              }}
            >

              <span>
                AI severity
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "5px",
                }}
              >
                {
                  citizenContext
                    .ai
                    ?.severity ||
                  "—"
                }
              </strong>

            </div>


            <div
              style={{
                padding:
                  "14px",
                background:
                  "#f5f7f5",
                borderRadius:
                  "10px",
              }}
            >

              <span>
                AI relevance
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "5px",
                }}
              >
                {Math.round(
                  (
                    Number(
                      citizenContext
                        .ai
                        ?.relevance
                    ) ||
                    0
                  ) *
                    100
                )}
                %
              </strong>

            </div>

          </div>


          <div
            style={{
              marginTop:
                "14px",
              padding:
                "15px",
              background:
                "#f8faf8",
              border:
                "1px solid #e1e7e2",
              borderRadius:
                "11px",
            }}
          >

            <strong>
              Citizen description
            </strong>

            <p
              className="muted"
              style={{
                margin:
                  "6px 0 0",
              }}
            >
              {
                citizenContext
                  .citizen_report
                  ?.description ||
                "No description provided."
              }
            </p>

          </div>

        </section>

      )}


      {citizenContextLoading && (

        <div
          style={{
            marginBottom:
              "20px",
            padding:
              "12px",
            borderRadius:
              "10px",
            background:
              "#f5f7f5",
            color:
              "#727b74",
            fontSize:
              "12px",
          }}
        >
          Loading citizen evidence context...
        </div>

      )}


      {/* ======================================================
          AI FINDINGS
          ====================================================== */}

      {citizenContext?.linked && (

        <section
          className="section-card"
          style={{
            marginBottom:
              "20px",
          }}
        >

          <div className="section-title">

            <div>

              <h3>
                AI screening evidence
              </h3>

              <span>
                AI supports the investigation; it
                does not make the government decision.
              </span>

            </div>

            <span className="badge amber">
              {
                citizenContext.ai
                  ?.status ||
                "UNKNOWN"
              }
            </span>

          </div>


          <div
            style={{
              marginTop:
                "14px",
              display:
                "grid",
              gridTemplateColumns:
                "1fr 1fr",
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
                Model
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "5px",
                }}
              >
                {
                  citizenContext.ai
                    ?.model ||
                  "SafeBite AI"
                }
              </strong>

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
                Evidence SHA-256
              </span>

              <code
                style={{
                  display:
                    "block",
                  marginTop:
                    "6px",
                  wordBreak:
                    "break-all",
                }}
              >
                {
                  citizenContext.evidence
                    ?.sha256 ||
                  "Unavailable"
                }
              </code>

            </div>

          </div>


          <pre
            style={{
              marginTop:
                "14px",
              padding:
                "15px",
              borderRadius:
                "11px",
              background:
                "#f7f9f7",
              overflowX:
                "auto",
              fontSize:
                "12px",
            }}
          >
            {
              JSON.stringify(
                citizenContext.ai
                  ?.findings ||
                  {},
                null,
                2
              )
            }
          </pre>

        </section>

      )}


      {/* ======================================================
          FINDINGS + EVIDENCE
          ====================================================== */}

      <div className="two-col">

        <section className="section-card">

          <h3>
            Findings & action
          </h3>

          <label
            style={{
              display:
                "block",
              marginTop:
                "15px",
            }}
          >

            <span>
              Inspection findings
            </span>

            <textarea
              rows="6"
              value={
                findings
              }
              onChange={(
                event
              ) =>
                setFindings(
                  event.target.value
                )
              }
              disabled={
                investigationStatus ===
                "CLOSED"
              }
            />

          </label>


          <label
            style={{
              display:
                "block",
              marginTop:
                "14px",
            }}
          >

            <span>
              Action taken
            </span>

            <textarea
              rows="5"
              value={
                action
              }
              onChange={(
                event
              ) =>
                setAction(
                  event.target.value
                )
              }
              disabled={
                investigationStatus ===
                "CLOSED"
              }
            />

          </label>


          <label
            style={{
              display:
                "block",
              marginTop:
                "14px",
            }}
          >

            <span>
              Corrective action / follow-up
            </span>

            <textarea
              rows="5"
              value={
                corrective
              }
              onChange={(
                event
              ) =>
                setCorrective(
                  event.target.value
                )
              }
              disabled={
                investigationStatus ===
                "CLOSED"
              }
            />

          </label>


          {investigationStatus !==
            "CLOSED" && (

            <button
              className="primary-button"
              onClick={
                save
              }
              disabled={
                saving
              }
              style={{
                marginTop:
                  "14px",
              }}
            >
              {saving
                ? "Submitting..."
                : "Submit for verification"}
            </button>

          )}

        </section>


        <section className="section-card">

          <h3>
            Investigation evidence
          </h3>

          <p className="muted">
            Upload additional evidence collected
            during the official investigation.
          </p>


          {investigationStatus !==
            "CLOSED" && (

            <div
              className="upload-box"
              style={{
                marginTop:
                  "14px",
              }}
            >

              <input
                id="investigation-evidence-file"
                type="file"
                onChange={(
                  event
                ) =>
                  setFile(
                    event.target.files?.[0] ||
                      null
                  )
                }
              />

              <button
                className="secondary-button"
                onClick={
                  upload
                }
                disabled={
                  uploading
                }
              >
                {uploading
                  ? "Uploading..."
                  : "Upload evidence"}
              </button>

            </div>

          )}


          <div
            style={{
              display:
                "grid",
              gap:
                "8px",
              marginTop:
                "16px",
            }}
          >

            {evidence.length === 0 ? (

              <div className="muted">
                No investigation evidence uploaded.
              </div>

            ) : (

              evidence.map(
                (item) => (

                  <div
                    className="evidence-row"
                    key={
                      item.id
                    }
                  >

                    <div>

                      <strong>
                        {
                          item.filename ||
                          item.original_filename ||
                          "Evidence"
                        }
                      </strong>

                      <span>
                        Uploaded{" "}
                        {
                          formatDate(
                            item.uploaded_at
                          )
                        }
                      </span>

                    </div>

                    <code>
                      {
                        item.sha256 ||
                        "Hash unavailable"
                      }
                    </code>

                  </div>

                )
              )

            )}

          </div>

        </section>

      </div>


      {/* ======================================================
          EXPIRY OCR
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
              Expiry OCR
            </h3>

            <span>
              Analyze a packaged-food label and record the
              expiry result against this investigation.
            </span>

          </div>

          {expiry?.status && (

            <span
              className={
                expiryStatusClass(
                  expiry.status
                )
              }
            >
              {
                formatStatus(
                  expiry.status
                )
              }
            </span>

          )}

        </div>


        {investigationStatus !==
          "CLOSED" && (

          <div
            className="upload-box"
            style={{
              marginTop:
                "15px",
            }}
          >

            <input
              id="expiry-ocr-file"
              type="file"
              accept=".jpg,.jpeg,.png,.webp,.bmp,image/*"
              onChange={(
                event
              ) =>
                setExpiryFile(
                  event.target.files?.[0] ||
                    null
                )
              }
            />

            <button
              className="secondary-button"
              onClick={
                analyzeExpiry
              }
              disabled={
                analyzingExpiry
              }
            >
              {analyzingExpiry
                ? "Analyzing..."
                : "Analyze expiry"}
            </button>

          </div>

        )}


        {expiryFile && (

          <div
            style={{
              marginTop:
                "10px",
              padding:
                "10px 12px",
              borderRadius:
                "9px",
              background:
                "#f5f7f5",
              fontSize:
                "12px",
            }}
          >

            Selected:
            {" "}
            <strong>
              {
                expiryFile.name
              }
            </strong>

          </div>

        )}


        {expiry && (

          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "repeat(3, 1fr)",
              gap:
                "12px",
              marginTop:
                "16px",
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
                Expiry date
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "6px",
                  fontSize:
                    "20px",
                }}
              >
                {
                  expiry.expiry_date ||
                  "Not found"
                }
              </strong>

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
                OCR status
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                  "6px",
                }}
              >
                {
                  expiry.status ||
                  "NOT_FOUND"
                }
              </strong>

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
                Days remaining
              </span>

              <strong
                style={{
                  display:
                    "block",
                  marginTop:
                    "6px",
                  fontSize:
                    "20px",
                }}
              >
                {
                  expiry.days_remaining ??
                  "—"
                }
              </strong>

            </div>

          </div>

        )}


        {expiry?.raw_match && (

          <div
            style={{
              marginTop:
                "12px",
              padding:
                "12px",
              borderRadius:
                "10px",
              background:
                "#f7f9f7",
            }}
          >

            <span>
              OCR match
            </span>

            <code
              style={{
                display:
                  "block",
                marginTop:
                  "5px",
              }}
            >
              {
                expiry.raw_match
              }
            </code>

          </div>

        )}


        {expiry?.ocr_text && (

          <details
            style={{
              marginTop:
                "12px",
            }}
          >

            <summary>
              View OCR text
            </summary>

            <pre
              style={{
                marginTop:
                  "8px",
                padding:
                  "12px",
                background:
                  "#f5f7f5",
                borderRadius:
                  "9px",
                whiteSpace:
                  "pre-wrap",
                fontSize:
                  "11px",
              }}
            >
              {
                expiry.ocr_text
              }
            </pre>

          </details>

        )}


        {expiryResult?.stored_detection && (

          <div
            className="success-box"
            style={{
              marginTop:
                "14px",
            }}
          >

            Expiry result stored in SafeBite AI evidence for
            this outlet.

          </div>

        )}

      </section>


      {/* ======================================================
          VERIFICATION
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
              Government verification
            </h3>

            <span>
              Final approval records the official decision.
            </span>

          </div>

          <span className="badge neutral large">
            {formatStatus(
              data.status
            )}
          </span>

        </div>


        <p
          className="muted"
          style={{
            marginTop:
              "14px",
          }}
        >
          Citizen reports, AI screening and Expiry OCR are
          supporting evidence. The authorised government
          officer determines the final case outcome.
        </p>


        <button
          className="primary-button"
          disabled={
            !canVerify ||
            verifying
          }
          onClick={
            verify
          }
          style={{
            marginTop:
              "12px",
          }}
        >
          {verifying
            ? "Verifying..."
            : "Verify & close case"}
        </button>


        {!canVerify && (

          <small
            style={{
              display:
                "block",
              marginTop:
                "8px",
              color:
                "#727b74",
            }}
          >
            Case must be in PENDING VERIFICATION
            status before closing.
          </small>

        )}

      </section>


      {/* ======================================================
          AUDIT / BLOCKCHAIN
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
              Audit / blockchain layer
            </h3>

            <span>
              Investigation events and hash integrity.
            </span>

          </div>

          <button
            className="secondary-button"
            onClick={
              loadAudit
            }
            disabled={
              loadingAudit
            }
          >
            {loadingAudit
              ? "Loading..."
              : "Load audit"}
          </button>

        </div>


        {audit && (

          <div
            style={{
              marginTop:
                "15px",
            }}
          >

            <div
              className={
                audit.chain_verified
                  ? "success-box"
                  : "error-box"
              }
            >
              {
                audit.chain_message
              }
            </div>


            {Array.isArray(
              audit.records
            ) &&
              audit.records.length > 0 && (

                <div
                  className="audit-list"
                  style={{
                    marginTop:
                      "14px",
                  }}
                >

                  {audit.records.map(
                    (record) => (

                      <div
                        className="audit-item"
                        key={
                          record.id
                        }
                      >

                        <div>

                          <strong>
                            {formatStatus(
                              record.record_type
                            )}
                          </strong>

                          <span>
                            {formatDate(
                              record.timestamp
                            )}
                          </span>

                        </div>

                        <code>
                          {
                            record.record_hash
                          }
                        </code>

                      </div>

                    )
                  )}

                </div>

              )}

          </div>

        )}


        {!audit && (

          <div
            className="muted"
            style={{
              marginTop:
                "14px",
            }}
          >
            Load the audit trail to inspect
            the investigation's hash chain.
          </div>

        )}

      </section>


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
          SafeBite decision principle
        </h3>

        <p className="muted">
          Sensors create signals. Citizens provide evidence.
          AI and OCR assist screening. Government investigation
          establishes facts, and government verification produces
          the official decision.
        </p>

      </section>

    </div>
  );
}