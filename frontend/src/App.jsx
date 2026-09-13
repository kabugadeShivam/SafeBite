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
import ItemScanner from "./pages/ItemScanner";
import MonthlyNotices from "./pages/MonthlyNotices";

import PublicOutlet from "./pages/PublicOutlet";
import PublicCitizenReport from "./pages/PublicCitizenReport";
import PublicReportStatus from "./pages/PublicReportStatus";


function ProtectedLayout() {
  const [me, setMe] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    api.me()
      .then(setMe)
      .catch(() => {
        localStorage.removeItem("safebite_token");
        localStorage.removeItem("safebite_officer");
        navigate("/login", { replace: true });
      });
  }, [navigate]);

  if (!localStorage.getItem("safebite_token")) {
    return <Navigate to="/login" replace />;
  }

  if (!me) {
    return <div className="loading-screen">Loading SafeBite...</div>;
  }

  const logout = () => {
    localStorage.removeItem("safebite_token");
    localStorage.removeItem("safebite_officer");
    navigate("/login", { replace: true });
  };

  const isActive = (prefix) =>
    location.pathname === prefix || location.pathname.startsWith(`${prefix}/`);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SB</div>
          <div>
            <strong>SafeBite</strong>
            <span>Government Portal</span>
          </div>
        </div>

        <nav>
          <Link className={location.pathname === "/" ? "nav-item active" : "nav-item"} to="/">
            Overview
          </Link>
          <Link className={isActive("/command-center") ? "nav-item active" : "nav-item"} to="/command-center">
            Command Center
          </Link>
          <Link className={isActive("/action-queue") ? "nav-item active" : "nav-item"} to="/action-queue">
            Action Queue
          </Link>
          <Link className={isActive("/item-scanner") ? "nav-item active" : "nav-item"} to="/item-scanner">
            Item Scanner
          </Link>
          <Link className={isActive("/monthly-notices") ? "nav-item active" : "nav-item"} to="/monthly-notices">
            Monthly Notices
          </Link>
          <Link className={isActive("/alerts") ? "nav-item active" : "nav-item"} to="/alerts">
            Alerts
          </Link>
          <Link className={isActive("/investigations") ? "nav-item active" : "nav-item"} to="/investigations">
            Investigations
          </Link>
          <Link className={isActive("/establishments") ? "nav-item active" : "nav-item"} to="/establishments">
            Establishments
          </Link>
          <Link className={isActive("/reports") ? "nav-item active" : "nav-item"} to="/reports">
            Reports
          </Link>
          <Link className={isActive("/audit-history") ? "nav-item active" : "nav-item"} to="/audit-history">
            Audit History
          </Link>
        </nav>

        <div className="sidebar-bottom">
          <div className="region-card">
            <small>AUTHORISED REGION</small>
            <strong>{me.role === "CENTRAL_ADMIN" ? "National / Central" : me.region}</strong>
            <span>{me.state}</span>
          </div>
          <button className="secondary-button full" onClick={logout}>Logout</button>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <div className="eyebrow">FOOD SAFETY SURVEILLANCE</div>
            <h1>{me.role === "CENTRAL_ADMIN" ? "Central Monitoring" : `${me.region} Monitoring`}</h1>
          </div>
          <div className="officer-pill">
            <div className="avatar">{me.name?.slice(0, 1) || "O"}</div>
            <div>
              <strong>{me.name}</strong>
              <span>{me.role.replaceAll("_", " ")}</span>
            </div>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/command-center" element={<CommandCenter />} />
          <Route path="/action-queue" element={<ActionQueue />} />
          <Route path="/item-scanner" element={<ItemScanner />} />
          <Route path="/monthly-notices" element={<MonthlyNotices />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/alerts/:id" element={<AlertDetails />} />
          <Route path="/investigations" element={<Investigations />} />
          <Route path="/investigations/:id" element={<InvestigationDetails />} />
          <Route path="/establishments" element={<Establishments />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/audit-history" element={<AuditHistory />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}


export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/public/outlet/:registrationId" element={<PublicOutlet />} />
      <Route path="/public/outlet/:registrationId/report" element={<PublicCitizenReport />} />
      <Route path="/public/reports/:reportId" element={<PublicReportStatus />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  );
}
