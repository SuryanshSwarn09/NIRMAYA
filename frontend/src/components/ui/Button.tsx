import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "outline-primary" | "ghost" | "link" | "danger" | "emerald";
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
    // Sovereign UI Button Styling (Tailwind v4 with Official Government Tokens)
    const variantMap: Record<string, string> = {
      primary: "bg-[#0b4d8c] text-white hover:bg-[#083c6f] active:bg-[#062d53] border border-[#0b4d8c] shadow-xs",
      secondary: "bg-[#e8f1f9] text-[#0b4d8c] hover:bg-[#d0e4f5] border border-[#b9d5ee]",
      outline: "bg-white text-[#0b4d8c] border border-[#0b4d8c] hover:bg-[#e8f1f9]",
      "outline-primary": "bg-white text-[#0b4d8c] border border-[#0b4d8c] hover:bg-[#e8f1f9]",
      ghost: "bg-transparent text-[#0b4d8c] hover:bg-[#f0f4f8]",
      link: "bg-transparent text-[#0b4d8c] hover:underline p-0 h-auto font-semibold",
      danger: "bg-[#db372d] text-white hover:bg-[#b3251e] border border-[#db372d]",
      emerald: "bg-[#046a38] text-white hover:bg-[#03522b] border border-[#046a38]",
    };

    const sizeMap: Record<string, string> = {
      sm: "h-8 px-3 text-xs rounded-[4px] gap-1.5 font-medium",
      md: "h-10 px-4 text-sm rounded-[6px] gap-2 font-semibold",
      lg: "h-12 px-6 text-base rounded-[6px] gap-2.5 font-semibold",
      icon: "h-9 w-9 p-0 rounded-[6px] justify-center border border-[#d1d5db] bg-white text-[#0b4d8c] hover:bg-[#e8f1f9]",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center transition-all duration-150 select-none cursor-pointer disabled:pointer-events-none disabled:opacity-50",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0b4d8c] focus-visible:ring-offset-2",
          variantMap[variant] || variantMap.primary,
          sizeMap[size] || sizeMap.md,
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
