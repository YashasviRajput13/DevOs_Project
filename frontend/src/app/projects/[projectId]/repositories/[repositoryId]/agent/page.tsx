"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

type AgentState = 
  | "idle" 
  | "planning" 
  | "planned" 
  | "rejected" 
  | "applying" 
  | "applied" 
  | "testing" 
  | "passed" 
  | "failed" 
  | "creating_pr" 
  | "pr_created" 
  | "error";

export default function AgentPage() {
  const { projectId, repositoryId } = useParams<{ projectId: string; repositoryId: string }>();
  const pid = Number(projectId), rid = Number(repositoryId);
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [state, setState] = useState<AgentState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  
  const [planId, setPlanId] = useState<string | null>(null);
  const [planResult, setPlanResult] = useState<any>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const [prResult, setPrResult] = useState<any>(null);

  async function handlePlan() {
    if (!query.trim()) return;
    setState("planning");
    setErrorMessage("");
    try {
      const res = await api.agent.plan(pid, rid, query);
      setPlanId(res.plan_id);
      setPlanResult(res);
      setState("planned");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to generate plan.");
      setState("error");
    }
  }

  async function handleApprove(approved: boolean) {
    if (!planId) return;
    
    if (!approved) {
      setState("idle");
      setQuery("");
      setPlanResult(null);
      return;
    }

    if (!confirm(`You are approving changes to ${planResult?.proposed_changes?.length || 0} file(s). Continue?`)) {
      return;
    }

    setState("applying");
    setErrorMessage("");
    try {
      const res = await api.agent.apply(planId, true);
      if (res.status === "changes_applied") {
        setState("applied");
        runTests(planId);
      } else {
        throw new Error(res.error || "Failed to apply changes.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Approval application failed.");
      setState("error");
    }
  }

  async function runTests(targetPlanId: string) {
    setState("testing");
    try {
      const res = await api.agent.test(targetPlanId, pid, rid);
      setTestResult(res);
      if (res.status === "passed") {
        setState("passed");
      } else if (res.status === "failed") {
        setState("failed");
      } else {
        setState("failed");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Tests failed to execute.");
      setState("error");
    }
  }

  async function handleCreatePR() {
    if (!planId) return;
    setState("creating_pr");
    setErrorMessage("");
    try {
      const res = await api.agent.pr(planId);
      setPrResult(res);
      setState("pr_created");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create PR.");
      setState("error");
    }
  }

  return (
    <div style={{ padding: "40px", maxWidth: 900, margin: "0 auto", background: "var(--bg)", minHeight: "100%" }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, color: "var(--text)" }}>DevOs Agent</h1>
        <p style={{ color: "var(--text-muted)", marginTop: 8 }}>
          Propose, approve, test, and branch changes securely.
        </p>
      </header>

      {/* ERROR */}
      {errorMessage && (
        <div style={{ padding: 16, background: "#ff4d4f22", color: "#ff4d4f", borderRadius: 8, marginBottom: 24, border: "1px solid #ff4d4f55" }}>
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* IDLE / PLANNING */}
      {(state === "idle" || state === "planning" || state === "error") && (
        <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 24, background: "var(--bg-card)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 500, marginBottom: 16 }}>Request</h2>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            disabled={state === "planning"}
            placeholder="Describe what you want DevOs to change..."
            rows={4}
            style={{
              width: "100%", padding: 16, borderRadius: 8, border: "1px solid var(--border)",
              background: "var(--bg)", color: "var(--text)", resize: "vertical", fontFamily: "var(--font-sans)"
            }}
          />
          <div style={{ marginTop: 16, textAlign: "right" }}>
            <button
              onClick={handlePlan}
              disabled={state === "planning" || !query.trim()}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "var(--accent)", color: "#fff",
                border: "none", cursor: (state === "planning" || !query.trim()) ? "not-allowed" : "pointer",
                fontWeight: 500, opacity: (state === "planning" || !query.trim()) ? 0.7 : 1
              }}
            >
              {state === "planning" ? "Generating Plan..." : "Generate Plan"}
            </button>
          </div>
        </div>
      )}

      {/* PLANNED (Review) */}
      {state === "planned" && planResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 24, background: "var(--bg-card)" }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Change Plan</h2>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 8 }}>Summary</div>
              <p style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.6 }}>{planResult.summary}</p>
            </div>
            
            {planResult.risks && planResult.risks.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 8 }}>Risks & Considerations</div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, color: "var(--text)" }}>
                  {planResult.risks.map((r: string, i: number) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}

            {planResult.recommended_tests && planResult.recommended_tests.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 8 }}>Tests</div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, color: "var(--text)" }}>
                  {planResult.recommended_tests.map((t: string, i: number) => <li key={i}>{t}</li>)}
                </ul>
              </div>
            )}
          </div>

          <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 24, background: "var(--bg-card)" }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Proposed Changes</h2>
            {planResult.proposed_changes?.map((ch: any, i: number) => (
              <div key={i} style={{ marginBottom: 24, border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
                <div style={{ background: "var(--bg-hover)", padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 600 }}>{ch.file}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Lines {ch.start_line} - {ch.end_line}
                  </div>
                </div>
                <div style={{ padding: "12px 16px", background: "var(--bg)", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 13, color: "var(--text)", fontStyle: "italic" }}>{ch.reason}</div>
                </div>
                <div style={{ padding: 16, background: "#1e1e1e", color: "#d4d4d4", fontFamily: "monospace", fontSize: 13, overflowX: "auto", whiteSpace: "pre" }}>
                  {ch.proposed_change}
                </div>
              </div>
            ))}
          </div>
          
          <div style={{ padding: 16, background: "rgba(255,165,0,0.1)", border: "1px solid rgba(255,165,0,0.5)", borderRadius: 8 }}>
            <p style={{ margin: 0, color: "var(--text)", fontSize: 14, fontWeight: 500 }}>
              DevOs will not modify your repository until you approve this change.
            </p>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 16 }}>
            <button onClick={() => handleApprove(false)} style={{ padding: "10px 24px", borderRadius: 8, background: "transparent", color: "var(--text)", border: "1px solid var(--border)", cursor: "pointer", fontWeight: 500 }}>
              Reject
            </button>
            <button onClick={() => handleApprove(true)} style={{ padding: "10px 24px", borderRadius: 8, background: "var(--accent)", color: "#fff", border: "none", cursor: "pointer", fontWeight: 500 }}>
              Approve Changes
            </button>
          </div>
        </div>
      )}

      {/* APPLYING / APPLIED / TESTING / RESULTS */}
      {(state === "applying" || state === "applied" || state === "testing" || state === "passed" || state === "failed" || state === "creating_pr" || state === "pr_created") && (
        <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 24, background: "var(--bg-card)", display: "flex", flexDirection: "column", gap: 24 }}>
          
          {state === "applying" && <div style={{ fontSize: 16 }}>Applying approved changes...</div>}
          
          {(state !== "applying") && (
            <div style={{ padding: 16, background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#52c41a", display: "flex", gap: 8, alignItems: "center" }}>
                <span>✓</span> Changes applied successfully
              </div>
            </div>
          )}
          
          {state === "testing" && <div style={{ fontSize: 16, animation: "pulse 1.5s infinite" }}>Testing changes...</div>}
          
          {testResult && (
            <div style={{ padding: 16, background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8 }}>
              {testResult.status === "passed" ? (
                <div style={{ fontSize: 16, fontWeight: 600, color: "#52c41a", marginBottom: 12 }}>✓ Tests Passed</div>
              ) : (
                <div style={{ fontSize: 16, fontWeight: 600, color: "#ff4d4f", marginBottom: 12 }}>✕ Tests Failed</div>
              )}
              
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, color: "var(--text)", lineHeight: 1.6, marginBottom: 16 }}>
                <li><strong>Framework:</strong> {testResult.framework || "None"}</li>
                <li><strong>Tests run:</strong> {testResult.tests_run || 0}</li>
                <li><strong>Tests failed:</strong> {testResult.tests_failed || 0}</li>
                <li><strong>Duration:</strong> {testResult.duration_seconds}s</li>
              </ul>
              
              {testResult.stderr && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 4 }}>Error Output</div>
                  <pre style={{ margin: 0, padding: 12, background: "#1e1e1e", color: "#ff4d4f", borderRadius: 6, fontSize: 12, overflowX: "auto" }}>
                    {testResult.stderr}
                  </pre>
                </div>
              )}

              {testResult.analysis && (
                <div style={{ marginTop: 16, padding: 16, background: "rgba(255,255,255,0.03)", borderRadius: 6, border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 8 }}>AI Analysis</div>
                  <div style={{ fontSize: 14, color: "var(--text)", whiteSpace: "pre-wrap" }}>{testResult.analysis}</div>
                  
                  {testResult.likely_causes && testResult.likely_causes.length > 0 && (
                     <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 4 }}>Likely Causes:</div>
                        <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: "var(--text)" }}>
                          {testResult.likely_causes.map((c: string, idx: number) => <li key={idx}>{c}</li>)}
                        </ul>
                     </div>
                  )}

                  {testResult.recommendations && testResult.recommendations.length > 0 && (
                     <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)", marginBottom: 4 }}>Recommendations:</div>
                        <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: "var(--text)" }}>
                          {testResult.recommendations.map((r: string, idx: number) => <li key={idx}>{r}</li>)}
                        </ul>
                     </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* PR CREATION */}
          {state === "passed" && (
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button onClick={handleCreatePR} style={{ padding: "10px 24px", borderRadius: 8, background: "#1890ff", color: "#fff", border: "none", cursor: "pointer", fontWeight: 500 }}>
                Create Pull Request
              </button>
            </div>
          )}

          {state === "failed" && (
            <div style={{ color: "var(--text-muted)", fontSize: 14, textAlign: "right" }}>
              Pull Request creation is blocked because tests did not pass.
            </div>
          )}
          
          {state === "creating_pr" && (
            <div style={{ color: "var(--text)", fontSize: 16, animation: "pulse 1.5s infinite" }}>
              Creating Git branch, committing, and pushing...
            </div>
          )}

          {state === "pr_created" && prResult && (
             <div style={{ padding: 24, background: "var(--bg)", border: "1px solid #1890ff", borderRadius: 8 }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: "#1890ff", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                  <span>✓</span> Pull Request Created
                </div>
                
                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
                    <span style={{ color: "var(--text-dim)", fontSize: 14 }}>Branch</span>
                    <span style={{ fontFamily: "monospace", fontSize: 14 }}>{prResult.branch}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
                    <span style={{ color: "var(--text-dim)", fontSize: 14 }}>Commit</span>
                    <span style={{ fontFamily: "monospace", fontSize: 14 }}>{prResult.commit_sha}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
                    <span style={{ color: "var(--text-dim)", fontSize: 14 }}>PR Number</span>
                    <span style={{ fontSize: 14 }}>#{prResult.pr_number}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
                    <span style={{ color: "var(--text-dim)", fontSize: 14 }}>PR URL</span>
                    <a href={prResult.pr_url} target="_blank" rel="noreferrer" style={{ fontSize: 14, color: "#1890ff", textDecoration: "none" }}>{prResult.pr_url}</a>
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <a href={prResult.pr_url} target="_blank" rel="noreferrer" style={{ display: "inline-block", padding: "10px 24px", borderRadius: 8, background: "#1890ff", color: "#fff", textDecoration: "none", fontWeight: 500 }}>
                    Open Pull Request
                  </a>
                </div>
             </div>
          )}

        </div>
      )}

    </div>
  );
}
