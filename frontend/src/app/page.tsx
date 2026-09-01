"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function LandingPage() {
  const [windowWidth, setWindowWidth] = useState(1200);

  useEffect(() => {
    setWindowWidth(window.innerWidth);
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const isMobile = windowWidth < 768;

  return (
    <div style={{
      minHeight: "100vh",
      backgroundColor: "#000000",
      color: "var(--text)",
      fontFamily: "var(--font-sans, system-ui, sans-serif)",
      overflowX: "hidden",
      position: "relative"
    }}>
      {/* Uiverse Midnight Sky Background */}
      <div className="uiverse-midnight-sky" style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, zIndex: 0, pointerEvents: "none" }}>
        <div className="sky-canvas">
          <div className="stars stars-1"></div>
          <div className="stars stars-2"></div>
          <div className="stars stars-3"></div>
          <div className="meteor m1"></div>
          <div className="meteor m2"></div>
          <div className="meteor m3"></div>
          <div className="moon"></div>
        </div>
      </div>

      {/* Navbar */}
      <header style={{
        position: "sticky", top: 0, zIndex: 50, width: "100%",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        background: "rgba(10, 10, 15, 0.8)", backdropFilter: "blur(12px)"
      }}>
        <div style={{
          maxWidth: 1200, margin: "0 auto", padding: "0 24px", height: 64,
          display: "flex", alignItems: "center", justifyContent: "space-between"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 28, height: 28, backgroundColor: "var(--accent)", borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontWeight: 700, color: "white", boxShadow: "0 0 15px rgba(6,182,212,0.5)"
            }}>D</div>
            <span style={{ fontWeight: 600, fontSize: 18, letterSpacing: "-0.02em" }}>DevOs</span>
          </div>
          {!isMobile && (
            <nav style={{ display: "flex", alignItems: "center", gap: 32, fontSize: 14, fontWeight: 500 }}>
              <a href="#features" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Features</a>
              <a href="#how-it-works" style={{ color: "var(--text-muted)", textDecoration: "none" }}>How it Works</a>
              <a href="#architecture" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Architecture</a>
            </nav>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {/* From Uiverse.io by andrew-demchenk0 */}
            <label className="switch" style={{ transform: "scale(0.8)", marginRight: 8, marginTop: 4 }}>
              <span className="sun"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="#ffd43b"><circle r="5" cy="12" cx="12"></circle><path d="m21 13h-1a1 1 0 0 1 0-2h1a1 1 0 0 1 0 2zm-17 0h-1a1 1 0 0 1 0-2h1a1 1 0 0 1 0 2zm13.66-5.66a1 1 0 0 1 -.66-.29 1 1 0 0 1 0-1.41l.71-.71a1 1 0 1 1 1.41 1.41l-.71.71a1 1 0 0 1 -.75.29zm-12.02 12.02a1 1 0 0 1 -.71-.29 1 1 0 0 1 0-1.41l.71-.66a1 1 0 0 1 1.41 1.41l-.71.71a1 1 0 0 1 -.7.24zm6.36-14.36a1 1 0 0 1 -1-1v-1a1 1 0 0 1 2 0v1a1 1 0 0 1 -1 1zm0 17a1 1 0 0 1 -1-1v-1a1 1 0 0 1 2 0v1a1 1 0 0 1 -1 1zm-5.66-14.66a1 1 0 0 1 -.7-.29l-.71-.71a1 1 0 0 1 1.41-1.41l.71.71a1 1 0 0 1 0 1.41 1 1 0 0 1 -.71.29zm12.02 12.02a1 1 0 0 1 -.7-.29l-.66-.71a1 1 0 0 1 1.36-1.36l.71.71a1 1 0 0 1 0 1.41 1 1 0 0 1 -.71.24z"></path></g></svg></span>
              <span className="moon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><path d="m223.5 32c-123.5 0-223.5 100.3-223.5 224s100 224 223.5 224c60.6 0 115.5-24.2 155.8-63.4 5-4.9 6.3-12.5 3.1-18.7s-10.1-9.7-17-8.5c-9.8 1.7-19.8 2.6-30.1 2.6-96.9 0-175.5-78.8-175.5-176 0-65.8 36-123.1 89.3-153.3 6.1-3.5 9.2-10.5 7.7-17.3s-7.3-11.9-14.3-12.5c-6.3-.5-12.6-.8-19-.8z"></path></svg></span>   
              <input type="checkbox" className="input" defaultChecked />
              <span className="slider"></span>
            </label>
            {!isMobile && (
              <Link href="/dashboard" style={{ fontSize: 14, fontWeight: 500, color: "var(--text-muted)", textDecoration: "none" }}>
                Sign In
              </Link>
            )}
            <Link href="/dashboard" style={{
              fontSize: 14, fontWeight: 500, backgroundColor: "white", color: "black",
              padding: "8px 16px", borderRadius: 8, textDecoration: "none", transition: "background 0.2s"
            }}>
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* HERO SECTION */}
        <section style={{
          position: "relative", paddingTop: isMobile ? 80 : 120, paddingBottom: 80,
          paddingLeft: 24, paddingRight: 24, maxWidth: 1200, margin: "0 auto",
          textAlign: "center", zIndex: 10
        }}>


          <h1 style={{
            fontSize: isMobile ? 42 : 72, fontWeight: 800, letterSpacing: "-0.03em",
            marginBottom: 24, lineHeight: 1.1, color: "white"
          }}>
            Understand. Build. Ship.<br />
            With the <span style={{ color: "#06B6D4" }}>Power of AI.</span>
          </h1>

          <p style={{
            fontSize: isMobile ? 16 : 20, color: "var(--text-muted)", maxWidth: 680, margin: "0 auto",
            marginBottom: 48, lineHeight: 1.6
          }}>
            DevOs transforms your GitHub repositories into an intelligent workspace where you can explore code, understand architecture, and collaborate with AI.
          </p>

          <div style={{
            display: "flex", flexDirection: isMobile ? "column" : "row",
            alignItems: "center", justifyContent: "center", gap: 16, marginBottom: 80
          }}>
            <Link href="/dashboard" style={{
              width: isMobile ? "100%" : "auto", padding: "14px 32px",
              backgroundColor: "var(--accent)", color: "white", borderRadius: 12,
              fontSize: 15, fontWeight: 500, textDecoration: "none",
              boxShadow: "0 0 30px rgba(6,182,212,0.3)"
            }}>
              Get Started Free →
            </Link>
            <Link href="#demo" style={{
              width: isMobile ? "100%" : "auto", padding: "14px 32px",
              border: "1px solid rgba(255,255,255,0.1)", backgroundColor: "transparent",
              color: "var(--text)", borderRadius: 12, fontSize: 15, fontWeight: 500,
              textDecoration: "none"
            }}>
              See DevOs in Action
            </Link>
          </div>

          {/* VIDEO SHOWCASE MOCKUP */}
          <div id="demo" style={{
            position: "relative", maxWidth: 1024, margin: "0 auto", borderRadius: 16,
            border: "1px solid rgba(255,255,255,0.1)", backgroundColor: "#0d0d14",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)", overflow: "hidden"
          }}>
            <div style={{
              position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(6,182,212,0.05), transparent)",
              pointerEvents: "none"
            }} />

            {/* Fake browser bar */}
            <div style={{
              height: 48, borderBottom: "1px solid rgba(255,255,255,0.05)",
              display: "flex", alignItems: "center", padding: "0 16px", gap: 8, backgroundColor: "rgba(0,0,0,0.4)"
            }}>
              <div style={{ display: "flex", gap: 6 }}>
                <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#334155" }}></div>
                <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#334155" }}></div>
                <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#334155" }}></div>
              </div>
              <div style={{ margin: "0 auto", width: "50%", height: 24, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 6, border: "1px solid rgba(255,255,255,0.05)" }}></div>
            </div>

            {/* Dashboard UI Mockup inside Video Container */}
            <div style={{
              position: "relative", aspectRatio: "16/9", display: "flex",
              flexDirection: isMobile ? "column" : "row", backgroundColor: "#08080c"
            }}>

              {/* Play Button Overlay */}
              <div style={{
                position: "absolute", inset: 0, zIndex: 20, display: "flex", alignItems: "center", justifyContent: "center",
                backgroundColor: "rgba(0,0,0,0.4)", backdropFilter: "blur(2px)", cursor: "pointer"
              }}>
                <div style={{
                  width: 80, height: 80, borderRadius: "50%", backgroundColor: "rgba(6,182,212,0.9)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 0 30px rgba(6,182,212,0.6)", paddingLeft: 4
                }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="white"><path d="M5 3l14 9-14 9V3z" /></svg>
                </div>
              </div>

              {/* Sidebar Mockup */}
              {!isMobile && (
                <div style={{
                  width: 200, borderRight: "1px solid rgba(255,255,255,0.05)",
                  display: "flex", flexDirection: "column", padding: 16, gap: 16, opacity: 0.5
                }}>
                  <div style={{ height: 16, width: 96, backgroundColor: "rgba(255,255,255,0.1)", borderRadius: 4, marginBottom: 16 }} />
                  <div style={{ height: 32, width: "100%", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 4 }} />
                  <div style={{ height: 32, width: "100%", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 4 }} />
                  <div style={{ height: 32, width: "100%", backgroundColor: "rgba(6,182,212,0.2)", borderRadius: 4, border: "1px solid rgba(6,182,212,0.3)" }} />
                </div>
              )}

              {/* Main Content Mockup */}
              <div style={{ flex: 1, padding: isMobile ? 16 : 32, display: "flex", flexDirection: "column", gap: 24, opacity: 0.6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ height: 24, width: 192, backgroundColor: "rgba(255,255,255,0.1)", borderRadius: 4 }} />
                  <div style={{ height: 24, width: 96, backgroundColor: "rgba(34,197,94,0.2)", borderRadius: 12, border: "1px solid rgba(34,197,94,0.3)" }} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                  <div style={{ height: 80, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.05)" }} />
                  <div style={{ height: 80, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.05)" }} />
                  <div style={{ height: 80, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.05)" }} />
                </div>
                <div style={{ flex: 1, display: "flex", gap: 16 }}>
                  <div style={{ flex: 1, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.05)", padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
                    <div style={{ height: 16, width: 128, backgroundColor: "rgba(255,255,255,0.1)", borderRadius: 4 }} />
                    <div style={{ height: "100%", backgroundColor: "#111118", borderRadius: 4, border: "1px solid rgba(255,255,255,0.05)", padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                      <div style={{ height: 12, width: "75%", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 4 }} />
                      <div style={{ height: 12, width: "50%", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 4 }} />
                      <div style={{ height: 12, width: "83%", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 4 }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Video control bar fake */}
              <div style={{
                position: "absolute", bottom: 0, left: 0, right: 0, height: 40,
                backgroundColor: "rgba(0,0,0,0.8)", borderTop: "1px solid rgba(255,255,255,0.1)",
                display: "flex", alignItems: "center", padding: "0 16px", gap: 16, zIndex: 20
              }}>
                <div style={{ width: 12, height: 12, backgroundColor: "white", borderRadius: 2 }}></div>
                <div style={{ flex: 1, height: 4, backgroundColor: "rgba(255,255,255,0.2)", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{ width: "33%", height: "100%", backgroundColor: "var(--accent)" }}></div>
                </div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)", fontFamily: "monospace" }}>0:42 / 2:15</div>
              </div>

            </div>
          </div>
        </section>

        {/* FEATURES SECTION */}
        <section id="features" style={{ padding: "96px 24px", position: "relative" }}>
          <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            <div style={{ textAlign: "center", marginBottom: 64 }}>
              <h2 style={{ fontSize: isMobile ? 28 : 36, fontWeight: 700, marginBottom: 16 }}>Everything you need to understand your codebase</h2>
              <p style={{ color: "var(--text-muted)", maxWidth: 680, margin: "0 auto", fontSize: 16 }}>
                Turn raw source code into navigable, intelligent insights powered by LLMs.
              </p>
            </div>

            <div style={{
              display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3, 1fr)", gap: 24
            }}>
              <FeatureCard
                title="Intelligent Code Search"
                desc="Find relevant files, functions, dependencies, and implementation details quickly using semantic vector search."
              />
              <FeatureCard
                title="Architecture Intelligence"
                desc="Visualize and understand how your application components work together and map out critical dependencies."
              />
              <FeatureCard
                title="AI Code Chat"
                desc="Ask questions about your actual codebase and receive context-aware answers directly linked to your files."
              />
              <FeatureCard
                title="Repository Indexing"
                desc="Index GitHub repositories into searchable semantic chunks and embeddings seamlessly in the background."
              />
              <FeatureCard
                title="AI Repository Understanding"
                desc="Give AI the context of your entire repository instead of isolated files to get system-wide insights."
              />
              <FeatureCard
                title="AI Developer Agent"
                desc="Use AI assistance to investigate bugs, plan refactoring, and generate executable change plans for your codebase."
              />
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how-it-works" style={{
          padding: "96px 24px", backgroundColor: "transparent",
          borderTop: "1px solid rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.05)",
          position: "relative", overflow: "hidden"
        }}>
          {/* Radial glow */}
          <div style={{
            position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)",
            width: "100%", maxWidth: 800, height: 600, opacity: 0.1, pointerEvents: "none",
            backgroundColor: "var(--accent)", borderRadius: "50%", filter: "blur(120px)"
          }} />

          <div style={{ maxWidth: 1200, margin: "0 auto", position: "relative", zIndex: 10 }}>
            <h2 style={{ fontSize: isMobile ? 28 : 36, fontWeight: 700, textAlign: "center", marginBottom: 64 }}>How DevOs works</h2>

            <div style={{
              display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3, 1fr)", gap: 48, position: "relative"
            }}>
              {/* Connecting line */}
              {!isMobile && (
                <div style={{
                  position: "absolute", top: 28, left: "15%", right: "15%", height: 1,
                  background: "linear-gradient(to right, transparent, rgba(6,182,212,0.5), transparent)"
                }} />
              )}

              <StepItem
                num="01"
                title="Connect GitHub"
                desc="Connect your repository securely in seconds. No complex setup required."
              />
              <StepItem
                num="02"
                title="Index & Understand"
                desc="DevOs automatically analyzes files, code structure, dependencies, and extracts semantic chunks."
              />
              <StepItem
                num="03"
                title="Ask & Build"
                desc="Chat with your repository, explore architecture, and use AI to work significantly faster."
              />
            </div>
          </div>
        </section>

        {/* ARCHITECTURE VISUALIZATION */}
        <section id="architecture" style={{ padding: "96px 24px" }}>
          <div style={{
            maxWidth: 1200, margin: "0 auto", display: "grid",
            gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: 64, alignItems: "center"
          }}>
            <div>
              <h2 style={{ fontSize: isMobile ? 28 : 36, fontWeight: 700, marginBottom: 24 }}>Your repository, understood by AI.</h2>
              <p style={{ color: "var(--text-muted)", marginBottom: 32, fontSize: 16, lineHeight: 1.6 }}>
                We've built a pipeline that transforms plain text code into a rich knowledge graph.
                Vector search ensures every AI response is strictly grounded in your actual implementation.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <TechItem name="GitHub API" role="Source Control Integration" />
                <TechItem name="FastAPI & PostgreSQL" role="High-performance backend & relational data" />
                <TechItem name="Sentence Transformers" role="Local embeddings generation" />
                <TechItem name="pgvector" role="Vector similarity search database" />
                <TechItem name="Groq LLMs" role="Ultra-fast conversational AI inference" />
              </div>
            </div>

            {/* AI Example UI Mockup */}
            <div style={{
              backgroundColor: "#111118", border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 16, padding: 24, boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
              position: "relative", overflow: "hidden"
            }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 24, position: "relative", zIndex: 10 }}>
                {/* User message */}
                <div style={{ display: "flex", gap: 16 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%", backgroundColor: "#1e293b",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, border: "1px solid rgba(255,255,255,0.1)", fontSize: 12, color: "white"
                  }}>U</div>
                  <div style={{
                    backgroundColor: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.05)",
                    padding: 16, borderRadius: 16, borderTopLeftRadius: 4, fontSize: 14, color: "#e2e8f0"
                  }}>
                    Explain how authentication works in this repository.
                  </div>
                </div>

                {/* AI response */}
                <div style={{ display: "flex", gap: 16 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8, backgroundColor: "var(--accent)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, boxShadow: "0 0 10px rgba(6,182,212,0.4)", fontSize: 12, fontWeight: 700, color: "white"
                  }}>D</div>
                  <div style={{
                    backgroundColor: "rgba(6,182,212,0.1)", border: "1px solid rgba(6,182,212,0.2)",
                    padding: 16, borderRadius: 16, borderTopLeftRadius: 4, fontSize: 14, color: "#e0e7ff", lineHeight: 1.6
                  }}>
                    <p style={{ marginBottom: 12 }}>Authentication is handled through the API authentication layer via JWT tokens.</p>
                    <div style={{
                      backgroundColor: "#0a0a0f", padding: 12, borderRadius: 8, border: "1px solid rgba(255,255,255,0.05)",
                      marginBottom: 12, fontFamily: "monospace", fontSize: 12, color: "#cbd5e1"
                    }}>
                      <span style={{ color: "#22D3EE" }}>import</span> jwt<br />
                      <span style={{ color: "#60a5fa" }}>def</span> <span style={{ color: "#fef08a" }}>verify_token</span>(token: str):<br />
                      &nbsp;&nbsp;&nbsp;&nbsp;payload = jwt.decode(token, JWT_SECRET)
                    </div>
                    <p>The request is validated in <code style={{ backgroundColor: "rgba(255,255,255,0.05)", padding: "2px 6px", borderRadius: 4, color: "#a5b4fc" }}>auth.py</code>, user context is established, and protected routes use the resulting state.</p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </section>

        {/* BENEFITS SECTION */}
        <section style={{ padding: "96px 24px", backgroundColor: "transparent", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            <div style={{
              display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(4, 1fr)", gap: 32
            }}>
              <BenefitBlock title="Understand faster" desc="Reduce the time spent navigating unfamiliar codebases and complex inheritance trees." />
              <BenefitBlock title="Find anything" desc="Search through your repository using semantic context instead of exact regex matches." />
              <BenefitBlock title="Ask your code" desc="Get robust AI answers grounded securely in your indexed repository chunks." />
              <BenefitBlock title="Ship with confidence" desc="Understand architecture and dependencies clearly before making breaking changes." />
            </div>
          </div>
        </section>

        {/* CTA */}
        <section style={{ padding: "128px 24px", position: "relative", overflow: "hidden" }}>
          <div style={{
            position: "absolute", inset: 0, background: "linear-gradient(to bottom, transparent, rgba(8, 145, 178, 0.2))",
            pointerEvents: "none"
          }} />
          <div style={{ maxWidth: 800, margin: "0 auto", textAlign: "center", position: "relative", zIndex: 10 }}>
            <h2 style={{ fontSize: isMobile ? 32 : 48, fontWeight: 800, marginBottom: 24 }}>Ready to understand your code differently?</h2>
            <p style={{ fontSize: 18, color: "var(--text-muted)", marginBottom: 40, lineHeight: 1.6 }}>
              Connect your repository and let DevOs become your AI-powered development workspace.
            </p>
            <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", justifyContent: "center", gap: 16 }}>
              <Link href="/dashboard" style={{
                padding: "14px 32px", backgroundColor: "var(--accent)", color: "white", borderRadius: 12,
                fontSize: 15, fontWeight: 500, textDecoration: "none", boxShadow: "0 0 20px rgba(6,182,212,0.4)"
              }}>
                Get Started Free →
              </Link>
              <Link href="#demo" style={{
                padding: "14px 32px", backgroundColor: "#111118", border: "1px solid rgba(255,255,255,0.1)",
                color: "white", borderRadius: 12, fontSize: 15, fontWeight: 500, textDecoration: "none"
              }}>
                Explore DevOs
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid rgba(255,255,255,0.1)", backgroundColor: "#000000", padding: "48px 24px" }}>
        <div style={{
          maxWidth: 1200, margin: "0 auto", display: "flex", flexDirection: isMobile ? "column" : "row",
          justifyContent: "space-between", alignItems: "center", gap: 24
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 24, height: 24, backgroundColor: "var(--accent)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: "white", fontSize: 12 }}>D</div>
            <span style={{ fontWeight: 600, color: "#e2e8f0", letterSpacing: "-0.02em" }}>DevOs</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 32, fontSize: 14, color: "var(--text-muted)" }}>
            <a href="#features" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Features</a>
            <a href="#architecture" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Architecture</a>
            <a href="#how-it-works" style={{ color: "var(--text-muted)", textDecoration: "none" }}>How it Works</a>
            <a href="/dashboard" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Dashboard</a>
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 14 }}>
            © {new Date().getFullYear()} DevOs. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Components ────────────────────────────────────────────────────────────────

function FeatureCard({ title, desc }: { title: string, desc: string }) {
  return (
    <div style={{
      backgroundColor: "#0f0f15", border: "1px solid rgba(255,255,255,0.05)",
      borderRadius: 16, padding: "32px 24px", transition: "all 0.3s"
    }}>
      <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: "#e2e8f0" }}>{title}</h3>
      <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6 }}>{desc}</p>
    </div>
  );
}

function StepItem({ num, title, desc }: { num: string, title: string, desc: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", position: "relative" }}>
      <div style={{
        width: 56, height: 56, backgroundColor: "#111118", border: "1px solid rgba(6,182,212,0.3)",
        color: "var(--accent-hover)", fontWeight: 700, fontSize: 18, borderRadius: 16,
        display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24,
        boxShadow: "0 0 20px rgba(6,182,212,0.15)", position: "relative", zIndex: 10
      }}>
        {num}
      </div>
      <h3 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12, color: "#e2e8f0" }}>{title}</h3>
      <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6 }}>{desc}</p>
    </div>
  );
}

function TechItem({ name, role }: { name: string, role: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, paddingBottom: 12, borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
      <div style={{ width: 8, height: 8, backgroundColor: "rgba(6,182,212,0.5)", borderRadius: "50%" }} />
      <div>
        <div style={{ color: "#e2e8f0", fontWeight: 500, fontSize: 14 }}>{name}</div>
        <div style={{ color: "var(--text-muted)", fontSize: 12 }}>{role}</div>
      </div>
    </div>
  );
}

function BenefitBlock({ title, desc }: { title: string, desc: string }) {
  return (
    <div>
      <h4 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8, color: "#e2e8f0" }}>{title}</h4>
      <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6 }}>{desc}</p>
    </div>
  );
}
