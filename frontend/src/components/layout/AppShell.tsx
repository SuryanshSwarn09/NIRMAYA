"use client";

import React, { useState } from "react";
import { AuthProvider } from "@/context/AuthContext";
import { SystemStatusBar } from "./SystemStatusBar";
import { Navbar } from "./Navbar";
import { MobileNav } from "./MobileNav";
import { Footer } from "./Footer";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col bg-white text-[#111111] selection:bg-slate-200 selection:text-black">
        {/* 1. Primary Navigation Header */}
        <Navbar
          isMobileMenuOpen={isMobileMenuOpen}
          onToggleMobileMenu={() => setIsMobileMenuOpen((prev) => !prev)}
        />

        {/* 3. Animated Mobile Sheet Drawer */}
        <MobileNav
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
        />

        {/* 4. Main Page Viewport Container */}
        <main className="flex-1 w-full bg-white">{children}</main>

        {/* 5. Cal.com Dark Footer Closing Surface */}
        <Footer />
      </div>
    </AuthProvider>
  );
}
