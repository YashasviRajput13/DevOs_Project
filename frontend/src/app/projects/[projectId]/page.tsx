"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import TopNav from "@/components/TopNav";
import { api, Project, Repository } from "@/lib/api";

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const pid = Number(projectId);

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [indexingId, setIndexingId] = useState<number | null>(null);
  const [indexResult, setIndexResult] = useState<Record<number, any>>({});

  useEffect(() => { loadProject(); }, [pid]);

  async function loadProject() {
    try {
      const data = await api.projects.get(pid);
      setProject(data);
    } catch (err: any) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function addRepo(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setAdding(true);
    try {
      await api.repositories.add(pid, repoUrl.trim());
      setRepoUrl("");
      await loadProject();
    } catch (err: any) { alert(err.message); }
    finally { setAdding(false); }
  }

  async function indexRepo(repoId: number) {
    setIndexingId(repoId);
    setIndexResult(prev => ({ ...prev, [repoId]: null }));
    try {
      const result = await api.repositories.index(pid, repoId);
      setIndexResult(prev => ({ ...prev, [repoId]: result }));
      await loadProject();
    } catch (err: any) {
      setIndexResult(prev => ({ ...prev, [repoId]: { error: err.message } }));
    } finally { setIndexingId(null); }
  }

  if (loading) return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>Loading project...</div>
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

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <div style={{ maxWidth: 800, margin: "0 auto", padding: "40px 24px" }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 6 }}>{project.name}</h1>
        {project.description && <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 32 }}>{project.description}</p>}

        {/* Connect repository */}
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 10, padding: 24, marginBottom: 32 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Connect Repository</h2>
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
              padding: "9px 18px", borderRadius: 8, border: "none",
              background: "var(--accent)", color: "white", cursor: "pointer",
              fontSize: 13, fontWeight: 500, whiteSpace: "nowrap",
              opacity: adding ? 0.7 : 1,
            }}>
              {adding ? "Connecting..." : "Connect"}
            </button>
          </form>
        </div>

        {/* Repositories */}
        <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Repositories</h2>
        {project.repositories.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "20px 0" }}>No repositories connected yet.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {project.repositories.map(repo => {
              const res = indexResult[repo.id];
              const isIndexing = indexingId === repo.id;
              return (
                <div key={repo.id} style={{
                  background: "var(--bg-card)", border: "1px solid var(--border)",
                  borderRadius: 10, padding: "16px 20px",
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontWeight: 500, fontSize: 14 }}>{repo.full_name}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                        {repo.files_count} files · {repo.default_branch}
                        {repo.indexed && <span style={{ color: "var(--green)", marginLeft: 8 }}>● Indexed</span>}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      {!isIndexing && (
                        <button onClick={() => indexRepo(repo.id)} style={{
                          padding: "6px 14px", borderRadius: 6,
                          border: "1px solid var(--border)", background: "transparent",
                          color: "var(--text-muted)", cursor: "pointer", fontSize: 12,
                        }}>
                          {repo.indexed ? "Re-index" : "Index"}
                        </button>
                      )}
                      {isIndexing && (
                        <span style={{ fontSize: 12, color: "var(--accent)" }}>Indexing...</span>
                      )}
                      {repo.indexed && (
                        <a href={`/projects/${pid}/repositories/${repo.id}/overview`} style={{
                          padding: "6px 14px", borderRadius: 6,
                          background: "var(--accent)", color: "white",
                          textDecoration: "none", fontSize: 12, fontWeight: 500,
                        }}>Open →</a>
                      )}
                    </div>
                  </div>
                  {res && (
                    <div style={{ marginTop: 10, fontSize: 12, padding: "8px 12px", borderRadius: 6, background: "var(--bg)", border: "1px solid var(--border)" }}>
                      {res.error
                        ? <span style={{ color: "var(--red)" }}>Error: {res.error}</span>
                        : <span style={{ color: "var(--green)" }}>
                            ✓ {res.files_indexed} files · {res.chunks_created} chunks · {res.dependencies_extracted} dependencies
                          </span>
                      }
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
