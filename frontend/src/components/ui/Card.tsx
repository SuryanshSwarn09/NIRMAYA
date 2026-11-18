import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "feature" | "mockup" | "hero-mockup" | "featured-dark" | "default" | "elevated" | "outlined";
  glass?: boolean;
}

export function Card({
  className,
  variant = "feature",
  glass = false,
  ...props
}: CardProps) {
  // Cal.com Modern SaaS Card Styling & Indian Government Elevated Standards
  const variantStyles: Record<string, string> = {
    // Standard Feature Card: Clean white surface with subtle hairline border and 8px radius
    feature:
      "bg-white text-[#111827] rounded-[8px] p-6 sm:p-8 border border-[#e5e7eb] shadow-xs transition-all duration-150",
    // Official Government Outlined Card
    outlined:
      "bg-white text-[#111827] rounded-[8px] p-6 border-2 border-[#0b4d8c]/20 hover:border-[#0b4d8c] transition-colors",
    // Official Government Elevated Card
    elevated:
      "bg-white text-[#111827] rounded-[8px] p-6 sm:p-8 border border-[#d1d5db] shadow-sm transition-all duration-150",
    // Mockup card: crisp white canvas with hairline border & subtle shadow
    mockup:
      "bg-white text-[#111827] rounded-[8px] p-6 border border-[#e5e7eb] shadow-xs",
    // Hero marquee mockup container: elevated shadow
    "hero-mockup":
      "bg-white text-[#111827] rounded-[10px] p-6 sm:p-8 border border-[#b9d5ee] shadow-md",
    // Featured dark card (e.g. secure cryptographic ledger): #051c33 deep navy
    "featured-dark":
      "bg-[#051c33] text-white rounded-[8px] p-6 sm:p-8 border border-[#0b4d8c] shadow-md",
    default:
      "bg-white text-[#111827] rounded-[8px] p-6 border border-[#e5e7eb] shadow-xs",
  };

  return (
    <div
      className={cn(
        variantStyles[variant] || variantStyles.default,
        glass && "backdrop-blur-md bg-white/95 border-[#b9d5ee]",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 pb-4 border-b border-[#f0f4f8] mb-4", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-base sm:text-lg font-bold text-[#0b4d8c] leading-tight tracking-tight",
        className
      )}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-xs sm:text-sm text-[#4b5563] leading-relaxed", className)}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("pt-0", className)} {...props} />;
}

export function CardFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center pt-4 border-t border-[#f0f4f8] mt-4", className)}
      {...props}
    />
  );
}
