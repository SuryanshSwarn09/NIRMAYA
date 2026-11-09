"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { UniversalNationalGatewayCard } from "@/components/gateway";
import { Badge } from "@/components/ui";

export default function LoginPage() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12 bg-white">
      <div className="w-full max-w-xl space-y-6">
        
        {/* Clean Official Branding & Header */}
        <div className="text-center space-y-2">
          <div className="h-12 w-12 rounded-full overflow-hidden border border-[#e5e7eb] shadow-xs mx-auto mb-2 bg-white flex items-center justify-center">
            <Image
              src="/logo.png"
              alt="NIRMAYA National Health Gateway"
              width={48}
              height={48}
              priority
              className="object-contain"
            />
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-[6px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs font-medium text-[#111111]">
            <span className="h-2 w-2 rounded-full bg-[#10b981]" />
            <span>National Health Portal Authentication</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111827]">
            Universal National Health Gateway
          </h1>
          <p className="text-xs sm:text-sm text-[#6b7280] max-w-md mx-auto">
            Ayushman Bharat Digital Mission (ABDM) Multi-Channel Interoperability & Medical Records Access
          </p>
        </div>

        {/* Universal High-Density National Gateway Card */}
        <UniversalNationalGatewayCard />

        {/* Standard Citizen Registration Guidance */}
        <p className="text-center text-xs text-[#6b7280]">
          First-time citizen? Use the DigiLocker or Aadhaar OTP channel above to{" "}
          <span className="font-semibold text-[#111827]">
            auto-provision your ABHA health record in 15 seconds
          </span>.
        </p>

      </div>
    </div>
  );
}
