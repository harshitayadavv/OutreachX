"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, Send, Eye, MessageSquare, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const MOCK_DETAIL = {
  id: "1",
  name: "YC India Fintech Outreach",
  query: "YC India fintech startups 2021",
  status: "active",
  created: "Apr 18, 2025",
  leads: 47,
  sent: 32,
  opened: 12,
  replied: 3,
  open_rate: "37.5%",
  reply_rate: "9.4%",
};

export default function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const c = { ...MOCK_DETAIL, id };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <Link href="/dashboard/campaigns" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13, color: "#9ca3af", textDecoration: "none", marginBottom: 20 }}>
        <ArrowLeft size={13} /> Back to Campaigns
      </Link>

      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: "24px", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "#0a0a0a", letterSpacing: "-0.4px", marginBottom: 4 }}>{c.name}</h2>
            <p style={{ fontSize: 13, color: "#9ca3af", fontFamily: "'DM Mono', monospace" }}>"{c.query}"</p>
          </div>
          <Badge variant={c.status as any} style={{ textTransform: "capitalize" }}>{c.status}</Badge>
        </div>
        <p style={{ fontSize: 12, color: "#9ca3af" }}>Created {c.created}</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
        {[
          { label: "Total Leads", value: c.leads, icon: Users, color: "#7F77DD" },
          { label: "Sent", value: c.sent, icon: Send, color: "#3b82f6" },
          { label: "Opened", value: c.opened, icon: Eye, color: "#f59e0b" },
          { label: "Replied", value: c.replied, icon: MessageSquare, color: "#22c55e" },
        ].map((s, i) => (
          <div key={i} style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 10, padding: "18px 16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 10 }}>
              <s.icon size={13} color={s.color} />
              <span style={{ fontSize: 11, color: "#9ca3af", fontWeight: 500 }}>{s.label}</span>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: "#0a0a0a", letterSpacing: "-0.5px" }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: "20px 24px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Conversion Funnel</h3>
        {[
          { label: "Leads discovered", value: c.leads, pct: 100 },
          { label: "Emails sent", value: c.sent, pct: Math.round((c.sent / c.leads) * 100) },
          { label: "Opened", value: c.opened, pct: Math.round((c.opened / c.leads) * 100) },
          { label: "Replied", value: c.replied, pct: Math.round((c.replied / c.leads) * 100) },
        ].map((row, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
            <span style={{ width: 130, fontSize: 12, color: "#6b7280", fontWeight: 500 }}>{row.label}</span>
            <div style={{ flex: 1, height: 8, background: "#f5f5f5", borderRadius: 99, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${row.pct}%`, background: i === 0 ? "#7F77DD" : i === 1 ? "#3b82f6" : i === 2 ? "#f59e0b" : "#22c55e", borderRadius: 99 }} />
            </div>
            <span style={{ width: 36, fontSize: 12, fontWeight: 600, color: "#374151", textAlign: "right" }}>{row.value}</span>
            <span style={{ width: 36, fontSize: 11, color: "#9ca3af", textAlign: "right" }}>{row.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
