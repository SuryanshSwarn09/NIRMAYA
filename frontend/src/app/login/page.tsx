"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { Button, Badge, Card } from "@/components/ui";
import { useAuth, DEMO_PERSONAS, type UserRole } from "@/context/AuthContext";
import { PatientPasswordlessAuthCard } from "@/components/patient";
import { 
  Stethoscope, 
  UserCheck, 
  FlaskConical, 
  ShieldAlert, 
  ArrowRight, 
  CheckCircle2,
  Lock,
  Mail,
  User,
  Building2
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, loginAsDemoRole, isLoading } = useAuth();
  
  // Selected portal role tab: 'patient' | 'doctor' | 'staff'
  const [activePortal, setActivePortal] = useState<"patient" | "doctor" | "staff">("patient");

  // Clinical / Staff form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loadingPersona, setLoadingPersona] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setErrorMsg("Please enter your email or practitioner ID");
      return;
    }
    setErrorMsg("");
    const success = await login(email, password);
    if (success) {
      if (activePortal === "doctor") {
        router.push("/doctor");
      } else {
        router.push("/lab");
      }
    } else {
      setErrorMsg("Authentication failed. Please verify credentials or select a demo persona.");
    }
  };

  const handleDemoLogin = async (role: UserRole) => {
    setLoadingPersona(role);
    setErrorMsg("");
    const success = await loginAsDemoRole(role);
    if (success) {
      if (role === "doctor") {
        router.push("/doctor");
      } else if (role === "lab") {
        router.push("/lab");
      } else {
        router.push("/patient");
      }
    } else {
      setErrorMsg(`Failed to authenticate demo persona as ${role}.`);
      setLoadingPersona(null);
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12 bg-white">
      <div className="w-full max-w-lg space-y-6">
        
        {/* Clean Branding & Header */}
        <div className="text-center space-y-2">
          <div className="h-11 w-11 rounded-full overflow-hidden border border-[#e5e7eb] shadow-xs mx-auto mb-2 bg-white flex items-center justify-center">
            <Image
              src="/logo.png"
              alt="NIRMAYA Logo"
              width={44}
              height={44}
              priority
              className="object-contain"
            />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111827]">
            Welcome to NIRMAYA
          </h1>
          <p className="text-sm text-[#6b7280]">
            National Health Interoperability & Medical Records Gateway
          </p>
        </div>

        {/* Role Portal Switcher */}
        <div className="grid grid-cols-3 gap-1.5 p-1.5 bg-[#f9fafb] rounded-[8px] border border-[#e5e7eb] text-xs">
          <button
            type="button"
            onClick={() => {
              setActivePortal("patient");
              setErrorMsg("");
            }}
            className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              activePortal === "patient"
                ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111827]"
            }`}
          >
            <User className="h-3.5 w-3.5" />
            <span>Patient (Citizen)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActivePortal("doctor");
              setErrorMsg("");
            }}
            className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              activePortal === "doctor"
                ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111827]"
            }`}
          >
            <Stethoscope className="h-3.5 w-3.5" />
            <span>Doctor (EMR)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActivePortal("staff");
              setErrorMsg("");
            }}
            className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              activePortal === "staff"
                ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                : "text-[#6b7280] hover:text-[#111827]"
            }`}
          >
            <Building2 className="h-3.5 w-3.5" />
            <span>Lab / Staff</span>
          </button>
        </div>

        {/* Main Authentication Card */}
        <Card variant="mockup" className="p-6 sm:p-7 space-y-5">
          {activePortal === "patient" ? (
            /* PATIENT DOOR: Passwordless DigiLocker & Aadhaar OTP Gateway */
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-1 border-b border-[#f3f4f6]">
                <div>
                  <h2 className="text-sm font-semibold text-[#111827]">Patient Passwordless Access</h2>
                  <p className="text-xs text-[#6b7280]">Sign in or auto-create account via verified digital identity</p>
                </div>
                <Badge variant="emerald" size="sm">ABDM Verified</Badge>
              </div>

              <PatientPasswordlessAuthCard />
            </div>
          ) : (
            /* CLINICIAN & STAFF DOOR: Professional Credentials */
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-1 border-b border-[#f3f4f6]">
                <div>
                  <h2 className="text-sm font-semibold text-[#111827]">
                    {activePortal === "doctor" ? "Practitioner EMR Console" : "Hospital & Facility Portal"}
                  </h2>
                  <p className="text-xs text-[#6b7280]">
                    {activePortal === "doctor" ? "Sign in using registered council email or HPR ID" : "Sign in using institutional staff credentials"}
                  </p>
                </div>
                <Badge variant="verified" size="sm">
                  {activePortal === "doctor" ? "HPR Council" : "Facility"}
                </Badge>
              </div>

              <form onSubmit={handleSubmit} className="space-y-3.5">
                {errorMsg && (
                  <div className="p-3 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-xs text-[#991b1b] flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                )}

                <div className="space-y-1">
                  <label htmlFor="email" className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-[#6b7280]" />
                    {activePortal === "doctor" ? "Doctor Email or @hpr.abdm" : "Staff Email / Facility ID"}
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={activePortal === "doctor" ? "dr.ananya@aiims.edu or dr.sharma@hpr.abdm" : "lab@apollo.nirmaya.in"}
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#111827] transition-colors"
                  />
                </div>

                <div className="space-y-1">
                  <label htmlFor="password" className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                    <Lock className="h-3.5 w-3.5 text-[#6b7280]" />
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#111827] transition-colors"
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={isLoading && !loadingPersona}
                  className="w-full"
                >
                  <span>Sign In to Console</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </form>
            </div>
          )}

          {/* Hairline Divider */}
          <div className="relative my-3">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#e5e7eb]" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2.5 text-[#898989] font-medium tracking-wider text-[10px]">
                or sandbox 1-click evaluation personas
              </span>
            </div>
          </div>

          {/* Quick Demo Persona Switcher Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {/* 1. Doctor */}
            <button
              type="button"
              onClick={() => handleDemoLogin("doctor")}
              disabled={isLoading}
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111827] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111827] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <Stethoscope className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111827] flex items-center gap-1">
                  <span>Dr. Sharma</span>
                  <Badge variant="verified" size="sm">HPR</Badge>
                </div>
                <p className="text-[11px] text-[#6b7280]">AIIMS Cardiologist</p>
              </div>
            </button>

            {/* 2. Patient */}
            <button
              type="button"
              onClick={() => handleDemoLogin("patient")}
              disabled={isLoading}
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111827] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111827] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <UserCheck className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111827] flex items-center gap-1">
                  <span>Arun Patel</span>
                  <Badge variant="emerald" size="sm">ABHA</Badge>
                </div>
                <p className="text-[11px] text-[#6b7280]">Verified Citizen</p>
              </div>
            </button>

            {/* 3. Diagnostic Lab */}
            <button
              type="button"
              onClick={() => handleDemoLogin("lab")}
              disabled={isLoading}
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111827] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111827] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <FlaskConical className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111827] flex items-center gap-1">
                  <span>Apollo Lab</span>
                  <Badge variant="default" size="sm">Lab</Badge>
                </div>
                <p className="text-[11px] text-[#6b7280]">Diagnostic Ingest</p>
              </div>
            </button>

            {/* 4. Administrator */}
            <button
              type="button"
              onClick={() => handleDemoLogin("admin")}
              disabled={isLoading}
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111827] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111827] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111827] flex items-center gap-1">
                  <span>Root Admin</span>
                  <Badge variant="orange" size="sm">Super</Badge>
                </div>
                <p className="text-[11px] text-[#6b7280]">RBAC Superuser</p>
              </div>
            </button>
          </div>
        </Card>

        {/* Footer Link */}
        <p className="text-center text-xs text-[#6b7280]">
          New patient? Use the DigiLocker or Aadhaar OTP options above to{" "}
          <Link
            href="/login"
            className="font-semibold text-[#111827] hover:underline"
          >
            auto-register in 15 seconds
          </Link>.
        </p>

      </div>
    </div>
  );
}
