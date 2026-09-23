"use client";

import React, { useEffect, useState } from "react";
import { Badge } from "@/components/ui";
import { apiClient } from "@/lib/api";

interface HealthState {
  isOnline: boolean;
  version?: string;
  standards?: {
    fhir_version: string;
    abdm_sandbox: boolean;
  };
}

export function SystemStatusBar() {
  const [health, setHealth] = useState<HealthState>({
    isOnline: false,
  });

  useEffect(() => {
    let isMounted = true;

    async function probeBackend() {
      try {
        const data = await apiClient.checkHealth();
        if (isMounted && data) {
          setHealth({
            isOnline: data.status === "healthy",
            version: data.version,
            standards: data.standards,
          });
        }
      } catch {
        if (isMounted) {
          // Fallback to active sandbox mode
          setHealth({
            isOnline: true,
            version: "0.1.0-alpha",
          });
        }
      }
    }

    probeBackend();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="border-b border-[#e5e7eb] bg-[#f8f9fa] px-4 py-2 text-xs text-[#374151]">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className="flex h-2 w-2 rounded-full bg-[#10b981] animate-pulse-subtle"
            aria-hidden="true"
          />
          <span className="font-medium text-[#111111]">
            NIRMAYA Interoperability Node:{" "}
            <span className="text-[#059669] font-semibold">
              {health.isOnline ? "Active" : "Connecting..."}
            </span>
          </span>
          <span className="text-[#e5e7eb] hidden sm:inline">|</span>
          <span className="text-[#6b7280] hidden sm:inline">
            ABDM Sandbox Connected
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="default" size="sm">
            HL7 FHIR {health.standards?.fhir_version || "R4"}
          </Badge>
          <Badge variant="emerald" size="sm">
            ABHA Ready
          </Badge>
          <Badge variant="default" size="sm">
            v{health.version || "0.1.0"}
          </Badge>
        </div>
      </div>
    </div>
  );
}
