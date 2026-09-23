import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface BrandLogoProps {
  className?: string;
  showSubtitle?: boolean;
  size?: "sm" | "md" | "lg";
}

/**
 * Cal.com-inspired BrandLogo:
 * Clean, restrained geometric brand mark with monochrome wordmark.
 */
export function BrandLogo({
  className,
  showSubtitle = true,
  size = "md",
}: BrandLogoProps) {
  const iconSizes = {
    sm: "h-7 w-7 text-xs rounded-full",
    md: "h-8 w-8 text-sm rounded-full",
    lg: "h-10 w-10 text-base rounded-full",
  };

  const titleSizes = {
    sm: "text-base tracking-tight",
    md: "text-lg tracking-tight",
    lg: "text-xl tracking-tight",
  };

  return (
    <Link
      href="/"
      className={cn(
        "group flex items-center gap-2.5 select-none transition-transform active:scale-[0.99]",
        className
      )}
    >
      {/* Cal.com-style geometric circle brand icon */}
      <div
        className={cn(
          "bg-[#111111] text-white flex items-center justify-center font-bold shadow-sm transition-transform group-hover:scale-105",
          iconSizes[size]
        )}
      >
        <span>N</span>
      </div>

      {/* Brand Text Hierarchy */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "font-bold text-[#111111] leading-none",
              titleSizes[size]
            )}
          >
            nirmaya
          </span>
          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded-full bg-[#f5f5f5] text-[#6b7280] border border-[#e5e7eb] leading-none">
            Network
          </span>
        </div>

        {showSubtitle && (
          <p className="text-[10px] text-[#6b7280] font-normal tracking-tight mt-0.5 hidden sm:block">
            Networked Interoperable Records Medical Assets & Your Archives
          </p>
        )}
      </div>
    </Link>
  );
}
