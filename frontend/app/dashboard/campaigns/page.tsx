"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Plus } from "lucide-react";

const MOCK_CAMPAIGNS = [
  { id: "1", name: "YC India Fintech Outreach", query: "YC India fintech startups 2021", status: "active", leads: 47, sent: 32, open_rate: "38.2%", reply_rate: "9.4%", created: "Apr 18, 2025" },
  { id: "2", name: "SaaS CEOs — Series A", query: "Indian SaaS Series A startups 2023", status: "completed", leads: 28, sent: 28, open_rate: "42.8%", reply_rate: "14.2%", created: "Apr 14, 2025" },
  { id: "3", name: "Deep Tech CTO Blitz", query: "deep tech AI startups bangalore", status: "paused", leads: 61, sent: 45, open_rate: "29.1%", reply_rate: "6.7%", created: "Apr 10, 2025" },
  { id: "4", name: "Climate Founders", query: "climate tech startups India 2024", status: "active", leads: 22, sent: 18, open_rate: "44.4%", reply_rate: "11.1%", created: "Apr 7, 2025" },
  { id: "5", name: "Healthtech Decision Makers", query: "healthtech startups YC 2022 India", status: "completed", leads: 35, sent: 35, open_rate: "31.4%", reply_rate: "8.6%", created: "Apr 2, 2025" },
];

export default function CampaignsPage() {
  const [campaigns] = useState(MOCK_CAMPAIGNS);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <p style={{ fontSize: 13, color: "#9ca3af" }}>{campaigns.length} campaigns</p>
        <button style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", background: "#7F77DD", color: "#fff", border: "none", borderRadius: 7, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>
          <Plus size={13} /> New Campaign
        </button>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#fafafa" }}>
              {["Name", "Query", "Status", "Leads", "Sent", "Open Rate", "Reply Rate", "Created", ""].map(h => (
                <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontWeight: 500, color: "#9ca3af", fontSize: 11, borderBottom: "1px solid #f0f0f0", whiteSpace: "nowrap" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {campaigns.map(c => (
              <tr key={c.id} style={{ borderBottom: "1px solid #f5f5f5", cursor: "pointer", transition: "background 0.1s" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <td style={{ padding: "13px 14px", fontWeight: 600, color: "#0a0a0a" }}>{c.name}</td>
                <td style={{ padding: "13px 14px", color: "#6b7280", maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.query}</td>
                <td style={{ padding: "13px 14px" }}>
                  <Badge variant={c.status as any} style={{ textTransform: "capitalize" }}>{c.status}</Badge>
                </td>
                <td style={{ padding: "13px 14px", color: "#374151", fontWeight: 500 }}>{c.leads}</td>
                <td style={{ padding: "13px 14px", color: "#374151" }}>{c.sent}</td>
                <td style={{ padding: "13px 14px", color: "#374151" }}>{c.open_rate}</td>
                <td style={{ padding: "13px 14px", color: "#374151" }}>{c.reply_rate}</td>
                <td style={{ padding: "13px 14px", color: "#9ca3af" }}>{c.created}</td>
                <td style={{ padding: "13px 14px" }}>
                  <ExternalLink size={13} color="#9ca3af" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
