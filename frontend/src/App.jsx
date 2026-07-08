import { useEffect, useState } from "react";
import "./App.css";

const AGENTS = [
  { key: "email",    label: "Email",    icon: "📧", reportKey: "email_report" },
  { key: "calendar", label: "Calendar", icon: "📅", reportKey: "calendar_report" },
  { key: "news",     label: "Markets",  icon: "📈", reportKey: "news_report" },
  { key: "monitor",  label: "Health",   icon: "🩺", reportKey: "monitor_report" },
];

export default function App() {
  // useState = React's memory. When these change, the UI re-renders itself.
  const [running, setRunning] = useState(false);
  const [finished, setFinished] = useState({});   // {email: true, ...}
  const [reports, setReports] = useState({});     // {email_report: "...", ...}
  const [metrics, setMetrics] = useState([]);
  const [activeTab, setActiveTab] = useState("email");
  const [history, setHistory] = useState([]);

  // useEffect with [] = "run once when the page loads"
  useEffect(() => {
    fetch("http://localhost:8000/api/history")
      .then((r) => r.json())
      .then(setHistory)
      .catch(() => {});
  }, []);

  const runBriefing = () => {
    setRunning(true);
    setFinished({});
    setReports({});
    setMetrics([]);

    // EventSource = the browser's built-in SSE client.
    // Every yield from the FastAPI generator arrives here as a message.
    const source = new EventSource("http://localhost:8000/api/run/stream");

    source.onmessage = (event) => {
      const { node, update } = JSON.parse(event.data);

      if (node === "__done__") {
        source.close();
        setRunning(false);
        return;
      }

      setFinished((prev) => ({ ...prev, [node]: true }));
      setReports((prev) => ({ ...prev, ...update }));
      if (update.agent_metrics) {
        setMetrics((prev) => [...prev, ...update.agent_metrics]);
      }
    };

    source.onerror = () => {
      source.close();
      setRunning(false);
    };
  };

  const active = AGENTS.find((a) => a.key === activeTab);

  return (
    <div className="app">
      <header>
        <h1>☀️ Morning Agents</h1>
        <p className="subtitle">Your multi-agent daily briefing</p>
        <button className="run-btn" onClick={runBriefing} disabled={running}>
          {running ? "Agents running…" : "🚀 Run Briefing"}
        </button>
      </header>

      {/* Live agent status cards */}
      <div className="agent-grid">
        {AGENTS.map((a) => (
          <div
            key={a.key}
            className={`agent-card ${finished[a.key] ? "done" : ""} ${
              running && !finished[a.key] ? "working" : ""
            }`}
          >
            <span className="icon">{a.icon}</span>
            <span>{a.label}</span>
            <span className="status">
              {finished[a.key] ? "✅" : running ? "⏳" : "•"}
            </span>
          </div>
        ))}
      </div>

      {/* Report tabs */}
      {Object.keys(reports).length > 0 && (
        <div className="results">
          <div className="tabs">
            {AGENTS.map((a) => (
              <button
                key={a.key}
                className={activeTab === a.key ? "tab active" : "tab"}
                onClick={() => setActiveTab(a.key)}
              >
                {a.icon} {a.label}
              </button>
            ))}
          </div>
          <pre className="report">
            {reports[active.reportKey] || "Waiting for this agent…"}
          </pre>

          {activeTab === "monitor" && metrics.length > 0 && (
            <table className="metrics">
              <thead>
                <tr><th>Agent</th><th>Status</th><th>Seconds</th><th>Items</th></tr>
              </thead>
              <tbody>
                {metrics.map((m, i) => (
                  <tr key={i}>
                    <td>{m.agent_name}</td>
                    <td>{m.status === "success" ? "✅" : "❌"}</td>
                    <td>{m.duration_seconds}</td>
                    <td>{m.items_processed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Run history from past days */}
      {history.length > 0 && (
        <div className="history">
          <h3>Past runs</h3>
          {history.slice().reverse().map((run, i) => (
            <div key={i} className="history-row">
              <span>{new Date(run.run_at).toLocaleString()}</span>
              <span>
                {run.metrics.map((m) =>
                  m.status === "success" ? "✅" : "❌"
                ).join(" ")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}