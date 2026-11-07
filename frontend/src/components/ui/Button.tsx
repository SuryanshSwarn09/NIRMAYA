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
    // Official UX4G Design System Class Mapping (Base + Variant + Size)
    const ux4gVariantMap: Record<string, string> = {
      primary: "ux4g-btn-primary bg-[#0b4d8c] text-white hover:bg-[#083c6f] active:bg-[#062d53] border border-[#0b4d8c]",
      secondary: "ux4g-btn-tonal-primary bg-[#e8f1f9] text-[#0b4d8c] hover:bg-[#d0e4f5] border border-[#b9d5ee]",
      outline: "ux4g-btn-outline-primary bg-white text-[#0b4d8c] border border-[#0b4d8c] hover:bg-[#e8f1f9]",
      ghost: "ux4g-btn-text-primary bg-transparent text-[#0b4d8c] hover:bg-[#f0f4f8]",
      link: "bg-transparent text-[#0b4d8c] hover:underline p-0 h-auto font-semibold",
      danger: "ux4g-btn-danger bg-[#db372d] text-white hover:bg-[#b3251e] border border-[#db372d]",
      emerald: "ux4g-btn-primary bg-[#046a38] text-white hover:bg-[#03522b] border border-[#046a38]",
    };

    const ux4gSizeMap: Record<string, string> = {
      sm: "ux4g-btn-s h-8 px-3 text-xs rounded-[4px] gap-1.5 font-medium",
      md: "ux4g-btn-m h-10 px-4 text-sm rounded-[6px] gap-2 font-semibold",
      lg: "ux4g-btn-l h-12 px-6 text-base rounded-[6px] gap-2.5 font-semibold",
      icon: "ux4g-icon-btn ux4g-icon-btn-m h-9 w-9 p-0 rounded-[6px] justify-center border border-[#d1d5db] bg-white text-[#0b4d8c] hover:bg-[#e8f1f9]",
    };

    const isIcon = size === "icon";
    const baseClass = isIcon ? "ux4g-icon-btn" : "ux4g-btn";

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          baseClass,
          "inline-flex items-center justify-center transition-all duration-150 select-none cursor-pointer disabled:pointer-events-none disabled:opacity-50",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0b4d8c] focus-visible:ring-offset-2",
          ux4gVariantMap[variant] || ux4gVariantMap.primary,
          ux4gSizeMap[size] || ux4gSizeMap.md,
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin mr-1.5" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
