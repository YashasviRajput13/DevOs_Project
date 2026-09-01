"use client";
import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, ChatResponse, Source } from "@/lib/api";

const SUGGESTED_QUERIES = [
  "Explain this repository",
  "How does repository indexing work?",
  "Where are embeddings generated?",
  "How does the API connect to PostgreSQL?",
  "What files are responsible for authentication?",
  "Show me the project architecture",
  "What frameworks does this project use?",
];

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  intent?: string;
  loading?: boolean;
}

function SourceCard({ source, projectId, repositoryId }: { source: Source; projectId: number; repositoryId: number }) {
  if (!source.file_path) return null;
  const href = `/projects/${projectId}/repositories/${repositoryId}/files?fileId=${source.file_id}&start=${source.start_line ?? ""}&end=${source.end_line ?? ""}`;
  return (
    <Link href={href} style={{ textDecoration: "none", display: "block" }}>
      <div style={{
        padding: "9px 12px", borderRadius: 8,
        border: "1px solid var(--border)", background: "var(--bg)",
        cursor: "pointer", transition: "border-color 0.15s",
      }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--accent)")}
        onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
      >
        <div style={{ fontFamily: "monospace", fontSize: 11.5, marginBottom: 3, color: "var(--text)" }}>
          {source.file_path}
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", gap: 10 }}>
          {source.start_line && source.end_line && (
            <span>Lines {source.start_line}–{source.end_line}</span>
          )}
          {source.language && <span>{source.language}</span>}
          {source.score != null && <span>Relevance {(source.score * 100).toFixed(0)}%</span>}
        </div>
      </div>
    </Link>
  );
}

function MessageBubble({ msg, projectId, repositoryId }: { msg: Message; projectId: number; repositoryId: number }) {
  const isUser = msg.role === "user";

  if (isUser) return (
    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
      <div style={{
        maxWidth: "75%", padding: "10px 14px", borderRadius: 12,
        background: "var(--accent)", color: "white", fontSize: 13, lineHeight: 1.6,
      }}>
        {msg.content}
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
      <div style={{
        width: 28, height: 28, flexShrink: 0,
        background: "var(--accent-dim)", border: "1px solid var(--border)",
        borderRadius: 6,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 11, color: "var(--accent)", fontWeight: 700,
      }}>D</div>
      <div style={{ flex: 1 }}>
        {msg.loading ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "8px 0" }}>
            <span style={{ animation: "pulse 1.4s ease-in-out infinite" }}>DevOs is analyzing</span>
            <span style={{ marginLeft: 2 }}>…</span>
          </div>
        ) : (
          <>
            <div style={{ fontSize: 13, lineHeight: 1.8, color: "var(--text)", whiteSpace: "pre-wrap" }}>
              {msg.content}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 8 }}>
                  Sources
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {msg.sources.slice(0, 5).map((s, i) => (
                    <SourceCard key={i} source={s} projectId={projectId} repositoryId={repositoryId} />
                  ))}
                </div>
              </div>
            )}
            
            {msg.intent === "PLAN_CHANGE" && (
              <div style={{ marginTop: 16 }}>
                <div style={{ padding: 16, background: "rgba(24, 144, 255, 0.08)", border: "1px solid rgba(24, 144, 255, 0.3)", borderRadius: 8 }}>
                  <div style={{ fontSize: 13, color: "var(--text)", marginBottom: 12 }}>
                    DevOs detected a request to modify code. Would you like to create a change plan?
                  </div>
                  <Link href={`/projects/${projectId}/repositories/${repositoryId}/agent`} style={{ display: "inline-block", padding: "8px 16px", background: "#1890ff", color: "#fff", textDecoration: "none", borderRadius: 6, fontSize: 13, fontWeight: 500 }}>
                    Create Change Plan
                  </Link>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { projectId, repositoryId } = useParams<{ projectId: string; repositoryId: string }>();
  const pid = Number(projectId), rid = Number(repositoryId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  
  const [provider, setProvider] = useState<string>("devos_auto");
  const [geminiConfigured, setGeminiConfigured] = useState<boolean>(false);

  useEffect(() => {
    api.health().then((res: any) => {
      setGeminiConfigured(!!res.gemini_configured);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(q: string) {
    if (!q.trim() || loading) return;
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: q };
    const loadingMsg: Message = { id: (Date.now() + 1).toString(), role: "assistant", content: "", loading: true };
    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setQuery("");
    setLoading(true);

    try {
      const res = await api.chat(q, pid, rid, provider);
      setMessages(prev => prev.map(m =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, content: res.answer, sources: res.sources, intent: res.intent }
          : m
      ));
    } catch (err: any) {
      setMessages(prev => prev.map(m =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, content: `Error: ${err.message}. Make sure the backend is running.` }
          : m
      ));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "var(--bg)" }}>
      {/* Settings / Model Provider Header */}
      <div style={{ 
        padding: "16px 32px", borderBottom: "1px solid var(--border)", 
        display: "flex", alignItems: "center", gap: 12, flexShrink: 0
      }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-dim)" }}>AI Model</div>
        <select 
          value={provider} 
          onChange={e => setProvider(e.target.value)}
          disabled={loading}
          style={{
            padding: "8px 12px", borderRadius: 8, background: "var(--bg-card)",
            border: "1px solid var(--border)", color: "var(--text)", fontSize: 13,
            outline: "none", cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          <option value="devos_auto">DevOs Auto</option>
          <option value="groq">Groq (Llama)</option>
          <option value="gemini" disabled={!geminiConfigured}>
            Google Gemini {geminiConfigured ? "● Available" : "○ Not configured"}
          </option>
        </select>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: "auto", padding: "28px 32px" }}>
        {messages.length === 0 ? (
          <div style={{ maxWidth: 620 }}>
            <div style={{ marginBottom: 32 }}>
              <h1 style={{ fontSize: 17, fontWeight: 600, marginBottom: 8 }}>Ask DevOs</h1>
              <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.7 }}>
                Ask anything about this repository. DevOs uses your indexed code to give accurate, cited answers.
              </p>
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 12 }}>
                Suggested Questions
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {SUGGESTED_QUERIES.map(q => (
                  <button key={q} onClick={() => sendMessage(q)} style={{
                    textAlign: "left", padding: "10px 14px", borderRadius: 8,
                    border: "1px solid var(--border)", background: "var(--bg-card)",
                    color: "var(--text-muted)", cursor: "pointer", fontSize: 13,
                    transition: "border-color 0.15s, color 0.15s",
                  }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.color = "var(--text)"; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-muted)"; }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ maxWidth: 740 }}>
            {messages.map(msg => (
              <MessageBubble key={msg.id} msg={msg} projectId={pid} repositoryId={rid} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ borderTop: "1px solid var(--border)", padding: "16px 32px", background: "var(--bg)" }}>
        <form onSubmit={e => { e.preventDefault(); sendMessage(query); }} style={{ display: "flex", gap: 10, maxWidth: 740 }}>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(query); } }}
            placeholder="Ask about this repository…"
            rows={1}
            disabled={loading}
            style={{
              flex: 1, padding: "10px 14px", borderRadius: 10,
              border: "1px solid var(--border)", background: "var(--bg-card)",
              color: "var(--text)", fontSize: 13, resize: "none", lineHeight: 1.5,
              outline: "none",
            }}
          />
          <button type="submit" disabled={loading || !query.trim()} style={{
            padding: "10px 20px", borderRadius: 10, border: "none",
            background: loading || !query.trim() ? "var(--bg-hover)" : "var(--accent)",
            color: loading || !query.trim() ? "var(--text-dim)" : "white",
            cursor: loading || !query.trim() ? "not-allowed" : "pointer",
            fontSize: 13, fontWeight: 500, whiteSpace: "nowrap",
          }}>
            {loading ? "..." : "Ask"}
          </button>
        </form>
        <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 8 }}>
          Enter to send · Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}
