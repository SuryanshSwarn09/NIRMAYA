"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { MAIN_NAV_ITEMS } from "@/config/navigation";
import { Badge, Button } from "@/components/ui";
import { 
  ShieldCheck, 
  Stethoscope, 
  FlaskConical, 
  Database, 
  Layers, 
  Activity,
  X,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

const ICON_MAP = {
  ShieldCheck,
  Stethoscope,
  FlaskConical,
  Database,
  Layers,
  Activity,
};

export function MobileNav({ isOpen, onClose }: MobileNavProps) {
  const pathname = usePathname();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs lg:hidden"
            aria-hidden="true"
          />

          {/* Slide-in Navigation Sheet */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 260 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-xs bg-white border-l border-[#e5e7eb] p-6 flex flex-col justify-between shadow-xl lg:hidden"
          >
            <div>
              {/* Header with Close Action */}
              <div className="flex items-center justify-between pb-6 border-b border-[#e5e7eb]">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#111111] text-lg tracking-tight">
                    Navigation
                  </span>
                  <Badge variant="default" size="sm">
                    NIRMAYA
                  </Badge>
                </div>
                <button
                  onClick={onClose}
                  className="h-8 w-8 flex items-center justify-center rounded-full border border-[#e5e7eb] text-[#111111] hover:bg-[#f5f5f5] transition-colors"
                  aria-label="Close navigation"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Navigation Items List */}
              <div className="mt-6 space-y-1.5">
                {MAIN_NAV_ITEMS.map((item) => {
                  const Icon = ICON_MAP[item.iconName] || Activity;
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/" && pathname.startsWith(item.href));

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className={cn(
                        "group flex items-center justify-between p-3 rounded-[8px] transition-all",
                        isActive
                          ? "bg-[#f5f5f5] text-[#111111] font-semibold"
                          : "text-[#374151] hover:bg-[#f8f9fa] hover:text-[#111111]"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            "p-2 rounded-[6px] border",
                            isActive
                              ? "bg-[#111111] text-white border-[#111111]"
                              : "bg-[#f5f5f5] text-[#374151] border-[#e5e7eb]"
                          )}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">
                              {item.title}
                            </span>
                            {item.badge && (
                              <Badge
                                variant={item.badgeVariant || "default"}
                                size="sm"
                              >
                                {item.badge}
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-[#6b7280] line-clamp-1">
                            {item.description}
                          </p>
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-[#898989] group-hover:text-[#111111] transition-colors" />
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Bottom Authentication Buttons */}
            <div className="pt-6 border-t border-[#e5e7eb] space-y-2.5">
              <Link href="/login" onClick={onClose} className="block w-full">
                <Button variant="secondary" size="md" className="w-full">
                  Sign In
                </Button>
              </Link>
              <Link href="/register" onClick={onClose} className="block w-full">
                <Button variant="primary" size="md" className="w-full">
                  Register with ABHA
                </Button>
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
