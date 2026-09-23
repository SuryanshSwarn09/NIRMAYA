"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLogo } from "@/components/common/BrandLogo";
import { Badge, Button } from "@/components/ui";
import { MAIN_NAV_ITEMS } from "@/config/navigation";
import { Menu, X } from "lucide-react";
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

  return (
    <header className="sticky top-0 z-40 h-16 bg-white border-b border-[#e5e7eb] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between gap-4">
        {/* Brand Wordmark & Geometric Mark */}
        <BrandLogo size="md" />

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
                {item.badge && (
                  <Badge variant={item.badgeVariant || "default"} size="sm">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Action Cluster: Sign In link + Primary #111111 CTA + Mobile Hamburger */}
        <div className="flex items-center gap-3">
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
