import React from "react";
import { cn } from "@/lib/utils";
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from "lucide-react";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "info" | "warning" | "error" | "success";
  title?: string;
}

export function Alert({
  className,
  variant = "info",
  title,
  children,
  ...props
}: AlertProps) {
  const variantMap = {
    info: {
      container: "ux4g-alert ux4g-alert-info bg-[#e8f1f9] text-[#0b4d8c] border-[#b9d5ee]",
      icon: <Info className="h-5 w-5 text-[#0b4d8c] flex-shrink-0" />,
      titleColor: "text-[#0b4d8c]",
    },
    warning: {
      container: "ux4g-alert ux4g-alert-warning bg-[#fff5ea] text-[#b45309] border-[#ffd9af]",
      icon: <AlertTriangle className="h-5 w-5 text-[#f47920] flex-shrink-0" />,
      titleColor: "text-[#b45309]",
    },
    error: {
      container: "ux4g-alert ux4g-alert-danger bg-[#fde8e8] text-[#9b1c1c] border-[#f8b4b4]",
      icon: <AlertCircle className="h-5 w-5 text-[#db372d] flex-shrink-0" />,
      titleColor: "text-[#9b1c1c]",
    },
    success: {
      container: "ux4g-alert ux4g-alert-success bg-[#e6f4ea] text-[#046a38] border-[#a3d9b8]",
      icon: <CheckCircle2 className="h-5 w-5 text-[#046a38] flex-shrink-0" />,
      titleColor: "text-[#046a38]",
    },
  };

  const selected = variantMap[variant] || variantMap.info;

  return (
    <div
      role="alert"
      className={cn(
        "rounded-[8px] border p-4 flex gap-3 transition-colors",
        selected.container,
        className
      )}
      {...props}
    >
      {selected.icon}
      <div className="space-y-1">
        {title && <h5 className={cn("text-sm font-bold leading-tight", selected.titleColor)}>{title}</h5>}
        <div className="text-xs sm:text-sm leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
