"use client";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import TopNav from "@/components/TopNav";
import { api, Project, Repository } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

type IndexStatus = "idle" | "indexing" | "done" | "error";

interface RepoState {
  status: IndexStatus;
  result?: { files_indexed: number; chunks_created: number; dependencies_extracted: number };
  error?: string;
}

// ── Sub-components ───────────────────────────────────────────────────────────

function StatusBadge({ indexed, status }: { indexed: boolean; status: IndexStatus }) {
  if (status === "indexing") {
    return (
      <span style={{
        display: "inline-flex", alignItems: "center", gap: 5,
        fontSize: 11, fontWeight: 500, padding: "3px 10px", borderRadius: 20,
        background: "rgba(99,102,241,0.12)", color: "var(--accent)",
        border: "1px solid rgba(99,102,241,0.25)",
      }}>
        <SpinnerIcon size={10} />
        Indexing…
      </span>
    );
  }
  if (status === "error") {
    return (
      <span style={{
        fontSize: 11, fontWeight: 500, padding: "3px 10px", borderRadius: 20,
        background: "rgba(239,68,68,0.10)", color: "var(--red)",
        border: "1px solid rgba(239,68,68,0.25)",
      }}>⚠ Failed</span>
    );
  }
  if (indexed || status === "done") {
    return (
      <span style={{
        fontSize: 11, fontWeight: 500, padding: "3px 10px", borderRadius: 20,
        background: "rgba(34,197,94,0.10)", color: "var(--green)",
        border: "1px solid rgba(34,197,94,0.25)",
      }}>● Indexed</span>
    );
  }
  return (
    <span style={{
      fontSize: 11, fontWeight: 500, padding: "3px 10px", borderRadius: 20,
      background: "rgba(107,107,138,0.10)", color: "var(--text-muted)",
      border: "1px solid var(--border)",
    }}>◌ Not indexed</span>
  );
}

function SpinnerIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      style={{ animation: "spin 0.8s linear infinite", flexShrink: 0 }}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"
        strokeLinecap="round" strokeDasharray="40 20" />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </svg>
  );
}

function StatPill({ label, value }: { label: string; value: number | string }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      fontSize: 11, color: "var(--text-muted)",
      background: "var(--bg)", border: "1px solid var(--border)",
      padding: "2px 8px", borderRadius: 6,
    }}>
      <span style={{ color: "var(--text)", fontWeight: 500 }}>{value}</span>
      {label}
    </span>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const pid = Number(projectId);

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [repoStates, setRepoStates] = useState<Record<number, RepoState>>({});

  // Keep a ref to active polling intervals so we can cancel them
  const pollRefs = useRef<Record<number, ReturnType<typeof setInterval>>>({});

  useEffect(() => { loadProject(); }, [pid]);

  // Cleanup all polls on unmount
  useEffect(() => {
    return () => {
      Object.values(pollRefs.current).forEach(clearInterval);
    };
  }, []);

  async function loadProject() {
    try {
      const data = await api.projects.get(pid);
      setProject(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function setRepoState(repoId: number, patch: Partial<RepoState>) {
    setRepoStates(prev => ({ ...prev, [repoId]: { ...prev[repoId], ...patch } }));
  }

  async function addRepo(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setAdding(true);
    try {
      await api.repositories.add(pid, repoUrl.trim());
      setRepoUrl("");
      await loadProject();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setAdding(false);
    }
  }

  async function indexRepo(repoId: number) {
    // Prevent double-click
    if (repoStates[repoId]?.status === "indexing") return;

    setRepoState(repoId, { status: "indexing", result: undefined, error: undefined });

    try {
      const result = await api.repositories.index(pid, repoId);
      setRepoState(repoId, { status: "done", result });
      // Refresh project so files_count etc. update
      await loadProject();
    } catch (err: any) {
      setRepoState(repoId, { status: "error", error: err.message });
    }
  }

  // ── Render helpers ──────────────────────────────────────────────────────────

  function repoGitHubUrl(repo: Repository): string {
    return repo.url || `https://github.com/${repo.full_name}`;
  }

  if (loading) return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 80, gap: 10, color: "var(--text-muted)" }}>
        <SpinnerIcon /> Loading project…
      </div>
    </div>
  );

  if (error || !project) return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ maxWidth: 700, margin: "40px auto", padding: "0 24px" }}>
        <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, padding: 20, color: "var(--red)" }}>
          {error || "Project not found"}
        </div>
      </div>
    </div>
  );

  const indexedCount = project.repositories.filter(r => r.indexed).length;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ maxWidth: 860, margin: "0 auto", padding: "40px 24px" }}>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <h1 style={{ fontSize: 22, fontWeight: 600 }}>{project.name}</h1>
            {project.repositories.length > 0 && (
              <span style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg-card)", border: "1px solid var(--border)", padding: "2px 8px", borderRadius: 20 }}>
                {indexedCount}/{project.repositories.length} indexed
              </span>
            )}
          </div>
          {project.description && (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>{project.description}</p>
          )}
        </div>

        {/* Connect repository */}
        <div style={{
          background: "var(--bg-card)", border: "1px solid var(--border)",
          borderRadius: 12, padding: 24, marginBottom: 32,
        }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Connect Repository
          </h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
            Paste a GitHub repository URL to add it to this project.
          </p>
          <form onSubmit={addRepo} style={{ display: "flex", gap: 10 }}>
            <input
              value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              style={{
                flex: 1, padding: "9px 12px", borderRadius: 8,
                border: "1px solid var(--border)", background: "var(--bg)",
                color: "var(--text)", fontSize: 13,
              }}
            />
            <button type="submit" disabled={adding || !repoUrl.trim()} style={{
              padding: "9px 20px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500, whiteSpace: "nowrap",
              opacity: adding ? 0.7 : 1,
            }}>
              {adding ? "Connecting…" : "Connect"}
            </button>
          </form>
        </div>

        {/* Repositories */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Repositories ({project.repositories.length})
          </h2>
        </div>

        {project.repositories.length === 0 ? (
          <div style={{
            border: "1px dashed var(--border)", borderRadius: 12,
            padding: "36px 24px", textAlign: "center", color: "var(--text-muted)", fontSize: 13,
          }}>
            No repositories connected yet. Paste a GitHub URL above to get started.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {project.repositories.map(repo => {
              const rs = repoStates[repo.id] ?? { status: (repo.indexed ? "done" : "idle") as IndexStatus };
              const isIndexing = rs.status === "indexing";
              const isIndexed = rs.status === "done" || (rs.status === "idle" && repo.indexed);
              const ghUrl = repoGitHubUrl(repo);

              return (
                <div key={repo.id} style={{
                  background: "var(--bg-card)",
                  border: `1px solid ${rs.status === "error" ? "rgba(239,68,68,0.3)" : isIndexed ? "rgba(34,197,94,0.15)" : "var(--border)"}`,
                  borderRadius: 12, padding: "18px 22px",
                  transition: "border-color 0.2s",
                }}>
                  {/* Row 1: name + status badge */}
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
                    <div style={{ flex: 1, minWidth: 0, marginRight: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
                        <span style={{ fontWeight: 600, fontSize: 15, color: "var(--text)" }}>
                          {repo.name}
                        </span>
                        <StatusBadge indexed={repo.indexed} status={rs.status} />
                      </div>
                      <a
                        href={ghUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: 11, color: "var(--text-muted)", textDecoration: "none", wordBreak: "break-all" }}
                        onMouseEnter={e => (e.currentTarget.style.color = "var(--accent)")}
                        onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
                      >
                        {ghUrl} ↗
                      </a>
                    </div>

                    {/* Actions */}
                    <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
                      <button
                        onClick={() => indexRepo(repo.id)}
                        disabled={isIndexing}
                        style={{
                          padding: "6px 14px", borderRadius: 7,
                          border: "1px solid var(--border)", background: "transparent",
                          color: isIndexing ? "var(--accent)" : "var(--text-muted)",
                          cursor: isIndexing ? "not-allowed" : "pointer",
                          fontSize: 12, display: "flex", alignItems: "center", gap: 5,
                          opacity: isIndexing ? 0.8 : 1,
                        }}
                      >
                        {isIndexing ? <><SpinnerIcon size={11} /> Indexing…</> : (isIndexed ? "Re-index" : "Index")}
                      </button>
                      {isIndexed && (
                        <Link
                          href={`/projects/${pid}/repositories/${repo.id}/overview`}
                          style={{
                            padding: "6px 16px", borderRadius: 7,
                            background: "var(--accent)", color: "white",
                            textDecoration: "none", fontSize: 12, fontWeight: 500,
                          }}
                        >
                          Open →
                        </Link>
                      )}
                    </div>
                  </div>

                  {/* Row 2: stats pills */}
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                    <StatPill label="files" value={
                      rs.result ? rs.result.files_indexed : repo.files_count
                    } />
                    {rs.result && <StatPill label="chunks" value={rs.result.chunks_created} />}
                    {rs.result && <StatPill label="dependencies" value={rs.result.dependencies_extracted} />}
                    <StatPill label="branch" value={repo.default_branch} />
                    {repo.last_indexed_commit && (
                      <StatPill label="last indexed" value={repo.last_indexed_commit.slice(0, 7)} />
                    )}
                  </div>

                  {/* Row 3: result / error banner */}
                  {rs.status === "done" && rs.result && (
                    <div style={{
                      marginTop: 12, fontSize: 12, padding: "8px 12px",
                      borderRadius: 7, background: "rgba(34,197,94,0.07)",
                      border: "1px solid rgba(34,197,94,0.18)", color: "var(--green)",
                      display: "flex", gap: 16,
                    }}>
                      <span>✓ Indexed successfully</span>
                      <span>{rs.result.files_indexed} files</span>
                      <span>{rs.result.chunks_created} chunks</span>
                      <span>{rs.result.dependencies_extracted} dependencies</span>
                    </div>
                  )}
                  {rs.status === "error" && rs.error && (
                    <div style={{
                      marginTop: 12, fontSize: 12, padding: "8px 12px",
                      borderRadius: 7, background: "rgba(239,68,68,0.07)",
                      border: "1px solid rgba(239,68,68,0.2)", color: "var(--red)",
                    }}>
                      ✗ {rs.error}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
