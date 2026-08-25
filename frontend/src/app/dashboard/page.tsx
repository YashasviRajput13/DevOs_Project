"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import TopNav from "@/components/TopNav";
import { api, Project } from "@/lib/api";

function StatusBadge({ indexed }: { indexed: boolean }) {
  return (
    <span style={{
      fontSize: 11, fontWeight: 500, padding: "2px 8px", borderRadius: 20,
      background: indexed ? "rgba(34,197,94,0.1)" : "rgba(107,107,138,0.1)",
      color: indexed ? "var(--green)" : "var(--text-muted)",
      border: `1px solid ${indexed ? "rgba(34,197,94,0.2)" : "var(--border)"}`,
    }}>
      {indexed ? "Indexed" : "Not indexed"}
    </span>
  );
}

function CreateProjectModal({ onClose, onCreated }: { onClose: () => void; onCreated: (p: Project) => void }) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      const p = await api.projects.create(name.trim());
      onCreated(p);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 200,
      display: "flex", alignItems: "center", justifyContent: "center",
    }} onClick={onClose}>
      <div style={{
        background: "var(--bg-card)", border: "1px solid var(--border)",
        borderRadius: 12, padding: 28, width: 400, maxWidth: "90vw",
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
              color: "var(--text)", fontSize: 14, marginBottom: 16,
            }}
          />
          {error && <p style={{ color: "var(--red)", fontSize: 12, marginBottom: 12 }}>{error}</p>}
          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
            <button type="button" onClick={onClose} style={{
              padding: "8px 16px", borderRadius: 8, border: "1px solid var(--border)",
              background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: 13,
            }}>Cancel</button>
            <button type="submit" disabled={loading || !name.trim()} style={{
              padding: "8px 16px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer", fontSize: 13, fontWeight: 500,
              opacity: loading ? 0.7 : 1,
            }}>
              {loading ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => { loadProjects(); }, []);

  async function loadProjects() {
    try {
      const data = await api.projects.list();
      setProjects(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const totalRepos = projects.reduce((n, p) => n + p.repositories.length, 0);
  const totalIndexed = projects.reduce((n, p) => n + p.repositories.filter(r => r.indexed).length, 0);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ maxWidth: 960, margin: "0 auto", padding: "40px 24px" }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 40 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Dashboard</h1>
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Your AI-powered repository workspace</p>
          </div>
          <button onClick={() => setShowCreate(true)} style={{
            padding: "8px 16px", borderRadius: 8, border: "none",
            background: "var(--accent)", color: "white", cursor: "pointer",
            fontSize: 13, fontWeight: 500,
          }}>
            + New Project
          </button>
        </div>

        {/* Stats row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 36 }}>
          {[
            { label: "Projects", value: projects.length },
            { label: "Repositories", value: totalRepos },
            { label: "Indexed", value: totalIndexed },
          ].map(s => (
            <div key={s.label} style={{
              background: "var(--bg-card)", border: "1px solid var(--border)",
              borderRadius: 10, padding: "16px 20px",
            }}>
              <div style={{ fontSize: 24, fontWeight: 700, marginBottom: 2 }}>{s.value}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div style={{ color: "var(--text-muted)", textAlign: "center", padding: 48 }}>Loading projects...</div>
        ) : error ? (
          <div style={{
            background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: 10, padding: 20, color: "var(--red)",
          }}>
            <div style={{ fontWeight: 500, marginBottom: 4 }}>Cannot reach backend</div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>{error} — ensure the backend is running on {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</div>
          </div>
        ) : projects.length === 0 ? (
          <div style={{
            border: "1px dashed var(--border)", borderRadius: 12, padding: 48,
            textAlign: "center",
          }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>◈</div>
            <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 8 }}>No projects yet</div>
            <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>Create a project to connect your first GitHub repository.</div>
            <button onClick={() => setShowCreate(true)} style={{
              padding: "8px 20px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500,
            }}>Create Project</button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {projects.map(project => (
              <div key={project.id}>
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  marginBottom: 12,
                }}>
                  <h2 style={{ fontSize: 15, fontWeight: 600 }}>{project.name}</h2>
                  <Link href={`/projects/${project.id}`} style={{
                    fontSize: 12, color: "var(--accent)", textDecoration: "none",
                  }}>View project →</Link>
                </div>

                {project.repositories.length === 0 ? (
                  <Link href={`/projects/${project.id}`} style={{
                    display: "block", border: "1px dashed var(--border)",
                    borderRadius: 10, padding: "16px 20px", textDecoration: "none",
                    color: "var(--text-muted)", fontSize: 13, textAlign: "center",
                  }}>
                    + Connect a repository
                  </Link>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
                    {project.repositories.map(repo => (
                      <Link key={repo.id}
                        href={`/projects/${project.id}/repositories/${repo.id}/overview`}
                        style={{ textDecoration: "none" }}
                      >
                        <div style={{
                          background: "var(--bg-card)", border: "1px solid var(--border)",
                          borderRadius: 10, padding: "16px 20px",
                          cursor: "pointer",
                          transition: "border-color 0.15s",
                        }}
                          onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--accent)")}
                          onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
                        >
                          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
                            <div>
                              <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 2 }}>{repo.name}</div>
                              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{repo.full_name}</div>
                            </div>
                            <StatusBadge indexed={repo.indexed} />
                          </div>
                          <div style={{ fontSize: 11, color: "var(--text-dim)", display: "flex", gap: 12 }}>
                            {repo.files_count > 0 && <span>{repo.files_count} files</span>}
                            <span>{repo.default_branch}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
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
