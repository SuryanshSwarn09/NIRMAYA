import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "neutral"
    | "verified"
    | "pending"
    | "warning"
    | "critical"
    | "fhir"
    | "abdm"
    | "outline"
    | "orange"
    | "pink"
    | "violet"
    | "emerald";
  size?: "sm" | "md";
  dot?: boolean;
}

export function Badge({
  children,
  className,
  variant = "default",
  size = "md",
  dot = false,
  ...props
}: BadgeProps) {
  // Cal.com Design System Badge & Pastel Palette
  const variantStyles = {
    default: "bg-[#f5f5f5] text-[#111111] border-[#e5e7eb]",
    neutral: "bg-[#f5f5f5] text-[#111111] border-[#e5e7eb]",
    verified: "bg-[#ecfdf5] text-[#065f46] border-[#a7f3d0]",
    pending: "bg-[#fff7ed] text-[#9a3412] border-[#fed7aa]",
    warning: "bg-[#fff7ed] text-[#ea580c] border-[#fed7aa]",
    critical: "bg-[#fef2f2] text-[#991b1b] border-[#fecaca]",
    fhir: "bg-[#f8f9fa] text-[#111111] border-[#e5e7eb]",
    abdm: "bg-[#f5f3ff] text-[#5b21b6] border-[#ddd6fe]",
    outline: "bg-transparent text-[#111111] border-[#e5e7eb]",
    orange: "bg-[#fff7ed] text-[#ea580c] border-[#fed7aa]",
    pink: "bg-[#fdf2f8] text-[#db2777] border-[#fbcfe8]",
    violet: "bg-[#f5f3ff] text-[#7c3aed] border-[#ddd6fe]",
    emerald: "bg-[#ecfdf5] text-[#059669] border-[#a7f3d0]",
  };

  const dotColors = {
    default: "bg-[#111111]",
    neutral: "bg-[#6b7280]",
    verified: "bg-[#10b981]",
    pending: "bg-[#f59e0b]",
    warning: "bg-[#f59e0b]",
    critical: "bg-[#ef4444]",
    fhir: "bg-[#3b82f6]",
    abdm: "bg-[#8b5cf6]",
    outline: "bg-[#6b7280]",
    orange: "bg-[#fb923c]",
    pink: "bg-[#ec4899]",
    violet: "bg-[#8b5cf6]",
    emerald: "bg-[#34d399]",
  };

  const sizeStyles = {
    sm: "px-2.5 py-0.5 text-[11px] leading-tight font-medium",
    md: "px-3 py-1 text-xs font-medium", // Cal.com standard 4px 12px pill
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border transition-colors select-none",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn("h-1.5 w-1.5 rounded-full", dotColors[variant])}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  );
}
