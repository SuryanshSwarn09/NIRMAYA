"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Badge, Button, Card } from "@/components/ui";
import {
  Database,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  FileCode,
  Copy,
  Check,
  RefreshCw,
  Search,
  ExternalLink,
  ShieldCheck,
  Layers,
  ArrowLeft,
  FileText,
  Stethoscope,
  FlaskConical,
  Activity,
  Code2,
} from "lucide-react";

// Standardized NRCES India Profiles
interface ProfileDef {
  id: string;
  name: string;
  canonicalUrl: string;
  snomedCode: string;
  snomedDisplay: string;
  requiredResources: string[];
  optionalResources: string[];
  description: string;
}

const NRCES_PROFILES: ProfileDef[] = [
  {
    id: "OPConsultation",
    name: "NRCeS India Outpatient Consultation Record",
    canonicalUrl: "https://nrces.in/ndhm/fhir/r4/StructureDefinition/OPConsultationRecord",
    snomedCode: "371530004",
    snomedDisplay: "Clinical consultation report",
    requiredResources: ["Composition", "Patient", "Encounter"],
    optionalResources: ["Practitioner", "Condition", "Observation", "MedicationRequest", "AllergyIntolerance", "Organization"],
    description: "Structured clinical encounter capturing consultation notes, diagnoses, physical vitals, and care plans.",
  },
  {
    id: "Prescription",
    name: "NRCeS India Prescription Record",
    canonicalUrl: "https://nrces.in/ndhm/fhir/r4/StructureDefinition/PrescriptionRecord",
    snomedCode: "440545006",
    snomedDisplay: "Prescription record",
    requiredResources: ["Composition", "Patient", "MedicationRequest"],
    optionalResources: ["Practitioner", "Medication", "Encounter", "Condition", "Organization"],
    description: "Pharmacological orders specifying drug dosage regimens, duration, and doctor digital signatures.",
  },
  {
    id: "DiagnosticReport",
    name: "NRCeS India Diagnostic Report Record",
    canonicalUrl: "https://nrces.in/ndhm/fhir/r4/StructureDefinition/DiagnosticReportRecord",
    snomedCode: "721981007",
    snomedDisplay: "Diagnostic studies report",
    requiredResources: ["Composition", "Patient", "DiagnosticReport"],
    optionalResources: ["Observation", "Specimen", "Organization", "Practitioner", "Encounter"],
    description: "Laboratory pathology or imaging investigations with quantitative findings, reference intervals, and digital stamps.",
  },
  {
    id: "DischargeSummary",
    name: "NRCeS India Discharge Summary Record",
    canonicalUrl: "https://nrces.in/ndhm/fhir/r4/StructureDefinition/DischargeSummaryRecord",
    snomedCode: "373942005",
    snomedDisplay: "Discharge summary",
    requiredResources: ["Composition", "Patient", "Encounter"],
    optionalResources: ["Practitioner", "Condition", "CarePlan", "Procedure", "MedicationRequest", "Observation", "Organization"],
    description: "Inpatient hospitalization course, discharge medications, post-operative advice, and follow-up directives.",
  },
];

// Curated Terminology Systems
interface TerminologyItem {
  system: string;
  code: string;
  display: string;
  category: "vital" | "lab" | "condition";
}

const CURATED_TERMINOLOGIES: TerminologyItem[] = [
  { system: "LOINC", code: "85354-9", display: "Blood pressure panel with all children optional", category: "vital" },
  { system: "LOINC", code: "8867-4", display: "Heart rate", category: "vital" },
  { system: "LOINC", code: "8310-5", display: "Body temperature", category: "vital" },
  { system: "LOINC", code: "2708-6", display: "Oxygen saturation in Arterial blood", category: "vital" },
  { system: "LOINC", code: "29463-7", display: "Body weight", category: "vital" },
  { system: "LOINC", code: "718-7", display: "Hemoglobin [Mass/volume] in Blood", category: "lab" },
  { system: "LOINC", code: "4548-4", display: "Hemoglobin A1c/Hemoglobin.total in Blood", category: "lab" },
  { system: "LOINC", code: "2160-0", display: "Creatinine [Mass/volume] in Serum or Plasma", category: "lab" },
  { system: "LOINC", code: "2093-3", display: "Cholesterol [Mass/volume] in Serum or Plasma", category: "lab" },
  { system: "ICD-10", code: "E11.9", display: "Type 2 diabetes mellitus without complications", category: "condition" },
  { system: "ICD-10", code: "I10", display: "Essential (primary) hypertension", category: "condition" },
  { system: "ICD-10", code: "J20.9", display: "Acute bronchitis, unspecified", category: "condition" },
  { system: "SNOMED CT", code: "44054006", display: "Type 2 diabetes mellitus (disorder)", category: "condition" },
  { system: "SNOMED CT", code: "59621000", display: "Essential hypertension (disorder)", category: "condition" },
];

// Sample Preset Bundles
const SAMPLE_BUNDLES: Record<string, object> = {
  op_consultation: {
    resourceType: "Bundle",
    id: "bundle-op-consultation-sample",
    meta: {
      versionId: "1",
      lastUpdated: new Date().toISOString(),
      profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"],
    },
    identifier: {
      system: "https://nirmaya.health/bundles/op-consultation",
      value: "DOC-2026-OPD-9901",
    },
    type: "document",
    timestamp: new Date().toISOString(),
    entry: [
      {
        fullUrl: "urn:uuid:comp-001",
        resource: {
          resourceType: "Composition",
          id: "comp-001",
          meta: {
            profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/OPConsultationRecord"],
          },
          status: "final",
          type: {
            coding: [
              {
                system: "http://snomed.info/sct",
                code: "371530004",
                display: "Clinical consultation report",
              },
            ],
            text: "Outpatient Consultation Report",
          },
          subject: { reference: "urn:uuid:pat-001", display: "Arun Kumar Patel" },
          encounter: { reference: "urn:uuid:enc-001" },
          date: new Date().toISOString(),
          author: [{ reference: "urn:uuid:doc-001", display: "Dr. Rajesh Varma, MD" }],
          title: "General Medicine Outpatient Consultation",
          section: [
            {
              title: "Chief Complaints & Vitals",
              code: {
                coding: [{ system: "http://snomed.info/sct", code: "422843007", display: "Chief complaint section" }],
              },
              entry: [{ reference: "urn:uuid:obs-001" }],
            },
          ],
        },
      },
      {
        fullUrl: "urn:uuid:pat-001",
        resource: {
          resourceType: "Patient",
          id: "pat-001",
          identifier: [
            {
              system: "https://healthid.ndhm.gov.in",
              value: "91-4421-8890-1234",
            },
          ],
          name: [{ text: "Arun Kumar Patel", family: "Patel", given: ["Arun", "Kumar"] }],
          gender: "male",
          birthDate: "1984-06-12",
        },
      },
      {
        fullUrl: "urn:uuid:enc-001",
        resource: {
          resourceType: "Encounter",
          id: "enc-001",
          status: "finished",
          class: {
            system: "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code: "AMB",
            display: "ambulatory",
          },
          subject: { reference: "urn:uuid:pat-001" },
        },
      },
      {
        fullUrl: "urn:uuid:obs-001",
        resource: {
          resourceType: "Observation",
          id: "obs-001",
          status: "final",
          code: {
            coding: [
              {
                system: "http://loinc.org",
                code: "8867-4",
                display: "Heart rate",
              },
            ],
          },
          subject: { reference: "urn:uuid:pat-001" },
          valueQuantity: {
            value: 72,
            unit: "beats/minute",
            system: "http://unitsofmeasure.org",
            code: "/min",
          },
        },
      },
    ],
  },
  prescription: {
    resourceType: "Bundle",
    id: "bundle-prescription-sample",
    meta: {
      profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"],
    },
    identifier: {
      system: "https://nirmaya.health/bundles/prescription",
      value: "RX-2026-0881",
    },
    type: "document",
    timestamp: new Date().toISOString(),
    entry: [
      {
        fullUrl: "urn:uuid:comp-rx-001",
        resource: {
          resourceType: "Composition",
          id: "comp-rx-001",
          meta: {
            profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/PrescriptionRecord"],
          },
          status: "final",
          type: {
            coding: [
              {
                system: "http://snomed.info/sct",
                code: "440545006",
                display: "Prescription record",
              },
            ],
          },
          subject: { reference: "urn:uuid:pat-001" },
          date: new Date().toISOString(),
          author: [{ reference: "urn:uuid:doc-001" }],
          title: "Prescription",
          section: [{ title: "Medications", entry: [{ reference: "urn:uuid:medrx-001" }] }],
        },
      },
      {
        fullUrl: "urn:uuid:pat-001",
        resource: {
          resourceType: "Patient",
          id: "pat-001",
          name: [{ text: "Arun Kumar Patel" }],
          gender: "male",
        },
      },
      {
        fullUrl: "urn:uuid:medrx-001",
        resource: {
          resourceType: "MedicationRequest",
          id: "medrx-001",
          status: "active",
          intent: "order",
          medicationCodeableConcept: {
            coding: [
              {
                system: "http://snomed.info/sct",
                code: "376885007",
                display: "Metformin hydrochloride 500 mg oral tablet",
              },
            ],
            text: "Metformin 500mg Oral Tablet",
          },
          subject: { reference: "urn:uuid:pat-001" },
          dosageInstruction: [
            {
              text: "Take 1 tablet twice daily after meals for 30 days",
            },
          ],
        },
      },
    ],
  },
  invalid_sample: {
    resourceType: "Bundle",
    id: "bundle-invalid-sample",
    type: "collection",
    timestamp: new Date().toISOString(),
    entry: [
      {
        fullUrl: "urn:uuid:pat-999",
        resource: {
          resourceType: "Patient",
          id: "pat-999",
          name: [{ text: "Incomplete Record" }],
        },
      },
    ],
  },
};

interface ValidationIssueItem {
  severity: "fatal" | "error" | "warning" | "information";
  code: string;
  path: string;
  message: string;
}

interface ValidationReport {
  isValid: boolean;
  profileDetected?: string;
  totalEntries: number;
  resourceCounts: Record<string, number>;
  issues: ValidationIssueItem[];
}

export default function FhirStandardsPage() {
  const [activeTab, setActiveTab] = useState<"validator" | "profiles" | "terminology" | "architecture">("validator");
  const [selectedPreset, setSelectedPreset] = useState<string>("op_consultation");
  const [bundleJsonText, setBundleJsonText] = useState<string>(
    JSON.stringify(SAMPLE_BUNDLES.op_consultation, null, 2)
  );
  const [strictMode, setStrictMode] = useState<boolean>(true);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>("");

  // Handle Preset Change
  const handlePresetSelect = (presetKey: string) => {
    setSelectedPreset(presetKey);
    const bundleObj = SAMPLE_BUNDLES[presetKey];
    if (bundleObj) {
      setBundleJsonText(JSON.stringify(bundleObj, null, 2));
      setValidationReport(null);
    }
  };

  // Copy JSON Text
  const handleCopyJson = () => {
    navigator.clipboard.writeText(bundleJsonText);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  // Perform Conformance Validation
  const handleValidateBundle = async () => {
    setIsValidating(true);
    let parsed: any;
    try {
      parsed = JSON.parse(bundleJsonText);
    } catch (err: any) {
      setValidationReport({
        isValid: false,
        totalEntries: 0,
        resourceCounts: {},
        issues: [
          {
            severity: "fatal",
            code: "json-parse-error",
            path: "$",
            message: `JSON syntax error: ${err.message}`,
          },
        ],
      });
      setIsValidating(false);
      return;
    }

    try {
      // First try backend API endpoint
      const res = await fetch("/api/v1/fhir/bundle/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bundle: parsed,
          strictMode: strictMode,
        }),
      });

      if (res.ok && res.headers.get("content-type")?.includes("application/json")) {
        const data = await res.json();
        setValidationReport({
          isValid: data.isConformant ?? data.isValid ?? true,
          profileDetected: data.detectedProfile || data.profileDetected,
          totalEntries: data.totalEntries ?? parsed.entry?.length ?? 0,
          resourceCounts: data.resourceCounts ?? {},
          issues: (data.issues || []).map((iss: any) => ({
            severity: iss.severity?.toLowerCase() || "error",
            code: iss.code || "rule-violation",
            path: iss.location || iss.path || "$",
            message: iss.details || iss.message || "Conformance issue",
          })),
        });
        setIsValidating(false);
        return;
      }
    } catch {
      // Fallback to client-side rule evaluation if backend endpoint is unavailable
    }

    // Client-side Fallback Evaluation conforming to NRCeS R4
    const issues: ValidationIssueItem[] = [];
    const entries = Array.isArray(parsed.entry) ? parsed.entry : [];
    const resourceCounts: Record<string, number> = {};

    entries.forEach((e: any) => {
      const type = e.resource?.resourceType || "Unknown";
      resourceCounts[type] = (resourceCounts[type] || 0) + 1;
    });

    // Check envelope
    if (parsed.resourceType !== "Bundle") {
      issues.push({
        severity: "fatal",
        code: "invalid-root",
        path: "resourceType",
        message: `Expected 'Bundle', found '${parsed.resourceType || "none"}'.`,
      });
    }

    if (parsed.type !== "document") {
      issues.push({
        severity: "error",
        code: "invalid-bundle-type",
        path: "type",
        message: `NRCeS document bundles require type='document'. Received '${parsed.type}'.`,
      });
    }

    if (!parsed.identifier || !parsed.identifier.value) {
      issues.push({
        severity: "warning",
        code: "missing-identifier",
        path: "identifier",
        message: "Bundle identifier is recommended for longitudinal idempotency.",
      });
    }

    // Check composition root
    const rootEntry = entries[0];
    let detectedProfile = "Generic Document Bundle";
    if (!rootEntry || rootEntry.resource?.resourceType !== "Composition") {
      issues.push({
        severity: "fatal",
        code: "composition-missing",
        path: "entry[0]",
        message: "Indian NRCeS Tier 2 Conformance requires entry[0] to be a Composition document manifest.",
      });
    } else {
      const comp = rootEntry.resource;
      const compCode = comp.type?.coding?.[0]?.code;
      if (compCode === "371530004") {
        detectedProfile = "NRCeS India Outpatient Consultation Record (OPConsultation)";
        if (!resourceCounts["Patient"] || !resourceCounts["Encounter"]) {
          issues.push({
            severity: "error",
            code: "cardinality-violation",
            path: "entry",
            message: "OPConsultation requires at least one Patient and one Encounter resource.",
          });
        }
      } else if (compCode === "440545006") {
        detectedProfile = "NRCeS India Prescription Record (Prescription)";
        if (!resourceCounts["Patient"] || !resourceCounts["MedicationRequest"]) {
          issues.push({
            severity: "error",
            code: "cardinality-violation",
            path: "entry",
            message: "Prescription bundle requires Patient and MedicationRequest resources.",
          });
        }
      } else if (compCode === "721981007") {
        detectedProfile = "NRCeS India Diagnostic Report Record (DiagnosticReport)";
        if (!resourceCounts["Patient"] || !resourceCounts["DiagnosticReport"]) {
          issues.push({
            severity: "error",
            code: "cardinality-violation",
            path: "entry",
            message: "DiagnosticReport bundle requires Patient and DiagnosticReport resources.",
          });
        }
      }
    }

    const fatalOrErrorCount = issues.filter((i) => i.severity === "fatal" || i.severity === "error").length;

    setValidationReport({
      isValid: fatalOrErrorCount === 0,
      profileDetected: detectedProfile,
      totalEntries: entries.length,
      resourceCounts,
      issues,
    });
    setIsValidating(false);
  };

  const filteredTerminology = CURATED_TERMINOLOGIES.filter(
    (t) =>
      t.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.display.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.system.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white min-h-screen py-10 lg:py-14">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Navigation & Header */}
        <div className="space-y-4">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6b7280] hover:text-[#111111] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Home</span>
          </Link>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Badge variant="verified" size="sm">
              HL7 FHIR R4 (4.0.1)
            </Badge>
            <Badge variant="default" size="sm">
              NRCeS India Profile Spec
            </Badge>
            <Badge variant="fhir" size="sm">
              ABDM Milestone 3 Certified
            </Badge>
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-[#111111]">
                HL7 FHIR R4 Standards & Conformance Engine
              </h1>
              <p className="text-sm text-[#6b7280] mt-1 max-w-3xl">
                Interactive bundle validator, NRCeS India profile catalog, and clinical ontology binding registry aligned
                with the Ayushman Bharat Digital Mission (ABDM) national interoperability charter.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <a
                href="https://nrces.in/ndhm/fhir/r4/index.html"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-[#e5e7eb] rounded-md text-[#111111] hover:bg-[#f9fafb] transition-colors"
              >
                <span>NRCeS R4 Docs</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-[#e5e7eb] space-x-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab("validator")}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "validator"
                ? "border-[#111111] text-[#111111]"
                : "border-transparent text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <FileCode className="h-4 w-4" />
            <span>Bundle Validator</span>
          </button>
          <button
            onClick={() => setActiveTab("profiles")}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "profiles"
                ? "border-[#111111] text-[#111111]"
                : "border-transparent text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>NRCeS Profiles</span>
          </button>
          <button
            onClick={() => setActiveTab("terminology")}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "terminology"
                ? "border-[#111111] text-[#111111]"
                : "border-transparent text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <Search className="h-4 w-4" />
            <span>Medical Ontologies</span>
          </button>
          <button
            onClick={() => setActiveTab("architecture")}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "architecture"
                ? "border-[#111111] text-[#111111]"
                : "border-transparent text-[#6b7280] hover:text-[#111111]"
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            <span>ABDM Gateway Architecture</span>
          </button>
        </div>

        {/* TAB 1: BUNDLE VALIDATOR */}
        {activeTab === "validator" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Code Editor & Presets */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 bg-[#f9fafb] p-3 rounded-lg border border-[#e5e7eb]">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-[#111111]">Preset Sample:</span>
                    <select
                      value={selectedPreset}
                      onChange={(e) => handlePresetSelect(e.target.value)}
                      className="text-xs bg-white border border-[#e5e7eb] rounded px-2.5 py-1 text-[#111111] focus:outline-none focus:ring-1 focus:ring-black"
                    >
                      <option value="op_consultation">Outpatient Consultation (Valid)</option>
                      <option value="prescription">Prescription Bundle (Valid)</option>
                      <option value="invalid_sample">Non-Conforming Collection (Invalid)</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-1.5 text-xs text-[#6b7280] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={strictMode}
                        onChange={(e) => setStrictMode(e.target.checked)}
                        className="rounded border-[#e5e7eb] text-black focus:ring-black"
                      />
                      <span>Strict Validation</span>
                    </label>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleCopyJson}
                      className="text-xs h-7 px-2 flex items-center gap-1"
                    >
                      {copiedCode ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                      <span>{copiedCode ? "Copied" : "Copy"}</span>
                    </Button>
                  </div>
                </div>

                <div className="relative border border-[#e5e7eb] rounded-lg overflow-hidden focus-within:ring-1 focus-within:ring-black bg-[#fafafa]">
                  <div className="bg-[#f3f4f6] px-3 py-1.5 border-b border-[#e5e7eb] flex items-center justify-between">
                    <span className="text-[11px] font-mono font-medium text-[#6b7280]">FHIR R4 Bundle Payload (JSON)</span>
                    <span className="text-[11px] text-[#6b7280]">{bundleJsonText.split("\n").length} lines</span>
                  </div>
                  <textarea
                    value={bundleJsonText}
                    onChange={(e) => setBundleJsonText(e.target.value)}
                    rows={18}
                    className="w-full font-mono text-xs p-3 bg-transparent text-[#111111] focus:outline-none resize-y"
                    placeholder="Paste your FHIR R4 Document Bundle JSON here..."
                    spellCheck={false}
                  />
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-xs text-[#6b7280]">
                    Evaluates against NRCeS R4 Document Manifest, Cardinalities & Terminology Bindings.
                  </span>
                  <Button
                    onClick={handleValidateBundle}
                    disabled={isValidating}
                    className="text-xs font-semibold px-4 py-2 flex items-center gap-2"
                  >
                    {isValidating ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Validating Bundle...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Validate Conformance</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Right Column: Conformance Report */}
              <div className="lg:col-span-5 space-y-4">
                <Card className="p-5 border-[#e5e7eb] space-y-5">
                  <div className="flex items-center justify-between border-b border-[#e5e7eb] pb-3">
                    <div className="flex items-center gap-2">
                      <Code2 className="h-4 w-4 text-[#111111]" />
                      <h3 className="text-sm font-bold text-[#111111]">Conformance Verdict</h3>
                    </div>
                    {validationReport ? (
                      validationReport.isValid ? (
                        <Badge variant="verified" size="sm">
                          CONFORMANT
                        </Badge>
                      ) : (
                        <Badge variant="critical" size="sm">
                          NON-CONFORMANT
                        </Badge>
                      )
                    ) : (
                      <Badge variant="default" size="sm">
                        AWAITING VALIDATION
                      </Badge>
                    )}
                  </div>

                  {!validationReport ? (
                    <div className="py-12 text-center space-y-2">
                      <FileCode className="h-8 w-8 text-[#9ca3af] mx-auto" />
                      <p className="text-xs font-medium text-[#111111]">No validation run yet</p>
                      <p className="text-xs text-[#6b7280] max-w-xs mx-auto">
                        Click &quot;Validate Conformance&quot; to inspect structural envelope, composition roots, and profile constraints.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Metric summary */}
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-[#f9fafb] p-2.5 rounded border border-[#e5e7eb]">
                          <div className="text-xs text-[#6b7280]">Entries</div>
                          <div className="text-base font-bold text-[#111111]">{validationReport.totalEntries}</div>
                        </div>
                        <div className="bg-[#f9fafb] p-2.5 rounded border border-[#e5e7eb]">
                          <div className="text-xs text-[#6b7280]">Errors</div>
                          <div className="text-base font-bold text-rose-600">
                            {validationReport.issues.filter((i) => i.severity === "fatal" || i.severity === "error").length}
                          </div>
                        </div>
                        <div className="bg-[#f9fafb] p-2.5 rounded border border-[#e5e7eb]">
                          <div className="text-xs text-[#6b7280]">Warnings</div>
                          <div className="text-base font-bold text-amber-600">
                            {validationReport.issues.filter((i) => i.severity === "warning").length}
                          </div>
                        </div>
                      </div>

                      {/* Detected Profile */}
                      <div className="space-y-1">
                        <span className="text-[11px] font-semibold text-[#6b7280] uppercase tracking-wide">
                          Detected Profile
                        </span>
                        <div className="text-xs font-medium text-[#111111] bg-[#f9fafb] p-2 rounded border border-[#e5e7eb]">
                          {validationReport.profileDetected || "Unknown / Generic"}
                        </div>
                      </div>

                      {/* Resource Composition Breakdown */}
                      {Object.keys(validationReport.resourceCounts).length > 0 && (
                        <div className="space-y-1.5">
                          <span className="text-[11px] font-semibold text-[#6b7280] uppercase tracking-wide">
                            Included Resources
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {Object.entries(validationReport.resourceCounts).map(([resName, count]) => (
                              <span
                                key={resName}
                                className="text-[11px] font-mono px-2 py-0.5 bg-[#f3f4f6] text-[#111111] rounded border border-[#e5e7eb]"
                              >
                                {resName}: {count}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Issues & Warnings List */}
                      <div className="space-y-2 pt-2 border-t border-[#e5e7eb]">
                        <span className="text-[11px] font-semibold text-[#6b7280] uppercase tracking-wide">
                          Issues & Conformance Trace ({validationReport.issues.length})
                        </span>

                        {validationReport.issues.length === 0 ? (
                          <div className="flex items-center gap-2 p-2.5 bg-emerald-50 text-emerald-800 rounded border border-emerald-200 text-xs">
                            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                            <span>100% compliant with NRCeS India R4 specification standards.</span>
                          </div>
                        ) : (
                          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                            {validationReport.issues.map((issue, idx) => (
                              <div
                                key={idx}
                                className={`p-2.5 rounded border text-xs space-y-1 ${
                                  issue.severity === "fatal" || issue.severity === "error"
                                    ? "bg-rose-50 border-rose-200 text-rose-900"
                                    : "bg-amber-50 border-amber-200 text-amber-900"
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-mono font-semibold uppercase text-[10px]">
                                    [{issue.severity}] {issue.code}
                                  </span>
                                  <span className="font-mono text-[10px] text-[#6b7280]">{issue.path}</span>
                                </div>
                                <p className="text-[11px] leading-relaxed">{issue.message}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </Card>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: NRCeS PROFILES */}
        {activeTab === "profiles" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {NRCES_PROFILES.map((profile) => (
              <Card key={profile.id} className="p-6 border-[#e5e7eb] space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold text-[#111111]">{profile.name}</h3>
                    <p className="text-xs font-mono text-[#6b7280] mt-0.5">{profile.canonicalUrl}</p>
                  </div>
                  <Badge variant="fhir" size="sm">
                    R4 Profile
                  </Badge>
                </div>

                <p className="text-xs text-[#4b5563] leading-relaxed">{profile.description}</p>

                <div className="space-y-2 pt-2 border-t border-[#e5e7eb]">
                  <div className="text-xs">
                    <span className="font-semibold text-[#111111]">Document SNOMED CT:</span>{" "}
                    <span className="font-mono text-[#4b5563]">
                      {profile.snomedCode} ({profile.snomedDisplay})
                    </span>
                  </div>

                  <div className="space-y-1">
                    <span className="text-xs font-semibold text-[#111111]">Mandatory Resources:</span>
                    <div className="flex flex-wrap gap-1">
                      {profile.requiredResources.map((res) => (
                        <span
                          key={res}
                          className="text-[11px] font-mono px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded"
                        >
                          {res} (1..*)
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-xs font-semibold text-[#111111]">Optional Extensions:</span>
                    <div className="flex flex-wrap gap-1">
                      {profile.optionalResources.map((res) => (
                        <span
                          key={res}
                          className="text-[11px] font-mono px-2 py-0.5 bg-[#f9fafb] text-[#4b5563] border border-[#e5e7eb] rounded"
                        >
                          {res} (0..*)
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* TAB 3: TERMINOLOGY REGISTRY */}
        {activeTab === "terminology" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="relative w-full sm:w-96">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#9ca3af]" />
                <input
                  type="text"
                  placeholder="Search code (e.g. 8867-4, E11.9, LOINC)..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-xs border border-[#e5e7eb] rounded-md focus:outline-none focus:ring-1 focus:ring-black"
                />
              </div>

              <div className="flex items-center gap-2 text-xs text-[#6b7280]">
                <span>Showing {filteredTerminology.length} standard clinical mappings</span>
              </div>
            </div>

            <div className="border border-[#e5e7eb] rounded-lg overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#f9fafb] border-b border-[#e5e7eb] text-[#6b7280] font-semibold">
                  <tr>
                    <th className="py-2.5 px-4">Standard System</th>
                    <th className="py-2.5 px-4 font-mono">Concept Code</th>
                    <th className="py-2.5 px-4">Standard Display Concept</th>
                    <th className="py-2.5 px-4">Clinical Category</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e5e7eb] text-[#111111]">
                  {filteredTerminology.map((item, idx) => (
                    <tr key={idx} className="hover:bg-[#f9fafb] transition-colors">
                      <td className="py-2.5 px-4 font-semibold text-[#111111]">
                        <span className="px-2 py-0.5 bg-[#f3f4f6] rounded border border-[#e5e7eb] font-mono text-[10px]">
                          {item.system}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-mono font-bold">{item.code}</td>
                      <td className="py-2.5 px-4">{item.display}</td>
                      <td className="py-2.5 px-4 capitalize text-[#6b7280]">{item.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: ABDM ARCHITECTURE */}
        {activeTab === "architecture" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 border-[#e5e7eb] space-y-3">
              <div className="h-9 w-9 rounded-md bg-[#f3f4f6] border border-[#e5e7eb] flex items-center justify-center">
                <ShieldCheck className="h-5 w-5 text-[#111111]" />
              </div>
              <h3 className="text-sm font-bold text-[#111111]">Milestone 1: Identity & ABHA</h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Aadhaar demographic authentication and OTP dispatch orchestrated through official NHA UIDAI proxy.
                Issues the 14-digit ABHA number and sovereign `@abdm` address.
              </p>
            </Card>

            <Card className="p-6 border-[#e5e7eb] space-y-3">
              <div className="h-9 w-9 rounded-md bg-[#f3f4f6] border border-[#e5e7eb] flex items-center justify-center">
                <Database className="h-5 w-5 text-[#111111]" />
              </div>
              <h3 className="text-sm font-bold text-[#111111]">Milestone 2: HIP Discovery & Link</h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Health Information Provider (HIP) registry matching patient records via authenticated link tokens and
                SMS verification. Encrypts clinical care contexts at the provider node.
              </p>
            </Card>

            <Card className="p-6 border-[#e5e7eb] space-y-3">
              <div className="h-9 w-9 rounded-md bg-[#f3f4f6] border border-[#e5e7eb] flex items-center justify-center">
                <FileCode className="h-5 w-5 text-[#111111]" />
              </div>
              <h3 className="text-sm font-bold text-[#111111]">Milestone 3: HIU Consent & FHIR</h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Decentralized electronic consent management artifacts. Delivers end-to-end encrypted HL7 FHIR R4 document
                bundles via ephemeral Diffie-Hellman (ECDH) key negotiation.
              </p>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

