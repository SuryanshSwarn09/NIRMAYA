"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface NavPillItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string;
}

export interface NavPillGroupProps {
  items: NavPillItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
}

/**
 * Signature Cal.com NavPillGroup:
 * Pill-radius wrapper around sub-nav segments (e.g. switcher between product views).
 * Container: #f8f9fa, 6px padding, rounded-full.
 * Active Tab: #ffffff canvas with subtle drop shadow (0 1px 2px rgba(0,0,0,0.05)), rounded-full/md.
 * Inactive Tab: transparent, #6b7280 text.
 */
export function NavPillGroup({
  items,
  activeId,
  onChange,
  className,
}: NavPillGroupProps) {
  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex items-center p-1.5 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] max-w-full overflow-x-auto",
        className
      )}
    >
      {items.map((item) => {
        const isActive = activeId === item.id;
        return (
          <button
            key={item.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(item.id)}
            className={cn(
              "flex items-center gap-2 px-3.5 py-1.5 text-xs sm:text-sm font-medium rounded-full transition-all duration-150 select-none whitespace-nowrap cursor-pointer",
              isActive
                ? "bg-white text-[#111111] font-semibold shadow-[0_1px_3px_rgba(0,0,0,0.08)]"
                : "text-[#6b7280] hover:text-[#111111] hover:bg-black/[0.02]"
            )}
          >
            {item.icon && (
              <span
                className={cn(
                  "transition-colors",
                  isActive ? "text-[#111111]" : "text-[#6b7280]"
                )}
              >
                {item.icon}
              </span>
            )}
            <span>{item.label}</span>
            {item.badge && (
              <span
                className={cn(
                  "text-[10px] uppercase font-bold px-1.5 py-0.5 rounded-full leading-none",
                  isActive
                    ? "bg-[#111111] text-white"
                    : "bg-[#e5e7eb] text-[#374151]"
                )}
              >
                {item.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
