import { useEffect, useState } from "react";

import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { api } from "./api";

import Dashboard from "./pages/Dashboard";
import Alerts from "./pages/Alerts";
import AlertDetails from "./pages/AlertDetails";
import Investigations from "./pages/Investigations";
import InvestigationDetails from "./pages/InvestigationDetails";
import Establishments from "./pages/Establishments";
import Login from "./pages/Login";
import Reports from "./pages/Reports";
import AuditHistory from "./pages/AuditHistory";
import CommandCenter from "./pages/CommandCenter";
import ActionQueue from "./pages/ActionQueue";

import PublicOutlet from "./pages/PublicOutlet";
import PublicCitizenReport from "./pages/PublicCitizenReport";
import PublicReportStatus from "./pages/PublicReportStatus";


/* ============================================================
   PROTECTED GOVERNMENT LAYOUT
   ============================================================ */

function ProtectedLayout() {

  const [me, setMe] =
    useState(null);

  const navigate =
    useNavigate();

  const location =
    useLocation();


  /* ==========================================================
     LOAD OFFICER
     ========================================================== */

  useEffect(() => {

    api.me()
      .then(setMe)
      .catch(() => {

        localStorage.removeItem(
          "safebite_token"
        );

        localStorage.removeItem(
          "safebite_officer"
        );

        navigate(
          "/login",
          {
            replace: true,
          }
        );

      });

  }, [navigate]);


  /* ==========================================================
     AUTH
     ========================================================== */

  if (
    !localStorage.getItem(
      "safebite_token"
    )
  ) {

    return (
      <Navigate
        to="/login"
        replace
      />
    );

  }


  /* ==========================================================
     LOADING
     ========================================================== */

  if (!me) {

    return (
      <div className="loading-screen">
        Loading SafeBite...
      </div>
    );

  }


  /* ==========================================================
     LOGOUT
     ========================================================== */

  const logout = () => {

    localStorage.removeItem(
      "safebite_token"
    );

    localStorage.removeItem(
      "safebite_officer"
    );

    navigate(
      "/login",
      {
        replace: true,
      }
    );

  };


  return (

    <div className="app-shell">

      {/* ======================================================
          SIDEBAR
          ====================================================== */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">
            SB
          </div>

          <div>

            <strong>
              SafeBite
            </strong>

            <span>
              Government Portal
            </span>

          </div>

        </div>


        {/* ====================================================
            NAVIGATION
            ==================================================== */

        <nav>

          <Link
            className={
              location.pathname === "/"
                ? "nav-item active"
                : "nav-item"
            }
            to="/"
          >
            Overview
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/command-center"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/command-center"
          >
            Command Center
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/action-queue"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/action-queue"
          >
            Action Queue
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/alerts"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/alerts"
          >
            Alerts
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/investigations"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/investigations"
          >
            Investigations
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/establishments"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/establishments"
          >
            Establishments
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/reports"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/reports"
          >
            Reports
          </Link>


          <Link
            className={
              location.pathname.startsWith(
                "/audit-history"
              )
                ? "nav-item active"
                : "nav-item"
            }
            to="/audit-history"
          >
            Audit History
          </Link>

        </nav>


        {/* ====================================================
            SIDEBAR BOTTOM
            ==================================================== */

        <div className="sidebar-bottom">

          <div className="region-card">

            <small>
              AUTHORISED REGION
            </small>

            <strong>
              {
                me.role ===
                "CENTRAL_ADMIN"
                  ? "National / Central"
                  : me.region
              }
            </strong>

            <span>
              {me.state}
            </span>

          </div>


          <button
            className="secondary-button full"
            onClick={logout}
          >
            Logout
          </button>

        </div>

      </aside>


      {/* ======================================================
          MAIN CONTENT
          ====================================================== */

      <main className="content">

        <header className="topbar">

          <div>

            <div className="eyebrow">
              FOOD SAFETY SURVEILLANCE
            </div>

            <h1>
              {
                me.role ===
                "CENTRAL_ADMIN"
                  ? "Central Monitoring"
                  : `${me.region} Monitoring`
              }
            </h1>

          </div>


          <div className="officer-pill">

            <div className="avatar">
              {
                me.name?.slice(
                  0,
                  1
                ) || "O"
              }
            </div>

            <div>

              <strong>
                {me.name}
              </strong>

              <span>
                {
                  me.role.replaceAll(
                    "_",
                    " "
                  )
                }
              </span>

            </div>

          </div>

        </header>


        {/* ====================================================
            GOVERNMENT ROUTES
            ==================================================== */

        <Routes>

          <Route
            path="/"
            element={
              <Dashboard />
            }
          />

          <Route
            path="/command-center"
            element={
              <CommandCenter />
            }
          />

          <Route
            path="/action-queue"
            element={
              <ActionQueue />
            }
          />

          <Route
            path="/alerts"
            element={
              <Alerts />
            }
          />

          <Route
            path="/alerts/:id"
            element={
              <AlertDetails />
            }
          />

          <Route
            path="/investigations"
            element={
              <Investigations />
            }
          />

          <Route
            path="/investigations/:id"
            element={
              <InvestigationDetails />
            }
          />

          <Route
            path="/establishments"
            element={
              <Establishments />
            }
          />

          <Route
            path="/reports"
            element={
              <Reports />
            }
          />

          <Route
            path="/audit-history"
            element={
              <AuditHistory />
            }
          />

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />

        </Routes>

      </main>

    </div>
  );
}


/* ============================================================
   PUBLIC + GOVERNMENT ROUTING
   ============================================================ */

export default function App() {

  return (

    <Routes>

      {/* ======================================================
          GOVERNMENT LOGIN
          ====================================================== */

      <Route
        path="/login"
        element={
          <Login />
        }
      />


      {/* ======================================================
          PUBLIC OUTLET
          ====================================================== */

      <Route
        path="/public/outlet/:registrationId"
        element={
          <PublicOutlet />
        }
      />


      {/* ======================================================
          PUBLIC CITIZEN REPORT
          ====================================================== */

      <Route
        path="/public/outlet/:registrationId/report"
        element={
          <PublicCitizenReport />
        }
      />


      {/* ======================================================
          PUBLIC REPORT STATUS
          ====================================================== */

      <Route
        path="/public/reports/:reportId"
        element={
          <PublicReportStatus />
        }
      />


      {/* ======================================================
          PROTECTED GOVERNMENT APPLICATION
          ====================================================== */

      <Route
        path="/*"
        element={
          <ProtectedLayout />
        }
      />

    </Routes>

  );
}
