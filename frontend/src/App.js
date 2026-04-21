import { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, RadialBarChart, RadialBar,
  PieChart, Pie, Cell, AreaChart, Area
} from "recharts";

const API = "http://localhost:8000";

const api = {
  headers: (token) => ({ "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
  post: async (path, body, token) => {
    const r = await fetch(`${API}${path}`, { method: "POST", headers: api.headers(token), body: JSON.stringify(body) });
    if (!r.ok) throw await r.json();
    return r.json();
  },
  get: async (path, token) => {
    const r = await fetch(`${API}${path}`, { headers: api.headers(token) });
    if (!r.ok) throw await r.json();
    return r.json();
  },
  del: async (path, token) => {
    const r = await fetch(`${API}${path}`, { method: "DELETE", headers: api.headers(token) });
    if (!r.ok && r.status !== 204) throw await r.json();
    return true;
  },
};

const fmt = (n) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
const COLORS = ["#0a0a0f", "#c8f03a", "#22c55e", "#f59e0b", "#ff4d4d", "#6366f1", "#ec4899"];

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --ink: #0a0a0f; --paper: #f5f4ef; --accent: #c8f03a; --muted: #8b8a84;
    --surface: #ffffff; --border: #e2e1db; --danger: #ff4d4d; --good: #22c55e;
    --warn: #f59e0b; --card-shadow: 0 1px 3px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.04);
  }
  body { font-family: 'DM Mono', monospace; background: var(--paper); color: var(--ink); min-height: 100vh; }
  h1,h2,h3,h4 { font-family: 'Syne', sans-serif; }

  .auth-wrap { min-height: 100vh; display: grid; place-items: center; background: var(--ink); }
  .auth-box { width: 420px; padding: 48px; background: var(--surface); border-radius: 8px; box-shadow: 0 8px 40px rgba(0,0,0,.3); }
  .auth-logo { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; letter-spacing: -1px; margin-bottom: 6px; }
  .auth-logo span { color: var(--accent); background: var(--ink); padding: 2px 8px; border-radius: 3px; }
  .auth-sub { color: var(--muted); font-size: 12px; margin-bottom: 32px; }
  .auth-tab { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 2px solid var(--border); }
  .auth-tab button { flex: 1; padding: 10px; background: none; border: none; font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; color: var(--muted); cursor: pointer; padding-bottom: 12px; margin-bottom: -2px; border-bottom: 2px solid transparent; transition: all .2s; text-transform: uppercase; letter-spacing: .05em; }
  .auth-tab button.active { color: var(--ink); border-bottom-color: var(--accent); }
  .field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
  .field label { font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); }
  .field input, .field select { padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 4px; font-family: 'DM Mono', monospace; font-size: 13px; outline: none; transition: border-color .2s; background: var(--paper); width: 100%; color: var(--ink); }
  .field input:focus, .field select:focus { border-color: var(--ink); background: #fff; }
  .btn-primary { width: 100%; padding: 13px; background: var(--ink); color: var(--accent); border: none; border-radius: 4px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 14px; cursor: pointer; transition: opacity .15s; }
  .btn-primary:hover { opacity: .85; }
  .btn-primary:disabled { opacity: .4; cursor: not-allowed; }
  .err-msg { background: #fff0f0; color: var(--danger); padding: 10px 14px; border-radius: 4px; font-size: 12px; margin-bottom: 14px; border-left: 3px solid var(--danger); }

  .shell { display: grid; grid-template-columns: 220px 1fr; min-height: 100vh; }
  .sidebar { background: var(--ink); color: var(--paper); display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
  .sidebar-logo { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 800; letter-spacing: -0.5px; padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,.07); }
  .sidebar-logo span { color: var(--accent); }
  .nav { flex: 1; padding: 12px 10px; display: flex; flex-direction: column; gap: 1px; }
  .nav-section { padding: 16px 10px 5px 14px; font-size: 9px; text-transform: uppercase; letter-spacing: .12em; color: rgba(255,255,255,.2); }
  .nav-item { display: flex; align-items: center; gap: 9px; padding: 9px 12px; border-radius: 5px; font-size: 12px; color: rgba(255,255,255,.55); cursor: pointer; transition: all .15s; border: none; background: none; width: 100%; text-align: left; font-family: 'DM Mono', monospace; }
  .nav-item:hover { background: rgba(255,255,255,.06); color: rgba(255,255,255,.85); }
  .nav-item.active { background: rgba(200,240,58,.12); color: var(--accent); }
  .nav-item .nav-icon { font-size: 14px; width: 18px; text-align: center; }
  .sidebar-footer { padding: 14px 20px; border-top: 1px solid rgba(255,255,255,.07); }
  .user-pill { display: flex; align-items: center; gap: 10px; }
  .user-avatar { width: 30px; height: 30px; border-radius: 50%; background: var(--accent); display: grid; place-items: center; font-family: 'Syne', sans-serif; font-weight: 800; font-size: 12px; color: var(--ink); flex-shrink: 0; }
  .user-name { font-size: 12px; color: rgba(255,255,255,.75); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .logout-btn { background: none; border: none; color: rgba(255,255,255,.25); cursor: pointer; font-size: 16px; transition: color .15s; flex-shrink: 0; }
  .logout-btn:hover { color: var(--danger); }

  .main { padding: 32px 36px; overflow-y: auto; min-height: 100vh; }
  .page-head { margin-bottom: 28px; }
  .page-title { font-family: 'Syne', sans-serif; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
  .page-subtitle { color: var(--muted); font-size: 12px; margin-top: 5px; }

  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 14px; margin-bottom: 20px; }
  .card { background: var(--surface); border-radius: 8px; padding: 18px; box-shadow: var(--card-shadow); border: 1px solid var(--border); }
  .card-label { font-size: 10px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 7px; }
  .card-value { font-family: 'Syne', sans-serif; font-size: 24px; font-weight: 700; letter-spacing: -1px; line-height: 1; }
  .card-value.good { color: var(--good); }
  .card-value.warn { color: var(--warn); }
  .card-value.danger { color: var(--danger); }
  .card-sub { font-size: 11px; color: var(--muted); margin-top: 4px; }

  .section { background: var(--surface); border-radius: 8px; padding: 20px; box-shadow: var(--card-shadow); border: 1px solid var(--border); margin-bottom: 18px; }
  .section-title { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .section-title-tag { font-size: 11px; font-weight: 400; color: var(--muted); font-family: 'DM Mono'; }

  .tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
  .tbl th { text-align: left; padding: 7px 10px; font-size: 9px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); border-bottom: 2px solid var(--border); font-family: 'Syne', sans-serif; }
  .tbl td { padding: 10px 10px; border-bottom: 1px solid var(--border); }
  .tbl tr:last-child td { border-bottom: none; }
  .tbl tr:hover td { background: var(--paper); }
  .badge { display: inline-block; padding: 2px 7px; border-radius: 20px; font-size: 10px; font-weight: 500; }
  .badge-income { background: #dcfce7; color: #15803d; }
  .badge-expense { background: #fee2e2; color: #b91c1c; }
  .badge-cat { background: var(--paper); color: var(--muted); border: 1px solid var(--border); }

  .form-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 14px; }
  .form-row .field { margin-bottom: 0; }
  .btn-add { padding: 9px 18px; background: var(--accent); color: var(--ink); border: none; border-radius: 4px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 12px; cursor: pointer; transition: opacity .15s; }
  .btn-add:hover { opacity: .85; }
  .btn-del { background: none; border: none; color: var(--border); cursor: pointer; font-size: 14px; transition: color .15s; padding: 4px; }
  .btn-del:hover { color: var(--danger); }

  .btn-run { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: var(--ink); color: var(--accent); border: none; border-radius: 4px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 13px; cursor: pointer; transition: opacity .15s; }
  .btn-run:hover { opacity: .8; }
  .btn-run:disabled { opacity: .4; cursor: not-allowed; }

  .stress-bar-wrap { height: 10px; border-radius: 5px; background: var(--border); overflow: hidden; }
  .stress-bar { height: 100%; border-radius: 5px; transition: width .8s ease; }

  .spin { display: inline-block; width: 13px; height: 13px; border: 2px solid rgba(200,240,58,.3); border-top-color: var(--accent); border-radius: 50%; animation: spin .6s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .toast { position: fixed; bottom: 24px; right: 24px; background: var(--ink); color: var(--accent); padding: 10px 18px; border-radius: 5px; font-size: 12px; font-family: 'Syne', sans-serif; font-weight: 600; z-index: 1000; animation: slideUp .25s ease; }
  @keyframes slideUp { from { transform: translateY(10px); opacity: 0; } }

  .empty { text-align: center; padding: 32px; color: var(--muted); font-size: 13px; }
  .prog-wrap { height: 6px; border-radius: 3px; background: var(--border); overflow: hidden; margin: 4px 0; }
  .prog-bar { height: 100%; border-radius: 3px; background: var(--accent); transition: width .5s ease; }
  .tag { display: inline-block; padding: 2px 8px; background: rgba(200,240,58,.1); color: #5a6e00; border-radius: 20px; font-size: 10px; border: 1px solid rgba(200,240,58,.25); }

  .engine-page { max-width: 920px; }
  .engine-header { display: flex; align-items: center; gap: 14px; margin-bottom: 22px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
  .engine-icon { width: 46px; height: 46px; border-radius: 10px; background: var(--ink); color: var(--accent); display: grid; place-items: center; font-size: 20px; flex-shrink: 0; }
  .engine-title { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
  .engine-desc { font-size: 12px; color: var(--muted); margin-top: 3px; line-height: 1.5; }

  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 18px; }
  .alert-box { padding: 9px 13px; border-radius: 4px; font-size: 12px; margin-bottom: 7px; display: flex; align-items: flex-start; gap: 8px; line-height: 1.5; }
  .alert-warn { background: #fffbeb; border-left: 3px solid var(--warn); color: #78450a; }
  .alert-good { background: #f0fdf4; border-left: 3px solid var(--good); color: #14532d; }
  .alert-danger { background: #fff1f1; border-left: 3px solid var(--danger); color: #7f1d1d; }

  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { color: var(--muted); font-size: 11px; }
  .stat-value { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 14px; }
`;

const Toast = ({ msg }) => <div className="toast">{msg}</div>;

// ── Auth ──────────────────────────────────────────────────────────────────────
function AuthPage({ onLogin }) {
  const [tab, setTab] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", name: "", monthly_income: "" });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const submit = async () => {
    setErr(""); setLoading(true);
    try {
      if (tab === "register") await api.post("/auth/register", { email: form.email, password: form.password, name: form.name, monthly_income: parseFloat(form.monthly_income) || 0 });
      const fd = new FormData();
      fd.append("username", form.email); fd.append("password", form.password);
      const r = await fetch(`${API}/auth/login`, { method: "POST", body: fd });
      if (!r.ok) throw await r.json();
      const { access_token } = await r.json();
      const user = await api.get("/auth/me", access_token);
      onLogin(access_token, user);
    } catch (e) { setErr(e?.detail || "Something went wrong."); }
    finally { setLoading(false); }
  };
  return (
    <div className="auth-wrap">
      <div className="auth-box">
        <div className="auth-logo">SMARTSPEND</div>
        <div className="auth-sub">AI-Powered Financial Wellness Platform</div>
        <div className="auth-tab">
          <button className={tab === "login" ? "active" : ""} onClick={() => setTab("login")}>Sign In</button>
          <button className={tab === "register" ? "active" : ""} onClick={() => setTab("register")}>Register</button>
        </div>
        {err && <div className="err-msg">{err}</div>}
        {tab === "register" && <>
          <div className="field"><label>Full Name</label><input value={form.name} onChange={set("name")} placeholder="Priya Sharma" /></div>
          <div className="field"><label>Monthly Income (₹)</label><input type="number" value={form.monthly_income} onChange={set("monthly_income")} placeholder="100000" /></div>
        </>}
        <div className="field"><label>Email</label><input type="email" value={form.email} onChange={set("email")} placeholder="you@example.com" /></div>
        <div className="field"><label>Password</label><input type="password" value={form.password} onChange={set("password")} placeholder="••••••••" /></div>
        <button className="btn-primary" onClick={submit} disabled={loading}>{loading ? <span className="spin" /> : tab === "login" ? "Sign In →" : "Create Account →"}</button>
      </div>
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function Dashboard({ token, user }) {
  const [stress, setStress] = useState(null);
  const [stressLoading, setStressLoading] = useState(true);
  const [txns, setTxns] = useState([]);
  useEffect(() => {
    setStressLoading(true);
    api.get("/ai/stress-index", token).then(setStress).catch(() => setStress(null)).finally(() => setStressLoading(false));
    api.get("/transactions/?limit=100", token).then(setTxns).catch(() => {});
  }, [token]);
  const income = txns.filter(t => t.type === "income").reduce((a, t) => a + t.amount, 0);
  const expenses = txns.filter(t => t.type === "expense").reduce((a, t) => a + t.amount, 0);
  const stressVal = stress?.stress_index ?? null;
  const stressColor = stressVal === null ? "var(--muted)" : stressVal < 33 ? "var(--good)" : stressVal < 66 ? "var(--warn)" : "var(--danger)";
  const monthlyMap = {};
  txns.forEach(t => {
    if (!t.date) return;
    const d = new Date(t.date);
    const m = d.toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
    if (!monthlyMap[m]) monthlyMap[m] = { month: m, income: 0, expenses: 0, _ts: d.getTime() };
    if (t.type === "income") monthlyMap[m].income += t.amount;
    else monthlyMap[m].expenses += t.amount;
  });
  const chartData = Object.values(monthlyMap).sort((a, b) => a._ts - b._ts);
  const catMap = {};
  txns.filter(t => t.type === "expense").forEach(t => { catMap[t.category] = (catMap[t.category] || 0) + t.amount; });
  const catData = Object.entries(catMap).map(([name, value]) => ({ name, value: Math.round(value) })).sort((a, b) => b.value - a.value).slice(0, 6);
  return (
    <>
      <div className="page-head">
        <div className="page-title">Dashboard</div>
        <div className="page-subtitle">Welcome back, {user.name} · {new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}</div>
      </div>
      <div className="cards">
        <div className="card"><div className="card-label">Monthly Income</div><div className="card-value">{fmt(user.monthly_income)}</div><div className="card-sub">Base salary</div></div>
        <div className="card"><div className="card-label">Total Income</div><div className="card-value good">{fmt(income)}</div><div className="card-sub">All recorded</div></div>
        <div className="card"><div className="card-label">Total Expenses</div><div className="card-value danger">{fmt(expenses)}</div><div className="card-sub">All recorded</div></div>
        <div className="card"><div className="card-label">Net Savings</div><div className={`card-value ${income - expenses >= 0 ? "good" : "danger"}`}>{fmt(income - expenses)}</div></div>
        <div className="card"><div className="card-label">Stress Index</div><div className="card-value" style={{ color: stressColor }}>{stressLoading ? "..." : stressVal !== null ? `${stressVal}/100` : "—"}</div><div className="card-sub">{stress?.verdict || (stressLoading ? "Loading..." : "No data yet")}</div></div>
      </div>
      {chartData.length > 0 && (
        <div className="two-col">
          <div className="section" style={{ marginBottom: 0 }}>
            <div className="section-title">Monthly Cash Flow</div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} barCategoryGap="35%">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4, border: "1px solid var(--border)" }} />
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: "DM Mono" }} />
                <Bar dataKey="income" fill="#22c55e" radius={[3, 3, 0, 0]} name="Income" />
                <Bar dataKey="expenses" fill="#ff4d4d" radius={[3, 3, 0, 0]} name="Expenses" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="section" style={{ marginBottom: 0 }}>
            <div className="section-title">Spending by Category</div>
            {catData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={catData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" paddingAngle={3}>
                    {catData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                  <Legend wrapperStyle={{ fontSize: 10, fontFamily: "DM Mono" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="empty">Add expense transactions</div>}
          </div>
        </div>
      )}
      {!stressLoading && stressVal !== null && (
        <div className="section">
          <div className="section-title">Financial Stress Index <span className="section-title-tag" style={{ color: stressColor }}>{stress?.verdict}</span></div>
          <div className="stress-bar-wrap"><div className="stress-bar" style={{ width: `${stressVal}%`, background: stressColor }} /></div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
            <span>0 Calm</span><span style={{ color: stressColor, fontWeight: 600 }}>{stressVal} / 100</span><span>100 Critical</span>
          </div>
          {stress?.alerts?.map((a, i) => <div key={i} className="alert-box alert-warn" style={{ marginTop: 10 }}>⚠ {a}</div>)}
        </div>
      )}
      <div className="section">
        <div className="section-title">Recent Transactions <span className="section-title-tag">last 8</span></div>
        {txns.length === 0 ? <div className="empty">No transactions yet.</div> : (
          <table className="tbl">
            <thead><tr><th>Description</th><th>Type</th><th>Category</th><th>Amount</th><th>Date</th></tr></thead>
            <tbody>{txns.slice(0, 8).map(t => (
              <tr key={t.id}>
                <td>{t.description}</td>
                <td><span className={`badge badge-${t.type}`}>{t.type}</span></td>
                <td><span className="badge badge-cat">{t.category}</span></td>
                <td style={{ fontFamily: "Syne", fontWeight: 700 }}>{fmt(t.amount)}</td>
                <td style={{ color: "var(--muted)", fontSize: 11 }}>{t.date ? new Date(t.date).toLocaleDateString("en-IN") : "—"}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </>
  );
}

// ── Transactions ──────────────────────────────────────────────────────────────
function Transactions({ token, toast }) {
  const [txns, setTxns] = useState([]);
  const [form, setForm] = useState({ amount: "", type: "expense", description: "", date: "" });
  const [loading, setLoading] = useState(false);
  const load = useCallback(() => api.get("/transactions/?limit=100", token).then(setTxns).catch(() => {}), [token]);
  useEffect(() => { load(); }, [load]);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const add = async () => {
    if (!form.amount || !form.description) return;
    setLoading(true);
    try { await api.post("/transactions/", { ...form, amount: parseFloat(form.amount), date: form.date || new Date().toISOString() }, token); setForm({ amount: "", type: "expense", description: "", date: "" }); load(); toast("Transaction added ✓"); }
    catch { toast("Failed"); } finally { setLoading(false); }
  };
  const del = async (id) => { await api.del(`/transactions/${id}`, token); load(); toast("Deleted"); };
  const income = txns.filter(t => t.type === "income").reduce((a, t) => a + t.amount, 0);
  const expense = txns.filter(t => t.type === "expense").reduce((a, t) => a + t.amount, 0);
  return (
    <>
      <div className="page-head"><div className="page-title">Transactions</div><div className="page-subtitle">Manage your income and expenses</div></div>
      <div className="cards">
        <div className="card"><div className="card-label">Total Income</div><div className="card-value good">{fmt(income)}</div></div>
        <div className="card"><div className="card-label">Total Expenses</div><div className="card-value danger">{fmt(expense)}</div></div>
        <div className="card"><div className="card-label">Net</div><div className={`card-value ${income - expense >= 0 ? "good" : "danger"}`}>{fmt(income - expense)}</div></div>
        <div className="card"><div className="card-label">Entries</div><div className="card-value">{txns.length}</div></div>
      </div>
      <div className="section">
        <div className="section-title">Add Transaction</div>
        <div className="form-row">
          <div className="field"><label>Description</label><input value={form.description} onChange={set("description")} placeholder="Swiggy, Salary..." /></div>
          <div className="field"><label>Amount (₹)</label><input type="number" value={form.amount} onChange={set("amount")} placeholder="2500" /></div>
          <div className="field"><label>Type</label><select value={form.type} onChange={set("type")}><option value="expense">Expense</option><option value="income">Income</option></select></div>
          <div className="field"><label>Date</label><input type="date" value={form.date} onChange={set("date")} /></div>
        </div>
        <button className="btn-add" onClick={add} disabled={loading}>{loading ? "Adding..." : "+ Add"}</button>
      </div>
      <div className="section">
        <div className="section-title">All Transactions <span className="section-title-tag">{txns.length} entries</span></div>
        {txns.length === 0 ? <div className="empty">No transactions yet.</div> : (
          <table className="tbl">
            <thead><tr><th>Description</th><th>Type</th><th>Category</th><th>Amount</th><th>Date</th><th></th></tr></thead>
            <tbody>{txns.map(t => (
              <tr key={t.id}>
                <td>{t.description}</td><td><span className={`badge badge-${t.type}`}>{t.type}</span></td>
                <td><span className="badge badge-cat">{t.category}</span></td>
                <td style={{ fontFamily: "Syne", fontWeight: 700 }}>{fmt(t.amount)}</td>
                <td style={{ color: "var(--muted)", fontSize: 11 }}>{t.date ? new Date(t.date).toLocaleDateString("en-IN") : "—"}</td>
                <td><button className="btn-del" onClick={() => del(t.id)}>✕</button></td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </>
  );
}

// ── Loans ─────────────────────────────────────────────────────────────────────
function Loans({ token, toast }) {
  const [loans, setLoans] = useState([]);
  const [form, setForm] = useState({ name: "", principal: "", outstanding: "", interest_rate: "", monthly_emi: "", tenure_months_remaining: "" });
  const load = useCallback(() => api.get("/loans/", token).then(setLoans).catch(() => {}), [token]);
  useEffect(() => { load(); }, [load]);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const add = async () => {
    try { await api.post("/loans/", { name: form.name, principal: parseFloat(form.principal), outstanding: parseFloat(form.outstanding), interest_rate: parseFloat(form.interest_rate), monthly_emi: parseFloat(form.monthly_emi), tenure_months_remaining: parseInt(form.tenure_months_remaining) }, token); setForm({ name: "", principal: "", outstanding: "", interest_rate: "", monthly_emi: "", tenure_months_remaining: "" }); load(); toast("Loan added ✓"); }
    catch { toast("Failed"); }
  };
  const del = async (id) => { await api.del(`/loans/${id}`, token); load(); toast("Deleted"); };
  const totalEMI = loans.reduce((a, l) => a + l.monthly_emi, 0);
  const totalOutstanding = loans.reduce((a, l) => a + l.outstanding, 0);
  return (
    <>
      <div className="page-head"><div className="page-title">Loans & EMIs</div><div className="page-subtitle">Track all your loan obligations</div></div>
      <div className="cards">
        <div className="card"><div className="card-label">Active Loans</div><div className="card-value">{loans.length}</div></div>
        <div className="card"><div className="card-label">Monthly EMI Total</div><div className="card-value danger">{fmt(totalEMI)}</div></div>
        <div className="card"><div className="card-label">Total Outstanding</div><div className="card-value warn">{fmt(totalOutstanding)}</div></div>
      </div>
      <div className="section">
        <div className="section-title">Add Loan</div>
        <div className="form-row">
          <div className="field"><label>Name</label><input value={form.name} onChange={set("name")} placeholder="Car Loan" /></div>
          <div className="field"><label>Principal (₹)</label><input type="number" value={form.principal} onChange={set("principal")} placeholder="600000" /></div>
          <div className="field"><label>Outstanding (₹)</label><input type="number" value={form.outstanding} onChange={set("outstanding")} placeholder="380000" /></div>
          <div className="field"><label>Interest Rate (%)</label><input type="number" value={form.interest_rate} onChange={set("interest_rate")} placeholder="9.5" /></div>
          <div className="field"><label>Monthly EMI (₹)</label><input type="number" value={form.monthly_emi} onChange={set("monthly_emi")} placeholder="14000" /></div>
          <div className="field"><label>Months Remaining</label><input type="number" value={form.tenure_months_remaining} onChange={set("tenure_months_remaining")} placeholder="30" /></div>
        </div>
        <button className="btn-add" onClick={add}>+ Add Loan</button>
      </div>
      {loans.length > 0 && (
        <div className="section">
          <div className="section-title">Your Loans</div>
          <table className="tbl">
            <thead><tr><th>Name</th><th>Principal</th><th>Outstanding</th><th>Rate</th><th>EMI/mo</th><th>Months Left</th><th>Paid</th><th></th></tr></thead>
            <tbody>{loans.map(l => {
              const paid = ((l.principal - l.outstanding) / l.principal) * 100;
              return (
                <tr key={l.id}>
                  <td style={{ fontWeight: 500 }}>{l.name}</td><td>{fmt(l.principal)}</td>
                  <td style={{ color: "var(--warn)", fontWeight: 600 }}>{fmt(l.outstanding)}</td>
                  <td>{l.interest_rate}%</td><td style={{ fontFamily: "Syne", fontWeight: 700 }}>{fmt(l.monthly_emi)}</td>
                  <td>{l.tenure_months_remaining} mo</td>
                  <td><div style={{ display: "flex", alignItems: "center", gap: 6 }}><div className="prog-wrap" style={{ flex: 1, minWidth: 50 }}><div className="prog-bar" style={{ width: `${paid}%`, background: "var(--good)" }} /></div><span style={{ fontSize: 10, color: "var(--muted)" }}>{paid.toFixed(0)}%</span></div></td>
                  <td><button className="btn-del" onClick={() => del(l.id)}>✕</button></td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
      )}
    </>
  );
}

// ── Goals ─────────────────────────────────────────────────────────────────────
function Goals({ token, toast }) {
  const [goals, setGoals] = useState([]);
  const [form, setForm] = useState({ name: "", target_amount: "", current_amount: "", monthly_contribution: "", deadline_months: "" });
  const load = useCallback(() => api.get("/goals/", token).then(setGoals).catch(() => {}), [token]);
  useEffect(() => { load(); }, [load]);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const add = async () => {
    try { await api.post("/goals/", { name: form.name, target_amount: parseFloat(form.target_amount), current_amount: parseFloat(form.current_amount) || 0, monthly_contribution: parseFloat(form.monthly_contribution), deadline_months: parseInt(form.deadline_months) }, token); setForm({ name: "", target_amount: "", current_amount: "", monthly_contribution: "", deadline_months: "" }); load(); toast("Goal added ✓"); }
    catch { toast("Failed"); }
  };
  const del = async (id) => { await api.del(`/goals/${id}`, token); load(); toast("Deleted"); };
  return (
    <>
      <div className="page-head"><div className="page-title">Financial Goals</div><div className="page-subtitle">Track progress toward your targets</div></div>
      <div className="section">
        <div className="section-title">Add Goal</div>
        <div className="form-row">
          <div className="field"><label>Name</label><input value={form.name} onChange={set("name")} placeholder="Emergency Fund" /></div>
          <div className="field"><label>Target (₹)</label><input type="number" value={form.target_amount} onChange={set("target_amount")} placeholder="300000" /></div>
          <div className="field"><label>Current (₹)</label><input type="number" value={form.current_amount} onChange={set("current_amount")} placeholder="60000" /></div>
          <div className="field"><label>Monthly (₹)</label><input type="number" value={form.monthly_contribution} onChange={set("monthly_contribution")} placeholder="15000" /></div>
          <div className="field"><label>Deadline (months)</label><input type="number" value={form.deadline_months} onChange={set("deadline_months")} placeholder="18" /></div>
        </div>
        <button className="btn-add" onClick={add}>+ Add Goal</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 14 }}>
        {goals.length === 0 && <div className="empty">No goals yet.</div>}
        {goals.map(g => {
          const pct = Math.min(100, (g.current_amount / g.target_amount) * 100);
          const monthsLeft = Math.ceil((g.target_amount - g.current_amount) / (g.monthly_contribution || 1));
          return (
            <div className="card" key={g.id}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <div style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 14 }}>{g.name}</div>
                <button className="btn-del" onClick={() => del(g.id)}>✕</button>
              </div>
              <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
                <span className="tag">{g.deadline_months} mo deadline</span>
                <span className="tag">{pct.toFixed(0)}% done</span>
              </div>
              <div className="prog-wrap" style={{ height: 8 }}><div className="prog-bar" style={{ width: `${pct}%` }} /></div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--muted)", margin: "5px 0 10px" }}>
                <span>{fmt(g.current_amount)}</span><span>{fmt(g.target_amount)}</span>
              </div>
              <div style={{ fontSize: 11, color: "var(--muted)", borderTop: "1px solid var(--border)", paddingTop: 8 }}>
                +{fmt(g.monthly_contribution)}/mo · ~{monthsLeft} months to go
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

// ── Engine: Salary Allocation ─────────────────────────────────────────────────
function SalaryAllocation({ token, toast }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => { setLoading(true); try { setResult(await api.post("/ai/salary-allocation", {}, token)); toast("Done ✓"); } catch (e) { toast(e?.detail || "Error"); } finally { setLoading(false); } };
  const alloc = result?.allocation || {};
  const chartData = Object.entries(alloc).map(([k, v]) => ({ name: k.replace(/_/g, " "), value: Math.round(v || 0) })).filter(d => d.value > 0);
  return (
    <div className="engine-page">
      <div className="engine-header"><div className="engine-icon">💰</div><div><div className="engine-title">Salary Allocation</div><div className="engine-desc">Optimal breakdown of monthly income across EMIs, savings, investments & discretionary spend</div></div></div>
      <button className="btn-run" onClick={run} disabled={loading}>{loading ? <><span className="spin" /> Analysing...</> : "Run Analysis →"}</button>
      {result && (
        <>
          <div className="cards" style={{ marginTop: 20 }}>
            <div className="card"><div className="card-label">Monthly Income</div><div className="card-value">{fmt(result.monthly_income)}</div></div>
            <div className="card"><div className="card-label">Surplus</div><div className={`card-value ${(result.surplus_after_commitments || 0) >= 0 ? "good" : "danger"}`}>{fmt(result.surplus_after_commitments)}</div></div>
            <div className="card"><div className="card-label">Debt-to-Income</div><div className={`card-value ${(result.debt_to_income_ratio || 0) < 30 ? "good" : (result.debt_to_income_ratio || 0) < 50 ? "warn" : "danger"}`}>{(result.debt_to_income_ratio || 0).toFixed(1)}%</div></div>
            <div className="card"><div className="card-label">Health Score</div><div className={`card-value ${(result.health_score || 0) >= 70 ? "good" : (result.health_score || 0) >= 40 ? "warn" : "danger"}`}>{(result.health_score || 0).toFixed(0)}/100</div></div>
          </div>
          {chartData.length > 0 && (
            <div className="two-col">
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Allocation Pie</div>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart><Pie data={chartData} cx="50%" cy="50%" outerRadius={85} dataKey="value" paddingAngle={3}>
                    {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie><Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} /><Legend wrapperStyle={{ fontSize: 10, fontFamily: "DM Mono" }} /></PieChart>
                </ResponsiveContainer>
              </div>
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Amount per Bucket</div>
                {chartData.map(d => (
                  <div key={d.name} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}><span style={{ textTransform: "capitalize", color: "var(--muted)" }}>{d.name}</span><span style={{ fontFamily: "Syne", fontWeight: 700 }}>{fmt(d.value)}</span></div>
                    <div className="prog-wrap"><div className="prog-bar" style={{ width: `${(d.value / (result.monthly_income || 1)) * 100}%`, background: "var(--ink)" }} /></div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {Array.isArray(result.recommendations) && result.recommendations.length > 0 && (
            <div className="section">
              <div className="section-title">Recommendations</div>
              {result.recommendations.map((r, i) => (
                <div key={i} className="alert-box alert-warn">
                  💡 {typeof r === "string" ? r : (r?.message || r?.text || r?.tip || Object.values(r).filter(v => typeof v === "string")[0] || "See details above")}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Engine: Stress Index ──────────────────────────────────────────────────────
function StressIndex({ token, toast }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try { setResult(await api.get("/ai/stress-index", token)); toast("Done ✓"); }
    catch (e) { toast(e?.detail || "Error"); }
    finally { setLoading(false); }
  };

  // Backend returns: financial_stress_index, label, signals (array of objects), monthly_expense_trend, coverage_ratio, emi_burden_pct, statistical_score, ml_anomaly_score, interpretation
  const score = result?.financial_stress_index ?? 0;
  const stressColor = score < 33 ? "#22c55e" : score < 66 ? "#f59e0b" : "#ff4d4d";

  const statCards = result ? [
    { label: "Statistical Score", value: `${result.statistical_score ?? 0}/100` },
    { label: "ML Anomaly Score", value: `${(result.ml_anomaly_score ?? 0).toFixed(1)}/100` },
    { label: "Coverage Ratio", value: `${result.coverage_ratio ?? 0}%` },
    { label: "EMI Burden", value: `${result.emi_burden_pct ?? 0}%` },
  ] : [];

  const trendData = (result?.monthly_expense_trend || []).map(d => ({ month: d.month, total: d.total }));

  const signals = (result?.signals || []).filter(s => s && typeof s === "object");

  return (
    <div className="engine-page">
      <div className="engine-header">
        <div className="engine-icon">📊</div>
        <div>
          <div className="engine-title">Financial Stress Index</div>
          <div className="engine-desc">Hybrid ML + Statistical stress scoring — Isolation Forest anomaly detection combined with EMI burden, volatility & coverage signals</div>
        </div>
      </div>
      <button className="btn-run" onClick={run} disabled={loading}>{loading ? <><span className="spin" /> Analysing...</> : "Run Analysis →"}</button>

      {result && (
        <>
          {/* Score + stat cards */}
          <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: 16, marginTop: 20 }}>
            <div className="section" style={{ marginBottom: 0, textAlign: "center" }}>
              <div className="section-title" style={{ justifyContent: "center" }}>FSI Score</div>
              <div style={{ position: "relative", display: "inline-block" }}>
                <ResponsiveContainer width={150} height={150}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%" data={[{ value: score }]} startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="value" cornerRadius={8} background={{ fill: "var(--border)" }} fill={stressColor} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", textAlign: "center" }}>
                  <div style={{ fontFamily: "Syne", fontSize: 30, fontWeight: 800, color: stressColor, lineHeight: 1 }}>{score.toFixed(0)}</div>
                  <div style={{ fontSize: 10, color: "var(--muted)" }}>/ 100</div>
                </div>
              </div>
              <div style={{ fontFamily: "Syne", fontWeight: 700, color: stressColor, marginTop: 8, fontSize: 14 }}>{result.label}</div>
              <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>{result.method}</div>
            </div>
            <div className="section" style={{ marginBottom: 0 }}>
              <div className="section-title">Score Breakdown</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
                {statCards.map(c => (
                  <div key={c.label} style={{ padding: "10px 12px", background: "var(--paper)", borderRadius: 6 }}>
                    <div style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: ".07em" }}>{c.label}</div>
                    <div style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 18, marginTop: 3 }}>{c.value}</div>
                  </div>
                ))}
              </div>
              {result.interpretation && <div className="alert-box alert-good">💡 {result.interpretation}</div>}
            </div>
          </div>

          {/* Monthly trend chart */}
          {trendData.length > 1 && (
            <div className="section">
              <div className="section-title">Monthly Expense Trend</div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={trendData}>
                  <defs><linearGradient id="stressG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={stressColor} stopOpacity={0.15} /><stop offset="95%" stopColor={stressColor} stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                  <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                  <Area type="monotone" dataKey="total" stroke={stressColor} strokeWidth={2} fill="url(#stressG)" name="Expenses" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Signals */}
          {signals.length > 0 && (
            <div className="section">
              <div className="section-title">Detected Signals</div>
              {signals.map((s, i) => (
                <div key={i} className={`alert-box ${s.severity === "high" ? "alert-danger" : "alert-warn"}`}>
                  {s.severity === "high" ? "🔴" : "🟡"} <strong>{(s.type || "signal").replace(/_/g, " ")}</strong> — {s.message}
                </div>
              ))}
            </div>
          )}

          {/* Anomaly months */}
          {result.anomaly_months?.length > 0 && (
            <div className="section">
              <div className="section-title">Anomalous Months Detected by ML</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {result.anomaly_months.map(m => <span key={m} className="tag" style={{ background: "#fff0f0", color: "#b91c1c", border: "1px solid #fca5a5" }}>⚠ {m}</span>)}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Engine: What-If Simulation ────────────────────────────────────────────────
function WhatIfSim({ token, toast }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scenarios, setScenarios] = useState([{ description: "New EMI", monthly_impact: 8000, duration_months: 24, one_time_cost: 20000 }]);
  const run = async () => {
    setLoading(true);
    try { setResult(await api.post("/ai/what-if-simulation", { scenarios, projection_months: 12 }, token)); toast("Done ✓"); }
    catch (e) { toast(e?.detail || "Error"); }
    finally { setLoading(false); }
  };
  const upd = (i, k, v) => setScenarios(sc => sc.map((x, j) => j === i ? { ...x, [k]: v } : x));

  // Backend returns: baseline.balances[], with_scenarios.balances[], verdict{rating,summary,total_wealth_impact,breakeven_month}, monte_carlo{median,p10,p90,probability_negative}
  const baseBalances = result?.baseline?.balances || [];
  const scenBalances = result?.with_scenarios?.balances || [];
  const chartData = baseBalances.map((b, i) => ({
    month: `M${i + 1}`,
    baseline: Math.round(b),
    scenario: Math.round(scenBalances[i] ?? 0),
  }));

  const verdict = result?.verdict || {};
  const mc = result?.monte_carlo || {};
  const verdictColor = verdict.rating === "safe" ? "alert-good" : verdict.rating === "high_risk" ? "alert-danger" : "alert-warn";

  return (
    <div className="engine-page">
      <div className="engine-header">
        <div className="engine-icon">🔮</div>
        <div>
          <div className="engine-title">What-If Simulation</div>
          <div className="engine-desc">Monte Carlo + deterministic projection of how a financial decision impacts your balance month by month</div>
        </div>
      </div>
      <div className="section">
        <div className="section-title">Configure Scenario</div>
        {scenarios.map((s, i) => (
          <div key={i} className="form-row">
            <div className="field"><label>Description</label><input value={s.description} onChange={e => upd(i, "description", e.target.value)} /></div>
            <div className="field"><label>Monthly Impact (₹)</label><input type="number" value={s.monthly_impact} onChange={e => upd(i, "monthly_impact", parseFloat(e.target.value))} /></div>
            <div className="field"><label>Duration (months)</label><input type="number" value={s.duration_months} onChange={e => upd(i, "duration_months", parseInt(e.target.value))} /></div>
            <div className="field"><label>One-time Cost (₹)</label><input type="number" value={s.one_time_cost} onChange={e => upd(i, "one_time_cost", parseFloat(e.target.value))} /></div>
          </div>
        ))}
        <button className="btn-run" onClick={run} disabled={loading}>{loading ? <><span className="spin" /> Simulating...</> : "Run Simulation →"}</button>
      </div>

      {result && chartData.length > 0 && (
        <>
          <div className="cards">
            <div className="card"><div className="card-label">Baseline Final Balance</div><div className="card-value good">{fmt(result.baseline?.final_balance)}</div></div>
            <div className="card"><div className="card-label">Scenario Final Balance</div><div className={`card-value ${(result.with_scenarios?.final_balance || 0) >= 0 ? "warn" : "danger"}`}>{fmt(result.with_scenarios?.final_balance)}</div></div>
            <div className="card"><div className="card-label">Wealth Impact</div><div className={`card-value ${(verdict.total_wealth_impact || 0) >= 0 ? "good" : "danger"}`}>{fmt(verdict.total_wealth_impact)}</div></div>
            <div className="card"><div className="card-label">Breakeven Month</div><div className="card-value">{verdict.breakeven_month ? `M${verdict.breakeven_month}` : "None"}</div></div>
          </div>

          {/* Balance projection chart */}
          <div className="section">
            <div className="section-title">Balance Projection — Baseline vs Scenario</div>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="baseG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} /><stop offset="95%" stopColor="#22c55e" stopOpacity={0} /></linearGradient>
                  <linearGradient id="scenG" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15} /><stop offset="95%" stopColor="#f59e0b" stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: "DM Mono" }} />
                <Area type="monotone" dataKey="baseline" stroke="#22c55e" strokeWidth={2} fill="url(#baseG)" name="Baseline" />
                <Area type="monotone" dataKey="scenario" stroke="#f59e0b" strokeWidth={2} fill="url(#scenG)" name="With Scenario" strokeDasharray="5 3" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Monte Carlo results */}
          {mc.median_final_balance != null && (
            <div className="two-col">
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Monte Carlo Outcomes (500 simulations)</div>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={[
                    { name: "Pessimistic (P10)", value: Math.round(mc.p10_balance) },
                    { name: "Median", value: Math.round(mc.median_final_balance) },
                    { name: "Optimistic (P90)", value: Math.round(mc.p90_balance) },
                  ]} barCategoryGap="40%">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 9, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                    <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                    <Bar dataKey="value" radius={[4,4,0,0]}><Cell fill="#ff4d4d" /><Cell fill="#f59e0b" /><Cell fill="#22c55e" /></Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Risk Metrics</div>
                <div className="stat-row"><span className="stat-label">Probability of Negative Balance</span><span className="stat-value danger">{mc.probability_negative_balance?.toFixed(1)}%</span></div>
                <div className="stat-row"><span className="stat-label">Median Final Balance</span><span className="stat-value">{fmt(mc.median_final_balance)}</span></div>
                <div className="stat-row"><span className="stat-label">Best Case (P90)</span><span className="stat-value good">{fmt(mc.p90_balance)}</span></div>
                <div className="stat-row"><span className="stat-label">Worst Case (P10)</span><span className="stat-value danger">{fmt(mc.p10_balance)}</span></div>
              </div>
            </div>
          )}

          {/* Verdict */}
          {verdict.summary && (
            <div className="section">
              <div className="section-title">Verdict — <span style={{ textTransform: "capitalize", color: verdict.rating === "safe" ? "var(--good)" : verdict.rating === "high_risk" ? "var(--danger)" : "var(--warn)" }}>{(verdict.rating || "").replace("_", " ")}</span></div>
              <div className={`alert-box ${verdictColor}`}>💡 {verdict.summary}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Engine: Goal Probability ──────────────────────────────────────────────────
function GoalProbability({ token, toast }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [goals, setGoals] = useState([]);
  const [goalId, setGoalId] = useState("");
  useEffect(() => { api.get("/goals/", token).then(setGoals).catch(() => {}); }, [token]);
  const run = async () => { if (!goalId) return toast("Select a goal first"); setLoading(true); try { setResult(await api.post("/ai/goal-probability", { goal_id: parseInt(goalId) }, token)); toast("Done ✓"); } catch (e) { toast(e?.detail || "Error"); } finally { setLoading(false); } };
  const prob = result?.probability_pct ?? 0;
  const probColor = prob >= 70 ? "#22c55e" : prob >= 40 ? "#f59e0b" : "#ff4d4d";
  const pr = result?.projected_range || {};
  const rangeData = pr.p10 != null ? [
    { name: "Pessimistic", value: Math.round(pr.p10) },
    { name: "Median", value: Math.round(pr.p50_median) },
    { name: "Optimistic", value: Math.round(pr.p90) },
  ] : [];
  return (
    <div className="engine-page">
      <div className="engine-header"><div className="engine-icon">🎯</div><div><div className="engine-title">Goal Probability Predictor</div><div className="engine-desc">Monte Carlo simulation (2000 trials) estimating your chance of hitting a savings goal</div></div></div>
      <div className="section">
        <div className="section-title">Select Goal</div>
        <div className="field" style={{ maxWidth: 320, marginBottom: 14 }}>
          <label>Goal</label>
          <select value={goalId} onChange={e => setGoalId(e.target.value)}>
            <option value="">-- select --</option>
            {goals.map(g => <option key={g.id} value={g.id}>{g.name} — {fmt(g.target_amount)}</option>)}
          </select>
        </div>
        <button className="btn-run" onClick={run} disabled={loading || !goalId}>{loading ? <><span className="spin" /> Simulating...</> : "Run 2000 Simulations →"}</button>
      </div>
      {result && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: 16 }}>
            <div className="section" style={{ marginBottom: 0, textAlign: "center" }}>
              <div className="section-title" style={{ justifyContent: "center" }}>Probability</div>
              <div style={{ position: "relative", display: "inline-block" }}>
                <ResponsiveContainer width={140} height={140}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%" data={[{ value: prob }]} startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="value" cornerRadius={8} background={{ fill: "var(--border)" }} fill={probColor} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", textAlign: "center" }}>
                  <div style={{ fontFamily: "Syne", fontSize: 26, fontWeight: 800, color: probColor, lineHeight: 1 }}>{prob.toFixed(0)}%</div>
                </div>
              </div>
              <div style={{ fontFamily: "Syne", fontWeight: 700, color: probColor, marginTop: 8, fontSize: 12 }}>{result.confidence_label}</div>
            </div>
            <div className="section" style={{ marginBottom: 0 }}>
              <div className="section-title">Key Metrics</div>
              <div className="stat-row"><span className="stat-label">Expected Shortfall</span><span className="stat-value danger">{fmt(result.expected_shortfall)}</span></div>
              <div className="stat-row"><span className="stat-label">Required Monthly</span><span className="stat-value">{fmt(result.required_monthly_contribution)}</span></div>
              <div className="stat-row"><span className="stat-label">Months at Current Rate</span><span className="stat-value">{result.months_to_achieve_at_current_rate}</span></div>
              {result.goal && <>
                <div className="stat-row"><span className="stat-label">Target</span><span className="stat-value">{fmt(result.goal.target_amount)}</span></div>
                <div className="stat-row"><span className="stat-label">Saved So Far</span><span className="stat-value good">{fmt(result.goal.current_amount)}</span></div>
                <div className="stat-row"><span className="stat-label">Deadline</span><span className="stat-value">{result.goal.deadline_months} months</span></div>
              </>}
            </div>
          </div>
          {rangeData.length > 0 && (
            <div className="section">
              <div className="section-title">Projected Outcome Range (Monte Carlo)</div>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={rangeData} barCategoryGap="40%">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                  <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}><Cell fill="#ff4d4d" /><Cell fill="#f59e0b" /><Cell fill="#22c55e" /></Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {Array.isArray(result.recommendations) && result.recommendations.length > 0 && (
            <div className="section">
              <div className="section-title">Recommendations</div>
              {result.recommendations.map((r, i) => (
                <div key={i} className="alert-box alert-warn">
                  💡 {typeof r === "string" ? r : (r?.message || r?.text || r?.tip || Object.values(r).filter(v => typeof v === "string")[0] || "Review your savings plan")}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Engine: Lifestyle Inflation ───────────────────────────────────────────────
function LifestyleInflation({ token, toast }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => { setLoading(true); try { setResult(await api.get("/ai/lifestyle-inflation", token)); toast("Done ✓"); } catch (e) { toast(e?.detail || "Error"); } finally { setLoading(false); } };
  const cats = Object.entries(result?.category_breakdown || {});
  const scoreData = cats.map(([cat, d]) => ({ cat: cat.charAt(0).toUpperCase() + cat.slice(1), score: d.combined_inflation_score ?? 0, pct: d.pct_change_overall ?? 0, inflating: d.inflating }));
  const months = result?.months || [];
  const trendData = months.map((m, i) => {
    const row = { month: m };
    cats.forEach(([cat, d]) => { row[cat] = d.monthly_trend?.[i] ?? 0; });
    return row;
  });
  return (
    <div className="engine-page">
      <div className="engine-header"><div className="engine-icon">📈</div><div><div className="engine-title">Lifestyle Inflation Detector</div><div className="engine-desc">Isolation Forest + % change analysis flags spending growing faster than income</div></div></div>
      <button className="btn-run" onClick={run} disabled={loading}>{loading ? <><span className="spin" /> Analysing...</> : "Run Analysis →"}</button>
      {result && (
        <>
          <div className="cards" style={{ marginTop: 20 }}>
            <div className="card"><div className="card-label">Inflation Score</div><div className={`card-value ${(result.lifestyle_inflation_score || 0) < 30 ? "good" : (result.lifestyle_inflation_score || 0) < 60 ? "warn" : "danger"}`}>{result.lifestyle_inflation_score}/100</div></div>
            <div className="card"><div className="card-label">Status</div><div className="card-value" style={{ fontSize: 16 }}>{result.label}</div></div>
            <div className="card"><div className="card-label">Discretionary / Income</div><div className={`card-value ${(result.discretionary_income_ratio_pct || 0) < 30 ? "good" : (result.discretionary_income_ratio_pct || 0) < 45 ? "warn" : "danger"}`}>{result.discretionary_income_ratio_pct}%</div></div>
            <div className="card"><div className="card-label">Months Analysed</div><div className="card-value">{result.months_analyzed}</div></div>
          </div>
          {scoreData.length > 0 && (
            <div className="two-col">
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Inflation Score by Category</div>
                <ResponsiveContainer width="100%" height={190}>
                  <BarChart data={scoreData} barCategoryGap="35%">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="cat" tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]} name="Score">{scoreData.map((d, i) => <Cell key={i} fill={d.score < 30 ? "#22c55e" : d.score < 60 ? "#f59e0b" : "#ff4d4d"} />)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">% Growth vs Income</div>
                <ResponsiveContainer width="100%" height={190}>
                  <BarChart data={scoreData} barCategoryGap="35%">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="cat" tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
                    <Tooltip formatter={v => `${v}%`} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                    <Bar dataKey="pct" radius={[4, 4, 0, 0]} name="% Change">{scoreData.map((d, i) => <Cell key={i} fill={d.pct <= 5 ? "#22c55e" : d.pct <= 20 ? "#f59e0b" : "#ff4d4d"} />)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {trendData.length > 1 && cats.length > 0 && (
            <div className="section">
              <div className="section-title">Monthly Spending Trends per Category</div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 10, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                  <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                  <Legend wrapperStyle={{ fontSize: 10, fontFamily: "DM Mono" }} />
                  {cats.map(([cat], i) => <Line key={cat} type="monotone" dataKey={cat} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 4 }} />)}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          {Array.isArray(result.inflation_flags) && result.inflation_flags.length > 0 && (
            <div className="section">
              <div className="section-title">Inflation Flags</div>
              {result.inflation_flags.map((f, i) => (
                <div key={i} className={`alert-box ${f.severity === "high" ? "alert-danger" : "alert-warn"}`}>
                  <div><strong>{f.category}</strong> — {f.message}{f.projected_annual_excess > 0 && <span style={{ opacity: .8 }}> · Annual excess: {fmt(f.projected_annual_excess)}</span>}</div>
                </div>
              ))}
            </div>
          )}
          {result.summary && <div className="section"><div className="section-title">Summary</div><div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--muted)" }}>{result.summary}</div></div>}
        </>
      )}
    </div>
  );
}

// ── Engine: Debt Optimizer ────────────────────────────────────────────────────
function DebtOptimizer({ token, toast }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState("avalanche");

  const run = async () => {
    setLoading(true);
    try { setResult(await api.post("/ai/debt-optimization", { strategy: "avalanche" }, token)); toast("Done ✓"); }
    catch (e) { toast(e?.detail || "Error"); }
    finally { setLoading(false); }
  };

  // Backend always returns recommended_plan=avalanche, alternative_plan=snowball
  // We swap based on which strategy the user has selected
  const avalanchePlan = result?.recommended_plan || {};
  const snowballPlan = result?.alternative_plan || {};
  const plan = strategy === "avalanche" ? avalanchePlan : snowballPlan;
  const comparison = result?.avalanche_vs_snowball || {};
  const schedule = (plan.first_24_months_schedule || []).slice(0, 24);
  const scheduleChart = schedule.map(m => ({ month: `M${m.month}`, principal: Math.round(m.principal || 0), interest: Math.round(m.interest || 0) }));
  const payoffOrder = plan.payoff_order || [];
  return (
    <div className="engine-page">
      <div className="engine-header"><div className="engine-icon">🏦</div><div><div className="engine-title">Debt Optimization Planner</div><div className="engine-desc">Avalanche vs Snowball — find the fastest, cheapest path to debt freedom</div></div></div>
      <div className="section">
        <div className="section-title">Choose Strategy</div>
        <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
          {["avalanche", "snowball"].map(s => (
            <button key={s} onClick={() => setStrategy(s)} style={{ padding: "8px 18px", border: `2px solid ${strategy === s ? "var(--ink)" : "var(--border)"}`, borderRadius: 4, background: strategy === s ? "var(--ink)" : "transparent", color: strategy === s ? "var(--accent)" : "var(--muted)", fontFamily: "Syne", fontWeight: 700, fontSize: 12, cursor: "pointer", transition: "all .15s", textTransform: "capitalize" }}>
              {s === "avalanche" ? "⚡ Avalanche" : "❄ Snowball"}
            </button>
          ))}
        </div>
        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>{strategy === "avalanche" ? "Highest interest rate first → minimises total interest paid" : "Smallest balance first → psychological wins, faster loan closures"}</div>
        {result && <div style={{ fontSize: 11, color: "var(--good)", marginBottom: 10 }}>✓ Switch between strategies instantly — both are pre-computed below</div>}
        <button className="btn-run" onClick={run} disabled={loading}>{loading ? <><span className="spin" /> Calculating...</> : result ? "Re-run →" : "Optimise →"}</button>
      </div>
      {result && (
        <>
          <div className="cards">
            <div className="card"><div className="card-label">Total Interest ({strategy})</div><div className="card-value danger">{fmt(plan.total_interest)}</div></div>
            <div className="card"><div className="card-label">Months to Debt-Free</div><div className="card-value warn">{plan.total_months} mo</div></div>
            <div className="card"><div className="card-label">Extra / Month</div><div className="card-value">{fmt(result.extra_monthly_payment)}</div></div>
            <div className="card"><div className="card-label">Total EMI</div><div className="card-value">{fmt(result.total_monthly_emi)}</div></div>
          </div>
          {comparison.recommendation && (
            <div className="two-col">
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Avalanche vs Snowball — Interest Paid</div>
                <ResponsiveContainer width="100%" height={170}>
                  <BarChart data={[
                    { name: "Avalanche", interest: Math.round(avalanchePlan.total_interest || 0) },
                    { name: "Snowball", interest: Math.round(snowballPlan.total_interest || 0) },
                  ]} barCategoryGap="40%">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                    <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                    <Bar dataKey="interest" name="Total Interest" radius={[4,4,0,0]}><Cell fill="#22c55e" /><Cell fill="#ff4d4d" /></Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="section" style={{ marginBottom: 0 }}>
                <div className="section-title">Comparison</div>
                <div className="stat-row"><span className="stat-label">Interest saved with Avalanche</span><span className="stat-value good">{fmt(comparison.interest_saved_with_avalanche)}</span></div>
                <div className="stat-row"><span className="stat-label">Month difference</span><span className="stat-value">{Math.abs(comparison.months_saved_with_avalanche ?? 0)} mo</span></div>
                <div style={{ marginTop: 12 }}><div className="alert-box alert-good">✅ {comparison.recommendation}</div></div>
              </div>
            </div>
          )}
          {scheduleChart.length > 0 && (
            <div className="section">
              <div className="section-title">Monthly Payment — Principal vs Interest (first 24 months)</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={scheduleChart} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 9, fontFamily: "DM Mono" }} axisLine={false} tickLine={false} interval={2} />
                  <YAxis tick={{ fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                  <Tooltip formatter={v => fmt(v)} contentStyle={{ fontFamily: "DM Mono", fontSize: 11, borderRadius: 4 }} />
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: "DM Mono" }} />
                  <Bar dataKey="principal" name="Principal" fill="#0a0a0f" radius={[2,2,0,0]} stackId="a" />
                  <Bar dataKey="interest" name="Interest" fill="#ff4d4d" radius={[2,2,0,0]} stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {payoffOrder.length > 0 && (
            <div className="section">
              <div className="section-title">Payoff Order</div>
              {payoffOrder.map((loan, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ width: 28, height: 28, borderRadius: "50%", background: "var(--ink)", color: "var(--accent)", display: "grid", placeItems: "center", fontFamily: "Syne", fontWeight: 800, fontSize: 13, flexShrink: 0 }}>{i + 1}</div>
                  <div><div style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 13 }}>{loan.name}</div><div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>Paid off in {loan.paid_off_in_months} months</div></div>
                </div>
              ))}
            </div>
          )}
          {result.tips?.length > 0 && (
            <div className="section"><div className="section-title">Smart Tips</div>{result.tips.map((tip, i) => <div key={i} className="alert-box alert-warn">💡 {tip}</div>)}</div>
          )}
        </>
      )}
    </div>
  );
}

// ── App Root ──────────────────────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("zf_token"));
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem("zf_user")); } catch { return null; } });
  const [page, setPage] = useState("dashboard");
  const [toastMsg, setToastMsg] = useState(null);
  const toast = (msg) => { setToastMsg(msg); setTimeout(() => setToastMsg(null), 2500); };
  const onLogin = (t, u) => { localStorage.setItem("zf_token", t); localStorage.setItem("zf_user", JSON.stringify(u)); setToken(t); setUser(u); };
  const logout = () => { localStorage.removeItem("zf_token"); localStorage.removeItem("zf_user"); setToken(null); setUser(null); };

  const navItems = [
    { section: "Overview" },
    { id: "dashboard", icon: "⬡", label: "Dashboard" },
    { section: "Data" },
    { id: "transactions", icon: "⇄", label: "Transactions" },
    { id: "loans", icon: "◈", label: "Loans & EMIs" },
    { id: "goals", icon: "◎", label: "Goals" },
    { section: "AI Engines" },
    { id: "salary", icon: "💰", label: "Salary Allocation" },
    { id: "stress", icon: "📊", label: "Stress Index" },
    { id: "whatif", icon: "🔮", label: "What-If Simulation" },
    { id: "goalprob", icon: "🎯", label: "Goal Probability" },
    { id: "inflation", icon: "📈", label: "Lifestyle Inflation" },
    { id: "debt", icon: "🏦", label: "Debt Optimizer" },
  ];

  if (!token || !user) return (<><style>{styles}</style><AuthPage onLogin={onLogin} /></>);

  const pages = {
    dashboard: <Dashboard token={token} user={user} />,
    transactions: <Transactions token={token} toast={toast} />,
    loans: <Loans token={token} toast={toast} />,
    goals: <Goals token={token} toast={toast} />,
    salary: <SalaryAllocation token={token} toast={toast} />,
    stress: <StressIndex token={token} toast={toast} />,
    whatif: <WhatIfSim token={token} toast={toast} />,
    goalprob: <GoalProbability token={token} toast={toast} />,
    inflation: <LifestyleInflation token={token} toast={toast} />,
    debt: <DebtOptimizer token={token} toast={toast} />,
  };

  return (
    <>
      <style>{styles}</style>
      <div className="shell">
        <aside className="sidebar">
          <div className="sidebar-logo">SMART <span>SPENDFIN</span></div>
          <nav className="nav">
            {navItems.map((n, i) => n.section
              ? <div key={i} className="nav-section">{n.section}</div>
              : <button key={n.id} className={`nav-item ${page === n.id ? "active" : ""}`} onClick={() => setPage(n.id)}>
                  <span className="nav-icon">{n.icon}</span>{n.label}
                </button>
            )}
          </nav>
          <div className="sidebar-footer">
            <div className="user-pill">
              <div className="user-avatar">{user.name[0].toUpperCase()}</div>
              <div className="user-name">{user.name}</div>
              <button className="logout-btn" onClick={logout} title="Sign out">⏻</button>
            </div>
          </div>
        </aside>
        <main className="main">{pages[page]}</main>
      </div>
      {toastMsg && <Toast msg={toastMsg} />}
    </>
  );
}
