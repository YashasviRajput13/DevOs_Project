"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AuthDashboard() {
  const { user, setToken, loading } = useAuth();
  const router = useRouter();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!loading && user) {
      router.replace("/projects");
    }
  }, [user, loading, router]);

  if (loading || user) return <div style={{ height: "100vh", background: "var(--bg)" }} />;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setSubmitting(true);
    try {
      if (mode === "login") {
        const res = await api.auth.login(email, password);
        setToken(res.access_token);
      } else {
        const res = await api.auth.register(name, email, password);
        setToken(res.access_token);
      }
    } catch (e: any) {
      setErr(e.message || "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", display: "flex", flexDirection: "column" }}>
      <header style={{ height: 60, padding: "0 24px", display: "flex", alignItems: "center", borderBottom: "1px solid var(--border)" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
          <div style={{
            width: 28, height: 28, background: "var(--accent)", borderRadius: 8,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 700, color: "white", boxShadow: "0 0 15px rgba(6,182,212,0.5)"
          }}>D</div>
          <span style={{ fontWeight: 600, fontSize: 18, color: "var(--text)" }}>DevOs</span>
        </Link>
      </header>

      <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <div style={{
          width: 400, maxWidth: "100%", background: "var(--bg-card)",
          borderRadius: 16, border: "1px solid var(--border)", padding: 32,
          boxShadow: "0 20px 40px rgba(0,0,0,0.2)"
        }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: "var(--text)" }}>
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 32 }}>
            {mode === "login" ? "Sign in to access your AI developer workspaces" : "Start connecting repositories and building with AI"}
          </p>

          <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {mode === "register" && (
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "var(--text-muted)", marginBottom: 8 }}>Full Name</label>
                <input
                  type="text" autoFocus required value={name} onChange={e => setName(e.target.value)}
                  style={{
                    width: "100%", padding: "12px", borderRadius: 8, border: "1px solid var(--border)",
                    background: "var(--bg)", color: "var(--text)", fontSize: 14, boxSizing: "border-box", outline: "none"
                  }}
                />
              </div>
            )}
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "var(--text-muted)", marginBottom: 8 }}>Email Address</label>
              <input
                type="email" required autoFocus={mode === "login"} value={email} onChange={e => setEmail(e.target.value)}
                style={{
                  width: "100%", padding: "12px", borderRadius: 8, border: "1px solid var(--border)",
                  background: "var(--bg)", color: "var(--text)", fontSize: 14, boxSizing: "border-box", outline: "none"
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "var(--text-muted)", marginBottom: 8 }}>Password</label>
              <input
                type="password" required value={password} onChange={e => setPassword(e.target.value)}
                style={{
                  width: "100%", padding: "12px", borderRadius: 8, border: "1px solid var(--border)",
                  background: "var(--bg)", color: "var(--text)", fontSize: 14, boxSizing: "border-box", outline: "none"
                }}
              />
            </div>

            {err && <div style={{ padding: 12, borderRadius: 8, background: "rgba(239,68,68,0.1)", color: "var(--red)", fontSize: 13, border: "1px solid rgba(239,68,68,0.2)" }}>
              {err}
            </div>}

            <button type="submit" disabled={submitting} style={{
              width: "100%", padding: "14px", borderRadius: 8, border: "none",
              background: submitting ? "var(--bg-hover)" : "var(--accent)", color: "white",
              fontSize: 14, fontWeight: 600, cursor: submitting ? "not-allowed" : "pointer",
              transition: "background 0.2s", marginTop: 8,
              boxShadow: "0 4px 15px rgba(6,182,212,0.3)"
            }}>
              {submitting ? "Please wait..." : (mode === "login" ? "Sign In" : "Create Account")}
            </button>
          </form>

          <div style={{ marginTop: 32, textAlign: "center", fontSize: 13, color: "var(--text-muted)" }}>
            {mode === "login" ? (
              <>Don't have an account? <button onClick={() => {setMode("register"); setErr("");}} style={{ background: "none", border: "none", color: "var(--accent)", fontWeight: 500, cursor: "pointer", padding: 0 }}>Sign up</button></>
            ) : (
              <>Already have an account? <button onClick={() => {setMode("login"); setErr("");}} style={{ background: "none", border: "none", color: "var(--accent)", fontWeight: 500, cursor: "pointer", padding: 0 }}>Sign in</button></>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
