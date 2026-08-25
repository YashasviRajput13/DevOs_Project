"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function TopNav({ projectId, repositoryId, repoName }: {
  projectId?: number;
  repositoryId?: number;
  repoName?: string;
}) {
  return (
    <header style={{
      height: 48,
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
      <Link href="/dashboard" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
        <div style={{
          width: 24, height: 24,
          background: "var(--accent)",
          borderRadius: 6,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 12, fontWeight: 700, color: "white",
        }}>D</div>
        <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text)" }}>DevOs</span>
      </Link>

      {repoName && (
        <>
          <span style={{ color: "var(--text-dim)" }}>/</span>
          <span style={{ color: "var(--text-muted)", fontSize: 13 }}>{repoName}</span>
        </>
      )}

      <div style={{ flex: 1 }} />

      <Link href="/dashboard" style={{
        fontSize: 13, color: "var(--text-muted)",
        textDecoration: "none", padding: "4px 10px",
        borderRadius: 6,
      }}
        onMouseEnter={e => (e.currentTarget.style.color = "var(--text)")}
        onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
      >
        Dashboard
      </Link>
    </header>
  );
}
