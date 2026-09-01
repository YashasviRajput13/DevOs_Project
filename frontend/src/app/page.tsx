import Link from "next/link";
import { ArrowRight, Box, Code2, Database, LayoutGrid, MessageSquare, Network, Search, Terminal } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#06060c] text-white selection:bg-indigo-500/30 font-sans overflow-hidden">
      {/* Background glowing gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-[1000px] h-[500px] opacity-30 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at top, rgba(99, 102, 241, 0.4) 0%, rgba(6, 6, 12, 0) 70%)" }} />

      {/* Navbar */}
      <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-indigo-500 rounded-lg flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(99,102,241,0.5)]">
              D
            </div>
            <span className="font-semibold text-lg tracking-tight">DevOs</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <Link href="#product" className="hover:text-white transition-colors">Product</Link>
            <Link href="#features" className="hover:text-white transition-colors">Features</Link>
            <Link href="#how-it-works" className="hover:text-white transition-colors">How it Works</Link>
            <Link href="#architecture" className="hover:text-white transition-colors">Architecture</Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm font-medium text-slate-300 hover:text-white transition-colors hidden sm:block">
              Sign In
            </Link>
            <Link href="/dashboard" className="text-sm font-medium bg-white text-black px-4 py-2 rounded-lg hover:bg-slate-200 transition-colors">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* HERO SECTION */}
        <section className="relative pt-32 pb-20 px-6 max-w-7xl mx-auto text-center z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-semibold mb-8 backdrop-blur-sm shadow-[0_0_20px_rgba(99,102,241,0.15)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            AI-powered developer intelligence
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-8 leading-[1.1]">
            Understand. Build. Ship.<br />
            With the <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Power of AI.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            DevOs transforms your GitHub repositories into an intelligent workspace where you can explore code, understand architecture, and collaborate with AI.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
            <Link href="/dashboard" className="w-full sm:w-auto px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-all shadow-[0_0_30px_rgba(99,102,241,0.3)] hover:shadow-[0_0_40px_rgba(99,102,241,0.5)]">
              Get Started Free →
            </Link>
            <Link href="#demo" className="w-full sm:w-auto px-8 py-3.5 border border-white/10 hover:bg-white/5 rounded-xl font-medium transition-colors text-slate-300">
              See DevOs in Action
            </Link>
          </div>

          {/* VIDEO SHOWCASE MOCKUP */}
          <div id="demo" className="relative max-w-5xl mx-auto rounded-2xl border border-white/10 bg-[#0d0d14] shadow-2xl overflow-hidden mt-12 group">
            <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 to-transparent pointer-events-none" />
            
            {/* Fake browser bar */}
            <div className="h-12 border-b border-white/5 flex items-center px-4 gap-2 bg-black/40">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-slate-700"></div>
                <div className="w-3 h-3 rounded-full bg-slate-700"></div>
                <div className="w-3 h-3 rounded-full bg-slate-700"></div>
              </div>
              <div className="mx-auto w-1/2 h-6 bg-white/5 rounded-md border border-white/5"></div>
            </div>

            {/* Dashboard UI Mockup inside Video Container */}
            <div className="relative aspect-video flex flex-col md:flex-row bg-[#08080c]">
              
              {/* Play Button Overlay */}
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/40 backdrop-blur-[2px] transition-all group-hover:bg-black/20 group-hover:backdrop-blur-0 cursor-pointer">
                <div className="w-20 h-20 rounded-full bg-indigo-600/90 flex items-center justify-center shadow-[0_0_30px_rgba(99,102,241,0.6)] group-hover:scale-110 transition-transform pl-1">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="white"><path d="M5 3l14 9-14 9V3z"/></svg>
                </div>
              </div>

              {/* Sidebar Mockup */}
              <div className="hidden md:flex w-48 border-r border-white/5 flex-col p-4 gap-4 opacity-50">
                <div className="h-4 w-24 bg-white/10 rounded mb-4" />
                <div className="h-8 w-full bg-white/5 rounded" />
                <div className="h-8 w-full bg-white/5 rounded" />
                <div className="h-8 w-full bg-indigo-500/20 rounded border border-indigo-500/30" />
              </div>
              
              {/* Main Content Mockup */}
              <div className="flex-1 p-6 md:p-8 flex flex-col gap-6 opacity-60">
                <div className="flex justify-between items-center">
                  <div className="h-6 w-48 bg-white/10 rounded" />
                  <div className="h-6 w-24 bg-green-500/20 rounded-full border border-green-500/30" />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="h-20 bg-white/5 rounded-xl border border-white/5" />
                  <div className="h-20 bg-white/5 rounded-xl border border-white/5" />
                  <div className="h-20 bg-white/5 rounded-xl border border-white/5" />
                </div>
                <div className="flex-1 flex gap-4">
                  <div className="flex-1 bg-white/5 rounded-xl border border-white/5 p-4 flex flex-col gap-3">
                    <div className="h-4 w-32 bg-white/10 rounded" />
                    <div className="h-full bg-[#111118] rounded border border-white/5 p-3 flex flex-col gap-2">
                      <div className="h-3 w-3/4 bg-white/5 rounded" />
                      <div className="h-3 w-1/2 bg-white/5 rounded" />
                      <div className="h-3 w-5/6 bg-white/5 rounded" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Video control bar fake */}
              <div className="absolute bottom-0 left-0 right-0 h-10 bg-black/80 border-t border-white/10 flex items-center px-4 gap-4 z-20">
                <div className="w-3 h-3 bg-white rounded-sm"></div>
                <div className="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
                  <div className="w-1/3 h-full bg-indigo-500"></div>
                </div>
                <div className="text-[10px] text-white/50 font-mono">0:42 / 2:15</div>
              </div>

            </div>
          </div>
          
          <div className="mt-16 text-slate-500 text-sm font-medium tracking-wide text-center">
            Built for developers who want to understand their code faster.
          </div>
        </section>

        {/* FEATURES SECTION */}
        <section id="features" className="py-24 px-6 relative">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need to understand your codebase</h2>
              <p className="text-slate-400 max-w-2xl mx-auto">Turn raw source code into navigable, intelligent insights powered by LLMs.</p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <FeatureCard 
                icon={<Search size={24} className="text-indigo-400" />}
                title="Intelligent Code Search"
                desc="Find relevant files, functions, dependencies, and implementation details quickly using semantic vector search."
              />
              <FeatureCard 
                icon={<Network size={24} className="text-purple-400" />}
                title="Architecture Intelligence"
                desc="Visualize and understand how your application components work together and map out critical dependencies."
              />
              <FeatureCard 
                icon={<MessageSquare size={24} className="text-blue-400" />}
                title="AI Code Chat"
                desc="Ask questions about your actual codebase and receive context-aware answers directly linked to your files."
              />
              <FeatureCard 
                icon={<Database size={24} className="text-emerald-400" />}
                title="Repository Indexing"
                desc="Index GitHub repositories into searchable semantic chunks and embeddings seamlessly in the background."
              />
              <FeatureCard 
                icon={<Box size={24} className="text-pink-400" />}
                title="AI Repository Understanding"
                desc="Give AI the context of your entire repository instead of isolated files to get system-wide insights."
              />
              <FeatureCard 
                icon={<Terminal size={24} className="text-cyan-400" />}
                title="AI Developer Agent"
                desc="Use AI assistance to investigate bugs, plan refactoring, and generate executable change plans for your codebase."
              />
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how-it-works" className="py-24 px-6 bg-[#0a0a0f] border-y border-white/5 relative overflow-hidden">
          {/* Radial glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[800px] h-[600px] opacity-10 pointer-events-none bg-indigo-500 rounded-full blur-[120px]" />

          <div className="max-w-7xl mx-auto relative z-10">
            <h2 className="text-3xl md:text-4xl font-bold text-center mb-16">How DevOs works</h2>
            
            <div className="grid md:grid-cols-3 gap-12 relative">
              {/* Connecting line */}
              <div className="hidden md:block absolute top-[28px] left-[15%] right-[15%] h-[1px] bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
              
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

        {/* AI & ARCHITECTURE VISUALIZATION */}
        <section id="architecture" className="py-24 px-6 max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">Your repository, understood by AI.</h2>
              <p className="text-slate-400 mb-8 text-lg">
                We've built a pipeline that transforms plain text code into a rich knowledge graph. 
                Vector search ensures every AI response is strictly grounded in your actual implementation.
              </p>
              
              <div className="flex flex-col gap-4">
                <TechItem name="GitHub API" role="Source Control Integration" />
                <TechItem name="FastAPI & PostgreSQL" role="High-performance backend & relational data" />
                <TechItem name="Sentence Transformers" role="Local embeddings generation" />
                <TechItem name="pgvector" role="Vector similarity search database" />
                <TechItem name="Groq LLMs" role="Ultra-fast conversational AI inference" />
                <TechItem name="React & Next.js" role="Interactive frontend experience" />
              </div>
            </div>

            {/* AI Example UI Mockup */}
            <div className="bg-[#111118] border border-white/10 rounded-2xl p-6 shadow-2xl relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="flex flex-col gap-6 relative z-10">
                {/* User message */}
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center flex-shrink-0 border border-white/10 text-xs text-white">U</div>
                  <div className="bg-white/5 border border-white/5 p-4 rounded-2xl rounded-tl-sm text-sm text-slate-200">
                    Explain how authentication works in this repository.
                  </div>
                </div>
                
                {/* AI response */}
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-[0_0_10px_rgba(99,102,241,0.4)] text-white text-xs font-bold">D</div>
                  <div className="bg-indigo-500/10 border border-indigo-500/20 p-4 rounded-2xl rounded-tl-sm text-sm text-indigo-100 leading-relaxed shadow-sm">
                    <p className="mb-3">Authentication is handled through the API authentication layer via JWT tokens.</p>
                    <div className="bg-[#0a0a0f] p-3 rounded-lg border border-white/5 mb-3 font-mono text-[11px] text-slate-300">
                      <span className="text-purple-400">import</span> jwt<br/>
                      <span className="text-blue-400">def</span> <span className="text-yellow-200">verify_token</span>(token: str):<br/>
                      &nbsp;&nbsp;&nbsp;&nbsp;payload = jwt.decode(token, JWT_SECRET)
                    </div>
                    <p>The request is validated in <code className="text-indigo-300 bg-white/5 px-1.5 py-0.5 rounded">auth.py</code>, user context is established, and protected routes use the resulting state.</p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </section>

        {/* BENEFITS SECTION */}
        <section className="py-24 px-6 bg-[#0a0a0f] border-t border-white/5">
          <div className="max-w-7xl mx-auto">
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <BenefitBlock title="Understand faster" desc="Reduce the time spent navigating unfamiliar codebases and complex inheritance trees." />
              <BenefitBlock title="Find anything" desc="Search through your repository using semantic context instead of exact regex matches." />
              <BenefitBlock title="Ask your code" desc="Get robust AI answers grounded securely in your indexed repository chunks." />
              <BenefitBlock title="Ship with confidence" desc="Understand architecture and dependencies clearly before making breaking changes." />
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-32 px-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-indigo-900/20 pointer-events-none" />
          <div className="max-w-4xl mx-auto text-center relative z-10">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">Ready to understand your code differently?</h2>
            <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto">
              Connect your repository and let DevOs become your AI-powered development workspace.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link href="/dashboard" className="px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-all shadow-[0_0_20px_rgba(99,102,241,0.4)]">
                Get Started Free →
              </Link>
              <Link href="#demo" className="px-8 py-3.5 bg-[#111118] border border-white/10 hover:border-white/30 text-white rounded-xl font-medium transition-all">
                Explore DevOs
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="border-t border-white/10 bg-[#06060c] py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-indigo-500 rounded flex items-center justify-center font-bold text-white text-xs">D</div>
            <span className="font-semibold text-slate-200 tracking-tight">DevOs</span>
          </div>
          <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-sm text-slate-500">
            <Link href="#product" className="hover:text-slate-300 transition-colors">Product</Link>
            <Link href="#features" className="hover:text-slate-300 transition-colors">Features</Link>
            <Link href="#" className="hover:text-slate-300 transition-colors">Documentation</Link>
            <Link href="#architecture" className="hover:text-slate-300 transition-colors">Architecture</Link>
            <Link href="#" className="hover:text-slate-300 transition-colors">GitHub</Link>
          </div>
          <div className="text-slate-600 text-sm">
            © {new Date().getFullYear()} DevOs. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Components ────────────────────────────────────────────────────────────────

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="bg-[#0f0f15] border border-white/5 rounded-2xl p-6 hover:bg-[#13131a] hover:border-white/10 transition-all duration-300 group">
      <div className="w-12 h-12 bg-white/5 rounded-xl border border-white/5 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-3 text-slate-200">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function StepItem({ num, title, desc }: { num: string, title: string, desc: string }) {
  return (
    <div className="flex flex-col items-center text-center relative">
      <div className="w-14 h-14 bg-[#111118] border border-indigo-500/30 text-indigo-400 font-bold text-lg rounded-2xl flex items-center justify-center mb-6 shadow-[0_0_20px_rgba(99,102,241,0.15)] relative z-10">
        {num}
      </div>
      <h3 className="text-xl font-semibold mb-3 text-slate-200">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function TechItem({ name, role }: { name: string, role: string }) {
  return (
    <div className="flex items-center gap-4 py-3 border-b border-white/5">
      <div className="w-2 h-2 bg-indigo-500/50 rounded-full" />
      <div>
        <div className="text-slate-200 font-medium text-sm">{name}</div>
        <div className="text-slate-500 text-xs">{role}</div>
      </div>
    </div>
  );
}

function BenefitBlock({ title, desc }: { title: string, desc: string }) {
  return (
    <div>
      <h4 className="text-lg font-semibold mb-2 text-slate-200">{title}</h4>
      <p className="text-slate-400 text-sm">{desc}</p>
    </div>
  );
}
