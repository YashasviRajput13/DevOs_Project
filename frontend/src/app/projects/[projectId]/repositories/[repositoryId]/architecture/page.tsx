"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ArchitectureData } from "@/lib/api";
import Link from "next/link";

type Tab = "graph" | "routes" | "models" | "services" | "deps";

function Section({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div style={{ marginBottom: 20 }}>
      <button onClick={() => setOpen(o => !o)} style={{
        display: "flex", alignItems: "center", gap: 8, background: "none", border: "none",
        cursor: "pointer", width: "100%", textAlign: "left", marginBottom: 10,
      }}>
        <span style={{ fontSize: 9 }}>{open ? "▼" : "▶"}</span>
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{title}</span>
        <span style={{ fontSize: 11, color: "var(--text-dim)", marginLeft: 4 }}>{count}</span>
      </button>
      {open && children}
    </div>
  );
}

function FileLink({ filePath, fileId, projectId, repositoryId }: { filePath: string; fileId: number; projectId: number; repositoryId: number }) {
  return (
    <Link
      href={`/projects/${projectId}/repositories/${repositoryId}/files?fileId=${fileId}`}
      style={{ fontFamily: "monospace", fontSize: 11, color: "var(--accent)", textDecoration: "none" }}
    >
      {filePath}
    </Link>
  );
}

// Simple SVG dependency graph
function DependencyGraph({ components, services, api_routes }: Pick<ArchitectureData, "components" | "services" | "api_routes">) {
  const nodes = [
    ...components.slice(0, 10).map((c, i) => ({ id: c.name, type: "class", file_id: c.file_id, x: 80 + (i % 4) * 160, y: 60 + Math.floor(i / 4) * 100 })),
    ...services.slice(0, 6).map((s, i) => ({ id: s.name, type: "service", file_id: s.file_id, x: 80 + (i % 3) * 220, y: 300 + Math.floor(i / 3) * 90 })),
  ];
  const allNodes = nodes.slice(0, 16);

  return (
    <div style={{ overflow: "auto", border: "1px solid var(--border)", borderRadius: 10, background: "var(--bg-card)" }}>
      <svg width={Math.max(800, allNodes.reduce((m, n) => Math.max(m, n.x + 140), 0))} height={Math.max(460, allNodes.reduce((m, n) => Math.max(m, n.y + 100), 0))} style={{ display: "block" }}>
        {/* Edges (placeholder for now — connecting sequential nodes) */}
        {allNodes.slice(1).map((n, i) => (
          <line key={i} x1={allNodes[i].x + 56} y1={allNodes[i].y + 20} x2={n.x + 56} y2={n.y + 20}
            stroke="var(--border)" strokeWidth={1} strokeDasharray="4 3" />
        ))}
        {/* Nodes */}
        {allNodes.map(n => (
          <g key={n.id} style={{ cursor: "pointer" }}>
            <rect x={n.x} y={n.y} width={112} height={36} rx={6}
              fill={n.type === "service" ? "var(--accent-dim)" : "var(--bg-hover)"}
              stroke={n.type === "service" ? "rgba(99,102,241,0.3)" : "var(--border)"}
              strokeWidth={1}
            />
            <text x={n.x + 56} y={n.y + 22} textAnchor="middle" fontSize={11} fill="var(--text)" fontFamily="monospace">
              {n.id.length > 14 ? n.id.slice(0, 12) + "…" : n.id}
            </text>
          </g>
        ))}
      </svg>
      <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border)", display: "flex", gap: 16, fontSize: 11, color: "var(--text-muted)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 12, height: 12, background: "var(--bg-hover)", border: "1px solid var(--border)", borderRadius: 2, display: "inline-block" }} /> Classes
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 12, height: 12, background: "var(--accent-dim)", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 2, display: "inline-block" }} /> Services
        </span>
      </div>
    </div>
  );
}

export default function ArchitecturePage() {
  const { projectId, repositoryId } = useParams<{ projectId: string; repositoryId: string }>();
  const pid = Number(projectId), rid = Number(repositoryId);
  const [data, setData] = useState<ArchitectureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("graph");

  useEffect(() => {
    api.repositories.architecture(pid, rid)
      .then(setData).catch((e: any) => setError(e.message)).finally(() => setLoading(false));
  }, [pid, rid]);

  if (loading) return <div style={{ padding: 40, color: "var(--text-muted)" }}>Loading architecture...</div>;
  if (error) return (
    <div style={{ padding: 40 }}>
      <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, padding: 20, color: "var(--red)" }}>
        {error.includes("indexed") ? "Repository not indexed yet." : error}
      </div>
    </div>
  );
  if (!data) return null;

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: "graph", label: "Graph", count: data.components.length + data.services.length },
    { id: "routes", label: "API Routes", count: data.api_routes.length },
    { id: "models", label: "Models", count: data.models.length },
    { id: "services", label: "Services", count: data.services.length },
    { id: "deps", label: "Dependencies", count: data.dependencies.length },
  ];

  return (
    <div style={{ padding: "28px 36px", maxWidth: 1100 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 17, fontWeight: 600, marginBottom: 4 }}>Architecture</h1>
        <p style={{ color: "var(--text-muted)", fontSize: 12 }}>
          {data.api_routes.length} routes · {data.models.length} models · {data.services.length} services · {data.components.length} classes · {data.dependencies.length} imports
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)", marginBottom: 24 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: "7px 14px", border: "none", background: "none", cursor: "pointer",
            fontSize: 13, fontWeight: tab === t.id ? 500 : 400,
            color: tab === t.id ? "var(--text)" : "var(--text-muted)",
            borderBottom: tab === t.id ? "2px solid var(--accent)" : "2px solid transparent",
            marginBottom: -1,
          }}>
            {t.label}
            <span style={{ marginLeft: 6, fontSize: 11, color: "var(--text-dim)" }}>{t.count}</span>
          </button>
        ))}
      </div>

      {/* Graph */}
      {tab === "graph" && (
        <DependencyGraph components={data.components} services={data.services} api_routes={data.api_routes} />
      )}

      {/* API Routes */}
      {tab === "routes" && (
        data.api_routes.length === 0
          ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No API routes detected.</div>
          : <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {data.api_routes.map((r, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }}>
                  <span style={{
                    fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 4,
                    background: r.method === "GET" ? "rgba(34,197,94,0.1)" : r.method === "POST" ? "rgba(99,102,241,0.1)" : "rgba(245,158,11,0.1)",
                    color: r.method === "GET" ? "var(--green)" : r.method === "POST" ? "var(--accent-hover)" : "var(--yellow)",
                    minWidth: 42, textAlign: "center",
                  }}>
                    {r.method}
                  </span>
                  <code style={{ fontSize: 12, flex: 1 }}>{r.path}</code>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{r.handler}</span>
                  <FileLink filePath={r.file_path} fileId={r.file_id} projectId={pid} repositoryId={rid} />
                </div>
              ))}
            </div>
      )}

      {/* Models */}
      {tab === "models" && (
        data.models.length === 0
          ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No database models detected.</div>
          : <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {data.models.map((m, i) => (
                <div key={i} style={{ padding: "10px 16px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, minWidth: 180 }}>
                  <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 4 }}>{m.name}</div>
                  <FileLink filePath={m.file_path} fileId={m.file_id} projectId={pid} repositoryId={rid} />
                </div>
              ))}
            </div>
      )}

      {/* Services */}
      {tab === "services" && (
        data.services.length === 0
          ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No service classes detected.</div>
          : <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {data.services.map((s, i) => (
                <div key={i} style={{ padding: "10px 16px", background: "var(--accent-dim)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, minWidth: 180 }}>
                  <div style={{ fontWeight: 500, fontSize: 13, color: "var(--accent-hover)", marginBottom: 4 }}>{s.name}</div>
                  <FileLink filePath={s.file_path} fileId={s.file_id} projectId={pid} repositoryId={rid} />
                </div>
              ))}
            </div>
      )}

      {/* Dependencies */}
      {tab === "deps" && (
        data.dependencies.length === 0
          ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No dependencies recorded.</div>
          : <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {data.dependencies.slice(0, 60).map((d, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 12px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 12 }}>
                  <code style={{ color: "var(--text-muted)", fontSize: 11 }}>{d.source_file}</code>
                  <span style={{ color: "var(--text-dim)" }}>→</span>
                  <code style={{ flex: 1 }}>{d.target_module ?? d.target_file ?? "?"}</code>
                  <span style={{ fontSize: 10, color: "var(--text-dim)", background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 4, padding: "1px 6px" }}>{d.dependency_type}</span>
                </div>
              ))}
              {data.dependencies.length > 60 && (
                <div style={{ color: "var(--text-dim)", fontSize: 11, padding: "8px 12px" }}>
                  +{data.dependencies.length - 60} more
                </div>
              )}
            </div>
      )}
    </div>
  );
}
