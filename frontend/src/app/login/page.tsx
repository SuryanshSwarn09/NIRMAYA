"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { Button, Badge, Card } from "@/components/ui";
import { useAuth, DEMO_PERSONAS, type UserRole } from "@/context/AuthContext";
import { 
  Stethoscope, 
  UserCheck, 
  FlaskConical, 
  ShieldAlert, 
  ArrowRight, 
  CheckCircle2,
  Lock,
  Mail
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, loginAsDemoRole, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loadingPersona, setLoadingPersona] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setErrorMsg("Please enter your email or ABHA handle");
      return;
    }
    setErrorMsg("");
    const success = await login(email, password);
    if (success) {
      router.push("/patient");
    } else {
      setErrorMsg("Authentication failed. Please check credentials or select a demo persona.");
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
      <div className="w-full max-w-md space-y-8">
        
        {/* Cal.com Clean Branding & Header */}
        <div className="text-center space-y-2">
          <div className="h-10 w-10 rounded-full overflow-hidden border border-[#e5e7eb] shadow-xs mx-auto mb-2 bg-white flex items-center justify-center">
            <Image
              src="/logo.png"
              alt="NIRMAYA Logo"
              width={40}
              height={40}
              priority
              className="object-contain"
            />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">

            Welcome back to NIRMAYA
          </h1>
          <p className="text-sm text-[#6b7280]">
            Sign in to access your longitudinal vault or clinical console.
          </p>
        </div>

        {/* Credentials Form Card */}
        <Card variant="mockup" className="p-6 sm:p-8 space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMsg && (
              <div className="p-3 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-xs text-[#991b1b] flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="text-xs font-semibold text-[#111111] flex items-center gap-1.5"
              >
                <Mail className="h-3.5 w-3.5 text-[#6b7280]" />
                Email or Health ID
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com or 91-xxxx-xxxx-xxxx"
                className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] placeholder:text-[#898989] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-xs font-semibold text-[#111111] flex items-center gap-1.5"
                >
                  <Lock className="h-3.5 w-3.5 text-[#6b7280]" />
                  Password
                </label>
                <span className="text-xs text-[#6b7280] hover:text-[#111111] cursor-pointer">
                  Forgot?
                </span>
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] placeholder:text-[#898989] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading && !loadingPersona}
              className="w-full"
            >
              <span>Sign In with Password</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </form>

          {/* Cal.com Hairline Divider */}
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#e5e7eb]" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-[#898989] font-medium tracking-wider text-[10px]">
                or sandbox 1-click persona
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
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111111] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111111] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <Stethoscope className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111111] flex items-center gap-1">
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
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111111] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111111] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <UserCheck className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111111] flex items-center gap-1">
                  <span>Arun Patel</span>
                  <Badge variant="emerald" size="sm">ABHA</Badge>
                </div>
                <p className="text-[11px] text-[#6b7280]">Patient Vault</p>
              </div>
            </button>

            {/* 3. Diagnostic Lab */}
            <button
              type="button"
              onClick={() => handleDemoLogin("lab")}
              disabled={isLoading}
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111111] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111111] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <FlaskConical className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111111] flex items-center gap-1">
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
              className="p-3 text-left rounded-[8px] border border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#111111] transition-all flex items-start gap-2.5 group cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-[#f5f5f5] text-[#111111] flex items-center justify-center shrink-0 border border-[#e5e7eb] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#111111] flex items-center gap-1">
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
          Don&apos;t have an ABHA Health ID yet?{" "}
          <Link
            href="/register"
            className="font-semibold text-[#111111] hover:underline"
          >
            Register with ABHA
          </Link>
        </p>

      </div>
    </div>
  );
}
