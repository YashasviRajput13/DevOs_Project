"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import TopNav from "@/components/TopNav";
import { api, Project } from "@/lib/api";

// ── Helpers ──────────────────────────────────────────────────────────────────

function StatusBadge({ indexed }: { indexed: boolean }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 20,
      letterSpacing: "0.04em", textTransform: "uppercase",
      background: indexed ? "rgba(34,197,94,0.10)" : "rgba(107,107,138,0.10)",
      color: indexed ? "var(--green)" : "var(--text-muted)",
      border: `1px solid ${indexed ? "rgba(34,197,94,0.22)" : "var(--border)"}`,
      flexShrink: 0,
    }}>
      {indexed ? "● Indexed" : "◌ Not indexed"}
    </span>
  );
}

function CreateProjectModal({ onClose, onCreated }: { onClose: () => void; onCreated: (p: Project) => void }) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      const p = await api.projects.create(name.trim());
      onCreated(p);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 200,
      display: "flex", alignItems: "center", justifyContent: "center",
    }} onClick={onClose}>
      <div style={{
        background: "var(--bg-card)", border: "1px solid var(--border)",
        borderRadius: 14, padding: 28, width: 420, maxWidth: "90vw",
      }} onClick={e => e.stopPropagation()}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>New Project</h2>
        <form onSubmit={submit}>
          <input
            value={name} onChange={e => setName(e.target.value)}
            placeholder="Project name"
            autoFocus
            style={{
              width: "100%", padding: "10px 12px", borderRadius: 8,
              border: "1px solid var(--border)", background: "var(--bg)",
              color: "var(--text)", fontSize: 14, marginBottom: 16, boxSizing: "border-box",
            }}
          />
          {err && <p style={{ color: "var(--red)", fontSize: 12, marginBottom: 12 }}>{err}</p>}
          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
            <button type="button" onClick={onClose} style={{
              padding: "8px 16px", borderRadius: 8, border: "1px solid var(--border)",
              background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: 13,
            }}>Cancel</button>
            <button type="submit" disabled={loading || !name.trim()} style={{
              padding: "8px 16px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500, opacity: loading ? 0.7 : 1,
            }}>
              {loading ? "Creating…" : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => { loadProjects(); }, []);

  async function loadProjects() {
    try {
      setProjects(await api.projects.list());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const totalRepos = projects.reduce((n, p) => n + p.repositories.length, 0);
  const totalIndexed = projects.reduce((n, p) => n + p.repositories.filter(r => r.indexed).length, 0);
  const totalFiles = projects.reduce((n, p) => n + p.repositories.reduce((m, r) => m + (r.files_count ?? 0), 0), 0);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px" }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 32 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Dashboard</h1>
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Your AI-powered repository workspace</p>
          </div>
          <button onClick={() => setShowCreate(true)} style={{
            padding: "8px 18px", borderRadius: 8, border: "none",
            background: "var(--accent)", color: "white", cursor: "pointer",
            fontSize: 13, fontWeight: 500,
          }}>
            + New Project
          </button>
        </div>

        {/* Stats row */}
        {!loading && !error && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 36 }}>
            {[
              { label: "Projects", value: projects.length },
              { label: "Repositories", value: totalRepos },
              { label: "Indexed", value: `${totalIndexed} / ${totalRepos}` },
              { label: "Total Files", value: totalFiles.toLocaleString() },
            ].map(s => (
              <div key={s.label} style={{
                background: "var(--bg-card)", border: "1px solid var(--border)",
                borderRadius: 10, padding: "16px 20px",
              }}>
                <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 3 }}>{s.value}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div style={{ color: "var(--text-muted)", textAlign: "center", padding: 60 }}>
            Loading projects…
          </div>
        ) : error ? (
          <div style={{
            background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: 10, padding: 20, color: "var(--red)",
          }}>
            <div style={{ fontWeight: 500, marginBottom: 4 }}>Cannot reach backend</div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>
              {error} — ensure the backend is running on {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </div>
          </div>
        ) : projects.length === 0 ? (
          <div style={{
            border: "1px dashed var(--border)", borderRadius: 12,
            padding: 56, textAlign: "center",
          }}>
            <div style={{ fontSize: 36, marginBottom: 16 }}>◈</div>
            <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 8 }}>No projects yet</div>
            <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 22 }}>
              Create a project and connect your first GitHub repository.
            </div>
            <button onClick={() => setShowCreate(true)} style={{
              padding: "8px 22px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500,
            }}>Create Project</button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
            {projects.map(project => (
              <div key={project.id}>
                {/* Project header */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <h2 style={{ fontSize: 15, fontWeight: 600 }}>{project.name}</h2>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {project.repositories.length} {project.repositories.length === 1 ? "repo" : "repos"}
                    </span>
                  </div>
                  <Link href={`/projects/${project.id}`} style={{
                    fontSize: 12, color: "var(--accent)", textDecoration: "none",
                    padding: "4px 12px", borderRadius: 6, border: "1px solid rgba(99,102,241,0.2)",
                  }}>
                    Manage →
                  </Link>
                </div>

                {/* Repo cards */}
                {project.repositories.length === 0 ? (
                  <Link href={`/projects/${project.id}`} style={{
                    display: "block", border: "1px dashed var(--border)",
                    borderRadius: 10, padding: "14px 20px", textDecoration: "none",
                    color: "var(--text-muted)", fontSize: 13, textAlign: "center",
                  }}>
                    + Connect a repository
                  </Link>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
                    {project.repositories.map(repo => {
                      const ghUrl = repo.url || `https://github.com/${repo.full_name}`;
                      return (
                        <div key={repo.id} style={{
                          background: "var(--bg-card)",
                          border: `1px solid ${repo.indexed ? "rgba(34,197,94,0.15)" : "var(--border)"}`,
                          borderRadius: 10, padding: "16px 18px",
                          display: "flex", flexDirection: "column", gap: 10,
                          transition: "border-color 0.2s",
                        }}
                          onMouseEnter={e => (e.currentTarget.style.borderColor = repo.indexed ? "rgba(34,197,94,0.35)" : "var(--accent)")}
                          onMouseLeave={e => (e.currentTarget.style.borderColor = repo.indexed ? "rgba(34,197,94,0.15)" : "var(--border)")}
                        >
                          {/* Name + badge */}
                          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
                            <div>
                              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{repo.name}</div>
                              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{repo.full_name}</div>
                            </div>
                            <StatusBadge indexed={repo.indexed} />
                          </div>

                          {/* GitHub URL */}
                          <a
                            href={ghUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            style={{ fontSize: 11, color: "var(--text-muted)", textDecoration: "none", wordBreak: "break-all" }}
                            onMouseEnter={e => (e.currentTarget.style.color = "var(--accent)")}
                            onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
                          >
                            {ghUrl} ↗
                          </a>

                          {/* Stats row */}
                          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                            {repo.files_count > 0 && (
                              <span style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg)", border: "1px solid var(--border)", padding: "2px 7px", borderRadius: 5 }}>
                                <span style={{ color: "var(--text)", fontWeight: 500 }}>{repo.files_count}</span> files
                              </span>
                            )}
                            <span style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg)", border: "1px solid var(--border)", padding: "2px 7px", borderRadius: 5 }}>
                              {repo.default_branch}
                            </span>
                          </div>

                          {/* Action */}
                          <div style={{ marginTop: 2 }}>
                            {repo.indexed ? (
                              <Link
                                href={`/projects/${project.id}/repositories/${repo.id}/overview`}
                                style={{
                                  display: "inline-block", padding: "6px 16px", borderRadius: 7,
                                  background: "var(--accent)", color: "white",
                                  textDecoration: "none", fontSize: 12, fontWeight: 500,
                                }}
                              >
                                Open →
                              </Link>
                            ) : (
                              <Link
                                href={`/projects/${project.id}`}
                                style={{
                                  display: "inline-block", padding: "6px 14px", borderRadius: 7,
                                  border: "1px solid var(--border)", color: "var(--text-muted)",
                                  textDecoration: "none", fontSize: 12,
                                }}
                              >
                                Index this repo →
                              </Link>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <CreateProjectModal
          onClose={() => setShowCreate(false)}
          onCreated={p => { setProjects(prev => [p, ...prev]); setShowCreate(false); }}
        />
      )}
    </div>
  );
}
