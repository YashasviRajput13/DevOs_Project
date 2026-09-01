"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import TopNav from "@/components/TopNav";
import { api, Project } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function CreateProjectModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { refreshProjects } = useAuth();
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      const p = await api.projects.create(name.trim(), desc.trim());
      await refreshProjects();
      onCreated();
      router.push(`/projects/${p.id}`);
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
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 20 }}>Create New Project</h2>
        <form onSubmit={submit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--text-muted)", marginBottom: 8 }}>Project Name</label>
            <input
              value={name} onChange={e => setName(e.target.value)}
              placeholder="e.g. Acme Engine"
              autoFocus
              style={{
                width: "100%", padding: "10px 12px", borderRadius: 8,
                border: "1px solid var(--border)", background: "var(--bg)",
                color: "var(--text)", fontSize: 14, boxSizing: "border-box", outline: "none"
              }}
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--text-muted)", marginBottom: 8 }}>Description (optional)</label>
            <textarea
              value={desc} onChange={e => setDesc(e.target.value)}
              placeholder="What is this project?"
              rows={2}
              style={{
                width: "100%", padding: "10px 12px", borderRadius: 8,
                border: "1px solid var(--border)", background: "var(--bg)",
                color: "var(--text)", fontSize: 14, boxSizing: "border-box", outline: "none", resize: "none"
              }}
            />
          </div>
          {err && <p style={{ color: "var(--red)", fontSize: 12, marginBottom: 12 }}>{err}</p>}
          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
            <button type="button" onClick={onClose} style={{
              padding: "10px 16px", borderRadius: 8, border: "1px solid var(--border)",
              background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: 13, fontWeight: 500
            }}>Cancel</button>
            <button type="submit" disabled={loading || !name.trim()} style={{
              padding: "10px 16px", borderRadius: 8, border: "none",
              background: loading || !name.trim() ? "var(--bg-hover)" : "var(--accent)", color: "white", cursor: loading || !name.trim() ? "not-allowed" : "pointer",
              fontSize: 13, fontWeight: 500, transition: "background 0.2s"
            }}>
              {loading ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function JoinProjectModal({ onClose, onJoined }: { onClose: () => void; onJoined: () => void }) {
  const { refreshProjects } = useAuth();
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!token.trim()) return;
    setLoading(true);
    try {
      const res = await api.projects.acceptInvitation(token.trim());
      await refreshProjects();
      onJoined();
      router.push(`/projects/${res.project_id}`);
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
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 20 }}>Join Project</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>Enter an invitation token provided by a project administrator to gain access.</p>
        <form onSubmit={submit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--text-muted)", marginBottom: 8 }}>Invitation Token</label>
            <input
              value={token} onChange={e => setToken(e.target.value)}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              autoFocus
              style={{
                width: "100%", padding: "10px 12px", borderRadius: 8,
                border: "1px solid var(--border)", background: "var(--bg)",
                color: "var(--text)", fontSize: 13, boxSizing: "border-box", outline: "none", fontFamily: "monospace"
              }}
            />
          </div>
          {err && <p style={{ color: "var(--red)", fontSize: 12, marginBottom: 12 }}>{err}</p>}
          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
            <button type="button" onClick={onClose} style={{
              padding: "10px 16px", borderRadius: 8, border: "1px solid var(--border)",
              background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: 13, fontWeight: 500
            }}>Cancel</button>
            <button type="submit" disabled={loading || !token.trim()} style={{
              padding: "10px 16px", borderRadius: 8, border: "none",
              background: loading || !token.trim() ? "var(--bg-hover)" : "var(--accent)", color: "white", cursor: loading || !token.trim() ? "not-allowed" : "pointer",
              fontSize: 13, fontWeight: 500, transition: "background 0.2s"
            }}>
              {loading ? "Joining..." : "Join Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  const { user, projects, loading } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);

  if (loading) return null;
  if (!user) return null; // Context redirects if not logged in

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      {showCreate && <CreateProjectModal onClose={() => setShowCreate(false)} onCreated={() => setShowCreate(false)} />}
      {showJoin && <JoinProjectModal onClose={() => setShowJoin(false)} onJoined={() => setShowJoin(false)} />}
      
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "64px 24px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 48 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>My Projects</h1>
            <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Manage your developer workspaces</p>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <button onClick={() => setShowJoin(true)} style={{
              padding: "10px 20px", borderRadius: 8, border: "1px solid var(--border)",
              background: "var(--bg-card)", color: "var(--text)", cursor: "pointer",
              fontSize: 13, fontWeight: 500, display: "flex", alignItems: "center", gap: 8
            }}>
              Join with Token
            </button>
            <button onClick={() => setShowCreate(true)} style={{
              padding: "10px 20px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500, display: "flex", alignItems: "center", gap: 8,
              boxShadow: "0 0 15px rgba(6,182,212,0.3)"
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
              Create New Project
            </button>
          </div>
        </div>

        {projects.length === 0 ? (
          <div style={{
            textAlign: "center", padding: "64px 24px", border: "1px dashed var(--border)",
            borderRadius: 16, background: "var(--bg-card)", display: "flex", flexDirection: "column",
            alignItems: "center"
          }}>
            <div style={{ width: 48, height: 48, borderRadius: "50%", background: "rgba(6,182,212,0.1)", color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Welcome to DevOs</h3>
            <p style={{ color: "var(--text-muted)", fontSize: 13, maxWidth: 300, lineHeight: 1.5, marginBottom: 24 }}>
              Create your first project to connect GitHub repositories and start analyzing code with AI.
            </p>
            <button onClick={() => setShowCreate(true)} style={{
              padding: "10px 20px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500,
            }}>
              Create Project
            </button>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
            {projects.map(p => (
              <div key={p.id} style={{
                background: "var(--bg-card)", border: "1px solid var(--border)",
                borderRadius: 12, padding: 20, display: "flex", flexDirection: "column",
                transition: "border-color 0.2s"
              }}
                onMouseEnter={e => e.currentTarget.style.borderColor = "var(--accent)"}
                onMouseLeave={e => e.currentTarget.style.borderColor = "var(--border)"}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--text)" }}>{p.name}</h3>
                  {/* @ts-ignore */}
                  {p.role === "OWNER" && (
                     <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 12, background: "rgba(6,182,212,0.1)", color: "var(--accent)", fontWeight: 600 }}>OWNER</span>
                   )}
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 24, display: "flex", alignItems: "center", gap: 8 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20M4 19.5V5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2H6.5A2.5 2.5 0 014 19.5z"/></svg>
                  {p.repositories?.length || 0} repositories
                </div>
                
                <div style={{ marginTop: "auto", display: "flex", justifyContent: "flex-end", borderTop: "1px solid var(--border)", paddingTop: 16 }}>
                  <Link href={`/projects/${p.id}`} style={{
                    color: "var(--text)", textDecoration: "none", fontSize: 13, fontWeight: 500,
                    display: "flex", alignItems: "center", gap: 6, transition: "color 0.2s"
                  }}
                    onMouseEnter={e => e.currentTarget.style.color = "var(--accent)"}
                    onMouseLeave={e => e.currentTarget.style.color = "var(--text)"}
                  >
                    Open Project →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
