"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Search, ExternalLink } from "lucide-react";

const MOCK_LEADS = [
  { id: "1", company: "Razorpay", website: "razorpay.com", country: "India", contact: "harshil@razorpay.com", role: "CEO", status: "replied", score: 92 },
  { id: "2", company: "Groww", website: "groww.in", country: "India", contact: "lalit@groww.in", role: "CEO", status: "opened", score: 87 },
  { id: "3", company: "Sarvam AI", website: "sarvam.ai", country: "India", contact: "vivek@sarvam.ai", role: "CTO", status: "sent", score: 95 },
  { id: "4", company: "Zepto", website: "zeptonow.com", country: "India", contact: "aadit@zepto.com", role: "CEO", status: "approved", score: 78 },
  { id: "5", company: "CRED", website: "cred.club", country: "India", contact: "kunal@cred.club", role: "CEO", status: "draft", score: 83 },
  { id: "6", company: "PhonePe", website: "phonepe.com", country: "India", contact: "sameer@phonepe.com", role: "CTO", status: "sent", score: 74 },
  { id: "7", company: "Meesho", website: "meesho.com", country: "India", contact: "vidit@meesho.com", role: "CEO", status: "opened", score: 81 },
];

export default function LeadsPage() {
  const [search, setSearch] = useState("");
  const filtered = MOCK_LEADS.filter(l => l.company.toLowerCase().includes(search.toLowerCase()) || l.contact.toLowerCase().includes(search.toLowerCase()));

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ marginBottom: 20, position: "relative" }}>
        <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "#9ca3af" }} />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search leads..."
          style={{ width: "100%", maxWidth: 320, paddingLeft: 34, paddingRight: 12, paddingTop: 9, paddingBottom: 9, border: "1px solid #e5e5e5", borderRadius: 8, fontSize: 13, outline: "none", fontFamily: "inherit" }}
        />
      </div>
      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#fafafa" }}>
              {["Company", "Website", "Country", "Contact Email", "Role", "Status", "Score", ""].map(h => (
                <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontWeight: 500, color: "#9ca3af", fontSize: 11, borderBottom: "1px solid #f0f0f0" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(l => (
              <tr key={l.id} style={{ borderBottom: "1px solid #f5f5f5" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <td style={{ padding: "12px 14px", fontWeight: 600, color: "#0a0a0a" }}>{l.company}</td>
                <td style={{ padding: "12px 14px", color: "#6b7280" }}>{l.website}</td>
                <td style={{ padding: "12px 14px", color: "#6b7280" }}>{l.country}</td>
                <td style={{ padding: "12px 14px", color: "#7F77DD", fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{l.contact}</td>
                <td style={{ padding: "12px 14px", color: "#6b7280" }}>{l.role}</td>
                <td style={{ padding: "12px 14px" }}><Badge variant={l.status as any} style={{ textTransform: "capitalize" }}>{l.status}</Badge></td>
                <td style={{ padding: "12px 14px", fontWeight: 600, color: l.score > 85 ? "#22c55e" : "#f59e0b" }}>{l.score}</td>
                <td style={{ padding: "12px 14px" }}><a href="#" style={{ color: "#9ca3af" }}><ExternalLink size={13} /></a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
