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
  // Official UX4G Government Badge Palette
  const variantStyles: Record<string, string> = {
    default: "ux4g-badge bg-[#e8f1f9] text-[#0b4d8c] border-[#b9d5ee]",
    neutral: "ux4g-badge bg-[#f3f4f6] text-[#374151] border-[#d1d5db]",
    verified: "ux4g-badge ux4g-badge-success bg-[#e6f4ea] text-[#046a38] border-[#a3d9b8]",
    pending: "ux4g-badge ux4g-badge-warning bg-[#fff4e5] text-[#b45309] border-[#fed7aa]",
    warning: "ux4g-badge ux4g-badge-warning bg-[#fff4e5] text-[#b45309] border-[#fed7aa]",
    critical: "ux4g-badge ux4g-badge-danger bg-[#fde8e8] text-[#9b1c1c] border-[#f8b4b4]",
    fhir: "ux4g-badge bg-[#e8f1f9] text-[#0b4d8c] border-[#b9d5ee]",
    abdm: "ux4g-badge bg-[#f3e8ff] text-[#6b21a8] border-[#d8b4fe]",
    outline: "ux4g-badge bg-transparent text-[#0b4d8c] border-2 border-[#0b4d8c]",
    orange: "ux4g-badge bg-[#fff5ea] text-[#f47920] border-[#ffd9af]",
    pink: "ux4g-badge bg-[#fdf2f8] text-[#be185d] border-[#fbcfe8]",
    violet: "ux4g-badge bg-[#f3e8ff] text-[#6b21a8] border-[#d8b4fe]",
    emerald: "ux4g-badge bg-[#e6f4ea] text-[#046a38] border-[#a3d9b8]",
  };

  const dotColors: Record<string, string> = {
    default: "bg-[#0b4d8c]",
    neutral: "bg-[#6b7280]",
    verified: "bg-[#046a38]",
    pending: "bg-[#f47920]",
    warning: "bg-[#f47920]",
    critical: "bg-[#db372d]",
    fhir: "bg-[#0b4d8c]",
    abdm: "bg-[#8b5cf6]",
    outline: "bg-[#0b4d8c]",
    orange: "bg-[#f47920]",
    pink: "bg-[#ec4899]",
    violet: "bg-[#8b5cf6]",
    emerald: "bg-[#046a38]",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px] gap-1",
    md: "px-2.5 py-0.5 text-[11px] gap-1.5",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center font-bold rounded-[4px] border leading-none transition-colors select-none",
        variantStyles[variant] || variantStyles.default,
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full flex-shrink-0",
            dotColors[variant] || "bg-[#0b4d8c]"
          )}
        />
      )}
      {children}
    </span>
  );
}
