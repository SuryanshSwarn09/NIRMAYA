"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { 
  User, 
  Stethoscope, 
  FlaskConical, 
  Pill, 
  ShieldCheck, 
  Smartphone, 
  FileCheck2, 
  AlertTriangle, 
  ArrowRight, 
  CheckCircle2, 
  RefreshCw, 
  PhoneCall, 
  Lock, 
  Fingerprint, 
  Building2,
  Clock
} from "lucide-react";
import { Button, Badge, Card } from "@/components/ui";
import { useAuth, DEMO_PERSONAS, getPortalRouteForRole, type UserRole } from "@/context/AuthContext";

export type NationalRole = "citizen" | "doctor" | "lab" | "pharmacy";
export type CitizenAuthChannel = "aadhaar_otp" | "digilocker" | "abha_mobile" | "offline_emergency";

interface UniversalNationalGatewayCardProps {
  initialRole?: NationalRole;
  onSuccess?: () => void;
}

export function UniversalNationalGatewayCard({
  initialRole = "citizen",
  onSuccess,
}: UniversalNationalGatewayCardProps) {
  const router = useRouter();
  const { login, loginWithToken, loginAsDemoRole, isLoading: authLoading } = useAuth();

  // Active role selector
  const [activeRole, setActiveRole] = useState<NationalRole>(initialRole);

  // Active citizen auth channel
  const [activeChannel, setActiveChannel] = useState<CitizenAuthChannel>("aadhaar_otp");

  // Remember device longevity (30 days default)
  const [rememberMe, setRememberMe] = useState<boolean>(true);

  // Shared UI states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Channel 1: Aadhaar OTP State
  const [aadhaarInput, setAadhaarInput] = useState<string>("9184 7210 4821");
  const [aadhaarStep, setAadhaarStep] = useState<"challenge" | "verify">("challenge");
  const [aadhaarTxnId, setAadhaarTxnId] = useState<string | null>(null);
  const [aadhaarOtp, setAadhaarOtp] = useState<string>("123456");
  const [maskedMobile, setMaskedMobile] = useState<string>("+91 ******4821");
  const [cooldown, setCooldown] = useState<number>(0);

  // Channel 2: DigiLocker State
  const [digiLockerLoading, setDigiLockerLoading] = useState<boolean>(false);

  // Channel 3: ABHA Mobile Fallback State
  const [mobileNumber, setMobileNumber] = useState<string>("9876543210");
  const [mobileOtp, setMobileOtp] = useState<string>("123456");
  const [abhaHandle, setAbhaHandle] = useState<string>("pooja.sharma@abdm");

  // Channel 4: Offline Emergency Break-The-Glass State
  const [facilityId, setFacilityId] = useState<string>("IN-DL-AIIMS-001");
  const [clinicianId, setClinicianId] = useState<string>("HPR-9921-DR");
  const [traumaPatientId, setTraumaPatientId] = useState<string>("TRAUMA-2026-DEL-894");
  const [emergencyReason, setEmergencyReason] = useState<string>("Unconscious polytrauma victim road traffic accident");
  const [emergencyTriage, setEmergencyTriage] = useState<"red" | "yellow">("red");
  const [tamperAttestation, setTamperAttestation] = useState<string>(
    "I declare clinical necessity under the Disaster and Emergency Care Framework."
  );

  // Professional form state (Doctor / Lab / Pharmacy)
  const [proEmail, setProEmail] = useState<string>("");
  const [proPassword, setProPassword] = useState<string>("");

  // Cooldown countdown
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleAadhaarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 12);
    const formatted = raw.replace(/(\d{4})(?=\d)/g, "$1 ");
    setAadhaarInput(formatted);
  };

  // Defensive API helper to prevent HTML parsing SyntaxErrors
  const postGateway = async <T,>(url: string, body: unknown): Promise<{ success: boolean; data: T; message?: string }> => {
    let resp: Response;
    try {
      resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch {
      throw new Error(
        "Unable to reach NIRMAYA Health Gateway API. Please verify the backend service is running and accessible."
      );
    }

    const contentType = resp.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      if (resp.status === 404) {
        throw new Error(
          "Gateway API endpoint not found (HTTP 404). Backend service is not connected to this deployment."
        );
      }
      if (resp.status === 429) {
        throw new Error(
          "Rate limit reached (HTTP 429): Too many verification requests. Please wait 30 to 60 seconds before trying again."
        );
      }
      throw new Error(`Gateway returned unexpected response format (HTTP ${resp.status}).`);
    }

    const data = await resp.json();
    if (!resp.ok) {
      if (resp.status === 429) {
        throw new Error(
          data.detail || data.message || "Rate limit reached (HTTP 429): Too many verification attempts. Please retry shortly."
        );
      }
      throw new Error(data.detail || data.message || `Authentication error (HTTP ${resp.status})`);
    }
    return data;
  };

  interface GatewaySessionData {
    session_id: string;
    access_token: string;
    user_role: string;
    auth_channel: string;
    user_id: string;
    name: string;
    abha_address?: string;
    abha_number?: string;
  }

  // Preserve real session credentials and route to authorized workspace
  const establishGatewaySession = (sessionData: GatewaySessionData, defaultRole: UserRole) => {
    const role: UserRole =
      sessionData.user_role === "doctor"
        ? "doctor"
        : sessionData.user_role === "lab"
        ? "lab"
        : sessionData.user_role === "admin"
        ? "admin"
        : defaultRole;

    const authUser = {
      id: sessionData.user_id,
      email: sessionData.abha_address
        ? `${sessionData.abha_address.replace("@", "")}@abdm`
        : `${sessionData.user_id.slice(0, 8)}@nirmaya.health`,
      role,
      fullName: sessionData.name || "Authenticated Citizen",
      isVerified: true,
    };

    loginWithToken(sessionData.access_token, authUser);
    if (onSuccess) onSuccess();
    window.location.href = getPortalRouteForRole(role);
  };

  // 1. Aadhaar OTP Challenge
  const handleAadhaarChallenge = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      interface ChallengeData {
        txn_id: string;
        masked_mobile: string;
      }
      const data = await postGateway<ChallengeData>(
        "/api/v1/gateway/auth/aadhaar/challenge",
        { aadhaar_number: aadhaarInput }
      );
      setAadhaarTxnId(data.data.txn_id);
      setMaskedMobile(data.data.masked_mobile);
      setAadhaarStep("verify");
      setCooldown(60);
      setSuccessMessage(data.message || "OTP challenge sent successfully.");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Challenge failed.");
    } finally {
      setIsLoading(false);
    }
  };

  // 1b. Aadhaar OTP Verify
  const handleAadhaarVerify = async () => {
    if (!aadhaarTxnId) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await postGateway<GatewaySessionData>(
        "/api/v1/gateway/auth/aadhaar/verify",
        {
          txn_id: aadhaarTxnId,
          otp: aadhaarOtp,
          remember_me: rememberMe,
        }
      );
      establishGatewaySession(data.data, "patient");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setIsLoading(false);
    }
  };

  // 2. DigiLocker e-KYC Verification
  const handleDigiLockerKyc = async () => {
    setDigiLockerLoading(true);
    setErrorMessage(null);
    try {
      const data = await postGateway<GatewaySessionData>(
        "/api/v1/gateway/auth/digilocker/verify",
        {
          code: "sandbox_auth_code_dl",
          state: "sandbox_state_csrf",
          code_verifier: "pkce_verifier_demo",
          remember_me: rememberMe,
        }
      );
      establishGatewaySession(data.data, "patient");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "DigiLocker error.");
    } finally {
      setDigiLockerLoading(false);
    }
  };

  // 3. ABHA Mobile Fallback
  const handleAbhaMobileLogin = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await postGateway<GatewaySessionData>(
        "/api/v1/gateway/auth/mobile/verify",
        {
          mobile_number: mobileNumber,
          otp: mobileOtp,
          abha_identifier: abhaHandle,
          remember_me: rememberMe,
        }
      );
      establishGatewaySession(data.data, "patient");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Mobile authentication error.");
    } finally {
      setIsLoading(false);
    }
  };

  // 4. Offline Emergency Break-The-Glass Mode
  const handleEmergencyBypass = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await postGateway<GatewaySessionData>(
        "/api/v1/gateway/auth/emergency/bypass",
        {
          facility_id: facilityId,
          clinician_id: clinicianId,
          patient_identifier: traumaPatientId,
          emergency_reason: emergencyReason,
          triage_level: emergencyTriage,
          tamper_attestation: tamperAttestation,
        }
      );
      establishGatewaySession(data.data, "doctor");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Emergency bypass error.");
    } finally {
      setIsLoading(false);
    }
  };

  // Professional form submit
  const handleProSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!proEmail) {
      setErrorMessage("Please enter your registered credentials or license ID.");
      return;
    }
    setErrorMessage(null);
    const targetRole: UserRole = activeRole === "doctor" ? "doctor" : activeRole === "lab" ? "lab" : "patient";
    const ok = await login(proEmail, proPassword, targetRole);
    if (ok) {
      if (onSuccess) onSuccess();
      window.location.href = getPortalRouteForRole(targetRole);
    } else {
      setErrorMessage("Authentication failed. Please verify credentials or select a demo persona.");
    }
  };

  const handleDemoSignIn = async (role: UserRole) => {
    setErrorMessage(null);
    const ok = await loginAsDemoRole(role);
    if (ok) {
      if (onSuccess) onSuccess();
      window.location.href = getPortalRouteForRole(role);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto space-y-4">
      {/* 1. Indian National Government Health Header & Helplines */}
      <div className="rounded-[10px] border border-[#e5e7eb] bg-white overflow-hidden shadow-xs">
        {/* Tricolor Micro-Strip */}
        <div className="h-1 w-full flex">
          <div className="h-full w-1/3 bg-[#ff9933]" />
          <div className="h-full w-1/3 bg-white" />
          <div className="h-full w-1/3 bg-[#138808]" />
        </div>

        {/* National Helplines Strip */}
        <div className="px-4 py-2.5 bg-[#f9fafb] border-b border-[#e5e7eb] flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#374151]">
            <span className="font-semibold text-[#111827]">National Helplines:</span>
            <span className="inline-flex items-center gap-1 font-mono text-[#111827] bg-white px-2 py-0.5 rounded border border-[#e5e7eb]">
              <PhoneCall className="h-3 w-3 text-[#111827]" />
              1075 (Tele-Consultation)
            </span>
            <span className="inline-flex items-center gap-1 font-mono text-[#991b1b] bg-[#fef2f2] px-2 py-0.5 rounded border border-[#fecaca]">
              108 (Ambulance)
            </span>
          </div>
          <Badge variant="emerald" size="sm">
            ABDM Gateway v0.5 M1/M2/M3
          </Badge>
        </div>

        {/* 2. Four-Role Segmented Control */}
        <div className="p-3 bg-white border-b border-[#e5e7eb]">
          <div className="text-[11px] font-semibold text-[#6b7280] uppercase tracking-wider mb-2">
            Select Healthcare Access Portal
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 p-1 bg-[#f9fafb] rounded-[8px] border border-[#e5e7eb] text-xs">
            <button
              type="button"
              onClick={() => {
                setActiveRole("citizen");
                setErrorMessage(null);
              }}
              className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                activeRole === "citizen"
                  ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                  : "text-[#6b7280] hover:text-[#111827]"
              }`}
            >
              <User className="h-3.5 w-3.5" />
              <span>Citizen</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveRole("doctor");
                setErrorMessage(null);
              }}
              className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                activeRole === "doctor"
                  ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                  : "text-[#6b7280] hover:text-[#111827]"
              }`}
            >
              <Stethoscope className="h-3.5 w-3.5" />
              <span>Doctor</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveRole("lab");
                setErrorMessage(null);
              }}
              className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                activeRole === "lab"
                  ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                  : "text-[#6b7280] hover:text-[#111827]"
              }`}
            >
              <FlaskConical className="h-3.5 w-3.5" />
              <span>Diagnostic</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveRole("pharmacy");
                setErrorMessage(null);
              }}
              className={`py-2 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                activeRole === "pharmacy"
                  ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                  : "text-[#6b7280] hover:text-[#111827]"
              }`}
            >
              <Pill className="h-3.5 w-3.5" />
              <span>Pharmacy</span>
            </button>
          </div>
        </div>

        {/* 3. Main Role Card Body */}
        <div className="p-5 sm:p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-xs text-[#991b1b] flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-[#ef4444]" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-[8px] bg-[#ecfdf5] border border-[#a7f3d0] text-xs text-[#065f46] flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-[#10b981]" />
              <span>{successMessage}</span>
            </div>
          )}

          {activeRole === "citizen" ? (
            /* CITIZEN PORTAL: 4 MULTI-MODAL CHANNELS */
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#f3f4f6]">
                <div>
                  <h3 className="text-sm font-semibold text-[#111827]">Universal Citizen Gateway</h3>
                  <p className="text-xs text-[#6b7280]">Select preferred digital identity verification channel</p>
                </div>
                <Badge variant="verified" size="sm">Passwordless</Badge>
              </div>

              {/* Citizen Channel Segmented Navigation */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 p-1 bg-[#f9fafb] rounded-[8px] border border-[#e5e7eb] text-xs">
                <button
                  type="button"
                  onClick={() => {
                    setActiveChannel("aadhaar_otp");
                    setErrorMessage(null);
                  }}
                  className={`py-1.5 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1 cursor-pointer ${
                    activeChannel === "aadhaar_otp"
                      ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                      : "text-[#6b7280] hover:text-[#111827]"
                  }`}
                >
                  <Fingerprint className="h-3 w-3" />
                  <span>Aadhaar OTP</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setActiveChannel("digilocker");
                    setErrorMessage(null);
                  }}
                  className={`py-1.5 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1 cursor-pointer ${
                    activeChannel === "digilocker"
                      ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                      : "text-[#6b7280] hover:text-[#111827]"
                  }`}
                >
                  <FileCheck2 className="h-3 w-3" />
                  <span>DigiLocker</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setActiveChannel("abha_mobile");
                    setErrorMessage(null);
                  }}
                  className={`py-1.5 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1 cursor-pointer ${
                    activeChannel === "abha_mobile"
                      ? "bg-white text-[#111827] shadow-xs border border-[#e5e7eb]"
                      : "text-[#6b7280] hover:text-[#111827]"
                  }`}
                >
                  <Smartphone className="h-3 w-3" />
                  <span>Mobile OTP</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setActiveChannel("offline_emergency");
                    setErrorMessage(null);
                  }}
                  className={`py-1.5 px-2 text-center font-medium rounded-[6px] transition-all flex items-center justify-center gap-1 cursor-pointer ${
                    activeChannel === "offline_emergency"
                      ? "bg-[#fef2f2] text-[#991b1b] shadow-xs border border-[#fecaca]"
                      : "text-[#6b7280] hover:text-[#991b1b]"
                  }`}
                >
                  <AlertTriangle className="h-3 w-3 text-[#ef4444]" />
                  <span>Emergency</span>
                </button>
              </div>

              {/* Channel 1: Aadhaar OTP Form */}
              {activeChannel === "aadhaar_otp" && (
                <div className="p-4 rounded-[8px] border border-[#e5e7eb] bg-[#f9fafb] space-y-3.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#111827]">UIDAI Demographic OTP Challenge</span>
                    <Badge variant="abdm" size="sm">Direct UIDAI</Badge>
                  </div>

                  {aadhaarStep === "challenge" ? (
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <label className="text-xs font-semibold text-[#111827] flex items-center gap-1">
                          <Fingerprint className="h-3.5 w-3.5 text-[#6b7280]" />
                          12-Digit Aadhaar Number
                        </label>
                        <input
                          type="text"
                          value={aadhaarInput}
                          onChange={handleAadhaarChange}
                          placeholder="XXXX XXXX XXXX"
                          maxLength={14}
                          className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white font-mono text-sm tracking-wider text-[#111827] focus:outline-none focus:border-[#111827]"
                        />
                        <p className="text-[11px] text-[#6b7280]">
                          Demo test Aadhaar: 9184 7210 4821
                        </p>
                      </div>

                      <Button
                        type="button"
                        variant="primary"
                        className="w-full justify-center"
                        disabled={isLoading || aadhaarInput.replace(/\s/g, "").length !== 12}
                        onClick={handleAadhaarChallenge}
                      >
                        {isLoading ? (
                          <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                        ) : (
                          <ArrowRight className="h-4 w-4 mr-1" />
                        )}
                        <span>Generate OTP Challenge</span>
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="p-2.5 rounded-[6px] bg-white border border-[#e5e7eb] text-xs text-[#374151] flex items-center justify-between">
                        <span>Dispatched to {maskedMobile}</span>
                        {cooldown > 0 ? (
                          <span className="text-[#6b7280] font-mono">{cooldown}s</span>
                        ) : (
                          <button
                            type="button"
                            onClick={handleAadhaarChallenge}
                            className="text-[#111827] font-semibold underline hover:text-black cursor-pointer"
                          >
                            Resend
                          </button>
                        )}
                      </div>

                      <div className="space-y-1">
                        <label className="text-xs font-semibold text-[#111827] flex items-center gap-1">
                          <Lock className="h-3.5 w-3.5 text-[#6b7280]" />
                          Enter 6-Digit OTP
                        </label>
                        <input
                          type="text"
                          value={aadhaarOtp}
                          onChange={(e) => setAadhaarOtp(e.target.value.slice(0, 6))}
                          placeholder="123456"
                          maxLength={6}
                          className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white font-mono text-base tracking-widest text-[#111827] text-center focus:outline-none focus:border-[#111827]"
                        />
                      </div>

                      <Button
                        type="button"
                        variant="primary"
                        className="w-full justify-center"
                        disabled={isLoading || aadhaarOtp.length !== 6}
                        onClick={handleAadhaarVerify}
                      >
                        {isLoading ? (
                          <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                        )}
                        <span>Verify & Open Patient Vault</span>
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {/* Channel 2: DigiLocker e-KYC */}
              {activeChannel === "digilocker" && (
                <div className="p-4 rounded-[8px] border border-[#e5e7eb] bg-[#f9fafb] space-y-3.5 text-center">
                  <div className="h-10 w-10 mx-auto rounded-full bg-[#ecfdf5] border border-[#a7f3d0] flex items-center justify-center">
                    <FileCheck2 className="h-5 w-5 text-[#065f46]" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-[#111827]">1-Click DigiLocker Verified Login</h4>
                    <p className="text-[11px] text-[#6b7280] max-w-sm mx-auto mt-1">
                      Instantly pulls certified demographic claims and reserved ABHA handle from your DigiLocker e-Aadhaar vault.
                    </p>
                  </div>

                  <Button
                    type="button"
                    variant="primary"
                    className="w-full justify-center"
                    disabled={digiLockerLoading}
                    onClick={handleDigiLockerKyc}
                  >
                    {digiLockerLoading ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <ArrowRight className="h-4 w-4 mr-1" />
                    )}
                    <span>Authenticate via DigiLocker e-KYC</span>
                  </Button>
                </div>
              )}

              {/* Channel 3: ABHA Mobile Fallback */}
              {activeChannel === "abha_mobile" && (
                <div className="p-4 rounded-[8px] border border-[#e5e7eb] bg-[#f9fafb] space-y-3.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#111827]">Active SIM Mobile Fallback</span>
                    <Badge variant="neutral" size="sm">SIM Verification</Badge>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[#111827]">10-Digit Mobile</label>
                      <input
                        type="tel"
                        value={mobileNumber}
                        onChange={(e) => setMobileNumber(e.target.value.slice(0, 10))}
                        placeholder="9876543210"
                        className="w-full h-10 px-3 rounded-[8px] border border-[#e5e7eb] bg-white font-mono text-sm text-[#111827] focus:outline-none focus:border-[#111827]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[#111827]">6-Digit OTP</label>
                      <input
                        type="text"
                        value={mobileOtp}
                        onChange={(e) => setMobileOtp(e.target.value.slice(0, 6))}
                        placeholder="123456"
                        className="w-full h-10 px-3 rounded-[8px] border border-[#e5e7eb] bg-white font-mono text-sm text-[#111827] text-center focus:outline-none focus:border-[#111827]"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-[#111827]">Optional @abdm Handle</label>
                    <input
                      type="text"
                      value={abhaHandle}
                      onChange={(e) => setAbhaHandle(e.target.value)}
                      placeholder="username@abdm"
                      className="w-full h-10 px-3 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] focus:outline-none focus:border-[#111827]"
                    />
                  </div>

                  <Button
                    type="button"
                    variant="primary"
                    className="w-full justify-center"
                    disabled={isLoading || mobileNumber.length !== 10}
                    onClick={handleAbhaMobileLogin}
                  >
                    {isLoading ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 mr-1" />
                    )}
                    <span>Authenticate via Mobile OTP</span>
                  </Button>
                </div>
              )}

              {/* Channel 4: Offline Emergency Mode */}
              {activeChannel === "offline_emergency" && (
                <div className="p-4 rounded-[8px] border border-[#fecaca] bg-[#fef2f2]/60 space-y-3.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#991b1b] flex items-center gap-1.5">
                      <AlertTriangle className="h-4 w-4 text-[#ef4444]" />
                      Break-The-Glass Emergency Intake
                    </span>
                    <Badge variant="critical" size="sm">High-Privilege Audit</Badge>
                  </div>
                  <p className="text-[11px] text-[#7f1d1d]">
                    For unconscious trauma patients, mass casualty events, or disaster response. All actions generate an immutable SHA-256 tamper seal and trigger audit notifications to legal guardians.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-[#7f1d1d]">Facility HFR ID</label>
                      <input
                        type="text"
                        value={facilityId}
                        onChange={(e) => setFacilityId(e.target.value)}
                        className="w-full h-9 px-3 rounded-[6px] border border-[#fecaca] bg-white font-mono text-xs text-[#111827]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-[#7f1d1d]">Clinician HPR ID</label>
                      <input
                        type="text"
                        value={clinicianId}
                        onChange={(e) => setClinicianId(e.target.value)}
                        className="w-full h-9 px-3 rounded-[6px] border border-[#fecaca] bg-white font-mono text-xs text-[#111827]"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-[#7f1d1d]">Patient Trauma Identifier</label>
                    <input
                      type="text"
                      value={traumaPatientId}
                      onChange={(e) => setTraumaPatientId(e.target.value)}
                      className="w-full h-9 px-3 rounded-[6px] border border-[#fecaca] bg-white font-mono text-xs text-[#111827]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-[#7f1d1d]">Emergency Clinical Rationale</label>
                    <input
                      type="text"
                      value={emergencyReason}
                      onChange={(e) => setEmergencyReason(e.target.value)}
                      className="w-full h-9 px-3 rounded-[6px] border border-[#fecaca] bg-white text-xs text-[#111827]"
                    />
                  </div>

                  <Button
                    type="button"
                    variant="primary"
                    className="w-full justify-center bg-[#991b1b] hover:bg-[#7f1d1d] text-white"
                    disabled={isLoading}
                    onClick={handleEmergencyBypass}
                  >
                    {isLoading ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 mr-1 text-white" />
                    )}
                    <span>Issue Break-The-Glass Session (SHA-256 Sealed)</span>
                  </Button>
                </div>
              )}

              {/* Remember Me Toggle */}
              <div className="flex items-center justify-between text-xs pt-1 border-t border-[#f3f4f6]">
                <label className="flex items-center gap-2 text-[#374151] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-[#d1d5db] text-[#111827] focus:ring-0"
                  />
                  <span>Keep this device authenticated for 30 days (National Security SLA)</span>
                </label>
              </div>
            </div>
          ) : (
            /* PROFESSIONAL PORTALS: DOCTOR, LAB, PHARMACY */
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#f3f4f6]">
                <div>
                  <h3 className="text-sm font-semibold text-[#111827]">
                    {activeRole === "doctor" && "Doctor & Practitioner Console (EMR)"}
                    {activeRole === "lab" && "Diagnostic Laboratory & Pathology Desk"}
                    {activeRole === "pharmacy" && "Pharmacy Dispensation & Drug Registry"}
                  </h3>
                  <p className="text-xs text-[#6b7280]">
                    Sign in with registered facility credentials or national council identifier
                  </p>
                </div>
                <Badge variant="verified" size="sm">
                  {activeRole === "doctor" ? "HPR Council" : "Facility HFR"}
                </Badge>
              </div>

              <form onSubmit={handleProSubmit} className="space-y-3.5">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#111827]">
                    {activeRole === "doctor" ? "Registered Email or @hpr.abdm" : "Institutional Facility User"}
                  </label>
                  <input
                    type="text"
                    value={proEmail}
                    onChange={(e) => setProEmail(e.target.value)}
                    placeholder={
                      activeRole === "doctor"
                        ? "dr.ananya@aiims.edu or dr.sharma@hpr.abdm"
                        : activeRole === "lab"
                        ? "lab@apollo.nirmaya.in"
                        : "pharmacy@civilhospital.in"
                    }
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] focus:outline-none focus:border-[#111827]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#111827]">Password or Security Token</label>
                  <input
                    type="password"
                    value={proPassword}
                    onChange={(e) => setProPassword(e.target.value)}
                    placeholder="Enter practitioner password"
                    className="w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] focus:outline-none focus:border-[#111827]"
                  />
                </div>

                <Button type="submit" variant="primary" className="w-full justify-center">
                  <span>Sign In to {activeRole.toUpperCase()} Portal</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </form>

              {/* 1-Click Evaluation Persona Quick Select */}
              <div className="pt-2 border-t border-[#f3f4f6] space-y-2">
                <div className="text-[11px] font-semibold text-[#6b7280]">
                  Evaluator Fast Track (1-Click Demo Sign-In):
                </div>
                {activeRole === "doctor" && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start text-xs h-9 bg-white hover:bg-[#f9fafb]"
                    onClick={() => handleDemoSignIn("doctor")}
                  >
                    <Stethoscope className="h-3.5 w-3.5 mr-2 text-[#111827]" />
                    <span>Sign in as Dr. Ananya Sharma (Cardiologist, AIIMS)</span>
                  </Button>
                )}
                {activeRole === "lab" && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start text-xs h-9 bg-white hover:bg-[#f9fafb]"
                    onClick={() => handleDemoSignIn("lab")}
                  >
                    <FlaskConical className="h-3.5 w-3.5 mr-2 text-[#111827]" />
                    <span>Sign in as Apollo Diagnostics Lab Technician</span>
                  </Button>
                )}
                {activeRole === "pharmacy" && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start text-xs h-9 bg-white hover:bg-[#f9fafb]"
                    onClick={() => handleDemoSignIn("patient")}
                  >
                    <Pill className="h-3.5 w-3.5 mr-2 text-[#111827]" />
                    <span>Sign in as Civil Hospital Dispensary Officer</span>
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

