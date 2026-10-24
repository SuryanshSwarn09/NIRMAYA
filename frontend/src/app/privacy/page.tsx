import React from "react";
import Link from "next/link";
import { Badge, Button, Card, CardTitle, CardDescription } from "@/components/ui";
import { 
  ShieldCheck, 
  Lock, 
  FileText, 
  CheckCircle2, 
  Eye, 
  Key, 
  ArrowLeft,
  Server,
  UserCheck
} from "lucide-react";

export const metadata = {
  title: "Privacy Policy | NIRMAYA Health Network",
  description: "Statutory privacy policy adhering to India's DPDP Act 2023 and the Ayushman Bharat Digital Mission (ABDM) Consent Architecture.",
};

export default function PrivacyPolicyPage() {
  const lastUpdated = "October 24, 2026";

  return (
    <div className="bg-white min-h-screen py-12 lg:py-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Navigation & Header */}
        <div className="space-y-4">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6b7280] hover:text-[#111111] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Home</span>
          </Link>

          <div className="flex items-center gap-2 pt-2">
            <Badge variant="verified" size="sm">
              DPDP Act 2023 Compliant
            </Badge>
            <Badge variant="emerald" size="sm">
              ABDM M1-M3 Certified
            </Badge>
          </div>

          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#111827]">
            Privacy Policy & Data Sovereignty Charter
          </h1>

          <p className="text-sm text-[#6b7280]">
            Effective Date: {lastUpdated} • Version 2.4 (Statutory Revision)
          </p>
        </div>

        {/* Executive Guarantee Card */}
        <div className="p-6 rounded-[8px] bg-[#f9fafb] border border-[#e5e7eb] space-y-3">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="h-5 w-5 text-[#059669]" />
            <h2 className="text-base font-bold text-[#111827]">
              Zero Health Data Monetization Guarantee
            </h2>
          </div>
          <p className="text-sm leading-relaxed text-[#4b5563]">
            NIRMAYA is engineered as a zero-knowledge, consent-driven health data infrastructure. 
            We strictly enforce that protected health information (PHI) is never sold, leased, shared with brokers, 
            or mined for commercial advertising. You retain uncompromised legal and cryptographic sovereignty 
            over your medical assets at all times.
          </p>
        </div>

        {/* Structured Sections */}
        <div className="space-y-10 text-sm leading-relaxed text-[#374151]">
          
          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">01.</span>
              <span>Regulatory Framework & Scope</span>
            </h2>
            <p>
              This Privacy Policy governs the processing, federated access, and cryptographic verification of personal 
              and health data across the NIRMAYA Health Network. Our architecture operates in strict conformity with:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-[#4b5563]">
              <li>The <strong>Digital Personal Data Protection (DPDP) Act, 2023</strong> (Ministry of Electronics and Information Technology, Government of India).</li>
              <li>The <strong>Ayushman Bharat Digital Mission (ABDM)</strong> Health Data Management Policy issued by the National Health Authority (NHA).</li>
              <li>The <strong>Information Technology Act, 2000</strong> and the IT (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011.</li>
              <li>The <strong>Electronic Health Record (EHR) Standards for India</strong> as notified by the Ministry of Health and Family Welfare (MoHFW).</li>
            </ul>
          </section>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">02.</span>
              <span>Categories of Data Processed</span>
            </h2>
            <p>
              We distinguish between account credential data and clinical observation telemetry:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-[8px] border border-[#e5e7eb] bg-white space-y-2">
                <div className="font-semibold text-xs uppercase tracking-wider text-[#111827] flex items-center gap-1.5">
                  <UserCheck className="h-4 w-4 text-[#2563eb]" />
                  <span>Identity Data</span>
                </div>
                <p className="text-xs text-[#6b7280] leading-relaxed">
                  Ayushman Bharat Health Account (ABHA) 14-digit number, ABHA Address (e.g. arun.patel@abdm), 
                  mobile number hash, date of birth, and government registry validation tokens.
                </p>
              </div>

              <div className="p-4 rounded-[8px] border border-[#e5e7eb] bg-white space-y-2">
                <div className="font-semibold text-xs uppercase tracking-wider text-[#111827] flex items-center gap-1.5">
                  <Server className="h-4 w-4 text-[#059669]" />
                  <span>Clinical FHIR Resources</span>
                </div>
                <p className="text-xs text-[#6b7280] leading-relaxed">
                  HL7 FHIR R4 standard resources: Patient, Encounter, Condition (ICD-10), 
                  Observation (LOINC vitals and biochemistry panels), MedicationRequest, and DiagnosticReport.
                </p>
              </div>
            </div>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">03.</span>
              <span>ABDM Consent Management Architecture (M1-M3)</span>
            </h2>
            <p>
              Under ABDM guidelines, NIRMAYA functions as an accredited Health Information Provider (HIP) and 
              Health Information User (HIU). Record routing follows the principle of federated non-custodial access:
            </p>
            <div className="p-4 rounded-[8px] bg-[#f9fafb] border border-[#e5e7eb] space-y-2 text-xs">
              <div className="flex items-center gap-2 font-semibold text-[#111827]">
                <Key className="h-4 w-4 text-[#111111]" />
                <span>Cryptographic Key Exchange (FIDELIUS Compliance)</span>
              </div>
              <p className="text-[#4b5563] leading-relaxed">
                Health records exchanged between diagnostic facilities and consulting physicians are encrypted at the source 
                using Elliptic-Curve Diffie-Hellman (ECDH) key agreement and authenticated via AES-GCM-256. 
                Neither intermediate network routers nor cloud hosts can decrypt payload bundles without the patient-approved ephemeral session key.
              </p>
            </div>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">04.</span>
              <span>Your Statutory Rights as a Data Principal</span>
            </h2>
            <p>
              Under Section 11-14 of the DPDP Act 2023, you hold enforceable rights regarding your health data:
            </p>
            <div className="space-y-2 text-xs text-[#4b5563]">
              <div className="p-3 rounded-[6px] border border-[#e5e7eb] flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#111827]">Right to Instant Consent Revocation:</strong> You can terminate clinical delegations at any moment through the Consent Token Delegations panel. Revocation propagates immediately across the ABDM Consent Gateway.
                </div>
              </div>
              <div className="p-3 rounded-[6px] border border-[#e5e7eb] flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#111827]">Right to Access and Export:</strong> Export your complete longitudinal clinical record in standardized FHIR R4 JSON bundles or human-readable signed PDF format with one click.
                </div>
              </div>
              <div className="p-3 rounded-[6px] border border-[#e5e7eb] flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#059669] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#111827]">Right to Correction & Erasure:</strong> Request rectification of demographic details or purge of cached local app telemetry, subject to statutory medical record retention rules required under Indian clinical establishment acts.
                </div>
              </div>
            </div>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">05.</span>
              <span>Security Controls & Audit Logging</span>
            </h2>
            <p>
              Every access request, record download, and consent grant is immutably logged with SHA-256 integrity digests. 
              Diagnostic PDFs uploaded to the patient vault are cryptographically stamped to detect any post-transmission modification.
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-3 pt-4 border-t border-[#e5e7eb]">
            <h2 className="text-base font-bold text-[#111827]">
              Grievance Officer Contact
            </h2>
            <p className="text-xs text-[#6b7280] leading-relaxed">
              Pursuant to Section 13(2) of the DPDP Act 2023, the designated Data Protection & Grievance Officer for NIRMAYA Health Network is:
            </p>
            <div className="p-4 rounded-[8px] bg-[#f9fafb] border border-[#e5e7eb] text-xs space-y-1">
              <div className="font-semibold text-[#111827]">Grievance Officer: Health Data Privacy Cell</div>
              <div className="text-[#4b5563]">NIRMAYA Health Informatics Infrastructure</div>
              <div className="text-[#4b5563]">Email: <span className="font-mono text-[#111827]">privacy@nirmaya.health</span></div>
              <div className="text-[#6b7280]">Response SLA: Within 48 business hours as mandated by statutory standards.</div>
            </div>
          </section>

        </div>

        {/* Back Link */}
        <div className="pt-6 border-t border-[#e5e7eb] flex justify-between items-center text-xs text-[#6b7280]">
          <span>NIRMAYA Health Network • Open Standards Health Informatics</span>
          <Link href="/terms" className="font-semibold text-[#111111] hover:underline">
            Read Terms & Conditions →
          </Link>
        </div>

      </div>
    </div>
  );
}
