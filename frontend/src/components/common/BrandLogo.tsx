import React from "react";
import Link from "next/link";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface BrandLogoProps {
  className?: string;
  showSubtitle?: boolean;
  size?: "sm" | "md" | "lg";
}

/**
 * Cal.com-inspired BrandLogo:
 * Renders custom brand icon mark with monochrome wordmark.
 */
export function BrandLogo({
  className,
  showSubtitle = true,
  size = "md",
}: BrandLogoProps) {
  const iconDimensions = {
    sm: { width: 28, height: 28, className: "h-7 w-7 rounded-full" },
    md: { width: 34, height: 34, className: "h-8.5 w-8.5 rounded-full" },
    lg: { width: 42, height: 42, className: "h-10.5 w-10.5 rounded-full" },
  };

  const titleSizes = {
    sm: "text-base tracking-tight",
    md: "text-lg tracking-tight",
    lg: "text-xl tracking-tight",
  };

  const dim = iconDimensions[size];

  return (
    <Link
      href="/"
      className={cn(
        "group flex items-center gap-2.5 select-none transition-transform active:scale-[0.99]",
        className
      )}
    >
      {/* Custom Designed Logo Icon */}
      <div
        className={cn(
          "relative overflow-hidden flex items-center justify-center shrink-0 border border-[#e5e7eb] shadow-xs group-hover:scale-105 transition-transform bg-white",
          dim.className
        )}
      >
        <Image
          src="/logo.png"
          alt="NIRMAYA Logo"
          width={dim.width}
          height={dim.height}
          priority
          className="object-contain"
        />
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
