"use client";

import { useState, useRef } from "react";
import {
  Users, Send, Eye, MessageSquare, TrendingUp, TrendingDown,
  Upload, Play, CheckCircle, Loader2, Circle, ExternalLink,
  ChevronDown, FileText, X, AlertCircle
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

// ── No hardcoded mock data ────────────────────────────────────────────────────

const PIPELINE_STEPS = [
  { id: "plan",      label: "Planning campaign strategy..." },
  { id: "discover",  label: "Discovering leads..." },
  { id: "research",  label: "Researching companies..." },
  { id: "contacts",  label: "Finding contacts & emails..." },
  { id: "emails",    label: "Generating personalized emails..." },
  { id: "done",      label: "Done!" },
];

const TARGET_ROLES = ["CEO", "CTO", "HR Manager", "Engineering Lead", "Founder", "VP Sales"];

type StepStatus   = "pending" | "active" | "done";
type EmailStatus  = "draft" | "approved" | "needs_review" | "skipped_no_email" | "sent" | "opened" | "replied";

interface Lead {
  company_name:   string;
  website?:       string;
  country?:       string;
  batch?:         string;
  ceo_email?:     string;
  cto_email?:     string;
  hr_email?:      string;
  ceo_name?:      string;
  ceo_linkedin?:  string;
  cto_linkedin?:  string;
  hr_linkedin?:   string;
  source?:        string;
  _email?:        EmailObj;
}

interface EmailObj {
  to_name?:              string;
  to_email:              string;
  subject:               string;
  body:                  string;
  personalization_score: number;
  status:                EmailStatus;
  lead_company:          string;
}

// Helper — get primary contact email from a lead
function primaryEmail(lead: Lead): string {
  return lead.ceo_email || lead.cto_email || lead.hr_email || "";
}

function primaryLinkedIn(lead: Lead): string {
  return lead.ceo_linkedin || lead.cto_linkedin || lead.hr_linkedin || "";
}

export default function DashboardPage() {
  const [query,       setQuery]       = useState("");
  const [targetRole,  setTargetRole]  = useState("CEO");
  const [leadsFile,   setLeadsFile]   = useState<File | null>(null);
  const [resumeFile,  setResumeFile]  = useState<File | null>(null);
  const [resumeParsed, setResumeParsed] = useState<{ name: string; role: string } | null>(null);
  const [running,     setRunning]     = useState(false);
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(PIPELINE_STEPS.map(() => "pending"));
  const [leads,       setLeads]       = useState<Lead[]>([]);
  const [emails,      setEmails]      = useState<EmailObj[]>([]);
  const [hasRun,      setHasRun]      = useState(false);
  const [error,       setError]       = useState<string | null>(null);
  const [selectedEmail, setSelectedEmail] = useState<EmailObj | null>(null);
  const [editMode,    setEditMode]    = useState(false);
  const [editSubject, setEditSubject] = useState("");
  const [editBody,    setEditBody]    = useState("");
  const [roleOpen,    setRoleOpen]    = useState(false);
  const [pipeline,    setPipeline]    = useState<any>(null);

  const leadsFileRef  = useRef<HTMLInputElement>(null);
  const resumeFileRef = useRef<HTMLInputElement>(null);

  // ── File handlers ───────────────────────────────────────────────────────────

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setResumeFile(f);

    // Try to parse resume via backend
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const form = new FormData();
      form.append("file", f);
      const res = await fetch(`${apiUrl}/resume/parse`, { method: "POST", body: form });
      if (res.ok) {
        const data = await res.json();
        if (data.name) {
          setResumeParsed({ name: data.name, role: data.current_role || "Professional" });
          return;
        }
      }
    } catch {}

    // Fallback: just show filename
    setResumeParsed({ name: f.name.replace(/\.[^.]+$/, ""), role: "Resume uploaded" });
  };

  const handleLeadsUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setLeadsFile(f);
  };

  // ── Run agent ───────────────────────────────────────────────────────────────

  const runAgent = async () => {
    if (!query && !leadsFile) return;

    // Clear everything first
    setLeads([]);
    setEmails([]);
    setHasRun(false);
    setError(null);
    setPipeline(null);
    setRunning(true);

    // Animate pipeline steps while waiting for API
    const statuses: StepStatus[] = PIPELINE_STEPS.map(() => "pending");
    setStepStatuses([...statuses]);

    // Start step animation (runs concurrently with API call)
    let stepIndex = 0;
    const stepInterval = setInterval(() => {
      if (stepIndex < PIPELINE_STEPS.length - 1) {
        statuses[stepIndex] = "done";
        stepIndex++;
        statuses[stepIndex] = "active";
        setStepStatuses([...statuses]);
      }
    }, 2500);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const formData = new FormData();

      if (query)     formData.append("query",       query.trim());
      if (leadsFile) formData.append("leads_file",  leadsFile);
      if (resumeFile) formData.append("resume_file", resumeFile);

      formData.append("target_role",       targetRole.toLowerCase().replace(" manager","").replace(" lead",""));
      formData.append("sender_name",       resumeParsed?.name || "Outreach User");
      formData.append("sender_value_prop", "AI-powered tools for modern engineering teams");

      const res = await fetch(`${apiUrl}/agents/run`, { method: "POST", body: formData });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `API error ${res.status}`);
      }

      const data = await res.json();

      // Mark all steps done
      clearInterval(stepInterval);
      const allDone: StepStatus[] = PIPELINE_STEPS.map(() => "done");
      setStepStatuses(allDone);

      setLeads(data.leads  || []);
      setEmails(data.emails || []);
      setPipeline(data.pipeline || null);
      setHasRun(true);

    } catch (err: any) {
      clearInterval(stepInterval);
      setError(err.message || "Something went wrong. Is the backend running?");
    } finally {
      setRunning(false);
    }
  };

  // ── Email panel ─────────────────────────────────────────────────────────────

  const openEmail = (lead: Lead) => {
    // Find matching email from emails array, or use lead._email
    const email = emails.find(e => e.lead_company?.toLowerCase() === lead.company_name?.toLowerCase())
                  || lead._email;
    if (!email) return;
    setSelectedEmail(email);
    setEditSubject(email.subject);
    setEditBody(email.body || "");
    setEditMode(false);
  };

  const saveEdit = () => {
    if (!selectedEmail) return;
    const updated = { ...selectedEmail, subject: editSubject, body: editBody };
    setEmails(prev => prev.map(e => e.lead_company === selectedEmail.lead_company ? updated : e));
    setSelectedEmail(updated);
    setEditMode(false);
  };

  const getEmailForLead = (lead: Lead): EmailObj | null => {
    return emails.find(e => e.lead_company?.toLowerCase() === lead.company_name?.toLowerCase())
           || lead._email
           || null;
  };

  const getEmailStatus = (lead: Lead): EmailStatus => {
    const email = getEmailForLead(lead);
    return email?.status || "draft";
  };

  const getScore = (lead: Lead): number => {
    const email = getEmailForLead(lead);
    return Math.round((email?.personalization_score || 0) * 100);
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Stats — start at 0 for new users ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 28 }}>
        {[
          { label: "Total Leads",  value: leads.length,
            sub: hasRun ? `from this run` : "Run a campaign to start",
            icon: Users, color: "#7F77DD" },
          { label: "Emails Ready", value: emails.filter(e => e.status === "approved" || e.body).length,
            sub: hasRun ? `of ${leads.length} leads` : "—",
            icon: Send, color: "#3b82f6" },
          { label: "Avg Score",
            value: emails.length ? Math.round(emails.reduce((s,e)=>s+(e.personalization_score||0),0)/emails.length*100)+"%" : "—",
            sub: "personalization quality",
            icon: Eye, color: "#22c55e" },
          { label: "Skipped",
            value: emails.filter(e=>e.status==="skipped_no_email").length || 0,
            sub: "no email found",
            icon: MessageSquare, color: "#f59e0b" },
        ].map((card, i) => (
          <div key={card.label} style={{
            background: "#fff", border: "1px solid #e5e5e5", borderRadius: 10, padding: "20px 20px 16px"
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ fontSize: 12, color: "#9ca3af", fontWeight: 500 }}>{card.label}</span>
              <div style={{ width: 30, height: 30, borderRadius: 7, background: `${card.color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <card.icon size={14} color={card.color} />
              </div>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: "#0a0a0a", letterSpacing: "-0.5px", marginBottom: 6 }}>
              {card.value}
            </div>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>{card.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Run campaign panel ── */}
      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: "24px", marginBottom: 24 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", marginBottom: 18, letterSpacing: "-0.3px" }}>Run AI Campaign</h2>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Query input */}
          <div>
            <label style={{ fontSize: 12, color: "#6b7280", fontWeight: 500, display: "block", marginBottom: 6 }}>Campaign Query</label>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder='e.g. "YC Europe startups after 2022" or "email Mistral AI, Alokai, Lago"'
              style={{
                width: "100%", padding: "10px 14px", border: "1px solid #e5e5e5", borderRadius: 8,
                fontSize: 14, outline: "none", background: "#fafafa", color: "#0a0a0a",
                fontFamily: "inherit", boxSizing: "border-box",
              }}
              onFocus={e => e.target.style.borderColor = "#7F77DD"}
              onBlur={e => e.target.style.borderColor = "#e5e5e5"}
              onKeyDown={e => e.key === "Enter" && !running && runAgent()}
            />
          </div>

          {/* Row: role + uploads */}
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
                  {targetRole} <ChevronDown size={14} color="#9ca3af" />
                </button>
                {roleOpen && (
                  <div style={{
                    position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
                    background: "#fff", border: "1px solid #e5e5e5", borderRadius: 8,
                    boxShadow: "0 8px 24px rgba(0,0,0,0.08)", zIndex: 100, overflow: "hidden"
                  }}>
                    {TARGET_ROLES.map(r => (
                      <button key={r} onClick={() => { setTargetRole(r); setRoleOpen(false); }}
                        style={{
                          width: "100%", padding: "8px 14px", border: "none",
                          background: r === targetRole ? "#f5f5ff" : "#fff",
                          color: r === targetRole ? "#7F77DD" : "#0a0a0a",
                          fontSize: 13, textAlign: "left", cursor: "pointer",
                          fontFamily: "inherit", fontWeight: r === targetRole ? 600 : 400
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
              <button onClick={() => leadsFileRef.current?.click()}
                style={{
                  width: "100%", padding: "9px 14px",
                  border: `1px dashed ${leadsFile ? "#7F77DD" : "#d1d5db"}`,
                  borderRadius: 8, fontSize: 13,
                  background: leadsFile ? "#f5f5ff" : "#fafafa",
                  color: leadsFile ? "#7F77DD" : "#9ca3af",
                  cursor: "pointer", display: "flex", alignItems: "center",
                  justifyContent: "center", gap: 6, fontFamily: "inherit"
                }}
              >
                <Upload size={13} />
                {leadsFile ? leadsFile.name.slice(0, 18) + "…" : "CSV / Excel / JSON"}
              </button>
            </div>

            {/* Resume file */}
            <div>
              <label style={{ fontSize: 12, color: "#6b7280", fontWeight: 500, display: "block", marginBottom: 6 }}>Upload Resume</label>
              <input ref={resumeFileRef} type="file" accept=".pdf,.txt" style={{ display: "none" }} onChange={handleResumeUpload} />
              <button onClick={() => resumeFileRef.current?.click()}
                style={{
                  width: "100%", padding: "9px 14px",
                  border: `1px dashed ${resumeFile ? "#7F77DD" : "#d1d5db"}`,
                  borderRadius: 8, fontSize: 13,
                  background: resumeFile ? "#f5f5ff" : "#fafafa",
                  color: resumeFile ? "#7F77DD" : "#9ca3af",
                  cursor: "pointer", display: "flex", alignItems: "center",
                  justifyContent: "center", gap: 6, fontFamily: "inherit"
                }}
              >
                <FileText size={13} />
                {resumeFile ? resumeFile.name.slice(0, 18) + "…" : "PDF / TXT"}
              </button>
            </div>
          </div>

          {/* Resume parsed preview */}
          {resumeParsed && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "#f0fdf4", borderRadius: 7, border: "1px solid #bbf7d0" }}>
              <CheckCircle size={13} color="#22c55e" />
              <span style={{ fontSize: 12, color: "#15803d" }}>
                Parsed: <strong>{resumeParsed.name}</strong> · {resumeParsed.role}
              </span>
            </div>
          )}

          {/* No resume warning */}
          {!resumeFile && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "#fffbeb", borderRadius: 7, border: "1px solid #fde68a" }}>
              <AlertCircle size={13} color="#d97706" />
              <span style={{ fontSize: 12, color: "#92400e" }}>
                Upload your resume for highly personalized emails. Without it, emails will be generic.
              </span>
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "#fef2f2", borderRadius: 7, border: "1px solid #fecaca" }}>
              <AlertCircle size={13} color="#ef4444" />
              <span style={{ fontSize: 12, color: "#991b1b" }}>{error}</span>
            </div>
          )}

          {/* Run button */}
          <button
            onClick={runAgent}
            disabled={running || (!query.trim() && !leadsFile)}
            style={{
              background: running || (!query.trim() && !leadsFile) ? "#c4c1ff" : "#7F77DD",
              color: "#fff", border: "none", borderRadius: 8, padding: "11px 20px",
              fontSize: 14, fontWeight: 600,
              cursor: running || (!query.trim() && !leadsFile) ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              alignSelf: "flex-start", minWidth: 180,
            }}
          >
            {running ? <Loader2 size={15} className="animate-spin-custom" /> : <Play size={15} />}
            {running ? "Running AI Agent..." : "Run AI Agent →"}
          </button>
        </div>

        {/* Pipeline progress — only show while running */}
        {running && (
          <div style={{ marginTop: 20, padding: "16px", background: "#0a0a0a", borderRadius: 10 }}>
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

        {/* Pipeline summary after run */}
        {pipeline && !running && (
          <div style={{ marginTop: 16, display: "flex", gap: 16, fontSize: 12, color: "#6b7280" }}>
            <span>✓ <strong>{pipeline.discovered}</strong> discovered</span>
            <span>✓ <strong>{pipeline.enriched}</strong> enriched</span>
            <span>✓ <strong>{pipeline.emails_approved}</strong> emails approved</span>
          </div>
        )}
      </div>

      {/* ── Leads results table ── */}
      {hasRun && leads.length === 0 && !running && (
        <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: 40, textAlign: "center", color: "#9ca3af" }}>
          <p style={{ fontSize: 14 }}>No leads found for this query.</p>
          <p style={{ fontSize: 12, marginTop: 6 }}>Try a different region, industry, or company names directly (e.g. "email Mistral AI, Alokai")</p>
        </div>
      )}

      {leads.length > 0 && (
        <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #e5e5e5", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a" }}>
              Results — {leads.length} leads found
            </h2>
            <span style={{ fontSize: 12, color: "#9ca3af" }}>
              {emails.filter(e => e.body && e.status !== "skipped_no_email").length} emails ready
            </span>
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
                {leads.map((lead, i) => {
                  const email  = getEmailForLead(lead);
                  const status = getEmailStatus(lead);
                  const score  = getScore(lead);
                  const email_addr = primaryEmail(lead);
                  const linkedin   = primaryLinkedIn(lead);

                  return (
                    <tr
                      key={lead.company_name + i}
                      style={{ borderBottom: "1px solid #f0f0f0" }}
                      onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                      onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                    >
                      <td style={{ padding: "12px 14px", fontWeight: 600, color: "#0a0a0a" }}>{lead.company_name}</td>
                      <td style={{ padding: "12px 14px", color: "#6b7280" }}>
                        {lead.website ? lead.website.replace("https://","").replace("http://","") : "—"}
                      </td>
                      <td style={{ padding: "12px 14px", color: "#6b7280" }}>{lead.country || "—"}</td>
                      <td style={{ padding: "12px 14px", color: "#6b7280" }}>{lead.batch || "—"}</td>
                      <td style={{ padding: "12px 14px", color: "#7F77DD", fontSize: 12 }}>
                        {email_addr || <span style={{ color: "#d1d5db" }}>not found</span>}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        {linkedin ? (
                          <a href={linkedin.startsWith("http") ? linkedin : `https://${linkedin}`}
                            target="_blank" rel="noreferrer"
                            style={{ color: "#0077b5", display: "inline-flex", alignItems: "center" }}>
                            <ExternalLink size={13} />
                          </a>
                        ) : <span style={{ color: "#d1d5db" }}>—</span>}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        <span style={{
                          padding: "3px 8px", borderRadius: 99, fontSize: 11, fontWeight: 500,
                          background: status === "replied" ? "#f0fdf4" : status === "opened" ? "#fffbeb" : status === "sent" ? "#eff6ff" : status === "approved" ? "#f5f5ff" : "#f9fafb",
                          color: status === "replied" ? "#15803d" : status === "opened" ? "#d97706" : status === "sent" ? "#2563eb" : status === "approved" ? "#7F77DD" : "#6b7280",
                        }}>
                          {status === "skipped_no_email" ? "no email" : status}
                        </span>
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        {score > 0 ? (
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{ width: 36, height: 4, borderRadius: 99, background: "#e5e5e5", overflow: "hidden" }}>
                              <div style={{ height: "100%", width: `${score}%`, borderRadius: 99,
                                background: score > 70 ? "#22c55e" : score > 50 ? "#f59e0b" : "#ef4444" }} />
                            </div>
                            <span style={{ fontWeight: 600, color: "#0a0a0a", fontSize: 12 }}>{score}</span>
                          </div>
                        ) : <span style={{ color: "#d1d5db" }}>—</span>}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        {email ? (
                          <button onClick={() => openEmail(lead)}
                            style={{ padding: "5px 10px", background: "#f5f5ff", border: "1px solid #e0ddff", borderRadius: 6, fontSize: 12, color: "#7F77DD", cursor: "pointer", fontWeight: 500, fontFamily: "inherit" }}>
                            View Email
                          </button>
                        ) : (
                          <span style={{ fontSize: 12, color: "#d1d5db" }}>no email</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Email slide-over ── */}
      {selectedEmail && (
        <>
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", zIndex: 100 }} onClick={() => setSelectedEmail(null)} />
          <div style={{
            position: "fixed", top: 0, right: 0, bottom: 0, width: 480,
            background: "#fff", zIndex: 110, display: "flex", flexDirection: "column",
            boxShadow: "-8px 0 40px rgba(0,0,0,0.1)"
          }}>
            <div style={{ padding: "20px 24px", borderBottom: "1px solid #e5e5e5", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>Email for</p>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: "#0a0a0a" }}>{selectedEmail.lead_company}</h3>
                <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>To: {selectedEmail.to_email}</p>
              </div>
              <button onClick={() => setSelectedEmail(null)} style={{ background: "none", border: "none", cursor: "pointer", color: "#9ca3af" }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 11, color: "#9ca3af", fontWeight: 500, display: "block", marginBottom: 6 }}>SUBJECT</label>
                {editMode ? (
                  <input value={editSubject} onChange={e => setEditSubject(e.target.value)}
                    style={{ width: "100%", padding: "8px 12px", border: "1px solid #7F77DD", borderRadius: 6, fontSize: 13, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }} />
                ) : (
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a" }}>{editSubject}</p>
                )}
              </div>

              <div>
                <label style={{ fontSize: 11, color: "#9ca3af", fontWeight: 500, display: "block", marginBottom: 6 }}>BODY</label>
                {editMode ? (
                  <textarea value={editBody} onChange={e => setEditBody(e.target.value)} rows={14}
                    style={{ width: "100%", padding: "10px 12px", border: "1px solid #7F77DD", borderRadius: 6, fontSize: 13, fontFamily: "inherit", resize: "vertical", outline: "none", lineHeight: 1.6, boxSizing: "border-box" }} />
                ) : (
                  <pre style={{ fontSize: 13, color: "#374151", lineHeight: 1.7, whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                    {editBody}
                  </pre>
                )}
              </div>
            </div>

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
                  <button
                    onClick={() => {
                      setEmails(prev => prev.map(e => e.lead_company === selectedEmail.lead_company ? { ...e, status: "sent" } : e));
                      setSelectedEmail(null);
                    }}
                    style={{ flex: 1, padding: "9px", background: "#7F77DD", color: "#fff", border: "none", borderRadius: 7, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                    <Send size={13} /> Approve & Send
                  </button>
                  <button onClick={() => setEditMode(true)} style={{ padding: "9px 14px", background: "#f5f5f5", border: "1px solid #e5e5e5", borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "inherit" }}>
                    Edit
                  </button>
                  <button onClick={() => setSelectedEmail(null)} style={{ padding: "9px 14px", background: "#fff5f5", border: "1px solid #fecaca", borderRadius: 7, fontSize: 13, color: "#ef4444", cursor: "pointer", fontFamily: "inherit" }}>
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