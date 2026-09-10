import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

const CONCERNS = [
  "Poor personal hygiene",
  "Uncovered food",
  "Pests / insects",
  "Improper food storage",
  "Suspected spoiled food",
  "Expired product",
  "Dirty kitchen / equipment",
  "Other",
];

function formatPercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function severityClass(severity) {
  if (severity === "CRITICAL") {
    return "public-report-severity critical";
  }

  if (severity === "MODERATE") {
    return "public-report-severity moderate";
  }

  return "public-report-severity low";
}

export default function PublicCitizenReport() {
  const { registrationId } = useParams();

  const [outlet, setOutlet] = useState(null);
  const [loadingOutlet, setLoadingOutlet] = useState(true);

  const [concernCategory, setConcernCategory] = useState(
    "Poor personal hygiene"
  );

  const [description, setDescription] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(true);
  const [file, setFile] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // ==========================================================
  // LOAD OFFICIAL OUTLET
  // ==========================================================

  useEffect(() => {
    let active = true;

    setLoadingOutlet(true);
    setError("");

    api.publicOutlet(registrationId)
      .then((data) => {
        if (active) {
          setOutlet(data);
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err.message ||
              "Unable to load the official outlet."
          );
        }
      })
      .finally(() => {
        if (active) {
          setLoadingOutlet(false);
        }
      });

    return () => {
      active = false;
    };
  }, [registrationId]);

  // ==========================================================
  // FILE SELECTION
  // ==========================================================

  function handleFileChange(event) {
    const selected = event.target.files?.[0] || null;

    setError("");
    setResult(null);

    if (!selected) {
      setFile(null);
      return;
    }

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
      "image/bmp",
      "video/mp4",
      "video/quicktime",
      "video/x-msvideo",
      "video/webm",
    ];

    if (!allowedTypes.includes(selected.type)) {
      setError(
        "Please upload a JPG, PNG, WEBP, BMP, MP4, MOV, AVI, or WEBM file."
      );
      setFile(null);
      return;
    }

    const maxSize = selected.type.startsWith("video/")
      ? 50 * 1024 * 1024
      : 15 * 1024 * 1024;

    if (selected.size > maxSize) {
      setError(
        selected.type.startsWith("video/")
          ? "Video must be smaller than 50 MB."
          : "Image must be smaller than 15 MB."
      );
      setFile(null);
      return;
    }

    setFile(selected);
  }

  // ==========================================================
  // SUBMIT
  // ==========================================================

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setResult(null);

    if (!file) {
      setError(
        "Please upload a photo or video as evidence."
      );
      return;
    }

    if (!concernCategory) {
      setError(
        "Please select the type of concern."
      );
      return;
    }

    setSubmitting(true);

    try {
      const data = await api.submitCitizenReport({
        registrationId,
        concernCategory,
        description,
        isAnonymous,
        file,
      });

      setResult(data);

      setDescription("");
      setFile(null);

      const input =
        document.getElementById(
          "citizen-report-file"
        );

      if (input) {
        input.value = "";
      }
    } catch (err) {
      setError(
        err.message ||
          "Unable to submit the report."
      );
    } finally {
      setSubmitting(false);
    }
  }

  // ==========================================================
  // LOADING
  // ==========================================================

  if (loadingOutlet) {
    return (
      <div className="public-report-page">
        <div className="public-report-card public-report-loading">
          <div className="public-report-logo">
            SB
          </div>

          <h1>SafeBite</h1>

          <p>
            Loading official outlet information...
          </p>
        </div>
      </div>
    );
  }

  // ==========================================================
  // OUTLET NOT FOUND
  // ==========================================================

  if (!outlet) {
    return (
      <div className="public-report-page">
        <div className="public-report-card public-report-error-card">
          <div className="public-report-logo">
            SB
          </div>

          <h1>SafeBite</h1>

          <p>
            {error ||
              "The registered outlet could not be found."}
          </p>

          <Link
            className="public-report-secondary"
            to="/"
          >
            Return to SafeBite
          </Link>
        </div>
      </div>
    );
  }

  const outletInfo = outlet.outlet;

  // ==========================================================
  // SUCCESS SCREEN
  // ==========================================================

  if (result) {
    return (
      <div className="public-report-page">
        <header className="public-report-header">
          <div className="public-report-brand">
            <div className="public-report-logo">
              SB
            </div>

            <div>
              <strong>SafeBite</strong>
              <span>
                Government Food Safety Platform
              </span>
            </div>
          </div>

          <div className="public-report-official">
            OFFICIAL REPORTING CHANNEL
          </div>
        </header>

        <main className="public-report-container">
          <section className="public-report-card public-report-success">
            <div className="public-report-success-icon">
              ✓
            </div>

            <div className="public-report-eyebrow">
              REPORT RECEIVED
            </div>

            <h1>
              Thank you for reporting your concern.
            </h1>

            <p>
              Your report has been recorded for
              government review.
            </p>

            <div className="public-report-id">
              <span>Report ID</span>
              <strong>
                #{result.report_id}
              </strong>
            </div>

            <div className="public-report-result-grid">
              <div>
                <span>Outlet</span>
                <strong>
                  {result.outlet?.name ||
                    outletInfo.name}
                </strong>
              </div>

              <div>
                <span>AI screening</span>
                <strong>
                  {result.ai_triage?.status ||
                    "SUBMITTED"}
                </strong>
              </div>

              <div>
                <span>AI relevance</span>
                <strong>
                  {formatPercent(
                    result.ai_triage?.relevance
                  )}
                </strong>
              </div>

              <div>
                <span>AI severity</span>
                <strong
                  className={severityClass(
                    result.ai_triage?.severity
                  )}
                >
                  {result.ai_triage?.severity ||
                    "UNKNOWN"}
                </strong>
              </div>
            </div>

            <div className="public-report-info">
              <strong>
                Important
              </strong>

              <p>
                AI screening is preliminary. A
                government officer will determine
                whether the concern requires further
                action.
              </p>
            </div>

            <div className="public-report-actions">
              <Link
                className="public-report-primary"
                to={`/public/reports/${result.report_id}`}
              >
                Track Report
              </Link>

              <Link
                className="public-report-secondary"
                to={`/public/outlet/${registrationId}`}
              >
                Back to Outlet
              </Link>
            </div>
          </section>
        </main>
      </div>
    );
  }

  // ==========================================================
  // FORM
  // ==========================================================

  return (
    <div className="public-report-page">
      <header className="public-report-header">
        <div className="public-report-brand">
          <div className="public-report-logo">
            SB
          </div>

          <div>
            <strong>SafeBite</strong>

            <span>
              Government Food Safety Platform
            </span>
          </div>
        </div>

        <div className="public-report-official">
          OFFICIAL REPORTING CHANNEL
        </div>
      </header>

      <main className="public-report-container">

        {/* ====================================================
            OUTLET
            ==================================================== */}

        <section className="public-report-card public-report-outlet">

          <div className="public-report-eyebrow">
            REPORTING AGAINST
          </div>

          <h1>
            {outletInfo.name}
          </h1>

          <p>
            {outletInfo.location ||
              outletInfo.region}
          </p>

          <div className="public-report-registration">
            Registration ID:
            <strong>
              {outletInfo.registration_id}
            </strong>
          </div>

        </section>

        {/* ====================================================
            FORM
            ==================================================== */}

        <section className="public-report-card">

          <div className="public-report-eyebrow">
            CITIZEN REPORT
          </div>

          <h2>
            Report a Food-Safety Concern
          </h2>

          <p className="public-report-intro">
            Upload evidence of a food-safety concern
            observed at this outlet. SafeBite AI may
            screen the submission before government review.
          </p>

          {error && (
            <div className="public-report-error">
              {error}
            </div>
          )}

          <form
            className="public-report-form"
            onSubmit={handleSubmit}
          >

            {/* CATEGORY */}

            <div className="public-report-field">
              <label htmlFor="citizen-category">
                What did you observe?
              </label>

              <select
                id="citizen-category"
                value={concernCategory}
                onChange={(event) =>
                  setConcernCategory(
                    event.target.value
                  )
                }
                disabled={submitting}
              >
                {CONCERNS.map((concern) => (
                  <option
                    key={concern}
                    value={concern}
                  >
                    {concern}
                  </option>
                ))}
              </select>
            </div>

            {/* DESCRIPTION */}

            <div className="public-report-field">
              <label htmlFor="citizen-description">
                Describe the concern
              </label>

              <textarea
                id="citizen-description"
                rows="5"
                value={description}
                onChange={(event) =>
                  setDescription(
                    event.target.value
                  )
                }
                disabled={submitting}
                placeholder="Describe what you observed, where it happened, and anything else that may help an officer review the report."
              />
            </div>

            {/* MEDIA */}

            <div className="public-report-field">
              <label htmlFor="citizen-report-file">
                Photo or video evidence
              </label>

              <input
                id="citizen-report-file"
                type="file"
                accept="image/*,video/*"
                onChange={handleFileChange}
                disabled={submitting}
              />

              <small>
                Images up to 15 MB. Videos up to
                50 MB.
              </small>

              {file && (
                <div className="public-report-file">
                  <strong>
                    {file.name}
                  </strong>

                  <span>
                    {(file.size / 1024 / 1024).toFixed(2)}
                    {" MB"}
                  </span>
                </div>
              )}
            </div>

            {/* ANONYMOUS */}

            <label className="public-report-checkbox">
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(event) =>
                  setIsAnonymous(
                    event.target.checked
                  )
                }
                disabled={submitting}
              />

              <span>
                Submit anonymously
              </span>
            </label>

            {/* TRUST NOTICE */}

            <div className="public-report-trust">
              <strong>
                Government-controlled reporting
              </strong>

              <p>
                Your report is submitted to the
                SafeBite platform. The outlet cannot
                edit, remove, or suppress your report.
              </p>
            </div>

            {/* BUTTON */}

            <button
              type="submit"
              className="public-report-submit"
              disabled={
                submitting || !file
              }
            >
              {submitting
                ? "Submitting report..."
                : "Submit Food-Safety Report"}
            </button>

          </form>

        </section>

        {/* ====================================================
            OUTLET LINK
            ==================================================== */}

        <section className="public-report-back">
          <Link
            to={`/public/outlet/${registrationId}`}
          >
            ← Back to official outlet status
          </Link>
        </section>

      </main>

      <footer className="public-report-footer">
        SafeBite • Official public food-safety
        reporting platform
      </footer>
    </div>
  );
}