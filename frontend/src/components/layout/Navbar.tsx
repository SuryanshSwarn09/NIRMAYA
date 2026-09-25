"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLogo } from "@/components/common/BrandLogo";
import { Badge, Button } from "@/components/ui";
import { MAIN_NAV_ITEMS } from "@/config/navigation";
import { useAuth } from "@/context/AuthContext";
import { Menu, X, LogOut, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface NavbarProps {
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
}

export function Navbar({
  onToggleMobileMenu,
  isMobileMenuOpen = false,
}: NavbarProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();

  const getInitials = (name?: string) => {
    if (!name) return "U";
    const parts = name.split(" ");
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <header className="sticky top-0 z-40 h-16 bg-white border-b border-[#e5e7eb] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between gap-4">
        {/* Brand Wordmark & Geometric Mark with Subtle Network Pill */}
        <div className="flex items-center gap-3">
          <BrandLogo size="md" />
          <div className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] text-[11px] text-[#4b5563] font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-[#10b981]" />
            <span>Network Active</span>
          </div>
        </div>

        {/* Center Desktop Navigation Links (Inter 14px / 500) */}
        <nav className="hidden lg:flex items-center gap-1">
          {MAIN_NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-[8px] text-sm font-medium transition-colors select-none",
                  isActive
                    ? "bg-[#f5f5f5] text-[#111111] font-semibold"
                    : "text-[#6b7280] hover:text-[#111111] hover:bg-[#f8f9fa]"
                )}
              >
                <span>{item.title}</span>
              </Link>
            );
          })}
          <a
            href="https://suryanshs-projects.gitbook.io/nirmaya-docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] text-sm font-medium text-[#6b7280] hover:text-[#111111] hover:bg-[#f8f9fa] transition-colors select-none"
          >
            <span>Documentation</span>
          </a>
        </nav>

        {/* Right Action Cluster: Authenticated User State vs Sign In CTA */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2.5">
              <Link
                href={user.role === "doctor" ? "/doctor" : "/patient"}
                className="flex items-center gap-2 py-1 px-2 rounded-full border border-[#e5e7eb] hover:bg-[#f8f9fa] transition-colors"
              >
                <div className="h-7 w-7 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-xs">
                  {getInitials(user.fullName)}
                </div>
                <div className="hidden sm:flex flex-col text-left">
                  <span className="text-xs font-semibold text-[#111111] leading-tight">
                    {user.fullName || user.email.split("@")[0]}
                  </span>
                  <span className="text-[10px] uppercase font-bold text-[#059669] leading-tight">
                    {user.role}
                  </span>
                </div>
              </Link>

              <button
                onClick={logout}
                title="Sign Out"
                className="h-8 w-8 flex items-center justify-center rounded-full border border-[#e5e7eb] text-[#6b7280] hover:text-[#111111] hover:bg-[#f5f5f5] transition-colors cursor-pointer"
                aria-label="Sign Out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-3">
              <Link
                href="/login"
                className="text-sm font-semibold text-[#111111] hover:text-[#6b7280] px-2 py-1.5 transition-colors select-none"
              >
                Sign In
              </Link>
              <Link href="/register">
                <Button variant="primary" size="md">
                  Register with ABHA
                </Button>
              </Link>
            </div>
          )}

          {/* Mobile Menu Toggle Button (36px circular) */}
          <button
            onClick={onToggleMobileMenu}
            className="lg:hidden h-9 w-9 flex items-center justify-center rounded-full border border-[#e5e7eb] text-[#111111] hover:bg-[#f5f5f5] transition-colors"
            aria-label={isMobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            {isMobileMenuOpen ? (
              <X className="h-4 w-4" />
            ) : (
              <Menu className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
