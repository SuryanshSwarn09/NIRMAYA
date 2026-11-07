import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
  requiredIndicator?: boolean;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = "text",
      error,
      label,
      requiredIndicator = false,
      helperText,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs sm:text-sm font-semibold text-[#171717] leading-tight"
          >
            {label}
            {requiredIndicator && <span className="text-[#db372d] ml-1" aria-hidden="true">*</span>}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          ref={ref}
          className={cn(
            "ux4g-input ux4g-input-m w-full h-10 px-3 py-2 text-sm rounded-[6px] bg-white text-[#171717]",
            "border border-[#d1d5db] transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0b4d8c] focus-visible:border-[#0b4d8c]",
            "disabled:bg-[#f3f4f6] disabled:text-[#9ca3af] disabled:cursor-not-allowed",
            error && "border-[#db372d] focus-visible:ring-[#db372d]",
            className
          )}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-desc` : undefined}
          {...props}
        />
        {helperText && !error && (
          <p id={`${inputId}-desc`} className="text-[11px] text-[#6b7280]">
            {helperText}
          </p>
        )}
        {error && (
          <p id={`${inputId}-error`} className="text-xs font-medium text-[#db372d] flex items-center gap-1">
            <span>{error}</span>
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
