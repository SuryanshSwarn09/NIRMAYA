"use client";

import React, { useState } from "react";
import { Badge, Button, Card, CardTitle, CardDescription, NavPillGroup } from "@/components/ui";
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
  Check
} from "lucide-react";

interface SoapNoteEditorProps {
  patientId: string;
  patientName?: string;
  doctorId?: string;
  doctorName?: string;
  encounterId?: string;
  isReadOnly?: boolean;
  onNoteSigned?: (note: SoapNote) => void;
}

const NOTE_TEMPLATES = [
  {
    name: "Hypertension Follow-up",
    chiefComplaint: "Occasional morning cephalalgia and borderline elevated home BP log",
    subjective: "39-year-old male presenting for quarterly cardiovascular review. Reports high work stress and 2-3 episodes of dull morning headache per week. Denies chest pain, orthopnea, or lower extremity edema. Adherent to daily antihypertensive therapy.",
    objective: "BP 138/88 mmHg right arm sitting, HR 78 bpm regular rhythm, SpO2 98% room air. BMI 27.2 kg/m². Heart sounds S1, S2 present, no murmurs. Lungs clear bilaterally.",
    assessment: "1. Essential (primary) hypertension (ICD-10 I10), stage 1, sub-optimally controlled.\n2. Overweight (BMI 27.2).\n3. Cardiovascular 10-year risk low to moderate.",
    plan: "1. Optimize lifestyle: DASH diet, reduce sodium intake < 2g/day.\n2. 30 min daily brisk walking.\n3. Requisition comprehensive lipid panel.\n4. Review home BP log in 2 weeks.",
  },
  {
    name: "Type 2 Diabetes Review",
    chiefComplaint: "Routine 3-month glycemic control follow-up",
    subjective: "Patient reports no polydipsia, polyuria, or unintended weight loss. No hypoglycemic episodes experienced. Following diabetic diet guidelines reasonably well.",
    objective: "Weight: 78 kg, BMI: 26.5 kg/m², BP: 126/80 mmHg, HR: 74 bpm. Foot exam: pedal pulses palpable bilaterally, monofilament sensation intact.",
    assessment: "Type 2 diabetes mellitus without complications (ICD-10 E11.9). Clinically stable.",
    plan: "1. Continue Metformin 500mg BID with meals.\n2. Requisition HbA1c test and urine microalbumin.\n3. Annual dilated eye exam scheduled.\n4. Follow-up in 3 months.",
  },
];

export const SoapNoteEditor: React.FC<SoapNoteEditorProps> = ({
  patientId,
  patientName = "Patient",
  doctorId = "doc-ananya-sharma",
  doctorName = "Dr. Ananya Sharma",
  encounterId,
  isReadOnly = false,
  onNoteSigned,
}) => {
  const [title, setTitle] = useState("Comprehensive Clinical Consultation SOAP Note");
  const [chiefComplaint, setChiefComplaint] = useState(NOTE_TEMPLATES[0].chiefComplaint);
  const [subjective, setSubjective] = useState(NOTE_TEMPLATES[0].subjective);
  const [objective, setObjective] = useState(NOTE_TEMPLATES[0].objective);
  const [assessment, setAssessment] = useState(NOTE_TEMPLATES[0].assessment);
  const [plan, setPlan] = useState(NOTE_TEMPLATES[0].plan);

  const [activeSection, setActiveSection] = useState<"all" | "s" | "o" | "a" | "p">("all");
  const [isSigned, setIsSigned] = useState(false);
  const [signatureHash, setSignatureHash] = useState("");
  const [isViewingFhir, setIsViewingFhir] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleApplyTemplate = (template: typeof NOTE_TEMPLATES[0]) => {
    if (isSigned) return;
    setChiefComplaint(template.chiefComplaint);
    setSubjective(template.subjective);
    setObjective(template.objective);
    setAssessment(template.assessment);
    setPlan(template.plan);
  };

  const handleSignNote = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate SHA-256 cryptographic signature
    const hash = Array.from({ length: 64 }, () =>
      Math.floor(Math.random() * 16).toString(16)
    ).join("");
    
    setIsSigned(true);
    setSignatureHash(hash);

    if (onNoteSigned) {
      const signedNote: SoapNote = {
        id: `note-${Date.now().toString().slice(-4)}`,
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
        is_signed: true,
        signature_hash: hash,
        signed_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      onNoteSigned(signedNote);
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
    author: [
      {
        reference: `Practitioner/${doctorId}`,
        display: doctorName,
      },
    ],
    date: new Date().toISOString(),
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

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#f8f9fa] p-4 rounded-xl border border-[#e5e7eb]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[#111111]">
              Structured SOAP Clinical Documentation
            </h3>
            {isSigned ? (
              <Badge variant="emerald" size="sm">
                Signed & Final
              </Badge>
            ) : (
              <Badge variant="warning" size="sm">
                Preliminary Draft
              </Badge>
            )}
          </div>
          <p className="text-xs text-[#6b7280]">
            HL7 FHIR R4 Composition • Standard LOINC Narrative Sections
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsViewingFhir(true)}
            className="flex items-center gap-1.5"
          >
            <Code className="h-3.5 w-3.5" />
            FHIR R4 JSON
          </Button>

          {!isSigned && !isReadOnly && (
            <Button
              size="sm"
              onClick={handleSignNote}
              className="flex items-center gap-1.5"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Sign & Finalize
            </Button>
          )}
        </div>
      </div>

      {/* Signature Confirmation Banner */}
      {isSigned && (
        <div className="p-3.5 bg-[#ecfdf5] border border-[#a7f3d0] rounded-xl space-y-1.5 text-xs text-[#065f46] animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold">
              <CheckCircle2 className="h-4 w-4 text-[#10b981]" />
              <span>Encounter Documentation Signed & Sealed Under Indian Medical Council Standards</span>
            </div>
            {!isReadOnly && (
              <button
                onClick={() => setIsSigned(false)}
                className="text-[11px] underline font-semibold text-[#047857] hover:text-[#065f46]"
              >
                Amend Note
              </button>
            )}
          </div>
          <div className="font-mono text-[11px] text-[#047857] truncate bg-white/70 p-1.5 rounded border border-[#a7f3d0]">
            SHA-256 Digest: {signatureHash}
          </div>
        </div>
      )}

      {/* Templates Selector */}
      {!isSigned && !isReadOnly && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <span className="text-[#6b7280] font-medium shrink-0">Clinical Presets:</span>
          {NOTE_TEMPLATES.map((tmpl) => (
            <button
              key={tmpl.name}
              type="button"
              onClick={() => handleApplyTemplate(tmpl)}
              className="px-2.5 py-1 rounded-lg border border-[#e5e7eb] bg-white hover:bg-[#f8f9fa] text-[#374151] font-medium text-xs shrink-0 transition-colors flex items-center gap-1"
            >
              <Sparkles className="h-3 w-3 text-[#111111]" />
              {tmpl.name}
            </button>
          ))}
        </div>
      )}

      {/* Section View Selector */}
      <div className="flex items-center gap-1 border-b border-[#e5e7eb] pb-2 text-xs">
        {[
          { id: "all", label: "All Sections" },
          { id: "s", label: "[S] Subjective" },
          { id: "o", label: "[O] Objective" },
          { id: "a", label: "[A] Assessment" },
          { id: "p", label: "[P] Plan of Care" },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveSection(tab.id as typeof activeSection)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              activeSection === tab.id
                ? "bg-[#111111] text-white"
                : "text-[#6b7280] hover:text-[#111111] hover:bg-[#f3f4f6]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Note Editor Body */}
      <div className="space-y-4">
        {/* Chief Complaint */}
        <Card className="p-4 border border-[#e5e7eb] space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-[#111111] uppercase tracking-wider">
              Chief Clinical Complaint (LOINC 10154-3)
            </label>
            <Badge variant="neutral" size="sm">Encounter Trigger</Badge>
          </div>
          <input
            type="text"
            disabled={isSigned || isReadOnly}
            value={chiefComplaint}
            onChange={(e) => setChiefComplaint(e.target.value)}
            className="w-full text-xs px-3 py-2 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] disabled:bg-[#f9fafb]"
          />
        </Card>

        {/* [S] Subjective */}
        {(activeSection === "all" || activeSection === "s") && (
          <Card className="p-4 border border-[#e5e7eb] space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold">
                  S
                </span>
                <span>Subjective History & Narrative (LOINC 61150-9)</span>
              </label>
              <span className="text-[11px] text-[#6b7280]">Patient reports & symptoms</span>
            </div>
            <textarea
              rows={3}
              disabled={isSigned || isReadOnly}
              value={subjective}
              onChange={(e) => setSubjective(e.target.value)}
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb]"
            />
          </Card>
        )}

        {/* [O] Objective */}
        {(activeSection === "all" || activeSection === "o") && (
          <Card className="p-4 border border-[#e5e7eb] space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold">
                  O
                </span>
                <span>Objective Examination & Vitals Review (LOINC 61149-1)</span>
              </label>
              <span className="text-[11px] text-[#6b7280]">Physical findings & biometrics</span>
            </div>
            <textarea
              rows={3}
              disabled={isSigned || isReadOnly}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb]"
            />
          </Card>
        )}

        {/* [A] Assessment */}
        {(activeSection === "all" || activeSection === "a") && (
          <Card className="p-4 border border-[#e5e7eb] space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold">
                  A
                </span>
                <span>Assessment & Differential Diagnoses (LOINC 51848-0)</span>
              </label>
              <span className="text-[11px] text-[#6b7280]">Clinical synthesis & ICD-10</span>
            </div>
            <textarea
              rows={3}
              disabled={isSigned || isReadOnly}
              value={assessment}
              onChange={(e) => setAssessment(e.target.value)}
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb]"
            />
          </Card>
        )}

        {/* [P] Plan */}
        {(activeSection === "all" || activeSection === "p") && (
          <Card className="p-4 border border-[#e5e7eb] space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <span className="h-5 w-5 rounded bg-[#111111] text-white flex items-center justify-center text-[10px] font-bold">
                  P
                </span>
                <span>Plan of Care & Requisitions (LOINC 18776-5)</span>
              </label>
              <span className="text-[11px] text-[#6b7280]">Rx, diagnostics & follow-up</span>
            </div>
            <textarea
              rows={3}
              disabled={isSigned || isReadOnly}
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              className="w-full text-xs p-3 border border-[#e5e7eb] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#111111] leading-relaxed disabled:bg-[#f9fafb]"
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
                <Code className="h-5 w-5 text-[#111111]" />
                <div>
                  <h3 className="font-semibold text-sm text-[#111111]">
                    HL7 FHIR Release 4 • Composition Resource
                  </h3>
                  <p className="text-xs text-[#6b7280]">
                    LOINC 11506-3 Narrative Progress Note Structure
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsViewingFhir(false)}
                className="text-[#6b7280] hover:text-[#111111]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <pre className="p-4 bg-[#101010] text-[#a1a1aa] rounded-xl text-xs font-mono overflow-x-auto max-h-[380px]">
              {JSON.stringify(fhirComposition, null, 2)}
            </pre>

            <div className="flex items-center justify-between pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(fhirComposition, null, 2));
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="flex items-center gap-1.5"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-[#10b981]" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied" : "Copy FHIR JSON"}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsViewingFhir(false)}
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
