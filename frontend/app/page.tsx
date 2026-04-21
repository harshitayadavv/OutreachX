import Link from "next/link";
import { ArrowRight, Zap, Mail, BarChart3, ChevronRight, GitBranch } from "lucide-react";

export default function LandingPage() {
  return (
    <div style={{ background: "#0a0a0a", minHeight: "100vh", color: "#fff", position: "relative", overflow: "hidden" }}>
      
      {/* Dot grid background */}
      <div className="dot-grid" style={{ position: "absolute", inset: 0, pointerEvents: "none" }} />
      
      {/* Radial glow */}
      <div style={{
        position: "absolute", top: "-20%", left: "50%", transform: "translateX(-50%)",
        width: "800px", height: "600px",
        background: "radial-gradient(ellipse at center, rgba(127,119,221,0.15) 0%, transparent 70%)",
        pointerEvents: "none"
      }} />

      {/* Nav */}
      <nav style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "20px 48px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: 32, height: 32, background: "#7F77DD", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13, letterSpacing: "-0.5px" }}>OX</div>
          <span style={{ fontWeight: 600, fontSize: 15, letterSpacing: "-0.3px" }}>OutreachX</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <Link href="/docs" style={{ color: "#9ca3af", fontSize: 14, textDecoration: "none" }}>Docs</Link>
          <Link href="/dashboard" style={{
            background: "#7F77DD", color: "#fff", padding: "7px 16px", borderRadius: 6,
            fontSize: 14, fontWeight: 500, textDecoration: "none", display: "flex", alignItems: "center", gap: 6
          }}>
            Dashboard <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ position: "relative", zIndex: 10, textAlign: "center", padding: "120px 24px 80px" }}>
        
        {/* Pill badge */}
        <div className="animate-fade-up" style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "rgba(127,119,221,0.12)", border: "1px solid rgba(127,119,221,0.25)", borderRadius: 99, padding: "5px 12px", marginBottom: 32, fontSize: 12, color: "#a5a0ff", fontWeight: 500 }}>
          <Zap size={11} />
          Powered by LangGraph + Groq
        </div>

        <h1 className="animate-fade-up delay-100" style={{ fontSize: "clamp(40px, 6vw, 80px)", fontWeight: 700, letterSpacing: "-2px", lineHeight: 1.05, maxWidth: 840, margin: "0 auto 24px" }}>
          <span className="gradient-text">AI-powered cold outreach,</span>
          <br />on autopilot
        </h1>

        <p className="animate-fade-up delay-200" style={{ fontSize: 18, color: "#9ca3af", maxWidth: 560, margin: "0 auto 40px", lineHeight: 1.6, fontWeight: 400 }}>
          Discover startups, find decision-maker emails, generate personalized cold emails, and track replies — all in one pipeline.
        </p>

        <div className="animate-fade-up delay-300" style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <Link href="/dashboard" style={{
            background: "#7F77DD", color: "#fff", padding: "12px 24px", borderRadius: 8,
            fontSize: 15, fontWeight: 600, textDecoration: "none", display: "flex", alignItems: "center", gap: 8,
            boxShadow: "0 0 30px rgba(127,119,221,0.4)"
          }}>
            Start a campaign <ArrowRight size={16} />
          </Link>
          <Link href="/docs" style={{
            background: "rgba(255,255,255,0.05)", color: "#e5e5e5", padding: "12px 24px", borderRadius: 8,
            fontSize: 15, fontWeight: 500, textDecoration: "none", border: "1px solid rgba(255,255,255,0.1)",
            display: "flex", alignItems: "center", gap: 8
          }}>
            View docs <ChevronRight size={15} />
          </Link>
        </div>

        {/* Fake pipeline preview */}
        <div className="animate-fade-up delay-400" style={{
          margin: "64px auto 0", maxWidth: 640, background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, padding: "16px 20px",
          display: "flex", alignItems: "center", gap: 8, justifyContent: "center", flexWrap: "wrap"
        }}>
          {["Planning", "Discovering leads", "Researching", "Finding contacts", "Generating emails", "Done ✓"].map((step, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                fontSize: 12, color: i === 5 ? "#22c55e" : i === 0 ? "#7F77DD" : "#6b7280",
                fontFamily: "'DM Mono', monospace", fontWeight: 500
              }}>{step}</span>
              {i < 5 && <span style={{ color: "#374151", fontSize: 12 }}>→</span>}
            </div>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section style={{ position: "relative", zIndex: 10, padding: "0 48px 100px", maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20 }}>
          
          {[
            {
              icon: <Zap size={20} color="#7F77DD" />,
              title: "3 ways to find leads",
              desc: "AI-powered company discovery, direct company name input, or upload your own CSV/Excel/JSON lead list.",
              items: ["AI discovery via natural language", "Direct company name input", "Upload CSV / Excel / JSON"]
            },
            {
              icon: <Mail size={20} color="#7F77DD" />,
              title: "Resume-aware emails",
              desc: "Upload your resume once. The AI reads your background and writes cold emails that sound authentically like you.",
              items: ["Parses your skills & experience", "Personalizes per company context", "Tone-matches your writing style"]
            },
            {
              icon: <BarChart3 size={20} color="#7F77DD" />,
              title: "Auto follow-ups",
              desc: "Tracks opens, clicks, and replies automatically. Sends smart follow-ups based on engagement signals.",
              items: ["Open & click tracking", "Reply detection", "Timed follow-up sequences"]
            }
          ].map((card, i) => (
            <div key={i} className="animate-fade-up" style={{
              animationDelay: `${0.1 * i + 0.4}s`,
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12, padding: "28px",
              transition: "border-color 0.2s, background 0.2s"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                <div style={{ width: 36, height: 36, background: "rgba(127,119,221,0.12)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {card.icon}
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 600, letterSpacing: "-0.3px" }}>{card.title}</h3>
              </div>
              <p style={{ fontSize: 14, color: "#9ca3af", lineHeight: 1.6, marginBottom: 18 }}>{card.desc}</p>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
                {card.items.map((item, j) => (
                  <li key={j} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#6b7280" }}>
                    <span style={{ width: 4, height: 4, borderRadius: "50%", background: "#7F77DD", flexShrink: 0 }} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{ position: "relative", zIndex: 10, borderTop: "1px solid rgba(255,255,255,0.06)", padding: "24px 48px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 24, height: 24, background: "#7F77DD", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 10 }}>OX</div>
          <span style={{ fontSize: 13, color: "#6b7280" }}>OutreachX</span>
        </div>
        <p style={{ fontSize: 13, color: "#4b5563" }}>Built with LangGraph + Groq</p>
        <a href="https://github.com" style={{ color: "#6b7280", display: "flex", alignItems: "center", gap: 6, fontSize: 13, textDecoration: "none" }}>
          <GitBranch size={14} /> GitHub
        </a>
      </footer>
    </div>
  );
}
