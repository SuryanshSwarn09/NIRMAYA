/**
 * Clinical Condition & Terminology Mapping Utilities
 * Bridges SNOMED-CT, ICD-10, and HL7 FHIR R4 Condition ontologies with patient-friendly context.
 */

import { ConditionCategory, ConditionSeverity, ClinicalStatus, VerificationStatus } from "./api";

export interface SnomedMapping {
  snomedCode: string;
  snomedDisplay: string;
  icd10Code: string;
  icd10Display: string;
  category: ConditionCategory;
  commonName: string;
  typicalSeverity: ConditionSeverity;
  patientSummary: string;
  lifestyleAdvice: string[];
  monitoringGoal: string;
  recommendedSpecialist: string;
}

export const SNOMED_ICD_MAPPINGS: Record<string, SnomedMapping> = {
  // 1. Essential Hypertension
  "38341003": {
    snomedCode: "38341003",
    snomedDisplay: "Essential hypertension (disorder)",
    icd10Code: "I10",
    icd10Display: "Essential (primary) hypertension",
    category: "chronic-condition",
    commonName: "Primary High Blood Pressure",
    typicalSeverity: "moderate",
    patientSummary: "Persistent elevation in systemic arterial blood pressure requiring continuous lifestyle and pharmacological management.",
    lifestyleAdvice: [
      "Follow a low-sodium DASH diet (< 2,000 mg/day).",
      "Engage in 150 minutes of moderate aerobic exercise weekly.",
      "Track home blood pressure daily using a validated digital cuff."
    ],
    monitoringGoal: "Maintain clinic BP below 130/80 mmHg.",
    recommendedSpecialist: "Cardiology / Internal Medicine"
  },
  "I10": {
    snomedCode: "38341003",
    snomedDisplay: "Essential hypertension (disorder)",
    icd10Code: "I10",
    icd10Display: "Essential (primary) hypertension",
    category: "chronic-condition",
    commonName: "Primary High Blood Pressure",
    typicalSeverity: "moderate",
    patientSummary: "Persistent elevation in systemic arterial blood pressure requiring continuous lifestyle and pharmacological management.",
    lifestyleAdvice: [
      "Follow a low-sodium DASH diet (< 2,000 mg/day).",
      "Engage in 150 minutes of moderate aerobic exercise weekly.",
      "Track home blood pressure daily using a validated digital cuff."
    ],
    monitoringGoal: "Maintain clinic BP below 130/80 mmHg.",
    recommendedSpecialist: "Cardiology / Internal Medicine"
  },

  // 2. Type 2 Diabetes Mellitus
  "44054006": {
    snomedCode: "44054006",
    snomedDisplay: "Type 2 diabetes mellitus (disorder)",
    icd10Code: "E11.9",
    icd10Display: "Type 2 diabetes mellitus without complications",
    category: "chronic-condition",
    commonName: "Type 2 Diabetes",
    typicalSeverity: "moderate",
    patientSummary: "Metabolic disorder characterized by insulin resistance and hyperglycemia with systemic vascular risk.",
    lifestyleAdvice: [
      "Balance carbohydrate intake and consume high-fiber whole foods.",
      "Conduct regular self-monitoring of blood glucose (SMBG).",
      "Undergo annual diabetic retinal screening and podiatry foot checks."
    ],
    monitoringGoal: "Maintain HbA1c < 7.0% and fasting glucose 80–130 mg/dL.",
    recommendedSpecialist: "Endocrinology / Diabetology"
  },
  "E11.9": {
    snomedCode: "44054006",
    snomedDisplay: "Type 2 diabetes mellitus (disorder)",
    icd10Code: "E11.9",
    icd10Display: "Type 2 diabetes mellitus without complications",
    category: "chronic-condition",
    commonName: "Type 2 Diabetes",
    typicalSeverity: "moderate",
    patientSummary: "Metabolic disorder characterized by insulin resistance and hyperglycemia with systemic vascular risk.",
    lifestyleAdvice: [
      "Balance carbohydrate intake and consume high-fiber whole foods.",
      "Conduct regular self-monitoring of blood glucose (SMBG).",
      "Undergo annual diabetic retinal screening and podiatry foot checks."
    ],
    monitoringGoal: "Maintain HbA1c < 7.0% and fasting glucose 80–130 mg/dL.",
    recommendedSpecialist: "Endocrinology / Diabetology"
  },

  // 3. Hyperlipidemia
  "55822004": {
    snomedCode: "55822004",
    snomedDisplay: "Hyperlipidemia (disorder)",
    icd10Code: "E78.5",
    icd10Display: "Hyperlipidemia, unspecified",
    category: "problem-list-item",
    commonName: "Elevated Cholesterol & Lipids",
    typicalSeverity: "mild",
    patientSummary: "Elevated circulating low-density lipoprotein (LDL) or triglycerides predisposing to atherosclerotic plaque formation.",
    lifestyleAdvice: [
      "Adopt Mediterranean diet rich in omega-3 fatty acids and plant sterols.",
      "Limit saturated fats (< 7% of total daily calories).",
      "Adhere strictly to prescribed HMG-CoA reductase inhibitor (statin) therapy."
    ],
    monitoringGoal: "Maintain LDL-C < 100 mg/dL (or < 70 mg/dL for high cardiovascular risk).",
    recommendedSpecialist: "Preventive Cardiology"
  },
  "E78.5": {
    snomedCode: "55822004",
    snomedDisplay: "Hyperlipidemia (disorder)",
    icd10Code: "E78.5",
    icd10Display: "Hyperlipidemia, unspecified",
    category: "problem-list-item",
    commonName: "Elevated Cholesterol & Lipids",
    typicalSeverity: "mild",
    patientSummary: "Elevated circulating low-density lipoprotein (LDL) or triglycerides predisposing to atherosclerotic plaque formation.",
    lifestyleAdvice: [
      "Adopt Mediterranean diet rich in omega-3 fatty acids and plant sterols.",
      "Limit saturated fats (< 7% of total daily calories).",
      "Adhere strictly to prescribed HMG-CoA reductase inhibitor (statin) therapy."
    ],
    monitoringGoal: "Maintain LDL-C < 100 mg/dL (or < 70 mg/dL for high cardiovascular risk).",
    recommendedSpecialist: "Preventive Cardiology"
  },

  // 4. Coronary Artery Disease
  "53741008": {
    snomedCode: "53741008",
    snomedDisplay: "Coronary arteriosclerosis (disorder)",
    icd10Code: "I25.10",
    icd10Display: "Atherosclerotic heart disease of native coronary artery",
    category: "chronic-condition",
    commonName: "Coronary Artery Disease (CAD)",
    typicalSeverity: "severe",
    patientSummary: "Narrowing or blockage of coronary arteries by atherosclerotic plaques, impeding myocardial perfusion.",
    lifestyleAdvice: [
      "Seek emergency medical attention immediately if experiencing exertional chest tightness or radiating pain.",
      "Participate in medically supervised cardiac rehabilitation.",
      "Strictly avoid active and passive tobacco smoke exposure."
    ],
    monitoringGoal: "Maintain resting heart rate 60–70 bpm and prevent angina episodes.",
    recommendedSpecialist: "Interventional Cardiology"
  },
  "I25.10": {
    snomedCode: "53741008",
    snomedDisplay: "Coronary arteriosclerosis (disorder)",
    icd10Code: "I25.10",
    icd10Display: "Atherosclerotic heart disease of native coronary artery",
    category: "chronic-condition",
    commonName: "Coronary Artery Disease (CAD)",
    typicalSeverity: "severe",
    patientSummary: "Narrowing or blockage of coronary arteries by atherosclerotic plaques, impeding myocardial perfusion.",
    lifestyleAdvice: [
      "Seek emergency medical attention immediately if experiencing exertional chest tightness or radiating pain.",
      "Participate in medically supervised cardiac rehabilitation.",
      "Strictly avoid active and passive tobacco smoke exposure."
    ],
    monitoringGoal: "Maintain resting heart rate 60–70 bpm and prevent angina episodes.",
    recommendedSpecialist: "Interventional Cardiology"
  },

  // 5. Bronchial Asthma
  "195967001": {
    snomedCode: "195967001",
    snomedDisplay: "Asthma (disorder)",
    icd10Code: "J45.909",
    icd10Display: "Unspecified asthma, uncomplicated",
    category: "problem-list-item",
    commonName: "Bronchial Asthma",
    typicalSeverity: "moderate",
    patientSummary: "Chronic inflammatory airway disorder causing reversible bronchoconstriction, wheezing, and dyspnea.",
    lifestyleAdvice: [
      "Identify and minimize exposure to environmental triggers (pollen, dust, mold).",
      "Always carry prescribed short-acting beta-agonist (salbutamol inhaler).",
      "Monitor peak expiratory flow (PEF) during seasonal fluctuations."
    ],
    monitoringGoal: "Achieve green zone peak flow (> 80% baseline) with zero nighttime awakenings.",
    recommendedSpecialist: "Pulmonology / Allergy"
  },
  "J45.909": {
    snomedCode: "195967001",
    snomedDisplay: "Asthma (disorder)",
    icd10Code: "J45.909",
    icd10Display: "Unspecified asthma, uncomplicated",
    category: "problem-list-item",
    commonName: "Bronchial Asthma",
    typicalSeverity: "moderate",
    patientSummary: "Chronic inflammatory airway disorder causing reversible bronchoconstriction, wheezing, and dyspnea.",
    lifestyleAdvice: [
      "Identify and minimize exposure to environmental triggers (pollen, dust, mold).",
      "Always carry prescribed short-acting beta-agonist (salbutamol inhaler).",
      "Monitor peak expiratory flow (PEF) during seasonal fluctuations."
    ],
    monitoringGoal: "Achieve green zone peak flow (> 80% baseline) with zero nighttime awakenings.",
    recommendedSpecialist: "Pulmonology / Allergy"
  },

  // 6. Chronic Kidney Disease
  "709044004": {
    snomedCode: "709044004",
    snomedDisplay: "Chronic kidney disease (disorder)",
    icd10Code: "N18.9",
    icd10Display: "Chronic kidney disease, unspecified",
    category: "chronic-condition",
    commonName: "Chronic Kidney Disease (CKD)",
    typicalSeverity: "moderate",
    patientSummary: "Gradual reduction in renal glomerular filtration requiring strict nephroprotection and blood pressure regulation.",
    lifestyleAdvice: [
      "Limit dietary protein and avoid nephrotoxic NSAIDs (ibuprofen, naproxen).",
      "Maintain strict euvolemia and monitor for peripheral pedal edema.",
      "Schedule quarterly serum creatinine and urinary albumin-to-creatinine ratio (uACR) tests."
    ],
    monitoringGoal: "Preserve eGFR stability and suppress proteinuria.",
    recommendedSpecialist: "Nephrology"
  },
  "N18.9": {
    snomedCode: "709044004",
    snomedDisplay: "Chronic kidney disease (disorder)",
    icd10Code: "N18.9",
    icd10Display: "Chronic kidney disease, unspecified",
    category: "chronic-condition",
    commonName: "Chronic Kidney Disease (CKD)",
    typicalSeverity: "moderate",
    patientSummary: "Gradual reduction in renal glomerular filtration requiring strict nephroprotection and blood pressure regulation.",
    lifestyleAdvice: [
      "Limit dietary protein and avoid nephrotoxic NSAIDs (ibuprofen, naproxen).",
      "Maintain strict euvolemia and monitor for peripheral pedal edema.",
      "Schedule quarterly serum creatinine and urinary albumin-to-creatinine ratio (uACR) tests."
    ],
    monitoringGoal: "Preserve eGFR stability and suppress proteinuria.",
    recommendedSpecialist: "Nephrology"
  },

  // 7. Gastroesophageal Reflux Disease
  "235595009": {
    snomedCode: "235595009",
    snomedDisplay: "Gastroesophageal reflux disease (disorder)",
    icd10Code: "K21.9",
    icd10Display: "Gastro-esophageal reflux disease without esophagitis",
    category: "problem-list-item",
    commonName: "Acid Reflux / GERD",
    typicalSeverity: "mild",
    patientSummary: "Retrograde movement of gastric acid into the esophagus producing heartburn and regurgitation.",
    lifestyleAdvice: [
      "Elevate head of bed by 15 cm and avoid lying down within 3 hours of meals.",
      "Limit citrus, caffeine, chocolate, and high-fat spicy foods.",
      "Take prescribed proton pump inhibitor 30 minutes before the morning meal."
    ],
    monitoringGoal: "Achieve complete relief from postprandial heartburn.",
    recommendedSpecialist: "Gastroenterology"
  },
  "K21.9": {
    snomedCode: "235595009",
    snomedDisplay: "Gastroesophageal reflux disease (disorder)",
    icd10Code: "K21.9",
    icd10Display: "Gastro-esophageal reflux disease without esophagitis",
    category: "problem-list-item",
    commonName: "Acid Reflux / GERD",
    typicalSeverity: "mild",
    patientSummary: "Retrograde movement of gastric acid into the esophagus producing heartburn and regurgitation.",
    lifestyleAdvice: [
      "Elevate head of bed by 15 cm and avoid lying down within 3 hours of meals.",
      "Limit citrus, caffeine, chocolate, and high-fat spicy foods.",
      "Take prescribed proton pump inhibitor 30 minutes before the morning meal."
    ],
    monitoringGoal: "Achieve complete relief from postprandial heartburn.",
    recommendedSpecialist: "Gastroenterology"
  }
};

/**
 * Resolve terminology metadata by code or search query.
 */
export function findConditionTerminology(codeOrQuery?: string): SnomedMapping | undefined {
  if (!codeOrQuery) return undefined;
  const clean = codeOrQuery.trim();
  
  if (SNOMED_ICD_MAPPINGS[clean]) {
    return SNOMED_ICD_MAPPINGS[clean];
  }

  const lower = clean.toLowerCase();
  return Object.values(SNOMED_ICD_MAPPINGS).find(
    (m) =>
      m.snomedCode.toLowerCase() === lower ||
      m.icd10Code.toLowerCase() === lower ||
      m.commonName.toLowerCase().includes(lower) ||
      m.snomedDisplay.toLowerCase().includes(lower) ||
      m.icd10Display.toLowerCase().includes(lower)
  );
}

/**
 * Visual badge variant mapping for clinical severity.
 */
export function getSeverityBadgeConfig(severity?: string): {
  variant: "neutral" | "emerald" | "warning" | "critical";
  label: string;
} {
  switch (severity?.toLowerCase()) {
    case "severe":
      return { variant: "critical", label: "Severe" };
    case "moderate":
      return { variant: "warning", label: "Moderate" };
    case "mild":
      return { variant: "emerald", label: "Mild" };
    default:
      return { variant: "neutral", label: severity || "Unassessed" };
  }
}

/**
 * Visual badge variant mapping for clinical status.
 */
export function getClinicalStatusBadgeConfig(status: string): {
  variant: "verified" | "emerald" | "critical" | "warning" | "neutral";
  label: string;
} {
  switch (status.toLowerCase()) {
    case "active":
      return { variant: "emerald", label: "Active Condition" };
    case "recurrence":
    case "relapse":
      return { variant: "warning", label: "Recurrence / Flare" };
    case "inactive":
    case "remission":
      return { variant: "neutral", label: "In Remission" };
    case "resolved":
      return { variant: "verified", label: "Resolved" };
    default:
      return { variant: "neutral", label: status };
  }
}

/**
 * Format ISO datetime into patient-friendly presentation.
 */
export function formatConditionDate(isoDate?: string): string {
  if (!isoDate) return "Date Not Specified";
  try {
    const d = new Date(isoDate);
    return d.toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return isoDate;
  }
}

/**
 * Human-readable label for condition categories.
 */
export function getCategoryLabel(category?: string): string {
  switch (category) {
    case "chronic-condition":
      return "Chronic Condition";
    case "problem-list-item":
      return "Active Health Problem";
    case "encounter-diagnosis":
      return "Encounter Diagnosis";
    default:
      return "Clinical Condition";
  }
}
