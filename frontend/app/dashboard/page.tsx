"use client";

import { useState, useRef } from "react";
import {
  Users, Send, Eye, MessageSquare, TrendingUp, TrendingDown,
  Upload, Play, CheckCircle, Loader2, Circle, ExternalLink,
  ChevronDown, FileText, X
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

const STAT_CARDS = [
  { label: "Total Leads", value: "1,284", trend: "+12%", up: true, icon: Users, color: "#7F77DD" },
  { label: "Emails Sent", value: "847", trend: "+8%", up: true, icon: Send, color: "#3b82f6" },
  { label: "Open Rate", value: "34.2%", trend: "+2.1%", up: true, icon: Eye, color: "#22c55e" },
  { label: "Reply Rate", value: "8.7%", trend: "-0.3%", up: false, icon: MessageSquare, color: "#f59e0b" },
];

const PIPELINE_STEPS = [
  { id: "plan", label: "Planning campaign strategy..." },
  { id: "discover", label: "Discovering leads..." },
  { id: "research", label: "Researching companies..." },
  { id: "contacts", label: "Finding contacts & emails..." },
  { id: "emails", label: "Generating personalized emails..." },
  { id: "done", label: "Done!" },
];

const TARGET_ROLES = ["CEO", "CTO", "HR Manager", "Engineering Lead", "Founder", "VP Sales"];

type StepStatus = "pending" | "active" | "done";
type EmailStatus = "draft" | "approved" | "sent" | "opened" | "replied";

interface Lead {
  id: string;
  company: string;
  website: string;
  country: string;
  batch: string;
  contact_email: string;
  linkedin: string;
  email_status: EmailStatus;
  score: number;
  subject: string;
  body: string;
}

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [targetRole, setTargetRole] = useState("CEO");
  const [leadsFile, setLeadsFile] = useState<File | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeParsed, setResumeParsed] = useState<{ name: string; role: string } | null>(null);
  const [running, setRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(PIPELINE_STEPS.map(() => "pending"));
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");
  const [roleOpen, setRoleOpen] = useState(false);
  const leadsFileRef = useRef<HTMLInputElement>(null);
  const resumeFileRef = useRef<HTMLInputElement>(null);

  const handleResumeUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setResumeFile(f);
    setResumeParsed({ name: "Harshita Yadav", role: "AI Engineer" });
  };

  const handleLeadsUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setLeadsFile(f);
  };

  const runAgent = async () => {
    if (!query && !leadsFile) return;
    setRunning(true);
    setLeads([]);
    const statuses: StepStatus[] = PIPELINE_STEPS.map(() => "pending");
    setStepStatuses([...statuses]);

    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
      setCurrentStep(i);
      statuses[i] = "active";
      setStepStatuses([...statuses]);
      await new Promise(r => setTimeout(r, i === PIPELINE_STEPS.length - 1 ? 400 : 1200 + Math.random() * 600));
      statuses[i] = "done";
      setStepStatuses([...statuses]);
    }

    // Mock result
    const mockLeads: Lead[] = [
      { id: "1", company: "Razorpay", website: "razorpay.com", country: "India", batch: "YC W15", contact_email: "harshil@razorpay.com", linkedin: "linkedin.com/in/harshil", email_status: "draft", score: 92, subject: "Quick question about your fintech infrastructure", body: "Hi Harshil,\n\nI came across Razorpay's recent expansion into Southeast Asia and was impressed by your payment stack.\n\nI'm an AI engineer building tools that help fintech teams automate their payment reconciliation. Given Razorpay's scale, I thought there could be a strong fit.\n\nWould you be open to a 15-minute call this week?\n\nBest,\nHarshita" },
      { id: "2", company: "Groww", website: "groww.in", country: "India", batch: "YC W19", contact_email: "lalit@groww.in", linkedin: "linkedin.com/in/lalit-keshre", email_status: "approved", score: 87, subject: "Automating investor onboarding at Groww", body: "Hi Lalit,\n\nGroww's growth to 50M+ users is remarkable. I'm working on AI-powered KYC automation that could reduce your onboarding drop-off by 30%.\n\nI'd love to share a quick demo.\n\nBest,\nHarshita" },
      { id: "3", company: "Sarvam AI", website: "sarvam.ai", country: "India", batch: "YC S23", contact_email: "vivek@sarvam.ai", linkedin: "linkedin.com/in/vivek-raghavan", email_status: "sent", score: 95, subject: "Collaboration on multilingual AI agents", body: "Hi Vivek,\n\nSarvam's work on Indic language models is exactly the direction the ecosystem needs. I'm building complementary outreach tooling that integrates with LLM providers like yours.\n\nOpen to a quick chat?\n\nBest,\nHarshita" },
      { id: "4", company: "Zepto", website: "zeptonow.com", country: "India", batch: "-", contact_email: "aadit@zepto.com", linkedin: "linkedin.com/in/aadit", email_status: "opened", score: 78, subject: "Supply chain AI for quick commerce", body: "Hi Aadit,\n\nZepto's 10-minute delivery model is operationally impressive. I'm exploring how AI forecasting tools can reduce last-mile waste for Q-commerce players like you.\n\nWould love your thoughts.\n\nBest,\nHarshita" },
      { id: "5", company: "CRED", website: "cred.club", country: "India", batch: "-", contact_email: "kunal@cred.club", linkedin: "linkedin.com/in/kunal-shah", email_status: "replied", score: 83, subject: "AI-powered member engagement at CRED", body: "Hi Kunal,\n\nCRED's community-first approach to fintech is unique. I'm working on personalization engines that could deepen your member engagement layer.\n\nHappy to share what we've built.\n\nBest,\nHarshita" },
    ];

    setLeads(mockLeads);
    setRunning(false);
    setCurrentStep(-1);

    // Try real API
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const formData = new FormData();
      formData.append("query", query);
      formData.append("target_role", targetRole);
      formData.append("sender_name", resumeParsed?.name || "User");
      formData.append("sender_value_prop", "AI-powered tools");
      if (leadsFile) formData.append("leads_file", leadsFile);
      if (resumeFile) formData.append("resume_file", resumeFile);
      const res = await fetch(`${apiUrl}/agents/run`, { method: "POST", body: formData });
      if (res.ok) {
        const data = await res.json();
        if (data.leads?.length) setLeads(data.leads);
      }
    } catch {}
  };

  const openEmail = (lead: Lead) => {
    setSelectedLead(lead);
    setEditSubject(lead.subject);
    setEditBody(lead.body);
    setEditMode(false);
  };

  const approveSend = (lead: Lead) => {
    setLeads(prev => prev.map(l => l.id === lead.id ? { ...l, email_status: "sent" as EmailStatus } : l));
    setSelectedLead(null);
  };

  const saveEdit = () => {
    if (!selectedLead) return;
    setLeads(prev => prev.map(l => l.id === selectedLead.id ? { ...l, subject: editSubject, body: editBody } : l));
    setSelectedLead(prev => prev ? { ...prev, subject: editSubject, body: editBody } : null);
    setEditMode(false);
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* Stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 28 }}>
        {STAT_CARDS.map((card, i) => (
          <div key={i} className="animate-fade-up" style={{
            animationDelay: `${i * 0.07}s`,
            background: "#fff", border: "1px solid #e5e5e5", borderRadius: 10,
            padding: "20px 20px 16px"
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ fontSize: 12, color: "#9ca3af", fontWeight: 500 }}>{card.label}</span>
              <div style={{ width: 30, height: 30, borderRadius: 7, background: `${card.color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <card.icon size={14} color={card.color} />
              </div>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: "#0a0a0a", letterSpacing: "-0.5px", marginBottom: 6 }}>{card.value}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
              {card.up ? <TrendingUp size={12} color="#22c55e" /> : <TrendingDown size={12} color="#ef4444" />}
              <span style={{ color: card.up ? "#22c55e" : "#ef4444", fontWeight: 500 }}>{card.trend}</span>
              <span style={{ color: "#9ca3af" }}>vs last month</span>
            </div>
          </div>
        ))}
      </div>

      {/* Run campaign panel */}
      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: "24px", marginBottom: 24 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", marginBottom: 18, letterSpacing: "-0.3px" }}>Run AI Campaign</h2>
        
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Query input */}
          <div>
            <label style={{ fontSize: 12, color: "#6b7280", fontWeight: 500, display: "block", marginBottom: 6 }}>Campaign Query</label>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder='e.g. "YC India fintech startups 2021" or "email Razorpay, Groww, Sarvam AI"'
              style={{
                width: "100%", padding: "10px 14px", border: "1px solid #e5e5e5", borderRadius: 8,
                fontSize: 14, outline: "none", background: "#fafafa", color: "#0a0a0a",
                fontFamily: "inherit", transition: "border-color 0.15s"
              }}
              onFocus={e => e.target.style.borderColor = "#7F77DD"}
              onBlur={e => e.target.style.borderColor = "#e5e5e5"}
            />
          </div>

          {/* Row: role + file uploads */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            
            {/* Target role */}
            <div>
              <label style={{ fontSize: 12, color: "#6b7280", fontWeight: 500, display: "block", marginBottom: 6 }}>Target Role</label>
              <div style={{ position: "relative" }}>
                <button
                  onClick={() => setRoleOpen(!roleOpen)}
                  style={{
                    width: "100%", padding: "9px 14px", border: "1px solid #e5e5e5", borderRadius: 8,
                    fontSize: 13, background: "#fafafa", color: "#0a0a0a", cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "space-between", fontFamily: "inherit"
                  }}
                >
                  {targetRole}
                  <ChevronDown size={14} color="#9ca3af" />
                </button>
                {roleOpen && (
                  <div style={{
                    position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
                    background: "#fff", border: "1px solid #e5e5e5", borderRadius: 8,
                    boxShadow: "0 8px 24px rgba(0,0,0,0.08)", zIndex: 100, overflow: "hidden"
                  }}>
                    {TARGET_ROLES.map(r => (
                      <button
                        key={r}
                        onClick={() => { setTargetRole(r); setRoleOpen(false); }}
                        style={{
                          width: "100%", padding: "8px 14px", border: "none", background: r === targetRole ? "#f5f5ff" : "#fff",
                          color: r === targetRole ? "#7F77DD" : "#0a0a0a", fontSize: 13, textAlign: "left",
                          cursor: "pointer", fontFamily: "inherit", fontWeight: r === targetRole ? 600 : 400
                        }}
                      >{r}</button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Leads file */}
            <div>
              <label style={{ fontSize: 12, color: "#6b7280", fontWeight: 500, display: "block", marginBottom: 6 }}>Upload Leads (optional)</label>
              <input ref={leadsFileRef} type="file" accept=".csv,.xlsx,.json" style={{ display: "none" }} onChange={handleLeadsUpload} />
              <button
                onClick={() => leadsFileRef.current?.click()}
                style={{
                  width: "100%", padding: "9px 14px", border: `1px dashed ${leadsFile ? "#7F77DD" : "#d1d5db"}`,
                  borderRadius: 8, fontSize: 13, background: leadsFile ? "#f5f5ff" : "#fafafa",
                  color: leadsFile ? "#7F77DD" : "#9ca3af", cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontFamily: "inherit"
                }}
              >
                <Upload size={13} />
                {leadsFile ? leadsFile.name.slice(0, 16) + "…" : "CSV / Excel / JSON"}
              </button>
            </div>

            {/* Resume file */}
            <div>
              <label style={{ fontSize: 12, color: "#6b7280", fontWeight: 500, display: "block", marginBottom: 6 }}>Upload Resume</label>
              <input ref={resumeFileRef} type="file" accept=".pdf,.txt" style={{ display: "none" }} onChange={handleResumeUpload} />
              <button
                onClick={() => resumeFileRef.current?.click()}
                style={{
                  width: "100%", padding: "9px 14px", border: `1px dashed ${resumeFile ? "#7F77DD" : "#d1d5db"}`,
                  borderRadius: 8, fontSize: 13, background: resumeFile ? "#f5f5ff" : "#fafafa",
                  color: resumeFile ? "#7F77DD" : "#9ca3af", cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontFamily: "inherit"
                }}
              >
                <FileText size={13} />
                {resumeFile ? resumeFile.name.slice(0, 16) + "…" : "PDF / TXT"}
              </button>
            </div>
          </div>

          {/* Resume parsed preview */}
          {resumeParsed && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "#f0fdf4", borderRadius: 7, border: "1px solid #bbf7d0" }}>
              <CheckCircle size={13} color="#22c55e" />
              <span style={{ fontSize: 12, color: "#15803d" }}>Parsed: <strong>{resumeParsed.name}</strong> · {resumeParsed.role}</span>
            </div>
          )}

          {/* Run button */}
          <button
            onClick={runAgent}
            disabled={running || (!query && !leadsFile)}
            style={{
              background: running || (!query && !leadsFile) ? "#c4c1ff" : "#7F77DD",
              color: "#fff", border: "none", borderRadius: 8, padding: "11px 20px",
              fontSize: 14, fontWeight: 600, cursor: running || (!query && !leadsFile) ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              alignSelf: "flex-start", minWidth: 180, transition: "background 0.15s",
              boxShadow: running ? "none" : "0 0 20px rgba(127,119,221,0.35)"
            }}
          >
            {running ? <Loader2 size={15} className="animate-spin-custom" /> : <Play size={15} />}
            {running ? "Running..." : "Run AI Agent →"}
          </button>
        </div>

        {/* Progress steps */}
        {(running || leads.length > 0) && currentStep >= 0 && (
          <div style={{ marginTop: 20, padding: "16px", background: "#0a0a0a", borderRadius: 10, fontFamily: "'DM Mono', monospace" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {PIPELINE_STEPS.map((step, i) => {
                const status = stepStatuses[i];
                return (
                  <div key={step.id} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    {status === "done" ? (
                      <CheckCircle size={13} color="#22c55e" />
                    ) : status === "active" ? (
                      <Loader2 size={13} color="#7F77DD" className="animate-spin-custom" />
                    ) : (
                      <Circle size={13} color="#374151" />
                    )}
                    <span style={{
                      fontSize: 12,
                      color: status === "done" ? "#22c55e" : status === "active" ? "#a5a0ff" : "#4b5563"
                    }}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Leads table */}
      {leads.length > 0 && (
        <div className="animate-fade-up" style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #e5e5e5", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a" }}>Results — {leads.length} leads found</h2>
            <span style={{ fontSize: 12, color: "#9ca3af" }}>{leads.filter(l => l.email_status !== "draft").length} emails ready</span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#fafafa" }}>
                  {["Company", "Website", "Country", "Batch", "Contact Email", "LinkedIn", "Status", "Score", "Actions"].map(h => (
                    <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontWeight: 500, color: "#9ca3af", fontSize: 11, whiteSpace: "nowrap", borderBottom: "1px solid #f0f0f0" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {leads.map((lead, i) => (
                  <tr key={lead.id} style={{ borderBottom: "1px solid #f0f0f0", transition: "background 0.1s" }}
                    onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                    onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                  >
                    <td style={{ padding: "12px 14px", fontWeight: 600, color: "#0a0a0a" }}>{lead.company}</td>
                    <td style={{ padding: "12px 14px", color: "#6b7280" }}>{lead.website}</td>
                    <td style={{ padding: "12px 14px", color: "#6b7280" }}>{lead.country}</td>
                    <td style={{ padding: "12px 14px", color: "#6b7280" }}>{lead.batch}</td>
                    <td style={{ padding: "12px 14px", color: "#7F77DD", fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{lead.contact_email}</td>
                    <td style={{ padding: "12px 14px" }}>
                      <a href={`https://${lead.linkedin}`} target="_blank" rel="noreferrer" style={{ color: "#0077b5", display: "inline-flex", alignItems: "center" }}>
                        <ExternalLink size={13} />
                      </a>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <Badge variant={lead.email_status as any} style={{ textTransform: "capitalize" }}>{lead.email_status}</Badge>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div style={{ width: 36, height: 4, borderRadius: 99, background: "#e5e5e5", overflow: "hidden" }}>
                          <div style={{ height: "100%", width: `${lead.score}%`, background: lead.score > 85 ? "#22c55e" : lead.score > 70 ? "#f59e0b" : "#ef4444", borderRadius: 99 }} />
                        </div>
                        <span style={{ fontWeight: 600, color: "#0a0a0a" }}>{lead.score}</span>
                      </div>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <button
                        onClick={() => openEmail(lead)}
                        style={{ padding: "5px 10px", background: "#f5f5ff", border: "1px solid #e0ddff", borderRadius: 6, fontSize: 12, color: "#7F77DD", cursor: "pointer", fontWeight: 500, fontFamily: "inherit" }}
                      >
                        View Email
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Slide-over email panel */}
      {selectedLead && (
        <>
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", zIndex: 100 }} onClick={() => setSelectedLead(null)} />
          <div className="animate-slide-in-right" style={{
            position: "fixed", top: 0, right: 0, bottom: 0, width: 480,
            background: "#fff", zIndex: 110, display: "flex", flexDirection: "column",
            boxShadow: "-8px 0 40px rgba(0,0,0,0.1)"
          }}>
            <div style={{ padding: "20px 24px", borderBottom: "1px solid #e5e5e5", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>Email for</p>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: "#0a0a0a" }}>{selectedLead.company}</h3>
              </div>
              <button onClick={() => setSelectedLead(null)} style={{ background: "none", border: "none", cursor: "pointer", color: "#9ca3af" }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: 24 }}>
              {/* Subject */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 11, color: "#9ca3af", fontWeight: 500, display: "block", marginBottom: 6 }}>SUBJECT</label>
                {editMode ? (
                  <input
                    value={editSubject}
                    onChange={e => setEditSubject(e.target.value)}
                    style={{ width: "100%", padding: "8px 12px", border: "1px solid #7F77DD", borderRadius: 6, fontSize: 13, fontFamily: "inherit", outline: "none" }}
                  />
                ) : (
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a" }}>{editSubject}</p>
                )}
              </div>

              {/* Body */}
              <div>
                <label style={{ fontSize: 11, color: "#9ca3af", fontWeight: 500, display: "block", marginBottom: 6 }}>BODY</label>
                {editMode ? (
                  <textarea
                    value={editBody}
                    onChange={e => setEditBody(e.target.value)}
                    rows={14}
                    style={{ width: "100%", padding: "10px 12px", border: "1px solid #7F77DD", borderRadius: 6, fontSize: 13, fontFamily: "'DM Mono', monospace", resize: "vertical", outline: "none", lineHeight: 1.6 }}
                  />
                ) : (
                  <pre style={{ fontSize: 13, color: "#374151", lineHeight: 1.7, whiteSpace: "pre-wrap", fontFamily: "'DM Sans', system-ui" }}>{editBody}</pre>
                )}
              </div>
            </div>

            {/* Actions */}
            <div style={{ padding: "16px 24px", borderTop: "1px solid #e5e5e5", display: "flex", gap: 8 }}>
              {editMode ? (
                <>
                  <button onClick={saveEdit} style={{ flex: 1, padding: "9px", background: "#7F77DD", color: "#fff", border: "none", borderRadius: 7, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>
                    Save Changes
                  </button>
                  <button onClick={() => setEditMode(false)} style={{ padding: "9px 14px", background: "#f5f5f5", border: "1px solid #e5e5e5", borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "inherit" }}>
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button onClick={() => approveSend(selectedLead)} style={{ flex: 1, padding: "9px", background: "#7F77DD", color: "#fff", border: "none", borderRadius: 7, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                    <Send size={13} /> Approve & Send
                  </button>
                  <button onClick={() => setEditMode(true)} style={{ padding: "9px 14px", background: "#f5f5f5", border: "1px solid #e5e5e5", borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "inherit" }}>
                    Edit
                  </button>
                  <button onClick={() => setSelectedLead(null)} style={{ padding: "9px 14px", background: "#fff5f5", border: "1px solid #fecaca", borderRadius: 7, fontSize: 13, color: "#ef4444", cursor: "pointer", fontFamily: "inherit" }}>
                    Skip
                  </button>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
