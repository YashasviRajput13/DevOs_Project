"use client";
import { useEffect, useState, useMemo } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { api, FileEntry, FileContent } from "@/lib/api";

// Build a tree structure from flat file list
function buildTree(files: FileEntry[]) {
  const tree: Record<string, any> = {};
  for (const f of files) {
    const parts = f.path.split("/");
    let node = tree;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!node[parts[i]]) node[parts[i]] = { __type: "dir", __children: {} };
      node = node[parts[i]].__children;
    }
    node[parts[parts.length - 1]] = { __type: "file", __file: f };
  }
  return tree;
}

function TreeNode({ name, node, depth, onSelect, selectedId }: { name: string; node: any; depth: number; onSelect: (f: FileEntry) => void; selectedId?: number }) {
  const [open, setOpen] = useState(depth < 2);
  const isDir = node.__type === "dir";
  const isSelected = !isDir && node.__file?.id === selectedId;

  if (isDir) {
    return (
      <div>
        <div
          onClick={() => setOpen(o => !o)}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "3px 0 3px", paddingLeft: depth * 14,
            cursor: "pointer", fontSize: 12, color: "var(--text-muted)",
            userSelect: "none",
          }}
        >
          <span style={{ fontSize: 9 }}>{open ? "▼" : "▶"}</span>
          <span>📁</span>
          <span>{name}</span>
        </div>
        {open && Object.entries(node.__children).map(([n, ch]) => (
          <TreeNode key={n} name={n} node={ch} depth={depth + 1} onSelect={onSelect} selectedId={selectedId} />
        ))}
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelect(node.__file)}
      style={{
        display: "flex", alignItems: "center", gap: 6,
        padding: "3px 0", paddingLeft: depth * 14,
        cursor: "pointer", fontSize: 12,
        color: isSelected ? "var(--text)" : "var(--text-muted)",
        background: isSelected ? "var(--bg-hover)" : "transparent",
        borderRadius: 4,
      }}
    >
      <span>📄</span>
      <span>{name}</span>
      {node.__file?.language && (
        <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--text-dim)", paddingRight: 4 }}>
          {node.__file.language}
        </span>
      )}
    </div>
  );
}

function CodeViewer({ content, language, highlightLines }: { content: string; language: string | null; highlightLines?: [number, number] }) {
  const lines = content.split("\n");
  return (
    <div style={{ fontFamily: "monospace", fontSize: 12.5, lineHeight: 1.7, overflow: "auto", height: "100%", padding: "16px 0" }}>
      {lines.map((line, i) => {
        const lineNum = i + 1;
        const highlighted = highlightLines && lineNum >= highlightLines[0] && lineNum <= highlightLines[1];
        return (
          <div key={i} id={`line-${lineNum}`} style={{
            display: "flex",
            background: highlighted ? "rgba(6,182,212,0.12)" : "transparent",
            borderLeft: highlighted ? "2px solid var(--accent)" : "2px solid transparent",
          }}>
            <span style={{
              width: 44, flexShrink: 0, textAlign: "right", paddingRight: 16,
              color: "var(--text-dim)", userSelect: "none", fontSize: 11,
            }}>{lineNum}</span>
            <pre style={{ flex: 1, margin: 0, paddingRight: 16, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
              {line || " "}
            </pre>
          </div>
        );
      })}
    </div>
  );
}

export default function FilesPage() {
  const { projectId, repositoryId } = useParams<{ projectId: string; repositoryId: string }>();
  const searchParams = useSearchParams();
  const pid = Number(projectId), rid = Number(repositoryId);

  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<FileEntry | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [contentLoading, setContentLoading] = useState(false);
  const [search, setSearch] = useState("");

  // URL params for source navigation
  const fileIdParam = searchParams.get("fileId");
  const startLine = searchParams.get("start") ? Number(searchParams.get("start")) : undefined;
  const endLine = searchParams.get("end") ? Number(searchParams.get("end")) : undefined;

  const tree = useMemo(() => buildTree(files.filter(f =>
    f.path.toLowerCase().includes(search.toLowerCase())
  )), [files, search]);

  useEffect(() => {
    api.repositories.files(pid, rid)
      .then(d => { setFiles(d.files); })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pid, rid]);

  // Auto-open file from URL param (source navigation)
  useEffect(() => {
    if (fileIdParam && files.length > 0) {
      const f = files.find(f => f.id === Number(fileIdParam));
      if (f) openFile(f);
    }
  }, [fileIdParam, files]);

  async function openFile(f: FileEntry) {
    setSelectedFile(f);
    setContentLoading(true);
    try {
      const data = await api.repositories.fileContent(pid, rid, f.id);
      setFileContent(data.content);
    } catch { setFileContent("Could not load file content."); }
    finally { setContentLoading(false); }
  }

  // Scroll to highlighted line
  useEffect(() => {
    if (startLine && fileContent) {
      setTimeout(() => {
        document.getElementById(`line-${startLine}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
    }
  }, [startLine, fileContent]);

  if (loading) return <div style={{ padding: 40, color: "var(--text-muted)" }}>Loading files...</div>;
  if (error) return (
    <div style={{ padding: 40 }}>
      <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, padding: 20, color: "var(--red)" }}>
        {error.includes("indexed") ? "Repository not indexed yet. Go to project page and index first." : error}
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", height: "100%", overflow: "hidden" }}>
      {/* File tree */}
      <div style={{ width: 240, borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", overflow: "hidden", flexShrink: 0 }}>
        <div style={{ padding: "12px 10px 8px", borderBottom: "1px solid var(--border)" }}>
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Filter files..."
            style={{
              width: "100%", padding: "6px 10px", borderRadius: 6,
              border: "1px solid var(--border)", background: "var(--bg)",
              color: "var(--text)", fontSize: 12,
            }}
          />
        </div>
        <div style={{ overflow: "auto", flex: 1, padding: "8px 6px" }}>
          {files.length === 0
            ? <div style={{ color: "var(--text-muted)", fontSize: 12, padding: 12 }}>No files indexed.</div>
            : Object.entries(tree).map(([name, node]) => (
              <TreeNode key={name} name={name} node={node} depth={0} onSelect={openFile} selectedId={selectedFile?.id} />
            ))
          }
        </div>
      </div>

      {/* Code viewer */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        {selectedFile ? (
          <>
            <div style={{
              borderBottom: "1px solid var(--border)", padding: "8px 16px",
              display: "flex", alignItems: "center", gap: 10, background: "var(--bg)",
            }}>
              <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--text-muted)" }}>{selectedFile.path}</span>
              {selectedFile.language && (
                <span style={{ fontSize: 10, color: "var(--text-dim)", marginLeft: "auto" }}>{selectedFile.language}</span>
              )}
              {fileContent && (
                <button onClick={() => navigator.clipboard.writeText(fileContent)} style={{
                  padding: "3px 10px", borderRadius: 5, border: "1px solid var(--border)",
                  background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: 11,
                }}>Copy</button>
              )}
            </div>
            <div style={{ flex: 1, overflow: "auto", background: "var(--bg)" }}>
              {contentLoading
                ? <div style={{ padding: 24, color: "var(--text-muted)" }}>Loading...</div>
                : <CodeViewer content={fileContent} language={selectedFile.language}
                    highlightLines={startLine && endLine ? [startLine, endLine] : undefined} />
              }
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 12, color: "var(--text-muted)" }}>
            <span style={{ fontSize: 32 }}>⊞</span>
            <span style={{ fontSize: 13 }}>Select a file to view its contents</span>
            <span style={{ fontSize: 11, opacity: 0.6 }}>{files.length} files indexed</span>
          </div>
        )}
      </div>
    </div>
  );
}
