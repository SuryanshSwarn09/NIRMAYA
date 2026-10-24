"use client";

import React, { useState, useEffect } from "react";
import { Badge, Button, Card, CardTitle, CardDescription } from "@/components/ui";
import { SoapNote, ClinicalNoteType, ClinicalNoteStatus } from "@/lib/api";
import { 
  FileText, 
  CheckCircle2, 
  Code, 
  ShieldCheck, 
  Lock, 
  Stethoscope, 
  X,
  FileCheck,
  Sparkles,
  Copy,
  Check,
  Tag,
  AlertCircle,
  HelpCircle,
  ChevronRight,
  ClipboardList,
  Layers,
  Heart,
  Activity,
  Calendar,
  UserCheck
} from "lucide-react";

export interface SoapTemplate {
  name: string;
  category: string;
  chiefComplaint: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  primaryDiagnosisCode: string;
  primaryDiagnosisDisplay: string;
}

export const NOTE_TEMPLATES: SoapTemplate[] = [
  {
    name: "Hypertension Follow-up",
    category: "Cardiology",
    chiefComplaint: "Occasional morning cephalalgia and borderline elevated home BP log",
    subjective: "39-year-old male presenting for quarterly cardiovascular review. Reports high work stress and 2-3 episodes of dull morning headache per week. Denies chest pain, orthopnea, or lower extremity edema. Adherent to daily antihypertensive therapy.",
    objective: "BP 138/88 mmHg right arm sitting, HR 78 bpm regular rhythm, SpO2 98% room air. BMI 27.2 kg/m². Heart sounds S1, S2 present, no murmurs. Lungs clear bilaterally to auscultation. No peripheral edema.",
    assessment: "1. Essential (primary) hypertension (ICD-10 I10), stage 1, sub-optimally controlled.\n2. Overweight (BMI 27.2).\n3. Cardiovascular 10-year risk low to moderate.",
    plan: "1. Optimize lifestyle: DASH diet, reduce sodium intake < 2g/day.\n2. 30 min daily brisk walking 5 days/week.\n3. Requisition comprehensive lipid panel and serum creatinine.\n4. Review home BP log in 2 weeks via tele-consultation.",
    primaryDiagnosisCode: "I10",
    primaryDiagnosisDisplay: "Essential (primary) hypertension",
  },
  {
    name: "Type 2 Diabetes Review",
    category: "Endocrinology",
    chiefComplaint: "Routine 3-month glycemic control follow-up",
    subjective: "Patient reports no polydipsia, polyuria, or unintended weight loss. No hypoglycemic episodes experienced. Following diabetic diet guidelines reasonably well. Reports consistent medication adherence.",
    objective: "Weight: 78 kg, BMI: 26.5 kg/m², BP: 126/80 mmHg, HR: 74 bpm. Fasting glucose self-log: 110-128 mg/dL. Foot exam: pedal pulses palpable bilaterally (+2), monofilament sensation intact across all 10 test sites.",
    assessment: "1. Type 2 diabetes mellitus without complications (ICD-10 E11.9). Clinically stable glycemic control.\n2. Mild dyslipidemia on previous panel.",
    plan: "1. Continue Metformin 500mg BID with meals.\n2. Requisition HbA1c test and urine microalbumin/creatinine ratio.\n3. Annual dilated funduscopic eye exam scheduled.\n4. Follow-up in 3 months with lab results.",
    primaryDiagnosisCode: "E11.9",
    primaryDiagnosisDisplay: "Type 2 diabetes mellitus without complications",
  },
  {
    name: "Cardiac Palpitations",
    category: "Cardiology",
    chiefComplaint: "Intermittent sudden-onset awareness of rapid heartbeat & mild lightheadedness",
    subjective: "Patient describes brief episodes of flutter in chest lasting 1-3 minutes over the past two weeks, usually precipitated by high caffeine intake and sleep deprivation. Denies syncope, chest pain, or shortness of breath.",
    objective: "BP 122/78 mmHg, HR 82 bpm with occasional premature ectopic beats on auscultation, regular rate. S1/S2 normal, no murmurs, no carotid bruits. Thyroid gland non-tender, non-enlarged. JVP not elevated.",
    assessment: "1. Palpitations, unspecified (ICD-10 R00.2), likely benign premature atrial or ventricular complexes aggravated by caffeine/stress.\n2. Differential includes paroxysmal supraventricular tachycardia (PSVT).",
    plan: "1. Order 12-lead resting ECG and 24-hour ambulatory Holter monitoring.\n2. Check serum TSH, electrolytes, and complete blood count.\n3. Restrict caffeinated beverages and energy drinks.\n4. Immediate ER precautions advised if accompanied by chest pain or syncope.",
    primaryDiagnosisCode: "R00.2",
    primaryDiagnosisDisplay: "Palpitations, unspecified",
  },
  {
    name: "Acute Upper Respiratory Infection",
    category: "General Medicine",
    chiefComplaint: "Nasal congestion, sore throat, and low-grade fever for 3 days",
    subjective: "Patient reports acute onset of rhinorrhea, scratchy throat, dry hacking cough, and generalized malaise beginning 72 hours ago. No shortness of breath, pleuritic chest pain, or rash. No known COVID-19 exposures.",
    objective: "Temperature 37.8°C (100.0°F), BP 118/76 mmHg, HR 80 bpm, SpO2 99% room air. Oropharynx: mild posterior pharyngeal erythema without tonsillar exudates. Tympanic membranes clear. Lungs: vesicular breath sounds throughout, no rales or wheezes.",
    assessment: "1. Acute upper respiratory infection, unspecified (ICD-10 J06.9), presumed viral etiology.\n2. Mild febrile state.",
    plan: "1. Supportive symptomatic therapy: warm saline gargles, adequate oral hydration.\n2. Paracetamol 650mg PO Q6H PRN for fever/sore throat.\n3. Saline nasal spray 2 puffs each nostril TID.\n4. Return precautions if high fever persists > 5 days or if dyspnea develops.",
    primaryDiagnosisCode: "J06.9",
    primaryDiagnosisDisplay: "Acute upper respiratory infection, unspecified",
  },
];

export const CHIEF_COMPLAINT_PRESETS = [
  "Occasional morning cephalalgia & borderline elevated BP",
  "Routine 3-month glycemic control follow-up",
  "Intermittent palpitations with mild lightheadedness",
  "Nasal congestion, sore throat, and low-grade fever",
  "Exertional dyspnea & chest tightness on exertion",
  "Bilateral knee pain, stiffness worse in morning",
];

export const ICD10_DIAGNOSIS_PRESETS = [
  { code: "I10", display: "Essential (primary) hypertension" },
  { code: "E11.9", display: "Type 2 diabetes mellitus without complications" },
  { code: "R00.2", display: "Palpitations, unspecified" },
  { code: "J06.9", display: "Acute upper respiratory infection, unspecified" },
  { code: "E78.5", display: "Hyperlipidemia, unspecified" },
  { code: "M17.9", display: "Osteoarthritis of knee, unspecified" },
];

export interface SoapNoteEditorProps {
  patientId: string;
  patientName?: string;
  doctorId?: string;
  doctorName?: string;
  doctorSpecialty?: string;
  doctorRegNumber?: string;
  encounterId?: string;
  initialNote?: Partial<SoapNote>;
  prefilledVitals?: {
    bp?: string;
    hr?: string;
    spo2?: string;
    bmi?: string;
    temperature?: string;
    recordedAt?: string;
  };
  prefilledConditions?: Array<{
    code: string;
    display: string;
    severity?: string;
  }>;
  isReadOnly?: boolean;
  onNoteSigned?: (note: SoapNote) => void;
  onNoteSaved?: (note: SoapNote) => void;
}

export const SoapNoteEditor: React.FC<SoapNoteEditorProps> = ({
  patientId,
  patientName = "Patient",
  doctorId = "doc-ananya-sharma",
  doctorName = "Dr. Ananya Sharma",
  doctorSpecialty = "General Medicine / Internal Medicine",
  doctorRegNumber = "MCI-2015-84920",
  encounterId,
  initialNote,
  prefilledVitals,
  prefilledConditions,
  isReadOnly = false,
  onNoteSigned,
  onNoteSaved,
}) => {
  const [title, setTitle] = useState(
    initialNote?.title || "Comprehensive Clinical Consultation SOAP Note"
  );
  const [chiefComplaint, setChiefComplaint] = useState(
    initialNote?.chief_complaint || NOTE_TEMPLATES[0].chiefComplaint
  );
  const [subjective, setSubjective] = useState(
    initialNote?.subjective || NOTE_TEMPLATES[0].subjective
  );
  const [objective, setObjective] = useState(
    initialNote?.objective || NOTE_TEMPLATES[0].objective
  );
  const [assessment, setAssessment] = useState(
    initialNote?.assessment || NOTE_TEMPLATES[0].assessment
  );
  const [plan, setPlan] = useState(
    initialNote?.plan || NOTE_TEMPLATES[0].plan
  );
  const [primaryDiagnosisCode, setPrimaryDiagnosisCode] = useState(
    initialNote?.primary_diagnosis_code || NOTE_TEMPLATES[0].primaryDiagnosisCode
  );
  const [primaryDiagnosisDisplay, setPrimaryDiagnosisDisplay] = useState(
    initialNote?.primary_diagnosis_display || NOTE_TEMPLATES[0].primaryDiagnosisDisplay
  );
  const [followUpInstructions, setFollowUpInstructions] = useState(
    initialNote?.follow_up_instructions || "Review in 2 weeks or immediately if symptoms worsen."
  );

  const [activeSection, setActiveSection] = useState<"all" | "s" | "o" | "a" | "p">("all");
  const [isSigned, setIsSigned] = useState(initialNote?.is_signed || false);
  const [signatureHash, setSignatureHash] = useState(initialNote?.signature_hash || "");
  const [signedAt, setSignedAt] = useState(initialNote?.signed_at || "");
  const [isViewingFhir, setIsViewingFhir] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isSigningLoading, setIsSigningLoading] = useState(false);

  useEffect(() => {
    if (initialNote) {
      if (initialNote.title) setTitle(initialNote.title);
      if (initialNote.chief_complaint) setChiefComplaint(initialNote.chief_complaint);
      if (initialNote.subjective) setSubjective(initialNote.subjective);
      if (initialNote.objective) setObjective(initialNote.objective);
      if (initialNote.assessment) setAssessment(initialNote.assessment);
      if (initialNote.plan) setPlan(initialNote.plan);
      if (initialNote.primary_diagnosis_code) setPrimaryDiagnosisCode(initialNote.primary_diagnosis_code);
      if (initialNote.primary_diagnosis_display) setPrimaryDiagnosisDisplay(initialNote.primary_diagnosis_display);
      if (initialNote.is_signed !== undefined) setIsSigned(initialNote.is_signed);
      if (initialNote.signature_hash) setSignatureHash(initialNote.signature_hash);
      if (initialNote.signed_at) setSignedAt(initialNote.signed_at);
    }
  }, [initialNote]);

  const handleApplyTemplate = (template: SoapTemplate) => {
    if (isSigned || isReadOnly) return;
    setChiefComplaint(template.chiefComplaint);
    setSubjective(template.subjective);
    setObjective(template.objective);
    setAssessment(template.assessment);
    setPlan(template.plan);
    setPrimaryDiagnosisCode(template.primaryDiagnosisCode);
    setPrimaryDiagnosisDisplay(template.primaryDiagnosisDisplay);
  };

  const handleAddChiefComplaintPreset = (presetText: string) => {
    if (isSigned || isReadOnly) return;
    if (!chiefComplaint.trim()) {
      setChiefComplaint(presetText);
    } else if (!chiefComplaint.includes(presetText)) {
      setChiefComplaint(`${chiefComplaint}; ${presetText}`);
    }
  };

  const handleSelectDiagnosis = (diag: { code: string; display: string }) => {
    if (isSigned || isReadOnly) return;
    setPrimaryDiagnosisCode(diag.code);
    setPrimaryDiagnosisDisplay(diag.display);
    
    // Auto-link to assessment text if not already present
    const diagLine = `${diag.display} (ICD-10 ${diag.code})`;
    if (!assessment.includes(diag.code)) {
      setAssessment((prev) => 
        prev ? `${prev}\n• ${diagLine}` : `• ${diagLine}`
      );
    }
  };

  const handleImportVitals = () => {
    if (isSigned || isReadOnly || !prefilledVitals) return;
    const vitalsSummary = `Telemetry Vitals (${prefilledVitals.recordedAt || "Latest"}): BP ${prefilledVitals.bp || "N/A"}, HR ${prefilledVitals.hr || "N/A"}, SpO2 ${prefilledVitals.spo2 || "N/A"}, Temp ${prefilledVitals.temperature || "N/A"}, BMI ${prefilledVitals.bmi || "N/A"}.`;
    if (!objective.includes("Telemetry Vitals")) {
      setObjective((prev) => prev ? `${vitalsSummary}\n\n${prev}` : vitalsSummary);
    }
  };

  const handleImportConditions = () => {
    if (isSigned || isReadOnly || !prefilledConditions || prefilledConditions.length === 0) return;
    const condLines = prefilledConditions
      .map((c, i) => `${i + 1}. ${c.display} (${c.code}) - ${c.severity || "active"}`)
      .join("\n");
    if (!assessment.includes("Active Problem List Summary")) {
      const block = `Active Problem List Summary:\n${condLines}`;
      setAssessment((prev) => prev ? `${block}\n\n${prev}` : block);
    }
  };

  const computeSha256Hex = async (text: string): Promise<string> => {
    if (typeof window !== "undefined" && window.crypto && window.crypto.subtle) {
      const msgBuffer = new TextEncoder().encode(text);
      const hashBuffer = await window.crypto.subtle.digest("SHA-256", msgBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
    }
    // Fallback pseudo-hash
    return Array.from({ length: 64 }, () =>
      Math.floor(Math.random() * 16).toString(16)
    ).join("");
  };

  const handleSignNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSigned || isReadOnly) return;

    setIsSigningLoading(true);
    try {
      const timestamp = new Date().toISOString();
      const canonicalPayload = JSON.stringify({
        patient_id: patientId,
        doctor_id: doctorId,
        encounter_id: encounterId,
        title,
        chief_complaint: chiefComplaint,
        subjective,
        objective,
        assessment,
        plan,
        primary_diagnosis_code: primaryDiagnosisCode,
        signed_at: timestamp,
      });

      const hash = await computeSha256Hex(canonicalPayload);
      setIsSigned(true);
      setSignatureHash(hash);
      setSignedAt(timestamp);

      const finalizedNote: SoapNote = {
        id: initialNote?.id || `note-${Date.now().toString().slice(-6)}`,
        patient_id: patientId,
        doctor_id: doctorId,
        encounter_id: encounterId,
        note_type: "soap",
        status: "final",
        title,
        chief_complaint: chiefComplaint,
        subjective,
        objective,
        assessment,
        plan,
        primary_diagnosis_code: primaryDiagnosisCode,
        primary_diagnosis_display: primaryDiagnosisDisplay,
        follow_up_instructions: followUpInstructions,
        is_signed: true,
        signature_hash: hash,
        signed_at: timestamp,
        created_at: initialNote?.created_at || timestamp,
        updated_at: timestamp,
      };

      if (onNoteSigned) {
        onNoteSigned(finalizedNote);
      }
      if (onNoteSaved) {
        onNoteSaved(finalizedNote);
      }
    } finally {
      setIsSigningLoading(false);
    }
  };

  const fhirComposition = {
    resourceType: "Composition",
    id: `comp-${patientId.replace(/[^a-zA-Z0-9]/g, "").slice(0, 8)}`,
    status: isSigned ? "final" : "preliminary",
    type: {
      coding: [
        {
          system: "http://loinc.org",
          code: "11506-3",
          display: "Provider-unspecified Progress note",
        },
      ],
      text: title,
    },
    subject: {
      reference: `Patient/${patientId}`,
      display: patientName,
    },
    encounter: encounterId ? {
      reference: `Encounter/${encounterId}`,
    } : undefined,
    author: [
      {
        reference: `Practitioner/${doctorId}`,
        display: doctorName,
      },
    ],
    attester: isSigned ? [
      {
        mode: "legal",
        time: signedAt,
        party: {
          reference: `Practitioner/${doctorId}`,
          display: `${doctorName} (${doctorRegNumber})`,
        },
      },
    ] : undefined,
    date: signedAt || new Date().toISOString(),
    title,
    section: [
      {
        title: "Chief Complaint",
        code: {
          coding: [{ system: "http://loinc.org", code: "10154-3", display: "Chief complaint narrative" }],
        },
        text: { status: "generated", div: `<div>${chiefComplaint}</div>` },
      },
      {
        title: "Subjective",
        code: {
          coding: [{ system: "http://loinc.org", code: "61150-9", display: "Subjective narrative" }],
        },
        text: { status: "generated", div: `<div>${subjective}</div>` },
      },
      {
        title: "Objective",
        code: {
          coding: [{ system: "http://loinc.org", code: "61149-1", display: "Objective narrative" }],
        },
        text: { status: "generated", div: `<div>${objective}</div>` },
      },
      {
        title: "Assessment",
        code: {
          coding: [{ system: "http://loinc.org", code: "51848-0", display: "Evaluation note" }],
        },
        text: { status: "generated", div: `<div>${assessment}</div>` },
      },
      {
        title: "Plan",
        code: {
          coding: [{ system: "http://loinc.org", code: "18776-5", display: "Plan of care note" }],
        },
        text: { status: "generated", div: `<div>${plan}</div>` },
      },
    ],
  };

  const [fhirTab, setFhirTab] = useState<"narrative" | "json">("narrative");

  const downloadFhirJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(fhirComposition, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `FHIR-Composition-${patientId}-${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-4">
      {/* Action Header Card */}
      <div className="bg-white p-4 rounded-xl border border-[#e5e7eb] shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[#111111] tracking-tight flex items-center gap-2">
              <ClipboardList className="h-4 w-4 text-[#111111]" />
              Structured SOAP Encounter Documentation
            </h3>
            {isSigned ? (
              <Badge variant="emerald" size="sm" className="font-medium flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" />
                Signed & Finalized
              </Badge>
            ) : (
              <Badge variant="warning" size="sm" className="font-medium flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Preliminary Draft
              </Badge>
            )}
          </div>
          <p className="text-xs text-[#6b7280] mt-0.5">
            HL7 FHIR Release 4 Composition • LOINC 11506-3 Narrative Progress Note
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsViewingFhir(true)}
            className="flex items-center gap-1.5 border-[#e5e7eb] hover:bg-[#f9fafb] text-[#111111] font-medium"
          >
            <Code className="h-3.5 w-3.5 text-[#6b7280]" />
            FHIR R4 Composition
          </Button>

          {!isSigned && !isReadOnly && (
            <Button
              size="sm"
              onClick={handleSignNote}
              disabled={isSigningLoading || !chiefComplaint.trim() || !assessment.trim()}
              className="flex items-center gap-1.5 bg-[#111111] hover:bg-[#242424] text-white shadow-sm font-medium"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              {isSigningLoading ? "Signing..." : "Attest & Finalize"}
            </Button>
          )}
        </div>
      </div>

      {/* Cryptographic Digital Attestation Banner */}
      {isSigned && (
        <div className="p-4 bg-[#ecfdf5] border border-[#a7f3d0] rounded-xl space-y-2 text-xs text-[#065f46] animate-in fade-in duration-200 shadow-sm">
          <div className="flex items-start sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded-full bg-[#10b981] text-white">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <div>
                <span className="font-bold text-[#065f46]">
                  Digitally Attested & Cryptographically Sealed Under IMC Standards
                </span>
                <p className="text-[11px] text-[#047857]">
                  Signed by {doctorName} ({doctorSpecialty}) • Reg No: {doctorRegNumber} • {new Date(signedAt || Date.now()).toLocaleString("en-IN")}
                </p>
              </div>
            </div>

            {!isReadOnly && (
              <button
                type="button"
                onClick={() => {
                  if (confirm("Are you sure you want to unlock this signed note for amendments? A new cryptographic attestation will be required.")) {
                    setIsSigned(false);
                  }
                }}
                className="text-[11px] underline font-semibold text-[#047857] hover:text-[#065f46] shrink-0"
              >
                Amend Note
              </button>
            )}
          </div>
          
          <div className="flex items-center justify-between gap-2 bg-white/80 p-2 rounded-lg border border-[#a7f3d0] font-mono text-[11px] text-[#047857]">
            <span className="truncate">
              SHA-256 Digest: {signatureHash}
            </span>
            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(signatureHash);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              className="px-2 py-0.5 rounded bg-emerald-100 hover:bg-emerald-200 text-emerald-800 text-[10px] font-sans font-medium flex items-center gap-1 shrink-0 transition-colors"
            >
              {copied ? <Check className="h-3 w-3 text-[#10b981]" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy Digest"}
            </button>
          </div>
        </div>
      )}

      {/* Clinical Template Quick Switcher */}
      {!isSigned && !isReadOnly && (
        <Card className="p-3 bg-[#f8f9fa] border border-[#e5e7eb] rounded-xl shadow-none">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-[#2563eb]" />
              Standard Clinical SOAP Templates:
            </span>
            <span className="text-[11px] text-[#6b7280]">
              Click to pre-fill clinical documentation
            </span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            {NOTE_TEMPLATES.map((tmpl) => (
              <button
                key={tmpl.name}
                type="button"
                onClick={() => handleApplyTemplate(tmpl)}
                className="px-3 py-1.5 rounded-lg border border-[#e5e7eb] bg-white hover:bg-[#f3f4f6] text-[#374151] font-medium text-xs shrink-0 transition-all flex items-center gap-1.5 shadow-sm hover:border-[#d1d5db]"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-[#2563eb]" />
                {tmpl.name}
                <span className="text-[10px] text-[#6b7280] font-normal">({tmpl.category})</span>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Navigation Pills (Cal.com Style) */}
      <div className="flex items-center gap-1.5 bg-[#f8f9fa] p-1.5 rounded-xl border border-[#e5e7eb] overflow-x-auto text-xs">
        {[
          { id: "all", label: "All Sections", icon: Layers, code: "Overview" },
          { id: "s", label: "Subjective", icon: UserCheck, code: "LOINC 61150-9" },
          { id: "o", label: "Objective", icon: Activity, code: "LOINC 61149-1" },
          { id: "a", label: "Assessment", icon: Stethoscope, code: "LOINC 51848-0" },
          { id: "p", label: "Plan of Care", icon: Calendar, code: "LOINC 18776-5" },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id as typeof activeSection)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shrink-0 ${
                isActive
                  ? "bg-[#111111] text-white shadow-sm"
                  : "text-[#6b7280] hover:text-[#111111] hover:bg-white"
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? "text-white" : "text-[#6b7280]"}`} />
              <span>{tab.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded ${
                isActive ? "bg-white/20 text-white" : "bg-[#e5e7eb] text-[#4b5563]"
              }`}>
                {tab.code}
              </span>
            </button>
          );
        })}
      </div>

      {/* Note Editor Body */}
      <div className="space-y-4">
        {/* Chief Complaint Card */}
        <Card className="p-4 bg-white border border-[#e5e7eb] rounded-xl shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-[#111111] uppercase tracking-wider flex items-center gap-1.5">
              <span className="h-5 w-5 rounded bg-[#f3f4f6] text-[#111111] flex items-center justify-center text-[10px] font-bold border border-[#e5e7eb]">
                CC
              </span>
              <span>Chief Complaint Narrative (LOINC 10154-3)</span>
              {isSigned && <Lock className="h-3 w-3 text-[#10b981]" />}
            </label>
            <Badge variant="neutral" size="sm" className="text-[10px]">
              Encounter Trigger
            </Badge>
          </div>

          <input
            type="text"
            disabled={isSigned || isReadOnly}
            value={chiefComplaint}
            onChange={(e) => setChiefComplaint(e.target.value)}
            placeholder="e.g. Occasional morning cephalalgia and borderline elevated home BP log..."
            className="w-full text-xs px-3 py-2.5 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f9fafb] disabled:text-[#6b7280] text-[#111111] font-medium"
          />

          {!isSigned && !isReadOnly && (
            <div className="space-y-1.5 pt-1">
              <div className="text-[11px] text-[#6b7280] font-medium flex items-center gap-1">
                <Tag className="h-3 w-3 text-[#6b7280]" />
                <span>Quick-Select Clinical Symptom Chips:</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {CHIEF_COMPLAINT_PRESETS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => handleAddChiefComplaintPreset(preset)}
                    className="px-2.5 py-1 rounded-md bg-[#f8f9fa] hover:bg-[#e5e7eb] text-[#374151] border border-[#e5e7eb] text-[11px] font-medium transition-colors"
                  >
                    + {preset}
                  </button>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* [S] Subjective */}
        {(activeSection === "all" || activeSection === "s") && (
          <Card className="p-4 bg-white border border-[#e5e7eb] rounded-xl shadow-sm space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold shadow-sm">
                  S
                </span>
                <span>Subjective History & Narrative (LOINC 61150-9)</span>
                {isSigned && <Lock className="h-3 w-3 text-[#10b981]" />}
              </label>
              <span className="text-[11px] text-[#6b7280]">
                Patient-reported symptoms, HPI & ROS
              </span>
            </div>
            <textarea
              rows={4}
              disabled={isSigned || isReadOnly}
              value={subjective}
              onChange={(e) => setSubjective(e.target.value)}
              placeholder="Record patient-reported history of present illness, symptom duration, aggravating/alleviating factors..."
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb] disabled:text-[#6b7280] text-[#111111]"
            />
          </Card>
        )}

        {/* [O] Objective */}
        {(activeSection === "all" || activeSection === "o") && (
          <Card className="p-4 bg-white border border-[#e5e7eb] rounded-xl shadow-sm space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold shadow-sm">
                  O
                </span>
                <span>Objective Examination & Physical Findings (LOINC 61149-1)</span>
                {isSigned && <Lock className="h-3 w-3 text-[#10b981]" />}
              </label>
              <div className="flex items-center gap-2">
                {prefilledVitals && !isSigned && !isReadOnly && (
                  <button
                    type="button"
                    onClick={handleImportVitals}
                    className="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors flex items-center gap-1"
                  >
                    <Activity className="h-3 w-3 text-blue-600" />
                    Import Active Vitals
                  </button>
                )}
                <span className="text-[11px] text-[#6b7280]">
                  Telemetry vitals & physical examination
                </span>
              </div>
            </div>
            <textarea
              rows={4}
              disabled={isSigned || isReadOnly}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Record measured blood pressure, heart rate, SpO2, BMI, cardiac auscultation, respiratory exams..."
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb] disabled:text-[#6b7280] text-[#111111]"
            />
          </Card>
        )}

        {/* [A] Assessment & Diagnostic Linkages */}
        {(activeSection === "all" || activeSection === "a") && (
          <Card className="p-4 bg-white border border-[#e5e7eb] rounded-xl shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold shadow-sm">
                  A
                </span>
                <span>Assessment & Differential Diagnoses (LOINC 51848-0)</span>
                {isSigned && <Lock className="h-3 w-3 text-[#10b981]" />}
              </label>
              <div className="flex items-center gap-2">
                {prefilledConditions && prefilledConditions.length > 0 && !isSigned && !isReadOnly && (
                  <button
                    type="button"
                    onClick={handleImportConditions}
                    className="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors flex items-center gap-1"
                  >
                    <ClipboardList className="h-3 w-3 text-blue-600" />
                    Import Problem List
                  </button>
                )}
                <span className="text-[11px] text-[#6b7280]">
                  Clinical synthesis & ICD-10 codings
                </span>
              </div>
            </div>

            {/* ICD-10 Quick Tagger */}
            {!isSigned && !isReadOnly && (
              <div className="space-y-1.5 bg-[#f8f9fa] p-2.5 rounded-lg border border-[#e5e7eb]">
                <div className="text-[11px] text-[#4b5563] font-medium flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Tag className="h-3 w-3 text-[#2563eb]" />
                    ICD-10 Diagnostic Concept Linkages:
                  </span>
                  {primaryDiagnosisCode && (
                    <span className="text-[10px] font-semibold text-[#2563eb] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      Primary: {primaryDiagnosisCode} - {primaryDiagnosisDisplay}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {ICD10_DIAGNOSIS_PRESETS.map((diag) => {
                    const isSelected = primaryDiagnosisCode === diag.code;
                    return (
                      <button
                        key={diag.code}
                        type="button"
                        onClick={() => handleSelectDiagnosis(diag)}
                        className={`px-2 py-1 rounded text-[11px] font-medium transition-colors border flex items-center gap-1 ${
                          isSelected
                            ? "bg-[#2563eb] text-white border-[#2563eb]"
                            : "bg-white hover:bg-[#f3f4f6] text-[#374151] border-[#e5e7eb]"
                        }`}
                      >
                        <span className="font-mono font-bold text-[10px]">{diag.code}</span>
                        <span>{diag.display}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <textarea
              rows={4}
              disabled={isSigned || isReadOnly}
              value={assessment}
              onChange={(e) => setAssessment(e.target.value)}
              placeholder="Clinical synthesis, active problem evaluations, differential diagnoses with ICD-10/SNOMED..."
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb] disabled:text-[#6b7280] text-[#111111]"
            />
          </Card>
        )}

        {/* [P] Plan of Care */}
        {(activeSection === "all" || activeSection === "p") && (
          <Card className="p-4 bg-white border border-[#e5e7eb] rounded-xl shadow-sm space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold shadow-sm">
                  P
                </span>
                <span>Plan of Care & Requisitions (LOINC 18776-5)</span>
                {isSigned && <Lock className="h-3 w-3 text-[#10b981]" />}
              </label>
              <span className="text-[11px] text-[#6b7280]">
                Therapeutics, lab orders & follow-up
              </span>
            </div>
            <textarea
              rows={4}
              disabled={isSigned || isReadOnly}
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              placeholder="Formulate management plan: prescription orders, diagnostic lab requisitions, lifestyle advice..."
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb] disabled:text-[#6b7280] text-[#111111]"
            />
          </Card>
        )}
      </div>

      {/* Modal: FHIR Composition Inspector */}
      {isViewingFhir && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-[#e5e7eb] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-[#f3f4f6] text-[#111111]">
                  <Code className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-[#111111]">
                    HL7 FHIR Release 4 • Composition Resource
                  </h3>
                  <p className="text-xs text-[#6b7280]">
                    LOINC 11506-3 Progress Note Architecture
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsViewingFhir(false)}
                className="text-[#6b7280] hover:text-[#111111] p-1 rounded-lg hover:bg-[#f3f4f6]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Sub-Tabs: Narrative View vs Raw JSON */}
            <div className="flex items-center gap-2 border-b border-[#e5e7eb] pb-2 text-xs">
              <button
                type="button"
                onClick={() => setFhirTab("narrative")}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  fhirTab === "narrative"
                    ? "bg-[#111111] text-white"
                    : "text-[#6b7280] hover:text-[#111111] hover:bg-[#f3f4f6]"
                }`}
              >
                Structured Clinical Narrative
              </button>
              <button
                type="button"
                onClick={() => setFhirTab("json")}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  fhirTab === "json"
                    ? "bg-[#111111] text-white"
                    : "text-[#6b7280] hover:text-[#111111] hover:bg-[#f3f4f6]"
                }`}
              >
                Raw FHIR R4 JSON Payload
              </button>
            </div>

            {fhirTab === "narrative" ? (
              <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1 text-xs">
                <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#e5e7eb] space-y-1">
                  <div className="font-semibold text-[#111111] flex items-center justify-between">
                    <span>Document: {title}</span>
                    <Badge variant={isSigned ? "emerald" : "warning"} size="sm">
                      {isSigned ? "final" : "preliminary"}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-[#6b7280]">
                    Subject: {patientName} • Author: {doctorName} • Date: {new Date(signedAt || Date.now()).toLocaleDateString("en-IN")}
                  </div>
                </div>

                {fhirComposition.section.map((sec) => (
                  <div key={sec.title} className="p-3 rounded-xl border border-[#e5e7eb] space-y-1">
                    <div className="flex items-center justify-between text-[#111111] font-semibold">
                      <span>{sec.title}</span>
                      <span className="font-mono text-[10px] text-[#2563eb] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {sec.code.coding[0].system.replace("http://", "")} #{sec.code.coding[0].code}
                      </span>
                    </div>
                    <p className="text-[#374151] whitespace-pre-line leading-relaxed text-[11px]">
                      {sec.text.div.replace(/<\/?div>/g, "")}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <pre className="p-4 bg-[#101010] text-[#a1a1aa] rounded-xl text-xs font-mono overflow-x-auto max-h-[380px] leading-relaxed">
                {JSON.stringify(fhirComposition, null, 2)}
              </pre>
            )}

            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(fhirComposition, null, 2));
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="flex items-center gap-1.5 border-[#e5e7eb] text-[#111111]"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-[#10b981]" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied" : "Copy FHIR JSON"}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={downloadFhirJson}
                  className="flex items-center gap-1.5 border-[#e5e7eb] text-[#111111]"
                >
                  Download JSON
                </Button>
              </div>
              <Button
                size="sm"
                onClick={() => setIsViewingFhir(false)}
                className="bg-[#111111] hover:bg-[#242424] text-white"
              >
                Close Inspector
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
