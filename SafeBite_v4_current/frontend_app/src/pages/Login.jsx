import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const [username, setUsername] = useState("officer_nm");
  const [password, setPassword] = useState("SafeBite@123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.login(username, password);
      localStorage.setItem("safebite_token", data.access_token);
      localStorage.setItem("safebite_officer", JSON.stringify(data.officer));
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-panel">
        <div className="brand large"><div className="brand-mark">SB</div><div><strong>SafeBite</strong><span>Government Food Safety Platform</span></div></div>
        <div className="eyebrow">SECURE REGIONAL ACCESS</div>
        <h1>Monitor. Investigate. Audit.</h1>
        <p className="muted">Access the food-safety alerts and cases assigned to your authorised jurisdiction.</p>
        <form className="form-card" onSubmit={submit}>
          <label>Officer username<input value={username} onChange={e => setUsername(e.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} /></label>
          {error && <div className="error-box">{error}</div>}
          <button className="primary-button full" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</button>
        </form>
        <div className="login-note">Demo regional account: <strong>officer_nm</strong> / <strong>SafeBite@123</strong></div>
      </div>
    </div>
  );
}
