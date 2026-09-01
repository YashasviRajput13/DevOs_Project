"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useState, useRef, useEffect } from "react";

export default function TopNav({ projectId, repositoryId, repoName, children }: {
  projectId?: number;
  repositoryId?: number;
  repoName?: string;
  children?: React.ReactNode;
}) {
  const { user, projects, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  
  const [showProjectNav, setShowProjectNav] = useState(false);
  const [showProfileNav, setShowProfileNav] = useState(false);
  
  const currentProject = projects.find(p => p.id === projectId);
  
  let resolvedRepoName = repoName;
  if (!resolvedRepoName && currentProject && repositoryId) {
    const r = currentProject.repositories?.find(r => r.id === repositoryId);
    if (r) resolvedRepoName = r.name;
  }
  
  const projRef = useRef<HTMLDivElement>(null);
  const profRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const clickOut = (e: MouseEvent) => {
      if (projRef.current && !projRef.current.contains(e.target as Node)) setShowProjectNav(false);
      if (profRef.current && !profRef.current.contains(e.target as Node)) setShowProfileNav(false);
    };
    document.addEventListener("mousedown", clickOut);
    return () => document.removeEventListener("mousedown", clickOut);
  }, []);

  return (
    <header style={{
      height: 52,
      borderBottom: "1px solid var(--border)",
      background: "var(--bg)",
      display: "flex",
      alignItems: "center",
      padding: "0 20px",
      gap: 16,
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      {/* BRAND & PROJECT SWITCHER */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <Link href="/projects" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
          <div style={{
            width: 24, height: 24,
            background: "var(--accent)", borderRadius: 6,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 12, fontWeight: 700, color: "white",
          }}>D</div>
          <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text)" }}>DevOs</span>
        </Link>

        {user && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }} ref={projRef}>
            <span style={{ color: "var(--border)", fontSize: 16 }}>/</span>
            <div style={{ position: "relative" }}>
              <button 
                onClick={() => setShowProjectNav(!showProjectNav)}
                style={{
                  display: "flex", alignItems: "center", gap: 6,
                  padding: "4px 10px", borderRadius: 6, border: "none",
                  background: showProjectNav ? "var(--bg-card)" : "transparent",
                  color: currentProject ? "var(--text)" : "var(--text-muted)",
                  fontSize: 13, fontWeight: 500, cursor: "pointer",
                  transition: "background 0.2s"
                }}
              >
                {currentProject ? currentProject.name : "Select Project"}
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M6 9l6 6 6-6"/>
                </svg>
              </button>

              {/* PROJECT DROPDOWN */}
              {showProjectNav && (
                <div style={{
                  position: "absolute", top: "calc(100% + 8px)", left: 0,
                  width: 260, background: "var(--bg-card)", border: "1px solid var(--border)",
                  borderRadius: 8, padding: 8, boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
                  zIndex: 200, display: "flex", flexDirection: "column", gap: 4
                }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", padding: "8px 12px", letterSpacing: "0.04em" }}>
                    My Projects
                  </div>
                  {projects.map(p => (
                    <Link key={p.id} href={`/projects/${p.id}`} onClick={() => setShowProjectNav(false)} style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      padding: "8px 12px", borderRadius: 6, textDecoration: "none",
                      background: projectId === p.id ? "rgba(6,182,212,0.1)" : "transparent",
                      color: projectId === p.id ? "var(--accent)" : "var(--text)",
                      fontSize: 13, fontWeight: projectId === p.id ? 500 : 400,
                    }}>
                      {p.name}
                      {projectId === p.id && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2"><path d="M20 6L9 17l-5-5"/></svg>}
                    </Link>
                  ))}
                  <div style={{ height: 1, background: "var(--border)", margin: "4px 0" }} />
                  <Link href="/projects" onClick={() => setShowProjectNav(false)} style={{
                    display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderRadius: 6,
                    textDecoration: "none", color: "var(--text-muted)", fontSize: 13,
                  }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
                    Create New Project
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}

        {resolvedRepoName && (
          <>
            <span style={{ color: "var(--border)", fontSize: 16 }}>/</span>
            <Link href={`/projects/${projectId}/repositories/${repositoryId}/overview`} style={{ 
              color: "var(--text-muted)", fontSize: 13, textDecoration: "none" 
            }}>
              {resolvedRepoName}
            </Link>
          </>
        )}
      </div>

      <div style={{ flex: 1 }}>{children}</div>
      
      {/* USER NAV */}
      {user ? (
        <div style={{ position: "relative" }} ref={profRef}>
          <button
            onClick={() => setShowProfileNav(!showProfileNav)}
            style={{
              padding: "4px 12px", borderRadius: 20, border: "1px solid var(--border)",
              background: showProfileNav ? "var(--bg-card)" : "transparent",
              color: "var(--text)", fontSize: 13, fontWeight: 500, cursor: "pointer",
              display: "flex", alignItems: "center", gap: 8
            }}
          >
            <div style={{ width: 22, height: 22, borderRadius: "50%", background: "var(--accent-dim)", color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11 }}>
              {user.name.charAt(0).toUpperCase()}
            </div>
            {user.name.split(" ")[0]} 
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </button>

          {showProfileNav && (
            <div style={{
              position: "absolute", top: "calc(100% + 8px)", right: 0,
              width: 220, background: "var(--bg-card)", border: "1px solid var(--border)",
              borderRadius: 8, padding: 8, boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
              zIndex: 200, display: "flex", flexDirection: "column", gap: 4
            }}>
              <div style={{ padding: "8px 12px" }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)" }}>{user.name}</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{user.email}</div>
              </div>
              <div style={{ height: 1, background: "var(--border)", margin: "4px 0" }} />
              <Link href="/projects" onClick={() => setShowProfileNav(false)} style={{
                display: "block", padding: "8px 12px", borderRadius: 6, textDecoration: "none",
                color: "var(--text-muted)", fontSize: 13,
              }}>
                My Projects
              </Link>
              <button 
                onClick={() => { setShowProfileNav(false); logout(); }}
                style={{
                  display: "block", width: "100%", textAlign: "left", padding: "8px 12px", borderRadius: 6, border: "none",
                  background: "transparent", cursor: "pointer", color: "var(--red)", fontSize: 13,
                }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      ) : (
        <Link href="/dashboard" style={{
          fontSize: 13, color: "var(--text-muted)",
          textDecoration: "none", padding: "4px 10px",
          borderRadius: 6,
        }}>
          Sign In
        </Link>
      )}
    </header>
  );
}
