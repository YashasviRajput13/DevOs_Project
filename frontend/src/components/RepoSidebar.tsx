"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { label: "Overview", href: "overview", icon: "◈" },
  { label: "Files", href: "files", icon: "⊞" },
  { label: "Architecture", href: "architecture", icon: "⬡" },
  { label: "AI Chat", href: "chat", icon: "◎" },
  { label: "Agent", href: "agent", icon: "✦" },
];

export default function RepoSidebar({ projectId, repositoryId }: {
  projectId: number;
  repositoryId: number;
}) {
  const pathname = usePathname();
  const base = `/projects/${projectId}/repositories/${repositoryId}`;

  return (
    <aside style={{
      width: 200,
      borderRight: "1px solid var(--border)",
      background: "var(--bg)",
      display: "flex",
      flexDirection: "column",
      padding: "16px 0",
      flexShrink: 0,
    }}>
      <div style={{ padding: "0 12px 12px", fontSize: 11, fontWeight: 600, color: "var(--text-dim)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
        Repository
      </div>
      {NAV_ITEMS.map(item => {
        const href = `${base}/${item.href}`;
        const active = pathname === href || pathname.startsWith(href + "/");
        return (
          <Link key={item.href} href={href} style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "7px 12px",
            margin: "1px 8px",
            borderRadius: 6,
            textDecoration: "none",
            fontSize: 13,
            fontWeight: active ? 500 : 400,
            color: active ? "var(--text)" : "var(--text-muted)",
            background: active ? "var(--bg-hover)" : "transparent",
            borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
          }}>
            <span style={{ fontSize: 14, opacity: 0.7 }}>{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </aside>
  );
}
