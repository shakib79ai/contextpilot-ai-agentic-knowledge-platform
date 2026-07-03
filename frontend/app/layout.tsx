import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ContextPilot AI",
  description: "Production-grade multi-agent knowledge learning platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <Link href="/" className="brand">ContextPilot AI</Link>
          <Link href="/chat">Chat</Link>
          <Link href="/documents">Documents</Link>
          <Link href="/review">Review</Link>
          <Link href="/login">Login</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
