import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from '@/lib/auth-context'

export const metadata: Metadata = {
  title: "OutreachX — AI-Powered Cold Outreach Automation",
  description: "Discover startups, find decision-maker emails, generate personalized cold emails, and track replies — all in one pipeline.",
};


export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}