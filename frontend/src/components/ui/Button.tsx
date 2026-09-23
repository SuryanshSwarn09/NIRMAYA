import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "link" | "danger" | "emerald";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    // Cal.com Design System Button Styles
    const variantStyles = {
      primary:
        "bg-[#111111] text-white hover:bg-[#242424] active:bg-[#242424] border border-[#111111] shadow-sm disabled:bg-[#e5e7eb] disabled:border-[#e5e7eb] disabled:text-[#6b7280]",
      secondary:
        "bg-white text-[#111111] border border-[#e5e7eb] hover:bg-[#f5f5f5] active:bg-[#e5e7eb] shadow-sm",
      outline:
        "bg-white text-[#111111] border border-[#e5e7eb] hover:bg-[#f5f5f5] active:bg-[#e5e7eb]",
      ghost:
        "bg-transparent text-[#374151] hover:bg-[#f5f5f5] hover:text-[#111111]",
      link:
        "bg-transparent text-[#111111] hover:underline p-0 h-auto font-semibold",
      danger:
        "bg-[#ef4444] text-white hover:bg-[#dc2626] border border-[#ef4444]",
      // Backwards-compatible alias to Cal.com primary
      emerald:
        "bg-[#111111] text-white hover:bg-[#242424] active:bg-[#242424] border border-[#111111] shadow-sm",
    };

    const sizeStyles = {
      sm: "h-8 px-3 text-xs rounded-[6px] gap-1.5 font-medium",
      md: "h-10 px-4 text-sm rounded-[8px] gap-2 font-semibold", // Cal.com standard 40px, 8px radius
      lg: "h-11 px-5 text-sm rounded-[8px] gap-2.5 font-semibold",
      icon: "h-9 w-9 p-0 rounded-full justify-center border border-[#e5e7eb] bg-white text-[#111111] hover:bg-[#f5f5f5]", // Cal.com circular 36px
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#111111] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
