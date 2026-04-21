"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Megaphone, Users, Mail, BarChart3, Settings, Plus, Menu, X
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Campaigns", href: "/dashboard/campaigns", icon: Megaphone },
  { label: "Leads", href: "/dashboard/leads", icon: Users },
  { label: "Emails", href: "/dashboard/emails", icon: Mail },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const currentPage = NAV_ITEMS.find(n => n.href === pathname)?.label || "Dashboard";

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: "#f8f8f8" }}>
      
      {/* Sidebar - desktop */}
      <aside style={{
        width: 240, background: "#111111", display: "flex", flexDirection: "column",
        borderRight: "1px solid rgba(255,255,255,0.06)", flexShrink: 0,
        position: "relative", zIndex: 20
      }} className="hidden-mobile">
        
        {/* Logo */}
        <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
            <div style={{ width: 32, height: 32, background: "#7F77DD", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13, color: "#fff", letterSpacing: "-0.5px" }}>OX</div>
            <span style={{ fontWeight: 600, fontSize: 15, color: "#fff", letterSpacing: "-0.3px" }}>OutreachX</span>
          </Link>
        </div>

        {/* Nav */}
        <nav style={{ padding: "12px 10px", flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => (
            <Link key={href} href={href} className={`nav-link ${pathname === href ? "active" : ""}`}>
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>

        {/* Bottom */}
        <div style={{ padding: "12px 10px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ padding: "10px 12px", background: "rgba(127,119,221,0.1)", borderRadius: 8, border: "1px solid rgba(127,119,221,0.2)" }}>
            <p style={{ fontSize: 11, color: "#7F77DD", fontWeight: 600, marginBottom: 2 }}>API Status</p>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e" }} />
              <span style={{ fontSize: 12, color: "#9ca3af" }}>Connected</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 40 }} onClick={() => setMobileOpen(false)} />
      )}
      {/* Mobile sidebar */}
      <aside style={{
        position: "fixed", top: 0, left: mobileOpen ? 0 : -260, width: 240, height: "100vh",
        background: "#111111", zIndex: 50, transition: "left 0.3s ease",
        display: "flex", flexDirection: "column"
      }}>
        <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, background: "#7F77DD", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13, color: "#fff" }}>OX</div>
            <span style={{ fontWeight: 600, fontSize: 15, color: "#fff" }}>OutreachX</span>
          </div>
          <button onClick={() => setMobileOpen(false)} style={{ background: "none", border: "none", color: "#9ca3af", cursor: "pointer" }}>
            <X size={18} />
          </button>
        </div>
        <nav style={{ padding: "12px 10px", flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => (
            <Link key={href} href={href} className={`nav-link ${pathname === href ? "active" : ""}`} onClick={() => setMobileOpen(false)}>
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        
        {/* Top bar */}
        <header style={{
          height: 56, background: "#fff", borderBottom: "1px solid #e5e5e5",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "0 24px", flexShrink: 0
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              onClick={() => setMobileOpen(true)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "#6b7280", display: "none" }}
              className="mobile-menu-btn"
            >
              <Menu size={20} />
            </button>
            <h1 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>{currentPage}</h1>
          </div>
          <Link href="/dashboard" style={{
            display: "flex", alignItems: "center", gap: 6,
            background: "#7F77DD", color: "#fff", padding: "7px 14px",
            borderRadius: 6, fontSize: 13, fontWeight: 600, textDecoration: "none"
          }}>
            <Plus size={14} />
            New Campaign
          </Link>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflow: "auto", padding: "24px" }}>
          {children}
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav style={{
        display: "none", position: "fixed", bottom: 0, left: 0, right: 0,
        background: "#111", borderTop: "1px solid rgba(255,255,255,0.08)",
        padding: "8px 16px", zIndex: 30
      }} className="mobile-nav">
        {NAV_ITEMS.slice(0, 5).map(({ label, href, icon: Icon }) => (
          <Link key={href} href={href} style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 3,
            color: pathname === href ? "#7F77DD" : "#6b7280", textDecoration: "none", flex: 1
          }}>
            <Icon size={18} />
            <span style={{ fontSize: 10, fontWeight: 500 }}>{label}</span>
          </Link>
        ))}
      </nav>

      <style>{`
        @media (max-width: 768px) {
          .hidden-mobile { display: none !important; }
          .mobile-nav { display: flex !important; }
          .mobile-menu-btn { display: flex !important; }
          main { padding: 16px !important; padding-bottom: 80px !important; }
        }
      `}</style>
    </div>
  );
}
