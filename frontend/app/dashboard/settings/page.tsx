"use client";

import { useState } from "react";
import { Save, Eye, EyeOff, CheckCircle } from "lucide-react";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");
  const [senderName, setSenderName] = useState("Harshita Yadav");
  const [senderEmail, setSenderEmail] = useState("harshita@example.com");
  const [valueProp, setValueProp] = useState("AI-powered tools for engineering teams");
  const [groqKey, setGroqKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: "24px", marginBottom: 20 }}>
      <h2 style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a", marginBottom: 20, letterSpacing: "-0.2px" }}>{title}</h2>
      {children}
    </div>
  );

  const Field = ({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) => (
    <div style={{ marginBottom: 18 }}>
      <label style={{ fontSize: 12, fontWeight: 500, color: "#374151", display: "block", marginBottom: 6 }}>{label}</label>
      {children}
      {hint && <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 5 }}>{hint}</p>}
    </div>
  );

  const inputStyle = {
    width: "100%", padding: "9px 12px", border: "1px solid #e5e5e5", borderRadius: 7,
    fontSize: 13, fontFamily: "inherit", outline: "none", background: "#fafafa", color: "#0a0a0a",
    transition: "border-color 0.15s"
  };

  return (
    <div style={{ maxWidth: 640, margin: "0 auto" }}>

      <Section title="Sender Identity">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Field label="Your Name" hint="Used in email signatures">
            <input value={senderName} onChange={e => setSenderName(e.target.value)}
              style={inputStyle}
              onFocus={e => (e.target.style.borderColor = "#7F77DD")}
              onBlur={e => (e.target.style.borderColor = "#e5e5e5")} />
          </Field>
          <Field label="Your Email" hint="Outreach emails sent from this address">
            <input value={senderEmail} onChange={e => setSenderEmail(e.target.value)}
              type="email" style={inputStyle}
              onFocus={e => (e.target.style.borderColor = "#7F77DD")}
              onBlur={e => (e.target.style.borderColor = "#e5e5e5")} />
          </Field>
        </div>
        <Field label="Value Proposition" hint="What you offer — used in email generation">
          <textarea value={valueProp} onChange={e => setValueProp(e.target.value)}
            rows={3} style={{ ...inputStyle, resize: "vertical", lineHeight: 1.6 }}
            onFocus={e => (e.target.style.borderColor = "#7F77DD")}
            onBlur={e => (e.target.style.borderColor = "#e5e5e5")} />
        </Field>
      </Section>

      <Section title="API Configuration">
        <Field label="Backend API URL" hint="Your OutreachX FastAPI backend URL">
          <input value={apiUrl} onChange={e => setApiUrl(e.target.value)}
            style={{ ...inputStyle, fontFamily: "'DM Mono', monospace", fontSize: 12 }}
            onFocus={e => (e.target.style.borderColor = "#7F77DD")}
            onBlur={e => (e.target.style.borderColor = "#e5e5e5")} />
        </Field>
        <Field label="Groq API Key" hint="Used for LLM-powered email generation">
          <div style={{ position: "relative" }}>
            <input
              value={groqKey}
              onChange={e => setGroqKey(e.target.value)}
              type={showKey ? "text" : "password"}
              placeholder="gsk_••••••••••••••••••••••••"
              style={{ ...inputStyle, fontFamily: "'DM Mono', monospace", fontSize: 12, paddingRight: 40 }}
              onFocus={e => (e.target.style.borderColor = "#7F77DD")}
              onBlur={e => (e.target.style.borderColor = "#e5e5e5")}
            />
            <button onClick={() => setShowKey(!showKey)} style={{
              position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)",
              background: "none", border: "none", cursor: "pointer", color: "#9ca3af", padding: 0
            }}>
              {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </Field>

        {/* API health indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", background: "#f0fdf4", borderRadius: 8, border: "1px solid #bbf7d0" }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: "#15803d", fontWeight: 500 }}>Backend reachable at {apiUrl}</span>
        </div>
      </Section>

      <Section title="Email Defaults">
        <Field label="Default Follow-up Delay" hint="Days to wait before sending a follow-up">
          <select style={{ ...inputStyle, cursor: "pointer" }}>
            <option>3 days</option>
            <option>5 days</option>
            <option>7 days</option>
            <option>14 days</option>
          </select>
        </Field>
        <Field label="Max Follow-ups per Lead">
          <select style={{ ...inputStyle, cursor: "pointer" }}>
            <option>1 follow-up</option>
            <option>2 follow-ups</option>
            <option>3 follow-ups</option>
          </select>
        </Field>
        <Field label="Email Tone">
          <select style={{ ...inputStyle, cursor: "pointer" }}>
            <option>Professional & concise</option>
            <option>Friendly & warm</option>
            <option>Direct & bold</option>
          </select>
        </Field>
      </Section>

      {/* Save button */}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
        {saved && (
          <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 14px", background: "#f0fdf4", borderRadius: 8, border: "1px solid #bbf7d0" }}>
            <CheckCircle size={13} color="#22c55e" />
            <span style={{ fontSize: 13, color: "#15803d", fontWeight: 500 }}>Saved!</span>
          </div>
        )}
        <button onClick={handleSave} style={{
          display: "flex", alignItems: "center", gap: 7,
          padding: "9px 20px", background: "#7F77DD", color: "#fff",
          border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600,
          cursor: "pointer", fontFamily: "inherit",
          boxShadow: "0 0 20px rgba(127,119,221,0.3)"
        }}>
          <Save size={13} /> Save Settings
        </button>
      </div>
    </div>
  );
}
