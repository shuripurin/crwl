"use client";

import { useEffect, useState } from "react";
import Image from "next/image";

interface Agent {
  agent_id: string;
  agent_type: string;
  status: string;
  updated_at: string;
}

interface Log {
  agent_id: string;
  agent_type: string;
  status: string;
  message: string;
  created_at: string;
}

interface Stats {
  total: number;
  labeled: number;
  unlabeled: number;
  agents: Agent[];
  recent_logs: Log[];
}

interface Result {
  id: number;
  topic: string;
  url: string;
  title: string;
  content: string;
  labeled: boolean;
  labels: Record<string, string> | null;
  created_at: string;
}

type View = "dashboard" | "agents" | "log" | "results";

function sc(status: string) {
  if (status === "running") return "running";
  if (status === "error") return "error";
  return "done";
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function badgeClass(val: string) {
  const v = val.toLowerCase();
  if (v === "high" || v === "yes" || v === "true") return "badge-green";
  if (v === "low" || v === "no" || v === "false") return "badge-red";
  if (v === "medium") return "badge-yellow";
  return "badge-muted";
}

export default function Page() {
  const [mounted, setMounted] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [now, setNow] = useState("");
  const [view, setView] = useState<View>("dashboard");

  useEffect(() => {
    setMounted(true);
    setNow(new Date().toLocaleTimeString());
    const tick = setInterval(
      () => setNow(new Date().toLocaleTimeString()),
      1000,
    );
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    async function poll() {
      try {
        const [s, r] = await Promise.all([
          fetch("/api/stats").then((res) => res.json()),
          fetch("/api/results").then((res) => res.json()),
        ]);
        setStats(s);
        setResults(r);
      } catch (err) {
        console.error("poll error:", err);
      }
    }
    poll();
    const id = setInterval(poll, 1000);
    return () => clearInterval(id);
  }, []);

  const pct =
    stats && stats.total > 0
      ? Math.round((stats.labeled / stats.total) * 100)
      : 0;

  if (!mounted) return <div className="shell" />;

  const navItems: { key: View; label: string }[] = [
    { key: "dashboard", label: "Dashboard" },
    { key: "agents", label: "Agents" },
    { key: "log", label: "Activity Log" },
    { key: "results", label: "Results" },
  ];

  return (
    <div className="shell">
      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-logo">
          <Image
            src="/logo.png"
            alt="crwl"
            width={32}
            height={32}
            className="sidebar-logo-img"
          />
          <div>
            <h1>crwl</h1>
            <p>Research Labeler</p>
          </div>
        </div>
        <div className="nav-section-label">Menu</div>
        {navItems.map(({ key, label }) => (
          <button
            key={key}
            className={`nav-item ${view === key ? "active" : ""}`}
            onClick={() => setView(key)}
          >
            <span className="nav-dot" />
            {label}
          </button>
        ))}
        <div className="sidebar-footer">
          <span className="live-dot" />
          Live · 1s poll
        </div>
      </nav>

      {/* Main area */}
      <main className="main">
        {/* WaterPod-style top stat bar */}
        <div className="stat-topbar">
          <div className="stat-topbar-item">
            <div className="stat-topbar-label">Total Results</div>
            <div className="stat-topbar-val">
              {stats?.total ?? "—"}
              <span className="stat-topbar-unit">results</span>
            </div>
          </div>
          <div className="stat-topbar-divider" />
          <div className="stat-topbar-item">
            <div className="stat-topbar-label">Labeled</div>
            <div className="stat-topbar-val">
              {stats?.labeled ?? "—"}
              <span className="stat-topbar-unit">done</span>
            </div>
          </div>
          <div className="stat-topbar-divider" />
          <div className="stat-topbar-item">
            <div className="stat-topbar-label">Unlabeled</div>
            <div className="stat-topbar-val">
              {stats?.unlabeled ?? "—"}
              <span className="stat-topbar-unit">pending</span>
            </div>
          </div>
          <div className="stat-topbar-divider" />
          <div className="stat-topbar-item">
            <div className="stat-topbar-label">Agents Online</div>
            <div className="stat-topbar-val">
              {stats?.agents.filter((a) => a.status === "running").length ??
                "—"}
              <span className="stat-topbar-unit">
                / {stats?.agents.length ?? "—"}
              </span>
            </div>
          </div>
          <div className="stat-topbar-right">
            <div className="topbar-pill">
              <span className="live-dot" />
              {pct}% complete
            </div>
            <span className="topbar-time" suppressHydrationWarning>
              {now}
            </span>
          </div>
        </div>

        <div className="page-content">
          {/* ── Dashboard ── */}
          {view === "dashboard" && (
            <div className="bento">
              {/* Progress + overview — pastel card */}
              <div className="card card-pastel bento-2">
                <div className="card-header">
                  <div>
                    <div className="card-title">Overview</div>
                    <div className="card-subtitle">live · updates every 1s</div>
                  </div>
                </div>
                <div className="inline-stats">
                  <div className="inline-stat">
                    <div className="inline-stat-label">Total</div>
                    <div className="inline-stat-val">{stats?.total ?? "—"}</div>
                    <div className="inline-stat-sub">results crawled</div>
                  </div>
                  <div className="inline-stat">
                    <div className="inline-stat-label">Labeled</div>
                    <div className="inline-stat-val">
                      {stats?.labeled ?? "—"}
                    </div>
                    <div className="inline-stat-sub">{pct}% of total</div>
                  </div>
                  <div className="inline-stat">
                    <div className="inline-stat-label">Remaining</div>
                    <div className="inline-stat-val">
                      {stats?.unlabeled ?? "—"}
                    </div>
                    <div className="inline-stat-sub">to classify</div>
                  </div>
                </div>
                <div className="progress-wrap">
                  <div className="progress-label">
                    <span>Labeling progress</span>
                    <span>{pct}%</span>
                  </div>
                  <div className="progress-track">
                    <div
                      className="progress-fill"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Agents card */}
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">Agents</div>
                    <div className="card-subtitle">
                      {stats?.agents.length ?? 0} recorded
                    </div>
                  </div>
                </div>
                <div className="agents-list">
                  {stats && stats.agents.length > 0 ? (
                    stats.agents.slice(0, 4).map((a) => (
                      <div className="agent-row" key={a.agent_id}>
                        <div className="agent-info">
                          <div className="agent-id">{a.agent_id}</div>
                          <div className="agent-type">{a.agent_type}</div>
                        </div>
                        <span className={`status-tag ${sc(a.status)}`}>
                          {a.status}
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="agents-empty">No agents yet.</p>
                  )}
                </div>
              </div>

              {/* Activity log card */}
              <div className="card bento-3">
                <div className="card-header">
                  <div>
                    <div className="card-title">Recent Activity</div>
                    <div className="card-subtitle">last 5 events</div>
                  </div>
                </div>
                <div className="log-list">
                  {stats && stats.recent_logs.length > 0 ? (
                    stats.recent_logs.slice(0, 5).map((l) => (
                      <div
                        className="log-row"
                        key={`${l.created_at}-${l.agent_id}`}
                      >
                        <span className="log-time">
                          {fmtTime(l.created_at)}
                        </span>
                        <span className="log-agent">{l.agent_id}</span>
                        <span className={`log-status ${sc(l.status)}`}>
                          {l.status}
                        </span>
                        <span className="log-msg">{l.message}</span>
                      </div>
                    ))
                  ) : (
                    <div className="log-empty">No activity yet.</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ── Agents ── */}
          {view === "agents" && (
            <>
              <p className="section-title">
                All Agents ({stats?.agents.length ?? 0})
              </p>
              <div className="agents-list">
                {stats && stats.agents.length > 0 ? (
                  stats.agents.map((a) => (
                    <div className="agent-row" key={a.agent_id}>
                      <div className="agent-info">
                        <div className="agent-id">{a.agent_id}</div>
                        <div className="agent-type">{a.agent_type}</div>
                      </div>
                      <span className="agent-ts">{fmtTime(a.updated_at)}</span>
                      <span className={`status-tag ${sc(a.status)}`}>
                        {a.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="agents-empty">No agents recorded yet.</p>
                )}
              </div>
            </>
          )}

          {/* ── Activity Log ── */}
          {view === "log" && (
            <>
              <p className="section-title">
                Activity Log ({stats?.recent_logs.length ?? 0} events)
              </p>
              <div className="card">
                <div className={`log-list log-scroll-full`}>
                  {stats && stats.recent_logs.length > 0 ? (
                    stats.recent_logs.map((l) => (
                      <div
                        className="log-row"
                        key={`${l.created_at}-${l.agent_id}`}
                      >
                        <span className="log-time">
                          {fmtTime(l.created_at)}
                        </span>
                        <span className="log-agent">{l.agent_id}</span>
                        <span className={`log-status ${sc(l.status)}`}>
                          {l.status}
                        </span>
                        <span className="log-msg">{l.message}</span>
                      </div>
                    ))
                  ) : (
                    <div className="log-empty">No activity yet.</div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* ── Results ── */}
          {view === "results" && (
            <>
              <p className="section-title">Results ({results.length})</p>
              <div className="card">
                <div className="results-table-wrap">
                  {results.length > 0 ? (
                    <table className="results-table">
                      <thead>
                        <tr>
                          <th>Title</th>
                          <th>URL</th>
                          <th>Topic</th>
                          <th>Labels</th>
                          <th>Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.map((r) => (
                          <tr key={r.id}>
                            <td className="td-title">
                              {r.title || "Untitled"}
                            </td>
                            <td className="td-url">
                              <a
                                href={r.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {r.url}
                              </a>
                            </td>
                            <td>{r.topic}</td>
                            <td>
                              <div className="badge-group">
                                {r.labels ? (
                                  Object.entries(r.labels).map(([k, v]) => (
                                    <span
                                      className={`badge ${badgeClass(v)}`}
                                      key={k}
                                    >
                                      {k}: {v}
                                    </span>
                                  ))
                                ) : (
                                  <span className="badge badge-muted">
                                    unlabeled
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="td-ts">{fmtTime(r.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="log-empty">No results yet.</div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
