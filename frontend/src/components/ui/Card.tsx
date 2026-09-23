import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "feature" | "mockup" | "hero-mockup" | "featured-dark" | "default";
  glass?: boolean;
}

export function Card({
  className,
  variant = "feature",
  glass = false,
  ...props
}: CardProps) {
  // Cal.com Card Styles
  const variantStyles = {
    // Standard Cal.com feature card: light-gray #f5f5f5, 12px radius, 32px padding
    feature:
      "rounded-[12px] bg-[#f5f5f5] text-[#111111] p-6 sm:p-8 border border-transparent transition-all duration-150",
    // Cal.com product mockup card: white #ffffff canvas with hairline border & subtle shadow
    mockup:
      "rounded-[12px] bg-white text-[#111111] p-6 border border-[#e5e7eb] shadow-[0_1px_2px_rgba(0,0,0,0.05)]",
    // Cal.com hero marquee mockup container: 16px radius, hairline border, elevated shadow
    "hero-mockup":
      "rounded-[16px] bg-white text-[#111111] p-6 border border-[#e5e7eb] shadow-[0_4px_12px_rgba(0,0,0,0.08)]",
    // Featured dark card (e.g. enterprise or featured tier): #101010
    "featured-dark":
      "rounded-[12px] bg-[#101010] text-white p-6 sm:p-8 border border-[#242424] shadow-md",
    default:
      "rounded-[12px] bg-white text-[#111111] p-6 border border-[#e5e7eb] shadow-[0_1px_2px_rgba(0,0,0,0.05)]",
  };

  return (
    <div
      className={cn(
        variantStyles[variant],
        glass && "backdrop-blur-md bg-white/90 border-[#e5e7eb]",
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
      className={cn("flex flex-col space-y-1.5 pb-4", className)}
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
        "text-lg sm:text-xl font-semibold tracking-tight text-[#111111]",
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
      className={cn("text-sm text-[#6b7280] leading-relaxed", className)}
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
      className={cn(
        "flex items-center pt-4 border-t border-[#e5e7eb]/80",
        className
      )}
      {...props}
    />
  );
}
