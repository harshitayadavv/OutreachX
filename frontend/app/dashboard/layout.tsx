'use client'

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Megaphone, Users, Mail, BarChart3, Settings, Plus, Menu, X
} from "lucide-react";
import { useAuth } from '@/lib/auth-context'

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

  const { user, logout } = useAuth()

  const currentPage = NAV_ITEMS.find(n => n.href === pathname)?.label || "Dashboard";

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: "#f8f8f8" }}>
      
      {/* Sidebar - desktop */}
      <aside style={{
        width: 240,
        background: "#111111",
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid rgba(255,255,255,0.06)",
        flexShrink: 0,
        position: "relative",
        zIndex: 20
      }} className="hidden-mobile">
        
        {/* Logo */}
        <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
            <div style={{
              width: 32,
              height: 32,
              background: "#7F77DD",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 13,
              color: "#fff"
            }}>
              OX
            </div>
            <span style={{ fontWeight: 600, fontSize: 15, color: "#fff" }}>OutreachX</span>
          </Link>
        </div>

        {/* Nav */}
        <nav style={{
          padding: "12px 10px",
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 2
        }}>
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => (
            <Link key={href} href={href} className={`nav-link ${pathname === href ? "active" : ""}`}>
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>

        {/* Bottom Section (API + User) */}
        <div style={{
          borderTop: "1px solid rgba(255,255,255,0.06)",
          padding: "12px 10px"
        }}>
          {/* API Status */}
          <div style={{
            padding: "10px 12px",
            background: "rgba(127,119,221,0.1)",
            borderRadius: 8,
            border: "1px solid rgba(127,119,221,0.2)",
            marginBottom: 12
          }}>
            <p style={{ fontSize: 11, color: "#7F77DD", fontWeight: 600, marginBottom: 2 }}>
              API Status
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#22c55e"
              }} />
              <span style={{ fontSize: 12, color: "#9ca3af" }}>Connected</span>
            </div>
          </div>

          {/* User Info */}
          <div style={{
            padding: "10px 12px",
            borderRadius: 8,
            background: "rgba(255,255,255,0.03)"
          }}>
            <p style={{ color: "#fff", fontSize: 13, fontWeight: 500 }}>
              {user?.name || "User"}
            </p>
            <p style={{ color: "#6b7280", fontSize: 11 }}>
              {user?.email || "No email"}
            </p>

            <button
              onClick={logout}
              style={{
                marginTop: 6,
                fontSize: 11,
                color: "#9ca3af",
                background: "none",
                border: "none",
                cursor: "pointer"
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#fff")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#9ca3af")}
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 40 }}
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside style={{
        position: "fixed",
        top: 0,
        left: mobileOpen ? 0 : -260,
        width: 240,
        height: "100vh",
        background: "#111111",
        zIndex: 50,
        transition: "left 0.3s ease",
        display: "flex",
        flexDirection: "column"
      }}>
        <div style={{
          padding: "20px 20px 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}>
          <span style={{ color: "#fff", fontWeight: 600 }}>OutreachX</span>
          <button onClick={() => setMobileOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <nav style={{ padding: "12px 10px", flex: 1 }}>
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => (
            <Link key={href} href={href}>
              <Icon size={16} /> {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <header style={{
          height: 56,
          background: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px"
        }}>
          <h1>{currentPage}</h1>

          <Link href="/dashboard" style={{
            background: "#7F77DD",
            color: "#fff",
            padding: "7px 14px",
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 600
          }}>
            <Plus size={14} /> New Campaign
          </Link>
        </header>

        <main style={{ flex: 1, overflow: "auto", padding: "24px" }}>
          {children}
        </main>
      </div>
    </div>
  );
}