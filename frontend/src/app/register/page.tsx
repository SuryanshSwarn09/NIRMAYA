"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { Button, Card, Badge } from "@/components/ui";
import { NationalEmblem } from "@/components/common/NationalEmblem";
import { useAuth, getPortalRouteForRole, type UserRole } from "@/context/AuthContext";
import { PatientPasswordlessAuthCard } from "@/components/patient";
import { 
  ShieldCheck, 
  Stethoscope, 
  FlaskConical, 
  ArrowRight, 
  User, 
  Mail, 
  Lock, 
  CreditCard,
  Building2,
  RefreshCw
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { isAuthenticated, user, isLoading, loginWithToken } = useAuth();
  const [role, setRole] = useState<UserRole>("patient");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [idNumber, setIdNumber] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      window.location.href = getPortalRouteForRole(user.role);
    }
  }, [isAuthenticated, user, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    setTimeout(() => {
      // Simulate account creation and auto-login
      const newUser = {
        id: `user-${Date.now()}`,
        email,
        role,
        fullName: fullName || email.split("@")[0],
        abhaId: role === "patient" ? (idNumber || "91-9988-7766-5544") : undefined,
        hprId: role === "doctor" ? (idNumber || `${email.split("@")[0]}@hpr.abdm`) : undefined,
        isVerified: true,
      };

      loginWithToken(`jwt-token-${Date.now()}`, newUser);
      setIsSubmitting(false);
      window.location.href = getPortalRouteForRole(role);
    }, 600);
  };

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
      <div className="w-full max-w-lg space-y-6">
        
        {/* Sovereign Branding & Header */}
        <div className="text-center space-y-3">
          <div className="flex justify-center">
            <NationalEmblem size="lg" />
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f0f6ff] border border-[#0b4d8c]/20 text-xs font-semibold text-[#0b4d8c]">
            <span className="h-2 w-2 rounded-full bg-[#046a38]" />
            <span>Ayushman Bharat Digital Mission (ABDM)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#0b4d8c]">
            Register on NIRMAYA
          </h1>
          <p className="text-sm text-[#4b5563]">
            Connect to the National Digital Health Grid in under 60 seconds
          </p>
        </div>

        {/* Role Switcher */}
        <div className="grid grid-cols-3 gap-1.5 p-1.5 bg-[#f0f6ff] rounded-[8px] border border-[#0b4d8c]/20 text-xs">
          <button
            type="button"
            onClick={() => setRole("patient")}
            className={`ux4g-btn ux4g-btn-s py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              role === "patient"
                ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                : "text-[#4b5563] hover:text-[#0b4d8c]"
            }`}
          >
            <User className="h-3.5 w-3.5" />
            <span>Citizen (Patient)</span>
          </button>
          <button
            type="button"
            onClick={() => setRole("doctor")}
            className={`ux4g-btn ux4g-btn-s py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              role === "doctor"
                ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                : "text-[#4b5563] hover:text-[#0b4d8c]"
            }`}
          >
            <Stethoscope className="h-3.5 w-3.5" />
            <span>Doctor (HPR)</span>
          </button>
          <button
            type="button"
            onClick={() => setRole("lab")}
            className={`ux4g-btn ux4g-btn-s py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              role === "lab"
                ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
                : "text-[#4b5563] hover:text-[#0b4d8c]"
            }`}
          >
            <Building2 className="h-3.5 w-3.5" />
            <span>Lab Facility</span>
          </button>
        </div>

        {/* Registration Card */}
        <Card variant="mockup" className="ux4g-card ux4g-card-elevated p-6 sm:p-7 space-y-5 border border-[#0b4d8c]/20">
          {role === "patient" ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-1 border-b border-[#f3f4f6]">
                <div>
                  <h2 className="text-sm font-semibold text-[#0b4d8c]">Instant 1-Tap Patient Registration</h2>
                  <p className="text-xs text-[#6b7280]">
                    Auto-mints 14-digit ABHA Number and @abdm handle &bull; Zero manual typing
                  </p>
                </div>
                <Badge variant="emerald" size="sm">No Password</Badge>
              </div>

              <PatientPasswordlessAuthCard />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-1 border-b border-[#f3f4f6]">
                <div>
                  <h2 className="text-sm font-semibold text-[#0b4d8c]">
                    {role === "doctor" ? "Practitioner Council Onboarding" : "Facility Registration"}
                  </h2>
                  <p className="text-xs text-[#6b7280]">
                    Register your verified credentials on the Healthcare Professional Registry
                  </p>
                </div>
                <Badge variant="verified" size="sm">Credentialed</Badge>
              </div>

              <form onSubmit={handleSubmit} className="space-y-3.5">
                <div className="space-y-1">
                  <label htmlFor="fullName" className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5 text-[#0b4d8c]" />
                    Full Legal Name
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. / Practitioner Name"
                    className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
                  />
                </div>

                <div className="space-y-1">
                  <label htmlFor="email" className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-[#0b4d8c]" />
                    Official Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="doctor@hospital.org"
                    className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
                  />
                </div>

                <div className="space-y-1">
                  <label htmlFor="idNumber" className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5 text-[#0b4d8c]" />
                    {role === "doctor" ? "State Medical Council Registration No." : "Facility License Number"}
                  </label>
                  <input
                    id="idNumber"
                    type="text"
                    value={idNumber}
                    onChange={(e) => setIdNumber(e.target.value)}
                    placeholder={role === "doctor" ? "DMC-2018-98412" : "HFR-DEL-91024"}
                    className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
                  />
                </div>

                <div className="space-y-1">
                  <label htmlFor="password" className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                    <Lock className="h-3.5 w-3.5 text-[#0b4d8c]" />
                    Create Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={isSubmitting}
                  className="ux4g-btn ux4g-btn-primary ux4g-btn-m w-full mt-2"
                >
                  <span>Complete Professional Registration</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </form>
            </div>
          )}
        </Card>

        {/* Footer Link */}
        <p className="text-center text-xs text-[#6b7280]">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold text-[#0b4d8c] hover:underline"
          >
            Sign In to Console
          </Link>
        </p>

      </div>
    </div>
  );
}
