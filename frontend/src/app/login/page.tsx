"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { UniversalNationalGatewayCard } from "@/components/gateway";
import { Badge } from "@/components/ui";
import { NationalEmblem } from "@/components/common/NationalEmblem";
import { useAuth, getPortalRouteForRole } from "@/context/AuthContext";
import { RefreshCw } from "lucide-react";

export default function LoginPage() {
  const { isAuthenticated, user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      window.location.href = getPortalRouteForRole(user.role);
    }
  }, [isAuthenticated, user, isLoading]);

  if (isLoading || (isAuthenticated && user)) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12 bg-white">
        <div className="flex flex-col items-center gap-3 text-center">
          <RefreshCw className="h-6 w-6 animate-spin text-[#0b4d8c]" />
          <p className="text-xs font-semibold text-[#0b4d8c]">
            Redirecting to your authorized workspace...
          </p>
        </div>
      </div>
    );
  }
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12 bg-[#f8fafc]">
      <div className="w-full max-w-xl space-y-6">
        
        {/* Sovereign Branding & Header */}
        <div className="text-center space-y-3">
          <div className="flex justify-center">
            <NationalEmblem size="lg" />
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f0f6ff] border border-[#0b4d8c]/20 text-xs font-semibold text-[#0b4d8c]">
            <span className="h-2 w-2 rounded-full bg-[#046a38]" />
            <span>National Health Portal • Single Sign-On (SSO)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#0b4d8c]">
            Universal National Health Gateway
          </h1>
          <p className="text-xs sm:text-sm text-[#4b5563] max-w-md mx-auto">
            Ayushman Bharat Digital Mission (ABDM) Multi-Channel Interoperability & Medical Records Access
          </p>
        </div>

        {/* Universal High-Density National Gateway Card */}
        <UniversalNationalGatewayCard />

        {/* Standard Citizen Registration Guidance */}
        <p className="text-center text-xs text-[#6b7280]">
          First-time citizen? Use the DigiLocker or Aadhaar OTP channel above to{" "}
          <Link href="/register" className="font-semibold text-[#0b4d8c] hover:underline">
            auto-provision your ABHA health record in 15 seconds
          </Link>.
        </p>

      </div>
    </div>
  );
}
