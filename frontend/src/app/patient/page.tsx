"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { 
  PatientHeader, 
  PatientMetricsBar, 
  PatientNavTabs, 
  PatientOverviewTab, 
  PatientPrescriptionsTab, 
  PatientRecordsTab, 
  PatientModals,
  AbhaCardExportModal,
  AbhaQrVerificationModal,
  PatientProblemsTab,
  PatientTabId,
  VitalMetricType,
  TelemedicineReadinessModal,
  AbhaCreationModal
} from "@/components/patient";
import { 
  ClinicalSlotPicker, 
  AppointmentBookingModal 
} from "@/components/appointments";
import { ProblemListPanel } from "@/components/clinical";
import { Badge } from "@/components/ui";
import { 
  apiClient, 
  DoctorSlot, 
  SlotHoldResponse, 
  Appointment, 
  MedicationRequest,
  ClinicalCondition 
} from "@/lib/api";
import {
  VitalsTimeSeriesPoint,
  evaluateBloodPressure,
  evaluateHeartRate,
  evaluateSpo2,
  evaluateBmi,
  evaluateTemperature,
  calculateBmi,
  LOINC_CODES,
} from "@/lib/vitals";

const CLINICIANS = [
  {
    id: "doc-ananya-sharma",
    name: "Dr. Ananya Sharma",
    specialty: "Chief Cardiologist",
    affiliation: "AIIMS New Delhi",
    fee: 1500,
    hpr: "ananya.sharma@hpr.abdm",
  },
  {
    id: "doc-rajesh-varma",
    name: "Dr. Rajesh Varma",
    specialty: "Consultant Physician",
    affiliation: "Fortis Escorts Heart Institute",
    fee: 1200,
    hpr: "rajesh.varma@hpr.abdm",
  },
  {
    id: "doc-kv-raman",
    name: "Dr. K. V. Raman",
    specialty: "Senior Dermatologist",
    affiliation: "Apollo Hospital Delhi",
    fee: 1000,
    hpr: "kv.raman@hpr.abdm",
  },
];

export default function PatientVaultPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<PatientTabId>("overview");
  const [consentActive, setConsentActive] = useState(true);

  // ABHA ID Card & QR Verification States (Day 32, Day 44)
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [isAbhaCreationModalOpen, setIsAbhaCreationModalOpen] = useState(false);
  
  // Telemedicine Pre-Consultation WebRTC Readiness Modal (Day 35)
  const [isTelemedicineModalOpen, setIsTelemedicineModalOpen] = useState(false);
  const [activeConsultationAppt, setActiveConsultationAppt] = useState<Appointment | null>(null);
  
  const [abhaCardData, setAbhaCardData] = useState<{
    abhaId: string;
    abhaAddress: string;
    patientName: string;
    gender: string;
    dob: string;
    mobile: string;
    bloodGroup: string;
    stateNode: string;
    distName: string;
    emergencyContact: string;
    organDonor: boolean;
    qrPayload: string;
  }>({
    abhaId: user?.abhaId || "91-8472-1092-4821",
    abhaAddress: "arun.patel@abdm",
    patientName: user?.fullName || "Arun Patel",
    gender: "Male",
    dob: "1990-06-04",
    mobile: "+91 98*** **421",
    bloodGroup: "O Positive (O+)",
    stateNode: "NCT of Delhi",
    distName: "South Delhi",
    emergencyContact: "Pooja Patel (+91 98*** **991)",
    organDonor: true,
    qrPayload: "",
  });

  // Attempt to load official ABHA card from backend if patient profile exists
  useEffect(() => {
    async function loadAbhaCard() {
      try {
        const patientId = user?.id || "pat-arun-patel";
        const res = await apiClient.getPatientAbhaCard(patientId);
        if (res && res.card_data) {
          setAbhaCardData({
            abhaId: res.card_data.abha_number || "91-8472-1092-4821",
            abhaAddress: res.card_data.abha_address || "arun.patel@abdm",
            patientName: res.card_data.name || user?.fullName || "Arun Patel",
            gender: res.card_data.gender === "M" ? "Male" : res.card_data.gender === "F" ? "Female" : "Other",
            dob: res.card_data.date_of_birth || "1990-06-04",
            mobile: res.card_data.mobile || "+91 98*** **421",
            bloodGroup: res.card_data.blood_group || "O Positive (O+)",
            stateNode: res.card_data.state || "NCT of Delhi",
            distName: res.card_data.district || "South Delhi",
            emergencyContact: res.card_data.emergency_contact_name 
              ? `${res.card_data.emergency_contact_name} (${res.card_data.emergency_contact_phone || ""})`
              : "Pooja Patel (+91 98*** **991)",
            organDonor: true,
            qrPayload: res.qr_payload || "",
          });
        }
      } catch (err) {
        // Fallback gracefully to default seeded identity
        console.info("Using local ABDM card identity", err);
      }
    }
    loadAbhaCard();
  }, [user?.id, user?.fullName, user?.abhaId]);

  // E-Prescriptions & Medication Tracker State (Day 27 & Day 29)
  const [prescriptions, setPrescriptions] = useState<MedicationRequest[]>([]);
  const [loadingPrescriptions, setLoadingPrescriptions] = useState(false);
  const [viewingFhirRx, setViewingFhirRx] = useState<Record<string, any> | null>(null);
  const [fetchingFhirId, setFetchingFhirId] = useState<string | null>(null);

  // Longitudinal Problem List & Active Conditions State (Day 33)
  const [conditions, setConditions] = useState<ClinicalCondition[]>([
    {
      id: "cond-101",
      patient_id: "pat-arun-patel",
      clinical_status: "active",
      verification_status: "confirmed",
      category: "chronic-condition",
      severity: "moderate",
      code_coding_system: "http://snomed.info/sct",
      code_value: "38341003",
      code_display: "Essential hypertension (disorder)",
      onset_date_time: "2024-03-15T09:00:00Z",
      note: "Baseline BP 138-142 / 88-92 mmHg. On Lisinopril 10mg daily and DASH diet.",
      created_at: "2024-03-15T09:00:00Z",
      updated_at: new Date().toISOString(),
    },
    {
      id: "cond-102",
      patient_id: "pat-arun-patel",
      clinical_status: "active",
      verification_status: "confirmed",
      category: "problem-list-item",
      severity: "mild",
      code_coding_system: "http://snomed.info/sct",
      code_value: "55822004",
      code_display: "Hyperlipidemia (disorder)",
      onset_date_time: "2024-06-10T11:30:00Z",
      note: "Elevated fasting triglycerides and direct LDL. On Atorvastatin 20mg daily.",
      created_at: "2024-06-10T11:30:00Z",
      updated_at: new Date().toISOString(),
    },
    {
      id: "cond-103",
      patient_id: "pat-arun-patel",
      clinical_status: "active",
      verification_status: "confirmed",
      category: "chronic-condition",
      severity: "moderate",
      code_coding_system: "http://snomed.info/sct",
      code_value: "44054006",
      code_display: "Type 2 diabetes mellitus (disorder)",
      onset_date_time: "2023-11-20T14:15:00Z",
      note: "HbA1c 6.8%. Managed with Metformin 500mg BD and carbohydrate portion control.",
      created_at: "2023-11-20T14:15:00Z",
      updated_at: new Date().toISOString(),
    },
  ]);
  const [loadingConditions, setLoadingConditions] = useState(false);

  const loadConditions = async () => {
    try {
      setLoadingConditions(true);
      const res = await apiClient.getPatientConditions(user?.id || "pat-arun-patel");
      if (res && res.items && res.items.length > 0) {
        setConditions(res.items);
      }
    } catch (err) {
      console.info("Using local problem list conditions", err);
    } finally {
      setLoadingConditions(false);
    }
  };

  const loadPrescriptions = async () => {
    try {
      setLoadingPrescriptions(true);
      const res = await apiClient.getPatientPrescriptions(user?.id || "pat-arun-patel");
      if (res.items) {
        setPrescriptions(res.items);
      }
    } catch (err) {
      console.warn("Could not load real patient prescriptions, using fallback records", err);
    } finally {
      setLoadingPrescriptions(false);
    }
  };

  useEffect(() => {
    loadPrescriptions();
    loadConditions();
  }, [user?.id]);

  // Selected Clinician for Booking (Day 19)
  const [selectedDoctor, setSelectedDoctor] = useState(CLINICIANS[0]);
  const [selectedSlot, setSelectedSlot] = useState<DoctorSlot | null>(null);
  const [activeHold, setActiveHold] = useState<SlotHoldResponse | null>(null);
  const [isHolding, setIsHolding] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Scheduled Appointments List
  const [scheduledAppointments, setScheduledAppointments] = useState<Appointment[]>([
    {
      id: "686523ba-744c-4bb7-925b-4f88eefcd269",
      patient_id: "pat-arun-patel",
      doctor_id: "doc-ananya-sharma",
      doctor_name: "Dr. Ananya Sharma",
      doctor_specialty: "Chief Cardiologist",
      appointment_type: "routine_checkup",
      status: "confirmed",
      scheduled_start: new Date(Date.now() + 86400000 * 2).toISOString(),
      scheduled_end: new Date(Date.now() + 86400000 * 2 + 1800000).toISOString(),
      reason: "Quarterly cardiovascular review and blood pressure evaluation",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);

  // Longitudinal Vitals Time Series (7-Day Telemetry Trajectory)
  const [vitalsTimeSeries, setVitalsTimeSeries] = useState<VitalsTimeSeriesPoint[]>([
    {
      timestamp: "2026-10-18T09:00:00Z",
      dateLabel: "18 Oct",
      fullDateTime: "18 Oct 2026, 09:00 AM",
      systolic: 138,
      diastolic: 88,
      heartRate: 78,
      spo2: 97,
      weight: 73.2,
      bmi: 24.5,
      temperature: 98.4,
      interpretation: "high",
    },
    {
      timestamp: "2026-10-19T09:15:00Z",
      dateLabel: "19 Oct",
      fullDateTime: "19 Oct 2026, 09:15 AM",
      systolic: 136,
      diastolic: 86,
      heartRate: 75,
      spo2: 98,
      weight: 73.0,
      bmi: 24.4,
      temperature: 98.6,
      interpretation: "high",
    },
    {
      timestamp: "2026-10-20T08:45:00Z",
      dateLabel: "20 Oct",
      fullDateTime: "20 Oct 2026, 08:45 AM",
      systolic: 132,
      diastolic: 84,
      heartRate: 74,
      spo2: 98,
      weight: 72.8,
      bmi: 24.3,
      temperature: 98.5,
      interpretation: "high",
    },
    {
      timestamp: "2026-10-21T09:30:00Z",
      dateLabel: "21 Oct",
      fullDateTime: "21 Oct 2026, 09:30 AM",
      systolic: 130,
      diastolic: 82,
      heartRate: 72,
      spo2: 99,
      weight: 72.6,
      bmi: 24.3,
      temperature: 98.6,
      interpretation: "high",
    },
    {
      timestamp: "2026-10-22T08:30:00Z",
      dateLabel: "22 Oct",
      fullDateTime: "22 Oct 2026, 08:30 AM",
      systolic: 128,
      diastolic: 82,
      heartRate: 71,
      spo2: 98,
      weight: 72.5,
      bmi: 24.2,
      temperature: 98.4,
      interpretation: "normal",
    },
    {
      timestamp: "2026-10-23T09:00:00Z",
      dateLabel: "23 Oct",
      fullDateTime: "23 Oct 2026, 09:00 AM",
      systolic: 126,
      diastolic: 80,
      heartRate: 70,
      spo2: 99,
      weight: 72.4,
      bmi: 24.2,
      temperature: 98.6,
      interpretation: "normal",
    },
    {
      timestamp: "2026-10-24T10:15:00Z",
      dateLabel: "24 Oct",
      fullDateTime: "24 Oct 2026, 10:15 AM",
      systolic: 134,
      diastolic: 86,
      heartRate: 72,
      spo2: 98,
      weight: 72.3,
      bmi: 24.1,
      temperature: 98.6,
      interpretation: "high",
    },
  ]);

  // Current Observational Telemetry Snapshot (Day 22 & 34)
  const [vitalsList, setVitalsList] = useState<any[]>([
    {
      id: "obs-bp-01",
      code_value: "85354-9",
      code_display: "Blood Pressure Panel",
      value_quantity: null,
      value_unit: "mmHg",
      interpretation: "high",
      components: [
        { code_value: "8480-6", code_display: "Systolic", value_quantity: 134, value_unit: "mmHg", interpretation: "high" },
        { code_value: "8462-4", code_display: "Diastolic", value_quantity: 86, value_unit: "mmHg", interpretation: "high" },
      ],
      effective_date_time: "Today, 10:15 AM",
      method: "Automated oscillometric",
    },
    {
      id: "obs-hr-01",
      code_value: "8867-4",
      code_display: "Heart Rate",
      value_quantity: 72,
      value_unit: "/min",
      interpretation: "normal",
      reference_range_text: "60 - 100 /min",
      effective_date_time: "Today, 10:15 AM",
    },
    {
      id: "obs-spo2-01",
      code_value: "2708-6",
      code_display: "Oxygen Saturation (SpO2)",
      value_quantity: 98,
      value_unit: "%",
      interpretation: "normal",
      reference_range_text: "95 - 100 %",
      effective_date_time: "Today, 10:15 AM",
    },
    {
      id: "obs-bmi-01",
      code_value: "39156-5",
      code_display: "Body Mass Index (BMI)",
      value_quantity: 24.1,
      value_unit: "kg/m²",
      interpretation: "normal",
      reference_range_text: "18.5 - 24.9 kg/m²",
      effective_date_time: "Today, 10:15 AM",
    },
  ]);

  // Vitals Logging & FHIR Modals State
  const [isLogVitalsOpen, setIsLogVitalsOpen] = useState(false);
  const [logVitalType, setLogVitalType] = useState<VitalMetricType>("hr");
  const [logValue, setLogValue] = useState("75");
  const [logSystolic, setLogSystolic] = useState("120");
  const [logDiastolic, setLogDiastolic] = useState("80");
  const [logWeight, setLogWeight] = useState("72");
  const [logHeight, setLogHeight] = useState("175");
  const [logTemp, setLogTemp] = useState("98.6");
  const [selectedFhirJson, setSelectedFhirJson] = useState<any | null>(null);

  // Diagnostic Lab Reports & Orders (Day 24)
  const [patientLabReports] = useState([
    {
      id: "dr-apollo-0925-01",
      order_id: "ord-req-901",
      title: "Comprehensive Lipid & Glycemic Diagnostic Panel",
      performer: "Apollo Diagnostics Central (HFR-DEL-91024)",
      code_value: "57021-8",
      code_display: "CBC and Comprehensive Metabolic Panel",
      issued_date_time: "Today, 11:15 AM",
      status: "final",
      is_abnormal: true,
      conclusion: "Borderline hypercholesterolemia with optimal fasting glucose. Dietary lipid modulation recommended.",
      coded_diagnosis_icd10: "E78.5 - Hyperlipidemia, unspecified",
      observations: [
        {
          code_value: "2093-3",
          code_display: "Total Serum Cholesterol",
          value_quantity: 215,
          value_unit: "mg/dL",
          reference_range_text: "< 200 mg/dL",
          interpretation: "high",
        },
        {
          code_value: "13457-7",
          code_display: "LDL Cholesterol (Calculated)",
          value_quantity: 142,
          value_unit: "mg/dL",
          reference_range_text: "< 100 mg/dL",
          interpretation: "high",
        },
        {
          code_value: "2085-9",
          code_display: "HDL Cholesterol",
          value_quantity: 44,
          value_unit: "mg/dL",
          reference_range_text: "> 40 mg/dL",
          interpretation: "normal",
        },
        {
          code_value: "2571-8",
          code_display: "Serum Triglycerides",
          value_quantity: 145,
          value_unit: "mg/dL",
          reference_range_text: "< 150 mg/dL",
          interpretation: "normal",
        },
        {
          code_value: "1558-6",
          code_display: "Fasting Blood Glucose",
          value_quantity: 94,
          value_unit: "mg/dL",
          reference_range_text: "70 - 99 mg/dL",
          interpretation: "normal",
        },
        {
          code_value: "4548-4",
          code_display: "Hemoglobin A1c (HbA1c)",
          value_quantity: 5.4,
          value_unit: "%",
          reference_range_text: "< 5.7 %",
          interpretation: "normal",
        },
      ],
    },
  ]);

  const [patientLabOrders] = useState([
    {
      id: "ord-req-901",
      code_value: "24331-1",
      code_display: "Lipid 1996 panel - Serum or Plasma",
      doctor_name: "Dr. Ananya Sharma (Chief Cardiologist, AIIMS)",
      priority: "routine",
      specimen_type: "serum",
      fasting_required: true,
      reason_display: "Cardiovascular risk stratification & baseline dyslipidemia surveillance",
      status: "completed",
      authored_on: "Today, 10:20 AM",
    },
  ]);

  // Slot Booking Handlers
  const handleHoldSlot = async (slot: DoctorSlot) => {
    setIsHolding(true);
    try {
      const hold = await apiClient.holdDoctorSlot(selectedDoctor.id, slot.id, 10);
      setActiveHold(hold);
      setIsModalOpen(true);
    } catch {
      const simulatedHold: SlotHoldResponse = {
        slot_id: slot.id,
        doctor_id: selectedDoctor.id,
        status: "held",
        held_until: new Date(Date.now() + 600000).toISOString(),
        held_by_patient_id: "pat-arun-patel",
        hold_duration_seconds: 600,
      };
      setActiveHold(simulatedHold);
      setIsModalOpen(true);
    } finally {
      setIsHolding(false);
    }
  };

  const handleReleaseHold = async () => {
    if (!activeHold) return;
    try {
      await apiClient.releaseDoctorSlot(selectedDoctor.id, activeHold.slot_id);
    } catch {
      // Ignore in demo
    } finally {
      setActiveHold(null);
      setSelectedSlot(null);
      setIsModalOpen(false);
    }
  };

  const handleBookingSuccess = (newAppt: Appointment) => {
    setScheduledAppointments((prev) => [
      {
        ...newAppt,
        doctor_name: selectedDoctor.name,
        doctor_specialty: selectedDoctor.specialty,
      },
      ...prev,
    ]);
    setActiveHold(null);
    setSelectedSlot(null);
  };

  // Enhanced Vitals Logging Submission with LOINC Clinical Evaluation
  const handleLogVitalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nowIso = new Date().toISOString();
    const dateLabel = "Today";
    const fullDateTime = "Today, Just now";
    const patientId = user?.id || "pat-arun-patel";

    if (logVitalType === "bp") {
      const sys = parseFloat(logSystolic) || 120;
      const dia = parseFloat(logDiastolic) || 80;
      const evalResult = evaluateBloodPressure(sys, dia);
      const newObs = {
        id: `obs-bp-${Date.now()}`,
        code_value: LOINC_CODES.BLOOD_PRESSURE_PANEL,
        code_display: "Blood Pressure Panel",
        value_quantity: null,
        value_unit: "mmHg",
        interpretation: evalResult.interpretation,
        components: [
          { code_value: LOINC_CODES.SYSTOLIC_BP, code_display: "Systolic", value_quantity: sys, value_unit: "mmHg", interpretation: evalResult.interpretation },
          { code_value: LOINC_CODES.DIASTOLIC_BP, code_display: "Diastolic", value_quantity: dia, value_unit: "mmHg", interpretation: evalResult.interpretation },
        ],
        effective_date_time: "Just now (Self-reported)",
        method: "Home digital cuff",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== LOINC_CODES.BLOOD_PRESSURE_PANEL)]);
      setVitalsTimeSeries((prev) => [
        ...prev,
        {
          timestamp: nowIso,
          dateLabel,
          fullDateTime,
          systolic: sys,
          diastolic: dia,
          interpretation: evalResult.interpretation,
        },
      ]);
      try {
        await apiClient.recordObservation(patientId, {
          category: "vital-signs",
          code_value: LOINC_CODES.BLOOD_PRESSURE_PANEL,
          code_display: "Blood Pressure Panel",
          value_unit: "mmHg",
          interpretation: evalResult.interpretation,
          components: [
            { code_system: "http://loinc.org", code_value: LOINC_CODES.SYSTOLIC_BP, code_display: "Systolic blood pressure", value_quantity: sys, value_unit: "mmHg" },
            { code_system: "http://loinc.org", code_value: LOINC_CODES.DIASTOLIC_BP, code_display: "Diastolic blood pressure", value_quantity: dia, value_unit: "mmHg" },
          ],
        });
      } catch (err) {
        console.info("Recorded locally in memory", err);
      }
    } else if (logVitalType === "hr") {
      const val = parseFloat(logValue) || 72;
      const evalResult = evaluateHeartRate(val);
      const newObs = {
        id: `obs-hr-${Date.now()}`,
        code_value: LOINC_CODES.HEART_RATE,
        code_display: "Heart Rate",
        value_quantity: val,
        value_unit: "/min",
        interpretation: evalResult.interpretation,
        reference_range_text: "60 - 100 /min",
        effective_date_time: "Just now (Self-reported)",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== LOINC_CODES.HEART_RATE)]);
      setVitalsTimeSeries((prev) => [
        ...prev,
        {
          timestamp: nowIso,
          dateLabel,
          fullDateTime,
          heartRate: val,
          interpretation: evalResult.interpretation,
        },
      ]);
      try {
        await apiClient.recordObservation(patientId, {
          category: "vital-signs",
          code_value: LOINC_CODES.HEART_RATE,
          code_display: "Heart rate",
          value_quantity: val,
          value_unit: "/min",
          interpretation: evalResult.interpretation,
        });
      } catch (err) {
        console.info("Recorded locally in memory", err);
      }
    } else if (logVitalType === "spo2") {
      const val = parseFloat(logValue) || 98;
      const evalResult = evaluateSpo2(val);
      const newObs = {
        id: `obs-spo2-${Date.now()}`,
        code_value: LOINC_CODES.OXYGEN_SATURATION,
        code_display: "Oxygen Saturation (SpO2)",
        value_quantity: val,
        value_unit: "%",
        interpretation: evalResult.interpretation,
        reference_range_text: "95 - 100 %",
        effective_date_time: "Just now (Self-reported)",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== LOINC_CODES.OXYGEN_SATURATION)]);
      setVitalsTimeSeries((prev) => [
        ...prev,
        {
          timestamp: nowIso,
          dateLabel,
          fullDateTime,
          spo2: val,
          interpretation: evalResult.interpretation,
        },
      ]);
      try {
        await apiClient.recordObservation(patientId, {
          category: "vital-signs",
          code_value: LOINC_CODES.OXYGEN_SATURATION,
          code_display: "Oxygen saturation in Arterial blood",
          value_quantity: val,
          value_unit: "%",
          interpretation: evalResult.interpretation,
        });
      } catch (err) {
        console.info("Recorded locally in memory", err);
      }
    } else if (logVitalType === "weight") {
      const wt = parseFloat(logWeight || logValue) || 72;
      const ht = parseFloat(logHeight || "175") || 175;
      const bmi = calculateBmi(wt, ht);
      const evalResult = evaluateBmi(bmi);
      const newObs = {
        id: `obs-bmi-${Date.now()}`,
        code_value: LOINC_CODES.BODY_MASS_INDEX,
        code_display: "Body Mass Index (BMI)",
        value_quantity: bmi,
        value_unit: "kg/m²",
        interpretation: evalResult.interpretation,
        reference_range_text: "18.5 - 24.9 kg/m²",
        effective_date_time: "Just now (Self-reported)",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== LOINC_CODES.BODY_MASS_INDEX)]);
      setVitalsTimeSeries((prev) => [
        ...prev,
        {
          timestamp: nowIso,
          dateLabel,
          fullDateTime,
          weight: wt,
          bmi,
          interpretation: evalResult.interpretation,
        },
      ]);
      try {
        await apiClient.recordObservation(patientId, {
          category: "vital-signs",
          code_value: LOINC_CODES.BODY_MASS_INDEX,
          code_display: "Body mass index (BMI)",
          value_quantity: bmi,
          value_unit: "kg/m2",
          interpretation: evalResult.interpretation,
        });
      } catch (err) {
        console.info("Recorded locally in memory", err);
      }
    } else if (logVitalType === "temp") {
      const temp = parseFloat(logTemp || logValue) || 98.6;
      const evalResult = evaluateTemperature(temp);
      const newObs = {
        id: `obs-temp-${Date.now()}`,
        code_value: LOINC_CODES.BODY_TEMPERATURE,
        code_display: "Body Temperature",
        value_quantity: temp,
        value_unit: "°F",
        interpretation: evalResult.interpretation,
        reference_range_text: "97.8 - 99.0 °F",
        effective_date_time: "Just now (Self-reported)",
      };
      setVitalsList((prev) => [newObs, ...prev.filter((v) => v.code_value !== LOINC_CODES.BODY_TEMPERATURE)]);
      setVitalsTimeSeries((prev) => [
        ...prev,
        {
          timestamp: nowIso,
          dateLabel,
          fullDateTime,
          temperature: temp,
          interpretation: evalResult.interpretation,
        },
      ]);
      try {
        await apiClient.recordObservation(patientId, {
          category: "vital-signs",
          code_value: LOINC_CODES.BODY_TEMPERATURE,
          code_display: "Body temperature",
          value_quantity: temp,
          value_unit: "[degF]",
          interpretation: evalResult.interpretation,
        });
      } catch (err) {
        console.info("Recorded locally in memory", err);
      }
    }
    setIsLogVitalsOpen(false);
  };

  const handleViewFhirRx = async (rxId: string) => {
    try {
      setFetchingFhirId(rxId);
      const fhirRes = await apiClient.getPrescriptionFhir(rxId);
      setViewingFhirRx(fhirRes);
    } catch (err) {
      console.error("Failed to load FHIR MedicationRequest", err);
    } finally {
      setFetchingFhirId(null);
    }
  };

  const handleConditionUpdated = async (condId: string, updateData: any) => {
    try {
      await apiClient.updateCondition(condId, {
        severity: updateData.severity,
        note: updateData.patientNote,
      });
    } catch (err) {
      console.info("Could not sync symptom update with backend, updating local state", err);
    }
    setConditions((prev) =>
      prev.map((c) =>
        c.id === condId
          ? {
              ...c,
              severity: updateData.severity,
              note: `${c.note ? c.note + " | " : ""}[Patient Log: ${updateData.trend}] ${updateData.patientNote}`,
              updated_at: new Date().toISOString(),
            }
          : c
      )
    );
  };

  const handleViewFhirCondition = async (cond: ClinicalCondition) => {
    try {
      const fhirData = await apiClient.getConditionFhir(cond.id);
      setSelectedFhirJson(fhirData);
    } catch {
      // Valid HL7 FHIR R4 Condition representation fallback
      setSelectedFhirJson({
        resourceType: "Condition",
        id: cond.id,
        meta: {
          profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Condition"],
          versionId: "1",
          lastUpdated: cond.updated_at,
        },
        clinicalStatus: {
          coding: [
            {
              system: "http://terminology.hl7.org/CodeSystem/condition-clinical",
              code: cond.clinical_status,
              display: cond.clinical_status.toUpperCase(),
            },
          ],
        },
        verificationStatus: {
          coding: [
            {
              system: "http://terminology.hl7.org/CodeSystem/condition-ver-status",
              code: cond.verification_status,
              display: cond.verification_status.toUpperCase(),
            },
          ],
        },
        category: [
          {
            coding: [
              {
                system: "http://terminology.hl7.org/CodeSystem/condition-category",
                code: cond.category,
                display: cond.category,
              },
            ],
          },
        ],
        severity: cond.severity
          ? {
              coding: [
                {
                  system: "http://snomed.info/sct",
                  code: cond.severity === "severe" ? "24484000" : cond.severity === "moderate" ? "6736007" : "255604002",
                  display: cond.severity.toUpperCase(),
                },
              ],
            }
          : undefined,
        code: {
          coding: [
            {
              system: cond.code_coding_system,
              code: cond.code_value,
              display: cond.code_display,
            },
          ],
          text: cond.code_display,
        },
        subject: {
          reference: `Patient/${cond.patient_id}`,
          display: user?.fullName || "Arun Patel",
        },
        onsetDateTime: cond.onset_date_time,
        recordedDate: cond.created_at,
        note: cond.note ? [{ text: cond.note }] : undefined,
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 bg-white min-h-screen">
      
      {/* 1. Cal.com Patient Header Shell */}
      <PatientHeader
        patientName={user?.fullName || "Arun Patel"}
        abhaId={user?.abhaId || "91-8472-1092-4821"}
        abhaAddress="arun.patel@abdm"
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onExportFhir={() => alert("Downloading encrypted HL7 FHIR Bundle...")}
      />

      {/* 2. Cal.com Metrics Overview Bar */}
      {(() => {
        const latestBpObs = vitalsList.find((v) => v.code_value === "85354-9" || v.code_value === LOINC_CODES.BLOOD_PRESSURE_PANEL);
        const dynamicBpText = latestBpObs?.components && latestBpObs.components.length >= 2
          ? `${latestBpObs.components[0].value_quantity}/${latestBpObs.components[1].value_quantity} mmHg`
          : "134/86 mmHg";
        const latestSpo2Obs = vitalsList.find((v) => v.code_value === "2708-6" || v.code_value === LOINC_CODES.OXYGEN_SATURATION);
        const dynamicSpo2Text = latestSpo2Obs?.value_quantity ? `${latestSpo2Obs.value_quantity}%` : "98%";
        const dynamicStatus: "normal" | "abnormal" =
          latestBpObs?.interpretation === "high" || latestBpObs?.interpretation === "critically-high" ||
          latestSpo2Obs?.interpretation === "low" || latestSpo2Obs?.interpretation === "critically-low"
            ? "abnormal"
            : "normal";

        return (
          <PatientMetricsBar
            activePrescriptionsCount={prescriptions.length}
            upcomingAppointmentsCount={scheduledAppointments.length}
            conditionsCount={conditions.filter((c) => c.clinical_status === "active").length}
            latestBpText={dynamicBpText}
            latestSpo2Text={dynamicSpo2Text}
            latestVitalsStatus={dynamicStatus}
            onSelectTab={setActiveTab}
            onOpenLogVitals={() => setIsLogVitalsOpen(true)}
          />
        );
      })()}

      {/* 3. Cal.com Segmented Nav-Pill-Group */}
      <PatientNavTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        prescriptionsBadgeCount={prescriptions.length}
        conditionsBadgeCount={conditions.filter((c) => c.clinical_status === "active").length}
      />

      {/* 4. Active Tab Views */}
      {activeTab === "overview" && (
        <PatientOverviewTab
          abhaId={abhaCardData.abhaId}
          abhaAddress={abhaCardData.abhaAddress}
          patientName={abhaCardData.patientName}
          gender={abhaCardData.gender}
          dob={abhaCardData.dob}
          mobile={abhaCardData.mobile}
          bloodGroup={abhaCardData.bloodGroup}
          stateNode={abhaCardData.stateNode}
          distName={abhaCardData.distName}
          emergencyContact={abhaCardData.emergencyContact}
          organDonor={abhaCardData.organDonor}
          qrPayload={abhaCardData.qrPayload}
          onOpenExport={() => setIsExportModalOpen(true)}
          onOpenVerify={() => setIsVerifyModalOpen(true)}
          onOpenCreateAbha={() => setIsAbhaCreationModalOpen(true)}
          consentActive={consentActive}
          onToggleConsent={setConsentActive}
          scheduledAppointments={scheduledAppointments}
          prescriptions={prescriptions}
          vitalsList={vitalsList}
          onSelectTab={setActiveTab}
          onOpenLogVitals={() => setIsLogVitalsOpen(true)}
          onViewFhirPrescription={(rx) => handleViewFhirRx(rx.id)}
          onStartTelemedicine={(appt) => {
            setActiveConsultationAppt(appt);
            setIsTelemedicineModalOpen(true);
          }}
        />
      )}

      {activeTab === "prescriptions" && (
        <PatientPrescriptionsTab
          prescriptions={prescriptions}
          loading={loadingPrescriptions}
          onRefresh={loadPrescriptions}
          onViewFhir={handleViewFhirRx}
          fetchingFhirId={fetchingFhirId}
        />
      )}

      {activeTab === "problems" && (
        <PatientProblemsTab
          conditions={conditions}
          loading={loadingConditions}
          onRefresh={loadConditions}
          onViewFhir={handleViewFhirCondition}
          onConditionUpdated={handleConditionUpdated}
        />
      )}

      {activeTab === "records" && (
        <PatientRecordsTab
          vitalsList={vitalsList}
          timeSeriesData={vitalsTimeSeries}
          patientLabReports={patientLabReports}
          patientLabOrders={patientLabOrders}
          onOpenLogVitals={() => setIsLogVitalsOpen(true)}
          onInspectFhir={(fhir) => setSelectedFhirJson(fhir)}
        />
      )}

      {activeTab === "book" && (
        <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
          {/* Clinician Directory Selector */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[#111111] tracking-tight">
                  Choose Clinical Specialist
                </h2>
                <p className="text-xs text-[#6b7280]">
                  Select an accredited practitioner to view real-time consultation availability.
                </p>
              </div>
              <Badge variant="default" size="sm">
                {CLINICIANS.length} Available
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {CLINICIANS.map((doc) => {
                const isSelected = selectedDoctor.id === doc.id;
                return (
                  <button
                    key={doc.id}
                    type="button"
                    onClick={() => {
                      setSelectedDoctor(doc);
                      setSelectedSlot(null);
                      setActiveHold(null);
                    }}
                    className={`p-4 rounded-[12px] border text-left transition-all cursor-pointer ${
                      isSelected
                        ? "bg-[#f8f9fa] border-[#111111] shadow-xs"
                        : "bg-white border-[#e5e7eb] hover:bg-[#f8f9fa] hover:border-[#d1d5db]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                        isSelected ? "bg-[#111111] text-white" : "bg-[#f5f5f5] text-[#111111]"
                      }`}>
                        {doc.name.replace("Dr. ", "").split(" ").map((n) => n[0]).join("")}
                      </div>
                      <div>
                        <div className="font-bold text-sm text-[#111111]">
                          {doc.name}
                        </div>
                        <div className="text-xs text-[#059669] font-medium">
                          {doc.specialty}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-[#e5e7eb] flex items-center justify-between text-xs">
                      <span className="text-[#6b7280]">{doc.affiliation}</span>
                      <span className="font-bold text-[#111111]">₹{doc.fee}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Embedded Interactive Slot Picker */}
          <ClinicalSlotPicker
            doctorId={selectedDoctor.id}
            doctorName={selectedDoctor.name}
            specialty={selectedDoctor.specialty}
            consultationFee={selectedDoctor.fee}
            selectedSlot={selectedSlot}
            onSelectSlot={(slot) => setSelectedSlot(slot)}
            onHoldSlot={handleHoldSlot}
            activeHold={activeHold}
            onReleaseHold={handleReleaseHold}
            isHolding={isHolding}
          />
        </div>
      )}

      {/* Appointment Intake Modal */}
      <AppointmentBookingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        slot={selectedSlot}
        doctorId={selectedDoctor.id}
        doctorName={selectedDoctor.name}
        specialty={selectedDoctor.specialty}
        consultationFee={selectedDoctor.fee}
        activeHold={activeHold}
        onHoldRelease={handleReleaseHold}
        onSuccess={handleBookingSuccess}
      />

      {/* Reusable Modals (Log Vitals, FHIR Observation/Composition, FHIR MedicationRequest) */}
      <PatientModals
        isLogVitalsOpen={isLogVitalsOpen}
        onCloseLogVitals={() => setIsLogVitalsOpen(false)}
        logVitalType={logVitalType}
        setLogVitalType={setLogVitalType}
        logValue={logValue}
        setLogValue={setLogValue}
        logSystolic={logSystolic}
        setLogSystolic={setLogSystolic}
        logDiastolic={logDiastolic}
        setLogDiastolic={setLogDiastolic}
        logWeight={logWeight}
        setLogWeight={setLogWeight}
        logHeight={logHeight}
        setLogHeight={setLogHeight}
        logTemp={logTemp}
        setLogTemp={setLogTemp}
        onLogVitalSubmit={handleLogVitalSubmit}
        selectedFhirJson={selectedFhirJson}
        onCloseFhirModal={() => setSelectedFhirJson(null)}
        viewingFhirRx={viewingFhirRx}
        onCloseFhirRxModal={() => setViewingFhirRx(null)}
      />

      {/* ABHA ID Card High-Res Export & Print Modal */}
      <AbhaCardExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        cardData={abhaCardData}
      />

      {/* ABDM Cryptographic QR Code Verification & Inspector Modal */}
      <AbhaQrVerificationModal
        isOpen={isVerifyModalOpen}
        onClose={() => setIsVerifyModalOpen(false)}
        defaultQrPayload={abhaCardData.qrPayload}
        patientName={abhaCardData.patientName}
        abhaId={abhaCardData.abhaId}
      />

      {/* ABDM 14-Digit ABHA Generation & @abdm PHR Address Reservation Modal (Day 44) */}
      <AbhaCreationModal
        isOpen={isAbhaCreationModalOpen}
        onClose={() => setIsAbhaCreationModalOpen(false)}
        defaultPatientName={abhaCardData.patientName}
        defaultGender={abhaCardData.gender}
        defaultDob={abhaCardData.dob}
        defaultMobile={abhaCardData.mobile}
        onSuccess={(cred) => {
          setAbhaCardData((prev) => ({
            ...prev,
            abhaId: cred.abhaNumber,
            abhaAddress: cred.phrAddress,
          }));
        }}
      />

      {/* Telemedicine WebRTC Device & Bandwidth Readiness Modal (Day 35) */}
      <TelemedicineReadinessModal
        isOpen={isTelemedicineModalOpen}
        onClose={() => setIsTelemedicineModalOpen(false)}
        doctorName={activeConsultationAppt?.doctor_name || "Dr. Ananya Sharma"}
        doctorSpecialty={activeConsultationAppt?.doctor_specialty || "Chief Cardiologist, AIIMS"}
        appointmentTime={
          activeConsultationAppt
            ? new Date(activeConsultationAppt.scheduled_start).toLocaleString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: true,
              })
            : "Today, In 15 minutes"
        }
        roomToken={`nirmaya-webrtc-${activeConsultationAppt?.id || "consult-8472"}`}
        onJoinRoom={() => {
          alert(`Connecting to peer WebRTC session with ${activeConsultationAppt?.doctor_name || "Dr. Ananya Sharma"}...`);
          setIsTelemedicineModalOpen(false);
        }}
      />

    </div>
  );
}
