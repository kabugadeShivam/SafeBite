import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";


/* ============================================================
   STATUS HELPERS
   ============================================================ */

function statusClass(status) {
  switch (status) {
    case "EXCELLENT":
      return "public-status excellent";

    case "COMPLIANT":
      return "public-status compliant";

    case "WATCHLIST":
      return "public-status watchlist";

    case "WARNING":
      return "public-status warning";

    case "CRITICAL":
      return "public-status critical";

    default:
      return "public-status";
  }
}


function statusLabel(status) {
  switch (status) {
    case "EXCELLENT":
      return "EXCELLENT";

    case "COMPLIANT":
      return "GOOD";

    case "WATCHLIST":
      return "UNDER MONITORING";

    case "WARNING":
      return "NEEDS ATTENTION";

    case "CRITICAL":
      return "CRITICAL";

    default:
      return "STATUS UNAVAILABLE";
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

  return date.toLocaleString(
    "en-IN"
  );
}


function decisionLabel(decision) {
  switch (
    String(
      decision || ""
    ).toUpperCase()
  ) {
    case "APPROVE":
      return "VERIFIED";

    case "VERIFIED":
      return "VERIFIED";

    case "REJECT":
      return "NOT VERIFIED";

    case "DISMISSED":
      return "DISMISSED";

    default:
      return String(
        decision || "NOT AVAILABLE"
      ).replaceAll(
        "_",
        " "
      );
  }
}


/* ============================================================
   PUBLIC OUTLET PAGE
   ============================================================ */

export default function PublicOutlet() {

  const { registrationId } =
    useParams();

  const [data, setData] =
    useState(null);

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(true);


  /* ==========================================================
     LOAD OFFICIAL OUTLET DATA
     ========================================================== */

  useEffect(() => {

    let active = true;

    setLoading(true);
    setError("");
    setData(null);

    api.publicOutlet(
      registrationId
    )
      .then((response) => {

        if (active) {
          setData(response);
        }

      })
      .catch((err) => {

        if (active) {

          setError(
            err.message ||
              "Unable to load official outlet information."
          );

        }

      })
      .finally(() => {

        if (active) {
          setLoading(false);
        }

      });

    return () => {
      active = false;
    };

  }, [registrationId]);


  /* ==========================================================
     LOADING
     ========================================================== */

  if (loading) {

    return (
      <div className="public-page">

        <div className="public-card public-loading">

          <div className="public-logo">
            SB
          </div>

          <h1>
            SafeBite
          </h1>

          <p>
            Loading official government status...
          </p>

        </div>

      </div>
    );

  }


  /* ==========================================================
     ERROR
     ========================================================== */

  if (error || !data) {

    return (
      <div className="public-page">

        <div className="public-card public-error-card">

          <div className="public-logo">
            SB
          </div>

          <h1>
            SafeBite
          </h1>

          <p>
            {
              error ||
              "Official outlet information is unavailable."
            }
          </p>

          <small>
            Please check the registration ID
            or try again later.
          </small>

        </div>

      </div>
    );

  }


  /* ==========================================================
     SAFE DATA EXTRACTION
     ========================================================== */

  const outlet =
    data.outlet || {};

  const officialStatus =
    data.official_status || {};

  const summary =
    data.public_summary || {};


  const score =
    Number(
      officialStatus.compliance_score ?? 0
    );


  const status =
    officialStatus.status ||
    "UNKNOWN";


  const strengths =
    Array.isArray(
      summary.strengths
    )
      ? summary.strengths
      : [];


  const concerns =
    Array.isArray(
      summary.concerns
    )
      ? summary.concerns
      : [];


  /*
   * The backend may expose the latest verified
   * investigation under one of these names.
   *
   * We only display it when real data exists.
   */

  const verifiedOutcome =
    data.latest_verified_outcome ||
    data.verified_investigation ||
    data.latest_investigation ||
    officialStatus.latest_verified_outcome ||
    null;


  const hasVerifiedOutcome =
    Boolean(
      verifiedOutcome &&
      (
        verifiedOutcome.decision ||
        verifiedOutcome.status ||
        verifiedOutcome.verified_at ||
        verifiedOutcome.remarks
      )
    );


  return (
    <div className="public-page">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <header className="public-header">

        <div className="public-brand">

          <div className="public-logo">
            SB
          </div>

          <div>

            <strong>
              SafeBite
            </strong>

            <span>
              Government Food Safety Platform
            </span>

          </div>

        </div>


        <div className="government-badge">
          GOVERNMENT VERIFIED
        </div>

      </header>


      {/* ======================================================
          MAIN
          ====================================================== */}

      <main className="public-container">

        {/* ====================================================
            HERO
            ==================================================== */}

        <section className="public-card public-hero">

          <div className="public-eyebrow">
            OFFICIAL OUTLET STATUS
          </div>

          <h1>
            {
              outlet.name ||
              "Registered Food Outlet"
            }
          </h1>

          <p className="public-location">
            {
              outlet.location ||
              outlet.region ||
              "Registered establishment"
            }
          </p>


          {/* SCORE */}

          <div
            className={statusClass(
              status
            )}
          >

            <div className="public-score">

              {Math.round(score)}

              <span>
                /100
              </span>

            </div>


            <div>

              <strong>
                {
                  statusLabel(
                    status
                  )
                }
              </strong>

              <small>
                Current government compliance status
              </small>

            </div>

          </div>


          {/* GOVERNMENT CONTROLLED NOTICE */}

          <div className="public-government-note">

            This information is published by the
            SafeBite government platform.

            <br />

            Outlet owners cannot edit the official
            compliance status shown here.

          </div>

        </section>


        {/* ====================================================
            OFFICIAL VERIFICATION OUTCOME
            ==================================================== */}

        {hasVerifiedOutcome && (

          <section className="public-card">

            <div className="public-eyebrow">
              OFFICIAL INVESTIGATION OUTCOME
            </div>

            <h2>
              Government verification
            </h2>

            <div
              className="public-list"
              style={{
                marginTop:
                  "15px",
              }}
            >

              {verifiedOutcome.decision && (

                <div>

                  <span>
                    Decision
                  </span>

                  <strong>
                    {
                      decisionLabel(
                        verifiedOutcome.decision
                      )
                    }
                  </strong>

                </div>

              )}


              {verifiedOutcome.status && (

                <div>

                  <span>
                    Investigation status
                  </span>

                  <strong>
                    {
                      String(
                        verifiedOutcome.status
                      ).replaceAll(
                        "_",
                        " "
                      )
                    }
                  </strong>

                </div>

              )}


              {verifiedOutcome.verified_at && (

                <div>

                  <span>
                    Verified at
                  </span>

                  <strong>
                    {
                      formatDate(
                        verifiedOutcome.verified_at
                      )
                    }
                  </strong>

                </div>

              )}

            </div>


            {verifiedOutcome.remarks && (

              <div
                className="public-government-note"
                style={{
                  marginTop:
                    "15px",
                }}
              >

                <strong>
                  Government remarks
                </strong>

                <br />

                {
                  verifiedOutcome.remarks
                }

              </div>

            )}

            <p
              className="public-muted"
              style={{
                marginTop:
                  "14px",
              }}
            >
              This outcome reflects an authorised
              government investigation and is separate
              from preliminary AI screening.
            </p>

          </section>

        )}


        {/* ====================================================
            SAFETY OVERVIEW + OBSERVATIONS
            ==================================================== */}

        <section className="public-grid">

          {/* SAFETY OVERVIEW */}

          <div className="public-card">

            <h2>
              Safety overview
            </h2>

            <div className="public-list">

              <div>

                <span>
                  Government status
                </span>

                <strong>
                  {
                    statusLabel(
                      status
                    )
                  }
                </strong>

              </div>


              <div>

                <span>
                  Inspection priority
                </span>

                <strong>
                  {
                    officialStatus.inspection_priority ||
                    "Not available"
                  }
                </strong>

              </div>


              <div>

                <span>
                  Registration ID
                </span>

                <strong>
                  {
                    outlet.registration_id ||
                    registrationId
                  }
                </strong>

              </div>


              <div>

                <span>
                  Last verified
                </span>

                <strong>
                  {
                    formatDate(
                      officialStatus.generated_at
                    )
                  }
                </strong>

              </div>

            </div>

          </div>


          {/* GOVERNMENT OBSERVATIONS */}

          <div className="public-card">

            <h2>
              Government observations
            </h2>


            {strengths.length > 0 && (

              <>

                <h3 className="public-subheading positive">
                  Positive findings
                </h3>

                <ul className="public-bullets">

                  {strengths.map(
                    (
                      item,
                      index
                    ) => (

                      <li
                        key={
                          `strength-${index}`
                        }
                      >
                        ✓ {item}
                      </li>

                    )
                  )}

                </ul>

              </>

            )}


            {concerns.length > 0 && (

              <>

                <h3 className="public-subheading concern">
                  Areas requiring attention
                </h3>

                <ul className="public-bullets">

                  {concerns.map(
                    (
                      item,
                      index
                    ) => (

                      <li
                        key={
                          `concern-${index}`
                        }
                      >
                        ⚠ {item}
                      </li>

                    )
                  )}

                </ul>

              </>

            )}


            {strengths.length === 0 &&
              concerns.length === 0 && (

                <p className="public-muted">
                  No additional public observations
                  are available.
                </p>

              )}

          </div>

        </section>


        {/* ====================================================
            RECOMMENDATION
            ==================================================== */}

        <section className="public-card public-recommendation">

          <div>

            <div className="public-eyebrow">
              GOVERNMENT RECOMMENDATION
            </div>

            <p>
              {
                summary.recommendation ||
                "Continue monitoring official food-safety status."
              }
            </p>

          </div>


          <Link
            className="public-report-button"
            to={`/public/outlet/${encodeURIComponent(
              registrationId
            )}/report`}
          >
            🚨 Report a Food-Safety Concern
          </Link>

        </section>


        {/* ====================================================
            PUBLIC VERIFICATION
            ==================================================== */}

        <section className="public-card public-verification">

          <div>

            <span>
              Official source
            </span>

            <strong>
              {
                data.source ||
                "SafeBite Government Platform"
              }
            </strong>

          </div>


          <div>

            <span>
              Outlet registration
            </span>

            <strong>
              {
                outlet.registration_id ||
                registrationId
              }
            </strong>

          </div>


          <div className="public-readonly">
            ✓ Government-controlled information
          </div>

        </section>


        {/* ====================================================
            CITIZEN REPORTING
            ==================================================== */}

        <section className="public-card">

          <div className="public-eyebrow">
            CITIZEN SAFETY REPORTING
          </div>

          <h2>
            See something unsafe?
          </h2>

          <p className="public-government-note">
            Customers can submit a photo or video
            describing a food-safety concern. SafeBite
            may use AI to screen the evidence before a
            government officer reviews it.
          </p>

          <div
            style={{
              display:
                "flex",
              gap:
                "10px",
              flexWrap:
                "wrap",
              marginTop:
                "18px",
            }}
          >

            <Link
              className="public-report-button"
              to={`/public/outlet/${encodeURIComponent(
                registrationId
              )}/report`}
            >
              Submit a Concern
            </Link>

          </div>

        </section>

      </main>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="public-footer">

        SafeBite • Official public food-safety information

      </footer>

    </div>
  );
}