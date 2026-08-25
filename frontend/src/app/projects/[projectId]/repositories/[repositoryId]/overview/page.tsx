"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, OverviewData } from "@/lib/api";

const pill = (label: string, value: string | number, color = "var(--text-muted)") => (
  <div key={label} style={{
    background: "var(--bg-card)", border: "1px solid var(--border)",
    borderRadius: 8, padding: "12px 16px",
  }}>
    <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{label}</div>
  </div>
);

export default function OverviewPage() {
  const { projectId, repositoryId } = useParams<{ projectId: string; repositoryId: string }>();
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.repositories.overview(Number(projectId), Number(repositoryId))
      .then(setData).catch((e: any) => setError(e.message)).finally(() => setLoading(false));
  }, [projectId, repositoryId]);

  if (loading) return (
    <div style={{ padding: 40, color: "var(--text-muted)" }}>
      <div style={{ marginBottom: 8 }}>Loading overview...</div>
      <div style={{ height: 3, width: 200, background: "var(--border)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ height: "100%", width: "60%", background: "var(--accent)", borderRadius: 2, animation: "none" }} />
      </div>
    </div>
  );

  if (error) return (
    <div style={{ padding: 40 }}>
      <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, padding: 20, color: "var(--red)" }}>
        <div style={{ fontWeight: 500, marginBottom: 4 }}>Failed to load overview</div>
        <div style={{ fontSize: 12 }}>{error}</div>
        {error.includes("indexed") && (
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
            Go to the project page and click "Index Repository" first.
          </div>
        )}
      </div>
    </div>
  );

  if (!data) return null;

  return (
    <div style={{ padding: "32px 36px", maxWidth: 900 }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <h1 style={{ fontSize: 18, fontWeight: 600 }}>{data.repository.name}</h1>
          <a href={data.repository.url} target="_blank" rel="noreferrer" style={{
            fontSize: 11, color: "var(--accent)", textDecoration: "none",
            border: "1px solid var(--accent-dim)", borderRadius: 20, padding: "2px 10px",
          }}>
            {data.repository.full_name} ↗
          </a>
        </div>
        {data.summary_context && (
          <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.7, maxWidth: 680 }}>
            {data.summary_context}
          </p>
        )}
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12, marginBottom: 32 }}>
        {pill("Indexed Files", data.statistics.files, "var(--text)")}
        {pill("Code Chunks", data.statistics.chunks, "var(--text)")}
      </div>

      {/* Languages */}
      {data.languages.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Languages</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {data.languages.map(l => (
              <div key={l.name} style={{
                background: "var(--bg-card)", border: "1px solid var(--border)",
                borderRadius: 6, padding: "5px 12px", fontSize: 12,
              }}>
                <span style={{ fontWeight: 500 }}>{l.name}</span>
                <span style={{ color: "var(--text-muted)", marginLeft: 6 }}>{l.files}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Frameworks */}
      {data.frameworks.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Frameworks & Libraries</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {data.frameworks.map(f => (
              <span key={f} style={{
                background: "var(--accent-dim)", border: "1px solid rgba(99,102,241,0.2)",
                borderRadius: 6, padding: "4px 11px", fontSize: 12, color: "var(--accent-hover)",
              }}>{f}</span>
            ))}
          </div>
        </section>
      )}

      {/* Top directories */}
      {data.directories.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Top Directories</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {data.directories.slice(0, 8).map(d => (
              <div key={d.path} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 12px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6 }}>
                <span style={{ fontFamily: "monospace", fontSize: 12 }}>{d.path}/</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{d.file_count} files</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Important files */}
      {data.important_files.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Key Files</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {data.important_files.map(f => (
              <div key={f.path} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 12px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6 }}>
                <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--text)" }}>{f.path}</span>
                {f.language && <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: "auto" }}>{f.language}</span>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
