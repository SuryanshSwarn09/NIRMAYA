/**
 * NIRMAYA Clinical Vitals & Observational Telemetry Engine
 * Standardized against LOINC (Logical Observation Identifiers Names and Codes)
 * and HL7 FHIR Release 4 Observation clinical profiles.
 */

import { ObservationInterpretation } from "./api";

export interface VitalSignComponent {
  code_value: string;
  code_display: string;
  value_quantity: number;
  value_unit: string;
  interpretation?: ObservationInterpretation | string;
}

export interface VitalSignRecord {
  id: string;
  patient_id: string;
  code_value: string;
  code_display: string;
  value_quantity?: number | null;
  value_unit: string;
  effective_date_time: string;
  interpretation?: ObservationInterpretation | string;
  components?: VitalSignComponent[];
  note?: string;
  created_at?: string;
}

export interface VitalsTimeSeriesPoint {
  id?: string;
  timestamp: string; // ISO 8601
  dateLabel: string; // e.g. "18 Oct"
  fullDateTime: string;
  systolic?: number;
  diastolic?: number;
  heartRate?: number;
  spo2?: number;
  weight?: number;
  bmi?: number;
  temperature?: number;
  respiratoryRate?: number;
  interpretation?: string;
}

export const LOINC_CODES = {
  BLOOD_PRESSURE_PANEL: "85354-9",
  SYSTOLIC_BP: "8480-6",
  DIASTOLIC_BP: "8462-4",
  HEART_RATE: "8867-4",
  OXYGEN_SATURATION: "2708-6",
  BODY_WEIGHT: "29463-7",
  BODY_HEIGHT: "8302-2",
  BODY_MASS_INDEX: "39156-5",
  BODY_TEMPERATURE: "8310-5",
  RESPIRATORY_RATE: "9279-1",
} as const;

export interface ClinicalEvaluation {
  interpretation: ObservationInterpretation;
  label: string;
  stage: string;
  category: "normal" | "elevated" | "warning" | "critical";
  recommendation: string;
}

/**
 * AHA/ACC 2017 Guideline Blood Pressure Evaluation
 */
export function evaluateBloodPressure(systolic: number, diastolic: number): ClinicalEvaluation {
  if (systolic > 180 || diastolic > 120) {
    return {
      interpretation: "critically-high",
      label: "Hypertensive Crisis",
      stage: "Crisis",
      category: "critical",
      recommendation: "Emergency evaluation required. Seek immediate medical attention.",
    };
  }
  if (systolic >= 140 || diastolic >= 90) {
    return {
      interpretation: "high",
      label: "Stage 2 Hypertension",
      stage: "Stage 2",
      category: "critical",
      recommendation: "Medical therapy review and lifestyle intervention recommended.",
    };
  }
  if ((systolic >= 130 && systolic <= 139) || (diastolic >= 80 && diastolic <= 89)) {
    return {
      interpretation: "high",
      label: "Stage 1 Hypertension",
      stage: "Stage 1",
      category: "warning",
      recommendation: "Lifestyle modification and regular monitoring advised.",
    };
  }
  if (systolic >= 120 && systolic <= 129 && diastolic < 80) {
    return {
      interpretation: "high",
      label: "Elevated Blood Pressure",
      stage: "Elevated",
      category: "elevated",
      recommendation: "Adopt heart-healthy lifestyle habits to prevent progression.",
    };
  }
  if (systolic < 90 || diastolic < 60) {
    return {
      interpretation: "low",
      label: "Hypotension",
      stage: "Low BP",
      category: "warning",
      recommendation: "Monitor for lightheadedness or dizziness upon standing.",
    };
  }
  return {
    interpretation: "normal",
    label: "Normal Blood Pressure",
    stage: "Normal",
    category: "normal",
    recommendation: "Optimal cardiovascular range. Maintain current healthy routine.",
  };
}

/**
 * Heart Rate / Pulse Evaluation (Adult Resting BPM)
 */
export function evaluateHeartRate(bpm: number): ClinicalEvaluation {
  if (bpm > 120) {
    return {
      interpretation: "critically-high",
      label: "Marked Tachycardia",
      stage: "High Alert",
      category: "critical",
      recommendation: "Significantly elevated resting heart rate. Assess for arrhythmia or distress.",
    };
  }
  if (bpm > 100) {
    return {
      interpretation: "high",
      label: "Tachycardia",
      stage: "Elevated",
      category: "warning",
      recommendation: "Elevated heart rate. Consider hydration, stress, or caffeine intake.",
    };
  }
  if (bpm < 50) {
    return {
      interpretation: "critically-low",
      label: "Sinus Bradycardia",
      stage: "Low Alert",
      category: "critical",
      recommendation: "Markedly low pulse. Confirm if patient is an athlete or symptomatic.",
    };
  }
  if (bpm < 60) {
    return {
      interpretation: "low",
      label: "Mild Bradycardia",
      stage: "Mildly Low",
      category: "warning",
      recommendation: "Resting pulse is below average baseline.",
    };
  }
  return {
    interpretation: "normal",
    label: "Normal Resting Pulse",
    stage: "Normal",
    category: "normal",
    recommendation: "Healthy resting cardiac rhythm.",
  };
}

/**
 * Oxygen Saturation SpO2 Evaluation (%)
 */
export function evaluateSpo2(percentage: number): ClinicalEvaluation {
  if (percentage < 90) {
    return {
      interpretation: "critically-low",
      label: "Severe Hypoxemia",
      stage: "Critical",
      category: "critical",
      recommendation: "Immediate oxygen therapy and emergency evaluation required.",
    };
  }
  if (percentage < 95) {
    return {
      interpretation: "low",
      label: "Mild to Moderate Hypoxia",
      stage: "Low Alert",
      category: "warning",
      recommendation: "Sub-optimal peripheral oxygen saturation. Monitor closely and notify clinician.",
    };
  }
  return {
    interpretation: "normal",
    label: "Normal Oxygen Saturation",
    stage: "Normal",
    category: "normal",
    recommendation: "Optimal arterial oxygenation.",
  };
}

/**
 * Body Mass Index (BMI) & Weight Evaluation
 */
export function calculateBmi(weightKg: number, heightCm: number): number {
  if (heightCm <= 0 || weightKg <= 0) return 0;
  const heightMeters = heightCm / 100;
  return Number((weightKg / (heightMeters * heightMeters)).toFixed(1));
}

export function evaluateBmi(bmi: number): ClinicalEvaluation {
  if (bmi >= 35) {
    return {
      interpretation: "critically-high",
      label: "Class II / III Obesity",
      stage: "Severe",
      category: "critical",
      recommendation: "Comprehensive metabolic and multidisciplinary care recommended.",
    };
  }
  if (bmi >= 30) {
    return {
      interpretation: "high",
      label: "Class I Obesity",
      stage: "Obese",
      category: "warning",
      recommendation: "Targeted nutritional counseling and weight management suggested.",
    };
  }
  if (bmi >= 25) {
    return {
      interpretation: "high",
      label: "Overweight",
      stage: "Elevated",
      category: "elevated",
      recommendation: "Preventive dietary modifications and regular physical activity advised.",
    };
  }
  if (bmi < 18.5) {
    return {
      interpretation: "low",
      label: "Underweight",
      stage: "Low",
      category: "warning",
      recommendation: "Nutritional assessment to ensure adequate caloric and protein intake.",
    };
  }
  return {
    interpretation: "normal",
    label: "Normal Weight",
    stage: "Healthy",
    category: "normal",
    recommendation: "Optimal body composition maintained.",
  };
}

/**
 * Body Temperature Evaluation (°F)
 */
export function evaluateTemperature(tempF: number): ClinicalEvaluation {
  if (tempF > 103) {
    return {
      interpretation: "critically-high",
      label: "High Fever (Hyperpyrexia)",
      stage: "Critical",
      category: "critical",
      recommendation: "High fever. Administer antipyretics and seek medical consultation.",
    };
  }
  if (tempF > 100.4) {
    return {
      interpretation: "high",
      label: "Pyrexia / Fever",
      stage: "Fever",
      category: "warning",
      recommendation: "Active febrile state. Maintain hydration and monitor trajectory.",
    };
  }
  if (tempF > 99.0) {
    return {
      interpretation: "high",
      label: "Low-Grade Temperature",
      stage: "Elevated",
      category: "elevated",
      recommendation: "Mild temperature elevation. Rest and monitor.",
    };
  }
  if (tempF < 95.0) {
    return {
      interpretation: "critically-low",
      label: "Hypothermia",
      stage: "Critical Low",
      category: "critical",
      recommendation: "Abnormally low core body temperature. Active rewarming required.",
    };
  }
  return {
    interpretation: "normal",
    label: "Normal Body Temperature",
    stage: "Normal",
    category: "normal",
    recommendation: "Core thermal homeostasis intact.",
  };
}

/**
 * Visual badge configuration for clinical interpretations.
 */
export function getVitalBadgeConfig(interpretation?: string): {
  variant: "verified" | "emerald" | "critical" | "warning" | "neutral";
  label: string;
} {
  switch (interpretation?.toLowerCase()) {
    case "critical":
    case "critically-high":
    case "critically-low":
      return { variant: "critical", label: "Critical" };
    case "high":
      return { variant: "warning", label: "High" };
    case "low":
      return { variant: "warning", label: "Low" };
    case "normal":
      return { variant: "emerald", label: "Normal" };
    default:
      return { variant: "neutral", label: interpretation || "Normal" };
  }
}
