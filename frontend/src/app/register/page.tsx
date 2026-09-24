"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card, NavPillGroup } from "@/components/ui";
import { useAuth, type UserRole } from "@/context/AuthContext";
import { 
  ShieldCheck, 
  Stethoscope, 
  FlaskConical, 
  ArrowRight, 
  User, 
  Mail, 
  Lock, 
  CreditCard,
  Building2
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { loginWithToken } = useAuth();
  const [role, setRole] = useState<UserRole>("patient");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [idNumber, setIdNumber] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

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

      if (role === "doctor") {
        router.push("/doctor");
      } else if (role === "lab") {
        router.push("/lab");
      } else {
        router.push("/patient");
      }
    }, 600);
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12 bg-white">
      <div className="w-full max-w-lg space-y-8">
        
        {/* Cal.com Clean Branding & Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-10 w-10 rounded-full bg-[#111111] text-white items-center justify-center font-bold text-sm shadow-xs mx-auto mb-2">
            N
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">
            Create your NIRMAYA Account
          </h1>
          <p className="text-sm text-[#6b7280]">
            Connect with your National Health Identity in under 60 seconds.
          </p>
        </div>

        {/* Registration Card */}
        <Card variant="mockup" className="p-6 sm:p-8 space-y-6">
          {/* Role Switcher NavPillGroup */}
          <div className="flex justify-center">
            <NavPillGroup
              items={[
                {
                  id: "patient",
                  label: "Patient",
                  icon: <ShieldCheck className="h-3.5 w-3.5" />,
                },
                {
                  id: "doctor",
                  label: "Doctor (HPR)",
                  icon: <Stethoscope className="h-3.5 w-3.5" />,
                },
                {
                  id: "lab",
                  label: "Diagnostic Lab",
                  icon: <FlaskConical className="h-3.5 w-3.5" />,
                },
              ]}
              activeId={role}
              onChange={(id) => setRole(id as UserRole)}
            />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label
                htmlFor="fullName"
                className="text-xs font-semibold text-[#111111] flex items-center gap-1.5"
              >
                <User className="h-3.5 w-3.5 text-[#6b7280]" />
                Full Legal Name
              </label>
              <input
                id="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. / Mr. / Ms. Full Name"
                className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] placeholder:text-[#898989] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="text-xs font-semibold text-[#111111] flex items-center gap-1.5"
              >
                <Mail className="h-3.5 w-3.5 text-[#6b7280]" />
                Official Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@healthcare.org"
                className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] placeholder:text-[#898989] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            {/* Dynamic Role-specific Identifier */}
            <div className="space-y-1.5">
              <label
                htmlFor="idNumber"
                className="text-xs font-semibold text-[#111111] flex items-center gap-1.5"
              >
                {role === "patient" && (
                  <>
                    <CreditCard className="h-3.5 w-3.5 text-[#6b7280]" />
                    <span>ABHA 14-Digit Number</span>
                  </>
                )}
                {role === "doctor" && (
                  <>
                    <Building2 className="h-3.5 w-3.5 text-[#6b7280]" />
                    <span>ABDM Healthcare Professional ID (@hpr.abdm)</span>
                  </>
                )}
                {role === "lab" && (
                  <>
                    <Building2 className="h-3.5 w-3.5 text-[#6b7280]" />
                    <span>NABL / Health Facility Registry (HFR) ID</span>
                  </>
                )}
              </label>
              <input
                id="idNumber"
                type="text"
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                placeholder={
                  role === "patient"
                    ? "91-8472-1092-4821"
                    : role === "doctor"
                    ? "doctor.name@hpr.abdm"
                    : "HFR-DEL-91024"
                }
                className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] placeholder:text-[#898989] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="password"
                className="text-xs font-semibold text-[#111111] flex items-center gap-1.5"
              >
                <Lock className="h-3.5 w-3.5 text-[#6b7280]" />
                Create Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111111] placeholder:text-[#898989] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isSubmitting}
              className="w-full mt-2"
            >
              <span>Complete ABDM Registration</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </form>
        </Card>

        {/* Footer Link */}
        <p className="text-center text-xs text-[#6b7280]">
          Already registered on the NIRMAYA network?{" "}
          <Link
            href="/login"
            className="font-semibold text-[#111111] hover:underline"
          >
            Sign In
          </Link>
        </p>

      </div>
    </div>
  );
}
