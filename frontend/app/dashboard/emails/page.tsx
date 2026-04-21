"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Send, Eye, MessageSquare, Clock } from "lucide-react";

const MOCK_EMAILS = [
  { id: "1", to: "harshil@razorpay.com", company: "Razorpay", subject: "Quick question about your fintech infrastructure", status: "replied", opened_at: "Apr 19, 10:24am", sent_at: "Apr 18, 9:00am" },
  { id: "2", to: "lalit@groww.in", company: "Groww", subject: "Automating investor onboarding at Groww", status: "opened", opened_at: "Apr 19, 2:15pm", sent_at: "Apr 18, 9:02am" },
  { id: "3", to: "vivek@sarvam.ai", company: "Sarvam AI", subject: "Collaboration on multilingual AI agents", status: "sent", opened_at: "—", sent_at: "Apr 18, 9:04am" },
  { id: "4", to: "aadit@zepto.com", company: "Zepto", subject: "Supply chain AI for quick commerce", status: "approved", opened_at: "—", sent_at: "—" },
  { id: "5", to: "kunal@cred.club", company: "CRED", subject: "AI-powered member engagement at CRED", status: "draft", opened_at: "—", sent_at: "—" },
];

export default function EmailsPage() {
  const [emails] = useState(MOCK_EMAILS);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 24 }}>
        {[
          { label: "Drafts", value: emails.filter(e => e.status === "draft").length, icon: Clock, color: "#9ca3af" },
          { label: "Sent", value: emails.filter(e => ["sent","opened","replied"].includes(e.status)).length, icon: Send, color: "#3b82f6" },
          { label: "Opened", value: emails.filter(e => ["opened","replied"].includes(e.status)).length, icon: Eye, color: "#f59e0b" },
          { label: "Replied", value: emails.filter(e => e.status === "replied").length, icon: MessageSquare, color: "#22c55e" },
        ].map((s, i) => (
          <div key={i} style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 10, padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <s.icon size={14} color={s.color} />
              <span style={{ fontSize: 12, color: "#9ca3af" }}>{s.label}</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#0a0a0a" }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#fafafa" }}>
              {["To", "Company", "Subject", "Status", "Sent At", "Opened At"].map(h => (
                <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontWeight: 500, color: "#9ca3af", fontSize: 11, borderBottom: "1px solid #f0f0f0" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {emails.map(e => (
              <tr key={e.id} style={{ borderBottom: "1px solid #f5f5f5" }}
                onMouseEnter={ev => (ev.currentTarget.style.background = "#fafafa")}
                onMouseLeave={ev => (ev.currentTarget.style.background = "transparent")}
              >
                <td style={{ padding: "12px 14px", color: "#7F77DD", fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{e.to}</td>
                <td style={{ padding: "12px 14px", fontWeight: 600, color: "#0a0a0a" }}>{e.company}</td>
                <td style={{ padding: "12px 14px", color: "#374151", maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.subject}</td>
                <td style={{ padding: "12px 14px" }}><Badge variant={e.status as any} style={{ textTransform: "capitalize" }}>{e.status}</Badge></td>
                <td style={{ padding: "12px 14px", color: "#9ca3af" }}>{e.sent_at}</td>
                <td style={{ padding: "12px 14px", color: "#9ca3af" }}>{e.opened_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
