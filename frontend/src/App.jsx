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
import "./dashboard-clean.css";

import Dashboard from "./pages/DashboardNew";
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
import Sensors from "./pages/Sensors";

import PublicOutlet from "./pages/PublicOutlet";
import PublicCitizenReport from "./pages/PublicCitizenReport";
import PublicReportStatus from "./pages/PublicReportStatus";

function NavGroup({ title, children }) {
  return <div className="nav-group"><div className="nav-group-title">{title}</div>{children}</div>;
}

function ProtectedLayout() {
  const [me, setMe] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    api.me().then(setMe).catch(() => {
      localStorage.removeItem("safebite_token");
      localStorage.removeItem("safebite_officer");
      navigate("/login", { replace: true });
    });
  }, [navigate]);

  if (!localStorage.getItem("safebite_token")) return <Navigate to="/login" replace />;
  if (!me) return <div className="loading-screen">Loading SafeBite...</div>;

  const isActive = (prefix) => location.pathname === prefix || location.pathname.startsWith(`${prefix}/`);
  const nav = (path, label) => <Link className={isActive(path) ? "nav-item active" : "nav-item"} to={path}>{label}</Link>;
  const logout = () => {
    localStorage.removeItem("safebite_token");
    localStorage.removeItem("safebite_officer");
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">SB</div><div><strong>SafeBite</strong><span>Government Portal</span></div></div>
        <nav className="sidebar-nav">
          <NavGroup title="MONITOR">{nav("/", "Overview")}{nav("/command-center", "Command Center")}{nav("/sensors", "Sensors")}</NavGroup>
          <NavGroup title="RESPOND">{nav("/action-queue", "Action Queue")}{nav("/alerts", "Alerts")}{nav("/investigations", "Investigations")}</NavGroup>
          <NavGroup title="COMPLIANCE">{nav("/establishments", "Establishments")}{nav("/item-scanner", "Item Scanner")}{nav("/monthly-notices", "Monthly Notices")}</NavGroup>
          <NavGroup title="RECORDS">{nav("/reports", "Reports")}{nav("/audit-history", "Audit History")}</NavGroup>
        </nav>
        <div className="sidebar-bottom">
          <div className="region-card"><small>AUTHORISED REGION</small><strong>{me.role === "CENTRAL_ADMIN" ? "National / Central" : me.region}</strong><span>{me.state}</span></div>
          <button className="secondary-button full" onClick={logout}>Logout</button>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div><div className="eyebrow">FOOD SAFETY SURVEILLANCE</div><h1>{me.role === "CENTRAL_ADMIN" ? "Central Monitoring" : `${me.region} Monitoring`}</h1></div>
          <div className="officer-pill"><div className="avatar">{me.name?.slice(0, 1) || "O"}</div><div><strong>{me.name}</strong><span>{me.role.replaceAll("_", " ")}</span></div></div>
        </header>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/command-center" element={<CommandCenter />} />
          <Route path="/action-queue" element={<ActionQueue />} />
          <Route path="/sensors" element={<Sensors />} />
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
  return <Routes><Route path="/login" element={<Login />} /><Route path="/public/outlet/:registrationId" element={<PublicOutlet />} /><Route path="/public/outlet/:registrationId/report" element={<PublicCitizenReport />} /><Route path="/public/reports/:reportId" element={<PublicReportStatus />} /><Route path="/*" element={<ProtectedLayout />} /></Routes>;
}
