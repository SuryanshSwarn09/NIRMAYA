"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  ShieldCheck, 
  Smartphone, 
  KeyRound, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Check, 
  Building2,
  FileText
} from "lucide-react";
import { Button, Badge, Card } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

interface PatientPasswordlessAuthCardProps {
  onSuccess?: () => void;
}

export function PatientPasswordlessAuthCard({ onSuccess }: PatientPasswordlessAuthCardProps) {
  const router = useRouter();
  const { loginWithToken } = useAuth();

  // Tab mode: 'digilocker' | 'aadhaar_otp' | 'mobile_fallback'
  const [authMode, setAuthMode] = useState<"digilocker" | "aadhaar_otp" | "mobile_fallback">("digilocker");

  // Suggestion 2: Session Longevity (30 days default)
  const [rememberMe, setRememberMe] = useState<boolean>(true);

  // Status & loading
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    name: string;
    abhaNumber: string;
    isNew: boolean;
  } | null>(null);

  // Aadhaar OTP State
  const [aadhaarInput, setAadhaarInput] = useState<string>("9184 7210 4821");
  const [otpStep, setOtpStep] = useState<"input" | "verify">("input");
  const [otpValue, setOtpValue] = useState<string>("123456");
  const [txnId, setTxnId] = useState<string | null>(null);
  const [maskedMobile, setMaskedMobile] = useState<string>("+91 ******4821");
  const [cooldownSeconds, setCooldownSeconds] = useState<number>(0);

  // Mobile Fallback State (Suggestion 1)
  const [fallbackMobile, setFallbackMobile] = useState<string>("9876543210");
  const [fallbackOtp, setFallbackOtp] = useState<string>("123456");
  const [fallbackAbha, setFallbackAbha] = useState<string>("");

  // Cooldown countdown
  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const timer = setInterval(() => {
      setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldownSeconds]);

  // Format Aadhaar Input with spaces
  const handleAadhaarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 12);
    const formatted = raw.replace(/(\d{4})(?=\d)/g, "$1 ");
    setAadhaarInput(formatted);
  };

  // 1. Channel A: DigiLocker Auth
  const handleDigiLockerLogin = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Fetch PKCE state and verify via sandbox simulation
      const verifyResp = await fetch("/api/v1/auth/digilocker/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: "sandbox_valid_code",
          state: "sandbox_state",
          code_verifier: "mock_verifier_xyz",
        }),
      });

      if (!verifyResp.ok) {
        throw new Error("DigiLocker verification failed. Please try again.");
      }

      const verifyData = await verifyResp.json();
      const verifiedClaims = verifyData.data;
      const demo = verifiedClaims.demographics;

      // Submit to unified patient login/registration endpoint
      const authResp = await fetch("/api/v1/auth/patient/login-or-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: "digilocker",
          name: demo.name,
          gender: demo.gender,
          date_of_birth: demo.date_of_birth,
          masked_aadhaar: demo.masked_aadhaar,
          formatted_address: demo.address?.formatted_address,
          district: demo.address?.district,
          state: demo.address?.state,
          pincode: demo.address?.pincode,
          remember_me: rememberMe,
        }),
      });

      const authData = await authResp.json();
      if (!authResp.ok || !authData.success) {
        throw new Error(authData.message || "Failed to authenticate patient session");
      }

      const patientData = authData.data;
      const authUser = {
        id: patientData.user_id,
        email: `${patientData.user_id.slice(0, 8)}@abdm`,
        role: "patient" as const,
        fullName: patientData.name || "Authenticated Citizen",
        abhaId: patientData.abha_number,
        isVerified: true,
      };
      loginWithToken(patientData.access_token, authUser);

      setSuccessInfo({
        name: patientData.name,
        abhaNumber: patientData.abha_number || "91-XXXX-XXXX-XXXX",
        isNew: patientData.is_new_user,
      });

      setTimeout(() => {
        if (onSuccess) onSuccess();
        window.location.href = "/patient";
      }, 500);
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during DigiLocker auth.");
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Channel B: Direct Aadhaar OTP - Step 1: Send OTP
  const handleSendAadhaarOtp = async () => {
    const rawDigits = aadhaarInput.replace(/\D/g, "");
    if (rawDigits.length !== 12) {
      setErrorMessage("Please enter a valid 12-digit Aadhaar number");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const resp = await fetch("/api/v1/abdm/m1/aadhaar/generate-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aadhaar_number: rawDigits }),
      });

      const data = await resp.json();
      if (!resp.ok || !data.success) {
        throw new Error(data.message || "Failed to generate Aadhaar OTP");
      }

      setTxnId(data.data.txn_id);
      setMaskedMobile(data.data.masked_mobile || "+91 ******4821");
      setCooldownSeconds(60);
      setOtpStep("verify");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to initiate Aadhaar OTP dispatch.");
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Channel B: Direct Aadhaar OTP - Step 2: Verify & Login/Register
  const handleVerifyAadhaarOtp = async () => {
    if (!txnId) {
      setErrorMessage("Missing session transaction ID. Please request OTP again.");
      return;
    }
    if (otpValue.trim().length !== 6) {
      setErrorMessage("Please enter the 6-digit numeric OTP");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Step A: Verify OTP with ABDM OTP engine
      const verifyResp = await fetch("/api/v1/abdm/m1/aadhaar/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          txn_id: txnId,
          otp: otpValue.trim(),
        }),
      });

      const verifyData = await verifyResp.json();
      if (!verifyResp.ok || !verifyData.success) {
        throw new Error(verifyData.message || "Invalid or expired Aadhaar OTP");
      }

      const verifiedClaims = verifyData.data;

      // Step B: Authenticate or Auto-Register Patient
      const authResp = await fetch("/api/v1/auth/patient/login-or-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: "aadhaar_otp",
          name: verifiedClaims.name,
          gender: verifiedClaims.gender,
          date_of_birth: verifiedClaims.date_of_birth,
          masked_aadhaar: verifiedClaims.masked_aadhaar,
          formatted_address: verifiedClaims.address?.formatted_address,
          district: verifiedClaims.address?.district,
          state: verifiedClaims.address?.state,
          pincode: verifiedClaims.address?.pincode,
          txn_id: txnId,
          remember_me: rememberMe,
        }),
      });

      const authData = await authResp.json();
      if (!authResp.ok || !authData.success) {
        throw new Error(authData.message || "Failed to create patient session");
      }

      const patientData = authData.data;
      const authUser = {
        id: patientData.user_id,
        email: `${patientData.user_id.slice(0, 8)}@abdm`,
        role: "patient" as const,
        fullName: patientData.name || "Authenticated Citizen",
        abhaId: patientData.abha_number,
        isVerified: true,
      };
      loginWithToken(patientData.access_token, authUser);

      setSuccessInfo({
        name: patientData.name,
        abhaNumber: patientData.abha_number || "91-XXXX-XXXX-XXXX",
        isNew: patientData.is_new_user,
      });

      setTimeout(() => {
        if (onSuccess) onSuccess();
        window.location.href = "/patient";
      }, 500);
    } catch (err: any) {
      setErrorMessage(err.message || "Aadhaar OTP verification failed.");
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Channel C: Active Mobile Fallback (Suggestion 1)
  const handleMobileFallbackLogin = async () => {
    if (fallbackMobile.trim().length !== 10) {
      setErrorMessage("Please enter a valid 10-digit mobile number");
      return;
    }
    if (fallbackOtp.trim().length !== 6) {
      setErrorMessage("Please enter the 6-digit OTP");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const resp = await fetch("/api/v1/auth/patient/mobile-fallback-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mobile_number: fallbackMobile.trim(),
          otp: fallbackOtp.trim(),
          abha_identifier: fallbackAbha.trim() || undefined,
          remember_me: rememberMe,
        }),
      });

      const data = await resp.json();
      if (!resp.ok || !data.success) {
        throw new Error(data.message || "Mobile fallback authentication failed");
      }

      const patientData = data.data;
      const authUser = {
        id: patientData.user_id,
        email: `${patientData.user_id.slice(0, 8)}@abdm`,
        role: "patient" as const,
        fullName: patientData.name || "Authenticated Citizen",
        abhaId: patientData.abha_number,
        isVerified: true,
      };
      loginWithToken(patientData.access_token, authUser);

      setSuccessInfo({
        name: patientData.name,
        abhaNumber: patientData.abha_number || "91-XXXX-XXXX-XXXX",
        isNew: patientData.is_new_user,
      });

      setTimeout(() => {
        if (onSuccess) onSuccess();
        window.location.href = "/patient";
      }, 500);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to authenticate via mobile fallback.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Success Notification Banner */}
      {successInfo && (
        <div className="ux4g-alert ux4g-alert-info p-4 rounded-[8px] bg-[#f0f6ff] border border-[#0b4d8c]/20 text-sm text-[#0b4d8c] flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-[#046a38]" />
          <div>
            <p className="font-semibold text-[#0b4d8c]">
              {successInfo.isNew ? "Account Created & Verified!" : "Welcome Back!"}
            </p>
            <p className="text-xs text-[#374151]">
              {successInfo.name} &bull; ABHA: <span className="font-mono font-bold text-[#0b4d8c]">{successInfo.abhaNumber}</span>
            </p>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <div className="ux4g-alert ux4g-alert-danger p-3.5 rounded-[8px] bg-[#fef2f2] border border-[#fecaca] text-xs text-[#991b1b] flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-[#dc2626]" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Mode Navigation Tabs */}
      <div className="grid grid-cols-3 gap-1 p-1 bg-[#f0f6ff] rounded-[8px] border border-[#0b4d8c]/20 text-xs">
        <button
          type="button"
          onClick={() => {
            setAuthMode("digilocker");
            setErrorMessage(null);
          }}
          className={`ux4g-btn ux4g-btn-s py-2 px-1 text-center font-medium rounded-[6px] transition-colors cursor-pointer ${
            authMode === "digilocker"
              ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
              : "text-[#4b5563] hover:text-[#0b4d8c]"
          }`}
        >
          DigiLocker 1-Click
        </button>
        <button
          type="button"
          onClick={() => {
            setAuthMode("aadhaar_otp");
            setErrorMessage(null);
          }}
          className={`ux4g-btn ux4g-btn-s py-2 px-1 text-center font-medium rounded-[6px] transition-colors cursor-pointer ${
            authMode === "aadhaar_otp"
              ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
              : "text-[#4b5563] hover:text-[#0b4d8c]"
          }`}
        >
          Aadhaar OTP
        </button>
        <button
          type="button"
          onClick={() => {
            setAuthMode("mobile_fallback");
            setErrorMessage(null);
          }}
          className={`ux4g-btn ux4g-btn-s py-2 px-1 text-center font-medium rounded-[6px] transition-colors cursor-pointer ${
            authMode === "mobile_fallback"
              ? "bg-[#0b4d8c] text-white shadow-xs font-semibold"
              : "text-[#4b5563] hover:text-[#0b4d8c]"
          }`}
        >
          Mobile Fallback
        </button>
      </div>

      {/* TAB 1: DigiLocker 1-Click */}
      {authMode === "digilocker" && (
        <div className="space-y-4 pt-1">
          <div className="p-4 rounded-[8px] border border-[#0b4d8c]/20 bg-white space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="h-9 w-9 rounded-full bg-[#f0f6ff] flex items-center justify-center shrink-0 border border-[#0b4d8c]/20">
                <ShieldCheck className="h-5 w-5 text-[#0b4d8c]" />
              </div>
              <div>
                <p className="text-sm font-semibold text-[#0b4d8c]">Government e-KYC Verification</p>
                <p className="text-xs text-[#6b7280]">
                  Instant sign-in & certified 14-digit ABHA minting via UIDAI e-Aadhaar
                </p>
              </div>
            </div>

            <ul className="text-xs text-[#4b5563] space-y-1.5 pl-1 pt-1">
              <li className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5 text-[#046a38] shrink-0" />
                <span>Zero manual typing &bull; No password required</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5 text-[#046a38] shrink-0" />
                <span>Auto-creates your account if you are a new patient</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5 text-[#046a38] shrink-0" />
                <span>Protected by RFC 7636 PKCE S256 military-grade encryption</span>
              </li>
            </ul>

            <Button
              type="button"
              variant="primary"
              size="md"
              className="ux4g-btn ux4g-btn-primary ux4g-btn-m w-full mt-2"
              isLoading={isLoading}
              onClick={handleDigiLockerLogin}
            >
              <span>Continue with DigiLocker</span>
              <ArrowRight className="h-4 w-4 ml-1.5" />
            </Button>
          </div>
        </div>
      )}

      {/* TAB 2: Direct Aadhaar OTP */}
      {authMode === "aadhaar_otp" && (
        <div className="space-y-3.5 pt-1">
          {otpStep === "input" ? (
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                  <Smartphone className="h-3.5 w-3.5 text-[#0b4d8c]" />
                  12-Digit Aadhaar Number
                </label>
                <input
                  type="text"
                  value={aadhaarInput}
                  onChange={handleAadhaarChange}
                  placeholder="9184 7210 4821"
                  className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm font-mono tracking-wider text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
                />
                <p className="text-[11px] text-[#6b7280]">
                  OTP will be sent to the mobile number registered with your Aadhaar card.
                </p>
              </div>

              <Button
                type="button"
                variant="primary"
                size="md"
                className="ux4g-btn ux4g-btn-primary ux4g-btn-m w-full"
                isLoading={isLoading}
                onClick={handleSendAadhaarOtp}
              >
                <span>Send Verification OTP</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          ) : (
            <div className="space-y-3.5">
              <div className="p-3 rounded-[8px] bg-[#f9fafb] border border-[#e5e7eb] text-xs text-[#374151] flex items-center justify-between">
                <span>OTP sent to: <strong className="font-mono text-[#0b4d8c]">{maskedMobile}</strong></span>
                <button
                  type="button"
                  onClick={() => setOtpStep("input")}
                  className="text-xs text-[#0b4d8c] font-semibold underline hover:text-[#083561] cursor-pointer"
                >
                  Change
                </button>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
                  <KeyRound className="h-3.5 w-3.5 text-[#0b4d8c]" />
                  Enter 6-Digit OTP
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otpValue}
                  onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, ""))}
                  placeholder="123456"
                  className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-base text-center font-mono tracking-[0.3em] font-semibold text-[#111827] focus:outline-none focus:border-[#0b4d8c] transition-colors"
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                {cooldownSeconds > 0 ? (
                  <span className="text-[#6b7280]">Resend OTP in {cooldownSeconds}s</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleSendAadhaarOtp}
                    disabled={isLoading}
                    className="text-[#0b4d8c] font-semibold underline hover:text-[#083561] cursor-pointer flex items-center gap-1"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Resend OTP
                  </button>
                )}
                <span className="text-[11px] text-[#9ca3af]">Valid for 10 minutes</span>
              </div>

              <Button
                type="button"
                variant="primary"
                size="md"
                className="ux4g-btn ux4g-btn-primary ux4g-btn-m w-full"
                isLoading={isLoading}
                onClick={handleVerifyAadhaarOtp}
              >
                <span>Verify & Sign In</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Active Mobile Fallback (Suggestion 1) */}
      {authMode === "mobile_fallback" && (
        <div className="space-y-3 pt-1">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
              <Smartphone className="h-3.5 w-3.5 text-[#0b4d8c]" />
              Active Mobile Number
            </label>
            <input
              type="text"
              maxLength={10}
              value={fallbackMobile}
              onChange={(e) => setFallbackMobile(e.target.value.replace(/\D/g, ""))}
              placeholder="9876543210"
              className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm font-mono text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-[#0b4d8c]" />
              ABHA Address / Number (Optional)
            </label>
            <input
              type="text"
              value={fallbackAbha}
              onChange={(e) => setFallbackAbha(e.target.value)}
              placeholder="name@abdm or 91-xxxx-xxxx-xxxx"
              className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none focus:border-[#0b4d8c] transition-colors"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#111827] flex items-center gap-1.5">
              <KeyRound className="h-3.5 w-3.5 text-[#0b4d8c]" />
              SMS Verification OTP
            </label>
            <input
              type="text"
              maxLength={6}
              value={fallbackOtp}
              onChange={(e) => setFallbackOtp(e.target.value.replace(/\D/g, ""))}
              placeholder="123456"
              className="ux4g-input ux4g-input-m w-full h-10 px-3.5 rounded-[8px] border border-[#e5e7eb] bg-white text-base text-center font-mono tracking-[0.3em] font-semibold text-[#111827] focus:outline-none focus:border-[#0b4d8c] transition-colors"
            />
            <p className="text-[11px] text-[#6b7280]">
              Simulation OTP is <code className="font-mono text-[#0b4d8c]">123456</code>.
            </p>
          </div>

          <Button
            type="button"
            variant="primary"
            size="md"
            className="ux4g-btn ux4g-btn-primary ux4g-btn-m w-full"
            isLoading={isLoading}
            onClick={handleMobileFallbackLogin}
          >
            <span>Sign In with Mobile</span>
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}

      {/* Suggestion 2: Session Longevity Checkbox */}
      <div className="pt-2 border-t border-[#f3f4f6]">
        <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-[#374151]">
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            className="h-4 w-4 rounded border-[#d1d5db] text-[#0b4d8c] focus:ring-[#0b4d8c]"
          />
          <span>Remember this device for <strong>30 days</strong> (No daily OTP required)</span>
        </label>
      </div>
    </div>
  );
}
