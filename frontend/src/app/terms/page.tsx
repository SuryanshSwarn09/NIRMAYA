import React from "react";
import Link from "next/link";
import { Badge, Button, Card, CardTitle, CardDescription } from "@/components/ui";
import { 
  FileText, 
  AlertTriangle, 
  Stethoscope, 
  ShieldAlert, 
  CheckCircle2, 
  Scale, 
  ArrowLeft,
  Building2
} from "lucide-react";

export const metadata = {
  title: "Terms and Conditions | NIRMAYA Health Network",
  description: "Terms of service, clinical liability demarcation, and National Medical Commission telemedicine compliance guidelines for the NIRMAYA Health Network.",
};

export default function TermsAndConditionsPage() {
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
              Health Informatics Platform Terms
            </Badge>
            <Badge variant="default" size="sm">
              NMC Telemedicine Guidelines Aligned
            </Badge>
          </div>

          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#111827]">
            Terms of Service & Clinical Software Charter
          </h1>

          <p className="text-sm text-[#6b7280]">
            Effective Date: {lastUpdated} • Version 2.4 (Clinical Governance Revision)
          </p>
        </div>

        {/* Primary Medical Disclaimer Alert */}
        <div className="p-6 rounded-[8px] bg-[#fffbeb] border border-[#fde68a] space-y-3">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="h-5 w-5 text-[#b45309] shrink-0" />
            <h2 className="text-base font-bold text-[#92400e]">
              Critical Medical Practice Disclaimer
            </h2>
          </div>
          <p className="text-sm leading-relaxed text-[#78350f]">
            NIRMAYA is an interoperable health informatics technology platform engineered to facilitate 
            structured record exchange, longitudinal storage, and scheduling workflows. 
            <strong> NIRMAYA does not provide medical advice, diagnosis, or clinical care. </strong> 
            All clinical evaluations, diagnosis attributions, electronic prescriptions, and laboratory order interpretations 
            are the independent professional responsibility of licensed healthcare practitioners registered 
            with the National Medical Commission (NMC) or relevant State Medical Councils.
          </p>
        </div>

        {/* Structured Sections */}
        <div className="space-y-10 text-sm leading-relaxed text-[#374151]">

          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">01.</span>
              <span>Acceptance of Platform Terms</span>
            </h2>
            <p>
              By accessing or creating an account on the NIRMAYA Health Network (including the Patient Vault, 
              Provider EMR, and Diagnostic Gateway), you agree to be bound by these Terms of Service, our Privacy Policy, 
              and applicable provisions of the Ayushman Bharat Digital Mission (ABDM) guidelines. 
              If you do not accept these terms in their entirety, you must discontinue platform use immediately.
            </p>
          </section>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">02.</span>
              <span>Clinician & Provider Responsibilities (HPR Verification)</span>
            </h2>
            <p>
              Healthcare professionals utilizing the Provider EMR suite must maintain an active, unencumbered license 
              and a valid Healthcare Professional Registry (HPR) identifier. Practitioners warrant and covenant that:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-[#4b5563]">
              <li>All SOAP clinical encounters are documented with clinical veracity based on direct patient interaction.</li>
              <li>Every electronic prescription generated conforms to Schedule L-1 and Schedule H/H1 rules under the Drugs and Cosmetics Act, 1940.</li>
              <li>Digital signatures applied to MedicationRequests and Encounter bundles represent legitimate prescriber attestation under Section 5 of the Information Technology Act, 2000.</li>
              <li>Telemedicine consultations comply with the Board of Governors / NMC Telemedicine Practice Guidelines (March 2020 and subsequent amendments).</li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">03.</span>
              <span>Diagnostic Facility & Laboratory Standards (HFR & NABL)</span>
            </h2>
            <p>
              Diagnostic laboratories operating through the Diagnostic Gateway confirm registration on the Health Facility Registry (HFR) 
              and adherence to NABL ISO 15189 standards. Facilities commit that:
            </p>
            <div className="p-4 rounded-[8px] bg-[#f9fafb] border border-[#e5e7eb] space-y-2 text-xs">
              <div className="flex items-center gap-2 font-semibold text-[#111827]">
                <Building2 className="h-4 w-4 text-[#111111]" />
                <span>Diagnostic Integrity & SHA-256 Tamper Evidence</span>
              </div>
              <p className="text-[#4b5563] leading-relaxed">
                Biochemistry observations, LOINC mappings, and PDF reports uploaded into the network must accurately reflect validated laboratory instruments. 
                Each report is cryptographically hashed with SHA-256 upon ingestion to establish legal evidentiary chain of custody.
              </p>
            </div>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">04.</span>
              <span>Patient Sovereignty & Acceptable Use</span>
            </h2>
            <p>
              Patient users access longitudinal records through authenticated ABHA identity tokens. Users agree to:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-[#4b5563]">
              <li>Provide accurate identification information during ABHA credential pairing.</li>
              <li>Maintain the confidentiality of their session access tokens and multi-factor authenticators.</li>
              <li>Refrain from attempting automated penetration testing, unauthorized vulnerability scanning, or data extraction on the FHIR API endpoints.</li>
            </ul>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-[#111827] flex items-center gap-2">
              <span className="text-[#6b7280] font-mono text-xs">05.</span>
              <span>Limitation of Liability & Service Availability</span>
            </h2>
            <p>
              NIRMAYA is provided on an &quot;as is&quot; and &quot;as available&quot; basis for academic, demonstration, and operational health informatics deployments. 
              To the maximum extent permitted under applicable law, NIRMAYA and its developers shall not be liable for any direct, indirect, incidental, 
              or consequential damages resulting from telecommunication delays, medical treatment outcomes, or technical unavailability during emergency scenarios. 
              <strong> In life-threatening emergencies, patients must immediately contact emergency services (National Helpline 1075 / 112) or visit the nearest physical emergency department.</strong>
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-3 pt-4 border-t border-[#e5e7eb]">
            <h2 className="text-base font-bold text-[#111827] flex items-center gap-2">
              <Scale className="h-4 w-4 text-[#111111]" />
              <span>Governing Law & Dispute Resolution</span>
            </h2>
            <p className="text-xs text-[#6b7280] leading-relaxed">
              These Terms of Service are governed by and construed in accordance with the laws of the Republic of India. 
              Any disputes arising out of or in connection with the platform shall be subject to the exclusive jurisdiction 
              of the courts located in New Delhi, India.
            </p>
          </section>

        </div>

        {/* Back Link */}
        <div className="pt-6 border-t border-[#e5e7eb] flex justify-between items-center text-xs text-[#6b7280]">
          <span>NIRMAYA Health Network • Open Standards Health Informatics</span>
          <Link href="/privacy" className="font-semibold text-[#111111] hover:underline">
            Read Privacy Policy →
          </Link>
        </div>

      </div>
    </div>
  );
}
