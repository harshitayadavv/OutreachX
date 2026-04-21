"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";

const FUNNEL_DATA = [
  { stage: "Sent", count: 847, color: "#7F77DD" },
  { stage: "Opened", count: 290, color: "#a5a0ff" },
  { stage: "Clicked", count: 124, color: "#c4c1ff" },
  { stage: "Replied", count: 74, color: "#22c55e" },
];

const CAMPAIGNS_DATA = [
  { name: "YC India Fintech", sent: 32, opened: 12, replied: 3, open_rate: "38.2%", reply_rate: "9.4%" },
  { name: "SaaS CEOs S-A", sent: 28, opened: 12, replied: 4, open_rate: "42.8%", reply_rate: "14.2%" },
  { name: "Deep Tech CTOs", sent: 45, opened: 13, replied: 3, open_rate: "29.1%", reply_rate: "6.7%" },
  { name: "Climate Founders", sent: 18, opened: 8, replied: 2, open_rate: "44.4%", reply_rate: "11.1%" },
  { name: "Healthtech DMs", sent: 35, opened: 11, replied: 3, open_rate: "31.4%", reply_rate: "8.6%" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 8, padding: "10px 14px", boxShadow: "0 4px 16px rgba(0,0,0,0.06)" }}>
        <p style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, color: "#0a0a0a" }}>{label}</p>
        <p style={{ fontSize: 13, color: "#7F77DD" }}>{payload[0].value} emails</p>
      </div>
    );
  }
  return null;
};

export default function AnalyticsPage() {
  const convRate = (n: number) => ((n / 847) * 100).toFixed(1) + "%";

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      
      {/* Funnel chart */}
      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, padding: "24px", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Email Funnel</h2>
            <p style={{ fontSize: 12, color: "#9ca3af", marginTop: 2 }}>Overall pipeline conversion</p>
          </div>
          <span style={{ fontSize: 12, color: "#9ca3af", background: "#f5f5f5", padding: "4px 10px", borderRadius: 99 }}>All time</span>
        </div>

        {/* Funnel bars */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {FUNNEL_DATA.map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ width: 64, fontSize: 12, color: "#6b7280", fontWeight: 500, textAlign: "right", flexShrink: 0 }}>{item.stage}</span>
              <div style={{ flex: 1, height: 28, background: "#f5f5f5", borderRadius: 6, overflow: "hidden" }}>
                <div style={{
                  height: "100%", width: `${(item.count / 847) * 100}%`,
                  background: item.color, borderRadius: 6,
                  display: "flex", alignItems: "center", paddingLeft: 10,
                  transition: "width 1s ease"
                }}>
                  <span style={{ fontSize: 11, color: i < 2 ? "#fff" : "#fff", fontWeight: 600 }}>{item.count}</span>
                </div>
              </div>
              <span style={{ width: 52, fontSize: 12, color: "#9ca3af", textAlign: "right", flexShrink: 0 }}>{convRate(item.count)}</span>
            </div>
          ))}
        </div>

        {/* Bar chart */}
        <div style={{ marginTop: 32, height: 180 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={FUNNEL_DATA} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
              <XAxis dataKey="stage" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#9ca3af" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#9ca3af" }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {FUNNEL_DATA.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Campaigns comparison */}
      <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #e5e5e5" }}>
          <h2 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Campaign Comparison</h2>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#fafafa" }}>
              {["Campaign", "Sent", "Opened", "Replied", "Open Rate", "Reply Rate"].map(h => (
                <th key={h} style={{ padding: "10px 16px", textAlign: "left", fontWeight: 500, color: "#9ca3af", fontSize: 11, borderBottom: "1px solid #f0f0f0" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CAMPAIGNS_DATA.map((c, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #f5f5f5" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <td style={{ padding: "12px 16px", fontWeight: 600, color: "#0a0a0a" }}>{c.name}</td>
                <td style={{ padding: "12px 16px", color: "#374151" }}>{c.sent}</td>
                <td style={{ padding: "12px 16px", color: "#374151" }}>{c.opened}</td>
                <td style={{ padding: "12px 16px", color: "#374151" }}>{c.replied}</td>
                <td style={{ padding: "12px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ flex: 1, height: 4, background: "#f0f0f0", borderRadius: 99, maxWidth: 60 }}>
                      <div style={{ height: "100%", width: c.open_rate, background: "#7F77DD", borderRadius: 99 }} />
                    </div>
                    <span style={{ color: "#374151", fontWeight: 500 }}>{c.open_rate}</span>
                  </div>
                </td>
                <td style={{ padding: "12px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ flex: 1, height: 4, background: "#f0f0f0", borderRadius: 99, maxWidth: 60 }}>
                      <div style={{ height: "100%", width: c.reply_rate, background: "#22c55e", borderRadius: 99 }} />
                    </div>
                    <span style={{ color: "#374151", fontWeight: 500 }}>{c.reply_rate}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
