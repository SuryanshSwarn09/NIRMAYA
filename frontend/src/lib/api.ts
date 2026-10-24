/**
 * NIRMAYA Frontend API Client
 * Typed service layer for communicating with the FastAPI backend.
 */

export interface APIResponseEnvelope<T = unknown> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  request_id?: string;
}

export interface PaginationMeta {
  total_count: number;
  page: number;
  limit: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface ErrorDetail {
  location?: string;
  message: string;
  error_type?: string;
}

export interface ErrorResponseEnvelope {
  success: boolean;
  error_code: string;
  message: string;
  details: ErrorDetail[];
  timestamp: string;
  request_id?: string;
}

export class APIError extends Error {
  errorCode: string;
  status: number;
  details: ErrorDetail[];
  requestId?: string;

  constructor(errorData: ErrorResponseEnvelope, status: number) {
    super(errorData.message || "An unexpected error occurred");
    this.name = "APIError";
    this.errorCode = errorData.error_code || "UNKNOWN_ERROR";
    this.status = status;
    this.details = errorData.details || [];
    this.requestId = errorData.request_id;
  }
}

export interface RequestOptions extends RequestInit {
  token?: string;
  params?: Record<string, string | number | boolean | undefined>;
}

// ============================================================================
// Clinical Scheduling & Slot Models
// ============================================================================

export type SlotStatus = "available" | "held" | "booked" | "blocked";

export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "no_show";

export type AppointmentType =
  | "routine_checkup"
  | "follow_up"
  | "teleconsultation"
  | "emergency";

export interface DoctorProfile {
  id: string;
  user_id: string;
  full_name?: string;
  email?: string;
  registration_number: string;
  medical_council: string;
  specialty: string;
  qualifications?: string;
  experience_years?: number;
  consultation_fee: number;
  hospital_affiliation?: string;
  teleconsultation_available: boolean;
  hpr_id?: string;
}

export interface DoctorSlot {
  id: string;
  doctor_id: string;
  start_time: string;
  end_time: string;
  status: SlotStatus;
  is_teleconsult: boolean;
  held_until?: string | null;
  held_by_patient_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SlotHoldResponse {
  slot_id: string;
  doctor_id: string;
  status: SlotStatus;
  held_until: string;
  held_by_patient_id: string;
  hold_duration_seconds: number;
}

export interface SlotReleaseResponse {
  slot_id: string;
  status: SlotStatus;
  released: boolean;
}

export interface SlotGenerateRequest {
  doctor_id?: string;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  day_start_hour?: number;
  day_start_minute?: number;
  day_end_hour?: number;
  day_end_minute?: number;
  slot_duration_minutes?: number;
  break_start_hour?: number;
  break_start_minute?: number;
  break_end_hour?: number;
  break_end_minute?: number;
  is_teleconsult?: boolean;
}

export interface SlotGenerateResult {
  total_generated: number;
  total_skipped_existing: number;
  slots: DoctorSlot[];
}

export interface AppointmentCreate {
  doctor_id: string;
  slot_id?: string;
  scheduled_start?: string;
  scheduled_end?: string;
  appointment_type?: AppointmentType;
  reason?: string;
  clinical_notes?: string;
  teleconsultation_url?: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  slot_id?: string | null;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  scheduled_start: string;
  scheduled_end: string;
  reason?: string | null;
  clinical_notes?: string | null;
  teleconsultation_url?: string | null;
  created_at: string;
  updated_at: string;
  doctor_name?: string | null;
  doctor_specialty?: string | null;
  patient_name?: string | null;
}

export interface ABDMConsentLinkage {
  careContextReference: string;
  patientReference: string;
  hiType: string;
  hipId: string;
  consentArtifactId?: string | null;
  timestamp: string;
  signature: string;
  bundle: Record<string, unknown>;
}

class NIRMAYAAPIClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = (
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    ).replace(/\/$/, "");
  }

  private buildUrl(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>
  ): string {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseUrl}${cleanEndpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  private getAuthToken(overrideToken?: string): string | null {
    if (overrideToken) return overrideToken;
    if (typeof window !== "undefined") {
      try {
        return localStorage.getItem("nirmaya_token");
      } catch {
        return null;
      }
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { token, params, headers = {}, ...restOptions } = options;
    const url = this.buildUrl(endpoint, params);
    const resolvedToken = this.getAuthToken(token);

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(headers as Record<string, string>),
    };

    if (resolvedToken) {
      requestHeaders["Authorization"] = `Bearer ${resolvedToken}`;
    }

    const response = await fetch(url, {
      headers: requestHeaders,
      ...restOptions,
    });

    if (!response.ok) {
      let errorPayload: ErrorResponseEnvelope;
      try {
        errorPayload = await response.json();
      } catch {
        errorPayload = {
          success: false,
          error_code: `HTTP_${response.status}`,
          message: response.statusText || "Request failed",
          details: [],
          timestamp: new Date().toISOString(),
        };
      }
      throw new APIError(errorPayload, response.status);
    }

    const json = (await response.json()) as Record<string, unknown>;
    // If it is a paginated response containing pagination metadata, return the full envelope
    if ("pagination" in json) {
      return json as unknown as T;
    }
    // If wrapped in standard APIResponse, return the inner data
    return json.data !== undefined ? (json.data as T) : (json as unknown as T);
  }

  public get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { method: "GET", ...options });
  }

  public post<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  public put<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE", ...options });
  }

  /**
   * Healthcheck probe for validating backend connectivity.
   */
  public async checkHealth() {
    return this.get<{
      status: string;
      project: string;
      version: string;
      standards: {
        fhir_version: string;
        abdm_sandbox: boolean;
      };
    }>("/api/v1/health");
  }

  /**
   * Auth API helpers
   */
  public async getMe(token?: string) {
    return this.get<Record<string, unknown>>("/api/v1/auth/me", { token });
  }

  public async verifyToken(token: string) {
    return this.post<{ valid: boolean; claims?: Record<string, unknown> }>(
      "/api/v1/auth/verify",
      { token }
    );
  }

  public async issueTestToken(payload: {
    email: string;
    role: string;
    sub?: string;
    expires_minutes?: number;
  }) {
    return this.post<{ access_token: string }>(
      "/api/v1/auth/test-token",
      payload
    );
  }

  // ==========================================================================
  // Doctor & Provider Directory Methods
  // ==========================================================================

  public async getDoctors(params?: {
    query?: string;
    specialty?: string;
    teleconsult_only?: boolean;
    max_fee?: number;
    page?: number;
    limit?: number;
  }) {
    return this.get<DoctorProfile[]>("/api/v1/doctors/", { params });
  }

  public async getDoctorById(doctorId: string) {
    return this.get<DoctorProfile>(`/api/v1/doctors/${doctorId}`);
  }

  // ==========================================================================
  // Doctor Consultation Slots & Availability Engine
  // ==========================================================================

  public async getDoctorSlots(
    doctorId: string,
    params?: {
      target_date?: string;
      start_date?: string;
      end_date?: string;
      slot_status?: SlotStatus;
      is_teleconsult?: boolean;
    }
  ) {
    return this.get<DoctorSlot[]>(`/api/v1/doctors/${doctorId}/slots`, {
      params,
    });
  }

  public async generateDoctorSlots(
    doctorId: string,
    payload: SlotGenerateRequest
  ) {
    return this.post<SlotGenerateResult>(
      `/api/v1/doctors/${doctorId}/slots/generate`,
      payload
    );
  }

  public async holdDoctorSlot(
    doctorId: string,
    slotId: string,
    durationMinutes: number = 10
  ) {
    return this.post<SlotHoldResponse>(
      `/api/v1/doctors/${doctorId}/slots/${slotId}/hold`,
      { hold_duration_minutes: durationMinutes }
    );
  }

  public async releaseDoctorSlot(doctorId: string, slotId: string) {
    return this.post<SlotReleaseResponse>(
      `/api/v1/doctors/${doctorId}/slots/${slotId}/release`
    );
  }

  // ==========================================================================
  // Clinical Appointments & Encounter Lifecycle
  // ==========================================================================

  public async bookAppointment(payload: AppointmentCreate) {
    return this.post<Appointment>("/api/v1/appointments/", payload);
  }

  public async getAppointments(params?: {
    patient_id?: string;
    doctor_id?: string;
    status?: AppointmentStatus;
    page?: number;
    limit?: number;
  }) {
    return this.get<Appointment[]>("/api/v1/appointments/", { params });
  }

  public async getAppointmentById(appointmentId: string) {
    return this.get<Appointment>(`/api/v1/appointments/${appointmentId}`);
  }

  public async updateAppointmentStatus(
    appointmentId: string,
    payload: {
      status: AppointmentStatus;
      clinical_notes?: string;
      cancellation_reason?: string;
    }
  ) {
    return this.patch<Appointment>(
      `/api/v1/appointments/${appointmentId}/status`,
      payload
    );
  }

  // ==========================================================================
  // HL7 FHIR Release 4 & ABDM Consent Artifacts
  // ==========================================================================

  public async getAppointmentFhir(appointmentId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/appointments/${appointmentId}/fhir`
    );
  }

  public async getAppointmentEncounter(appointmentId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/appointments/${appointmentId}/encounter`
    );
  }

  public async getAppointmentFhirBundle(appointmentId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/appointments/${appointmentId}/fhir-bundle`
    );
  }

  public async linkAbdmConsent(
    appointmentId: string,
    payload?: { hip_id?: string; consent_artifact_id?: string }
  ) {
    return this.post<ABDMConsentLinkage>(
      `/api/v1/appointments/${appointmentId}/abdm/link-consent`,
      payload
    );
  }

  // ==========================================================================
  // Clinical Conditions & Longitudinal Problem List
  // ==========================================================================

  public async recordCondition(patientId: string, payload: ConditionCreate) {
    return this.post<ClinicalCondition>(
      `/api/v1/patients/${patientId}/conditions`,
      payload
    );
  }

  public async getPatientConditions(
    patientId: string,
    params?: {
      clinical_status?: ClinicalStatus;
      verification_status?: VerificationStatus;
      category?: ConditionCategory;
      severity?: ConditionSeverity;
      encounter_id?: string;
      page?: number;
      limit?: number;
    }
  ) {
    return this.get<PaginatedResponse<ClinicalCondition>>(
      `/api/v1/patients/${patientId}/conditions`,
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getConditionById(conditionId: string) {
    return this.get<ClinicalCondition>(`/api/v1/conditions/${conditionId}`);
  }

  public async updateCondition(
    conditionId: string,
    payload: Partial<ConditionCreate>
  ) {
    return this.patch<ClinicalCondition>(
      `/api/v1/conditions/${conditionId}`,
      payload
    );
  }

  public async getConditionFhir(conditionId: string) {
    return this.get<Record<string, unknown>>(`/api/v1/conditions/${conditionId}/fhir`);
  }

  // ==========================================================================
  // Clinical Observations & Vital Signs Telemetry
  // ==========================================================================

  public async recordObservation(
    patientId: string,
    payload: Partial<ClinicalObservation>
  ) {
    return this.post<ClinicalObservation>(
      `/api/v1/patients/${patientId}/observations`,
      payload
    );
  }

  public async getPatientObservations(
    patientId: string,
    params?: Record<string, string | number | boolean | undefined>
  ) {
    return this.get<ClinicalObservation[]>(
      `/api/v1/patients/${patientId}/observations`,
      { params }
    );
  }

  public async getLatestVitals(patientId: string) {
    return this.get<VitalsSummary>(
      `/api/v1/patients/${patientId}/observations/vitals/latest`
    );
  }

  public async getObservationById(observationId: string) {
    return this.get<ClinicalObservation>(
      `/api/v1/observations/${observationId}`
    );
  }

  public async updateObservation(
    observationId: string,
    payload: {
      status?: ObservationStatus;
      interpretation?: ObservationInterpretation;
      note?: string;
    }
  ) {
    return this.patch<ClinicalObservation>(
      `/api/v1/observations/${observationId}`,
      payload
    );
  }

  public async getObservationFhir(observationId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/observations/${observationId}/fhir`
    );
  }

  // ==========================================================================
  // Structured SOAP Clinical Notes Methods
  // ==========================================================================

  public async createSoapNote(patientId: string, payload: SoapNoteCreate) {
    return this.post<SoapNote>(
      `/api/v1/patients/${patientId}/soap-notes`,
      payload
    );
  }

  public async getPatientSoapNotes(
    patientId: string,
    params?: {
      status?: ClinicalNoteStatus;
      note_type?: ClinicalNoteType;
      encounter_id?: string;
      is_signed?: boolean;
      page?: number;
      limit?: number;
    }
  ) {
    return this.get<PaginatedResponse<SoapNote>>(
      `/api/v1/patients/${patientId}/soap-notes`,
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getSoapNoteById(noteId: string) {
    return this.get<SoapNote>(`/api/v1/soap-notes/${noteId}`);
  }

  public async updateSoapNote(
    noteId: string,
    payload: Partial<SoapNoteCreate>
  ) {
    return this.patch<SoapNote>(`/api/v1/soap-notes/${noteId}`, payload);
  }

  public async signSoapNote(
    noteId: string,
    payload?: { comments?: string }
  ) {
    return this.post<SoapNote>(`/api/v1/soap-notes/${noteId}/sign`, payload);
  }

  public async getSoapNoteFhir(noteId: string) {
    return this.get<Record<string, unknown>>(`/api/v1/soap-notes/${noteId}/fhir`);
  }

  // Diagnostic Orders (ServiceRequest)
  public async createDiagnosticOrder(
    patientId: string,
    payload: DiagnosticOrderCreate
  ) {
    return this.post<DiagnosticOrder>(
      `/api/v1/patients/${patientId}/diagnostic-orders`,
      payload
    );
  }

  public async getPatientDiagnosticOrders(
    patientId: string,
    params?: {
      status?: ServiceRequestStatus;
      priority?: ServiceRequestPriority;
      encounter_id?: string;
      page?: number;
      limit?: number;
    }
  ) {
    return this.get<PaginatedResponse<DiagnosticOrder>>(
      `/api/v1/patients/${patientId}/diagnostic-orders`,
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getDiagnosticOrderById(orderId: string) {
    return this.get<DiagnosticOrder>(`/api/v1/diagnostic-orders/${orderId}`);
  }

  public async updateDiagnosticOrder(
    orderId: string,
    payload: Partial<DiagnosticOrderCreate>
  ) {
    return this.patch<DiagnosticOrder>(
      `/api/v1/diagnostic-orders/${orderId}`,
      payload
    );
  }

  public async getDiagnosticOrderFhir(orderId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/diagnostic-orders/${orderId}/fhir`
    );
  }

  // Diagnostic Reports (DiagnosticReport)
  public async createDiagnosticReport(
    patientId: string,
    payload: DiagnosticReportCreate
  ) {
    return this.post<DiagnosticReport>(
      `/api/v1/patients/${patientId}/diagnostic-reports`,
      payload
    );
  }

  public async getPatientDiagnosticReports(
    patientId: string,
    params?: {
      status?: DiagnosticReportStatus;
      is_abnormal?: boolean;
      encounter_id?: string;
      order_id?: string;
      page?: number;
      limit?: number;
    }
  ) {
    return this.get<PaginatedResponse<DiagnosticReport>>(
      `/api/v1/patients/${patientId}/diagnostic-reports`,
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getDiagnosticReportById(reportId: string) {
    return this.get<DiagnosticReport>(`/api/v1/diagnostic-reports/${reportId}`);
  }

  public async getDiagnosticReportFhir(reportId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/diagnostic-reports/${reportId}/fhir`
    );
  }

  // Medication Formulary
  public async listMedications(params?: {
    q?: string;
    form?: MedicationForm;
    route?: AdministrationRoute;
    tier?: FormularyTier;
    atc_prefix?: string;
    is_prescription_required?: boolean;
    is_controlled_substance?: boolean;
    status?: MedicationStatus;
    page?: number;
    limit?: number;
    offset?: number;
  }) {
    return this.get<PaginatedResponse<Medication>>(
      "/api/v1/medications",
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getMedicationById(id: string) {
    return this.get<Medication>(`/api/v1/medications/${id}`);
  }

  public async getMedicationFhir(id: string) {
    return this.get<Record<string, unknown>>(`/api/v1/medications/${id}/fhir`);
  }

  public async getTherapeuticClasses() {
    return this.get<TherapeuticClassSummary[]>("/api/v1/medications/classes");
  }

  public async createMedication(payload: MedicationCreate) {
    return this.post<Medication>("/api/v1/medications", payload);
  }

  public async updateMedication(id: string, payload: Partial<MedicationCreate>) {
    return this.patch<Medication>(`/api/v1/medications/${id}`, payload);
  }

  // ==========================================================================
  // Electronic Prescriptions (MedicationRequest) Methods
  // ==========================================================================

  public async createPrescription(
    patientId: string,
    payload: MedicationRequestCreatePayload
  ) {
    return this.post<MedicationRequest>(
      `/api/v1/patients/${patientId}/prescriptions`,
      payload
    );
  }

  public async getPatientPrescriptions(
    patientId: string,
    params?: {
      status?: MedicationRequestStatus;
      is_signed?: boolean;
      doctor_id?: string;
      encounter_id?: string;
      page?: number;
      limit?: number;
    }
  ) {
    return this.get<PaginatedResponse<MedicationRequest>>(
      `/api/v1/patients/${patientId}/prescriptions`,
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getPrescriptionById(prescriptionId: string) {
    return this.get<MedicationRequest>(`/api/v1/prescriptions/${prescriptionId}`);
  }

  public async updatePrescription(
    prescriptionId: string,
    payload: MedicationRequestUpdatePayload
  ) {
    return this.patch<MedicationRequest>(
      `/api/v1/prescriptions/${prescriptionId}`,
      payload
    );
  }

  public async signPrescription(
    prescriptionId: string,
    payload?: { signature_notes?: string }
  ) {
    return this.post<MedicationRequest>(
      `/api/v1/prescriptions/${prescriptionId}/sign`,
      payload || {}
    );
  }

  public async cancelPrescription(
    prescriptionId: string,
    cancellationReason: string
  ) {
    return this.post<MedicationRequest>(
      `/api/v1/prescriptions/${prescriptionId}/cancel`,
      { cancellation_reason: cancellationReason }
    );
  }

  public async getPrescriptionFhir(prescriptionId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/prescriptions/${prescriptionId}/fhir`
    );
  }

  // ==========================================================================
  // Clinical Decision Support (CDS) Safety Engine
  // ==========================================================================

  public async evaluatePrescriptionSafety(
    patientId: string,
    payload: SafetyCheckPayload
  ) {
    return this.post<SafetyCheckResponse>(
      `/api/v1/patients/${patientId}/prescriptions/safety-check`,
      payload
    );
  }

  // ==========================================================================
  // Pharmacy Medication Dispense & Fulfillment
  // ==========================================================================

  public async dispensePrescription(
    prescriptionId: string,
    payload: MedicationDispenseCreatePayload
  ) {
    return this.post<MedicationDispense>(
      `/api/v1/prescriptions/${prescriptionId}/dispense`,
      payload
    );
  }

  public async getDispensations(params?: {
    patient_id?: string;
    prescription_id?: string;
    lot_number?: string;
    status?: MedicationDispenseStatus;
    skip?: number;
    limit?: number;
  }) {
    return this.get<PaginatedResponse<MedicationDispense>>(
      `/api/v1/dispensations`,
      { params: params as Record<string, string | number | boolean | undefined> }
    );
  }

  public async getDispenseFhir(dispenseId: string) {
    return this.get<Record<string, unknown>>(
      `/api/v1/dispensations/${dispenseId}/fhir`
    );
  }

  // ==========================================================================
  // ABDM Digital ABHA ID Card & QR Verification
  // ==========================================================================

  public async getPatientAbhaCard(patientId: string) {
    return this.get<AbhaCardApiResponse>(`/api/v1/patients/${patientId}/abha-card`);
  }

  public async verifyAbhaQr(qrString: string) {
    return this.post<AbhaQrVerificationApiResponse>(
      `/api/v1/patients/verify-abha-qr`,
      { qr_string: qrString }
    );
  }

  public patch<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }
}

// ============================================================================
// Clinical Conditions & Problem List Types
// ============================================================================

export type ClinicalStatus =
  | "active"
  | "recurrence"
  | "relapse"
  | "inactive"
  | "remission"
  | "resolved";

export type VerificationStatus =
  | "unconfirmed"
  | "provisional"
  | "differential"
  | "confirmed"
  | "refuted"
  | "entered-in-error";

export type ConditionCategory =
  | "problem-list-item"
  | "encounter-diagnosis"
  | "chronic-condition";

export type ConditionSeverity = "mild" | "moderate" | "severe";

export interface ClinicalCondition {
  id: string;
  patient_id: string;
  encounter_id?: string;
  recorder_doctor_id?: string;
  clinical_status: ClinicalStatus;
  verification_status: VerificationStatus;
  category: ConditionCategory;
  severity?: ConditionSeverity;
  code_coding_system: string;
  code_value: string;
  code_display: string;
  body_site?: string;
  onset_date_time?: string;
  abatement_date_time?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface ConditionCreate {
  encounter_id?: string;
  clinical_status?: ClinicalStatus;
  verification_status?: VerificationStatus;
  category?: ConditionCategory;
  severity?: ConditionSeverity;
  code_coding_system?: string;
  code_value: string;
  code_display: string;
  body_site?: string;
  onset_date_time?: string;
  abatement_date_time?: string;
  note?: string;
}

// ============================================================================
// Clinical Observation & Vital Signs Types
// ============================================================================

export type ObservationStatus =
  | "registered"
  | "preliminary"
  | "final"
  | "amended"
  | "corrected"
  | "cancelled"
  | "entered-in-error"
  | "unknown";

export type ObservationCategory =
  | "vital-signs"
  | "laboratory"
  | "imaging"
  | "exam"
  | "therapy"
  | "activity"
  | "social-history";

export type ObservationInterpretation =
  | "normal"
  | "high"
  | "low"
  | "critically-high"
  | "critically-low"
  | "abnormal";

export interface ObservationComponent {
  code_system: string;
  code_value: string;
  code_display: string;
  value_quantity: number;
  value_unit: string;
  value_code?: string;
  interpretation?: ObservationInterpretation;
  reference_range_low?: number;
  reference_range_high?: number;
}

export interface ClinicalObservation {
  id: string;
  patient_id: string;
  encounter_id?: string;
  performer_doctor_id?: string;
  status: ObservationStatus;
  category: ObservationCategory;
  code_coding_system: string;
  code_value: string;
  code_display: string;
  effective_date_time: string;
  issued_date_time: string;
  value_quantity?: number;
  value_unit?: string;
  value_system?: string;
  value_code?: string;
  value_string?: string;
  components?: ObservationComponent[];
  reference_range_low?: number;
  reference_range_high?: number;
  reference_range_text?: string;
  interpretation?: ObservationInterpretation;
  body_site?: string;
  method?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface VitalsSummary {
  blood_pressure?: ClinicalObservation;
  heart_rate?: ClinicalObservation;
  respiratory_rate?: ClinicalObservation;
  body_temperature?: ClinicalObservation;
  oxygen_saturation?: ClinicalObservation;
  body_mass_index?: ClinicalObservation;
  weight?: ClinicalObservation;
  height?: ClinicalObservation;
  blood_glucose?: ClinicalObservation;
  last_recorded_at?: string;
}

// ============================================================================
// Structured SOAP Clinical Notes Types
// ============================================================================

export type ClinicalNoteType =
  | "soap"
  | "consultation"
  | "progress-note"
  | "discharge-summary";

export type ClinicalNoteStatus =
  | "preliminary"
  | "final"
  | "amended"
  | "entered-in-error";

export interface SoapNote {
  id: string;
  patient_id: string;
  doctor_id?: string;
  encounter_id?: string;
  note_type: ClinicalNoteType;
  status: ClinicalNoteStatus;
  title: string;
  chief_complaint: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  primary_diagnosis_code?: string;
  primary_diagnosis_display?: string;
  follow_up_instructions?: string;
  is_signed: boolean;
  signed_at?: string;
  signature_hash?: string;
  created_at: string;
  updated_at: string;
}

export interface SoapNoteCreate {
  encounter_id?: string;
  doctor_id?: string;
  note_type?: ClinicalNoteType;
  title?: string;
  chief_complaint: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  primary_diagnosis_code?: string;
  primary_diagnosis_display?: string;
  follow_up_instructions?: string;
  status?: ClinicalNoteStatus;
}

// ============================================================================
// Diagnostic Lab Orders (ServiceRequest) & Reports (DiagnosticReport) Types
// ============================================================================

export type ServiceRequestStatus =
  | "draft"
  | "active"
  | "on-hold"
  | "revoked"
  | "completed"
  | "entered-in-error"
  | "unknown";

export type ServiceRequestIntent =
  | "proposal"
  | "plan"
  | "directive"
  | "order"
  | "original-order"
  | "reflex-order"
  | "filler-order"
  | "instance-order"
  | "option";

export type ServiceRequestPriority = "routine" | "urgent" | "asap" | "stat";

export type DiagnosticReportStatus =
  | "registered"
  | "partial"
  | "preliminary"
  | "final"
  | "amended"
  | "corrected"
  | "appended"
  | "cancelled"
  | "entered-in-error"
  | "unknown";

export type SpecimenType =
  | "blood"
  | "serum"
  | "plasma"
  | "urine"
  | "saliva"
  | "csf"
  | "biopsy"
  | "swab"
  | "other";

export interface DiagnosticOrder {
  id: string;
  patient_id: string;
  encounter_id?: string;
  doctor_id?: string;
  status: ServiceRequestStatus;
  intent: ServiceRequestIntent;
  priority: ServiceRequestPriority;
  code_system: string;
  code_value: string;
  code_display: string;
  category: string;
  reason_code?: string;
  reason_display?: string;
  clinical_notes?: string;
  specimen_type: SpecimenType;
  fasting_required: boolean;
  authored_on: string;
  created_at: string;
  updated_at: string;
}

export interface DiagnosticOrderCreate {
  encounter_id?: string;
  doctor_id?: string;
  status?: ServiceRequestStatus;
  intent?: ServiceRequestIntent;
  priority?: ServiceRequestPriority;
  code_system?: string;
  code_value: string;
  code_display: string;
  category?: string;
  reason_code?: string;
  reason_display?: string;
  clinical_notes?: string;
  specimen_type?: SpecimenType;
  fasting_required?: boolean;
}

export interface DiagnosticReport {
  id: string;
  patient_id: string;
  order_id?: string;
  encounter_id?: string;
  performer_doctor_id?: string;
  status: DiagnosticReportStatus;
  category: string;
  code_system: string;
  code_value: string;
  code_display: string;
  effective_date_time: string;
  issued_date_time: string;
  conclusion?: string;
  coded_diagnosis_icd10?: string;
  is_abnormal: boolean;
  observations: ClinicalObservation[];
  created_at: string;
  updated_at: string;
}

export interface DiagnosticReportCreate {
  order_id?: string;
  encounter_id?: string;
  performer_doctor_id?: string;
  status?: DiagnosticReportStatus;
  category?: string;
  code_system?: string;
  code_value: string;
  code_display: string;
  effective_date_time?: string;
  issued_date_time?: string;
  conclusion?: string;
  coded_diagnosis_icd10?: string;
  is_abnormal?: boolean;
  observation_ids?: string[];
}

export const apiClient = new NIRMAYAAPIClient();

// ============================================================================
// Medication Formulary & Catalog Types
// ============================================================================

export type MedicationForm =
  | "tablet"
  | "capsule"
  | "syrup"
  | "injection"
  | "inhaler"
  | "drops"
  | "ointment"
  | "patch"
  | "suspension"
  | "solution"
  | "powder"
  | "other";

export type AdministrationRoute =
  | "oral"
  | "intravenous"
  | "intramuscular"
  | "subcutaneous"
  | "inhalation"
  | "topical"
  | "ophthalmic"
  | "otic"
  | "nasal"
  | "rectal"
  | "sublingual"
  | "transdermal"
  | "other";

export type FormularyTier =
  | "tier_1_generic"
  | "tier_2_preferred_brand"
  | "tier_3_non_preferred_brand"
  | "tier_4_specialty"
  | "tier_5_otc";

export type MedicationStatus = "active" | "inactive" | "entered-in-error";

export interface Medication {
  id: string;
  name: string;
  generic_name: string;
  brand_name?: string;
  rxnorm_code: string;
  rxnorm_display?: string;
  atc_code?: string;
  atc_display?: string;
  snomed_code?: string;
  snomed_display?: string;
  form: MedicationForm;
  route: AdministrationRoute;
  strength: string;
  active_ingredient: string;
  is_prescription_required: boolean;
  is_controlled_substance: boolean;
  formulary_tier: FormularyTier;
  status: MedicationStatus;
  description?: string;
  contraindications_summary?: string;
  storage_instructions?: string;
  package_info?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MedicationCreate {
  name: string;
  generic_name: string;
  brand_name?: string;
  rxnorm_code: string;
  rxnorm_display?: string;
  atc_code?: string;
  atc_display?: string;
  snomed_code?: string;
  snomed_display?: string;
  form?: MedicationForm;
  route?: AdministrationRoute;
  strength: string;
  active_ingredient: string;
  is_prescription_required?: boolean;
  is_controlled_substance?: boolean;
  formulary_tier?: FormularyTier;
  status?: MedicationStatus;
  description?: string;
  contraindications_summary?: string;
  storage_instructions?: string;
  package_info?: Record<string, unknown>;
}

export interface TherapeuticClassSummary {
  atc_prefix: string;
  name: string;
  medication_count: number;
}

export type MedicationRequestStatus =
  | "draft"
  | "active"
  | "on-hold"
  | "cancelled"
  | "completed"
  | "entered-in-error"
  | "stopped";

export type MedicationRequestIntent =
  | "proposal"
  | "plan"
  | "order"
  | "original-order"
  | "reflex-order"
  | "filler-order"
  | "instance-order"
  | "option";

export type MedicationRequestPriority = "routine" | "urgent" | "asap" | "stat";

export interface MedicationRequest {
  id: string;
  patient_id: string;
  doctor_id?: string;
  encounter_id?: string;
  medication_id: string;
  status: MedicationRequestStatus;
  intent: MedicationRequestIntent;
  priority: MedicationRequestPriority;
  dosage_text: string;
  dose_quantity?: number;
  dose_unit?: string;
  route?: AdministrationRoute;
  frequency?: number;
  period?: number;
  period_unit?: string;
  as_needed: boolean;
  as_needed_reason?: string;
  additional_instructions?: string;
  dispense_quantity?: number;
  dispense_unit?: string;
  expected_supply_duration_days?: number;
  number_of_repeats_allowed: number;
  validity_period_start?: string;
  validity_period_end?: string;
  allow_generic_substitution: boolean;
  substitution_reason?: string;
  reason_code?: string;
  reason_reference_id?: string;
  note?: string;
  authored_on: string;
  is_signed: boolean;
  signed_at?: string;
  signature_hash?: string;
  cancellation_reason?: string;
  created_at: string;
  updated_at: string;
  medication?: Medication;
}

export interface MedicationRequestCreatePayload {
  medication_id: string;
  encounter_id?: string;
  intent?: MedicationRequestIntent;
  priority?: MedicationRequestPriority;
  dosage_text: string;
  dose_quantity?: number;
  dose_unit?: string;
  route?: AdministrationRoute;
  frequency?: number;
  period?: number;
  period_unit?: string;
  as_needed?: boolean;
  as_needed_reason?: string;
  additional_instructions?: string;
  dispense_quantity?: number;
  dispense_unit?: string;
  expected_supply_duration_days?: number;
  number_of_repeats_allowed?: number;
  validity_period_start?: string;
  validity_period_end?: string;
  allow_generic_substitution?: boolean;
  substitution_reason?: string;
  reason_code?: string;
  reason_reference_id?: string;
  note?: string;
}

export interface MedicationRequestUpdatePayload {
  dosage_text?: string;
  dose_quantity?: number;
  dose_unit?: string;
  route?: AdministrationRoute;
  frequency?: number;
  period?: number;
  period_unit?: string;
  as_needed?: boolean;
  as_needed_reason?: string;
  additional_instructions?: string;
  dispense_quantity?: number;
  dispense_unit?: string;
  expected_supply_duration_days?: number;
  number_of_repeats_allowed?: number;
  allow_generic_substitution?: boolean;
  note?: string;
}

// ============================================================================
// Clinical Decision Support (CDS) Safety Engine Types
// ============================================================================

export type CDSSeverity = "critical" | "major" | "moderate";

export type CDSAlertType = "drug-drug" | "drug-allergy" | "drug-condition";

export interface SafetyAlert {
  rule_id: string;
  alert_type: CDSAlertType;
  severity: CDSSeverity;
  title: string;
  offending_entity: string;
  mechanism: string;
  recommendation: string;
}

export interface SafetyCheckResponse {
  passed: boolean;
  has_critical_alerts: boolean;
  requires_override: boolean;
  alerts: SafetyAlert[];
  patient_id?: string;
  evaluated_at?: string;
}

export interface SafetyCheckPayload {
  medication_id: string;
  dosage_text?: string;
  supplemental_allergies?: string[];
  supplemental_conditions?: string[];
}

// ============================================================================
// Pharmacy Medication Dispense & Fulfillment Types
// ============================================================================

export type MedicationDispenseStatus =
  | "preparation"
  | "in-progress"
  | "cancelled"
  | "on-hold"
  | "completed"
  | "entered-in-error"
  | "stopped"
  | "declined"
  | "unknown";

export interface MedicationDispense {
  id: string;
  dispense_number: string;
  prescription_id: string;
  patient_id: string;
  medication_id: string;
  dispenser_user_id: string;
  status: MedicationDispenseStatus;
  quantity_dispensed: number;
  dispense_unit: string;
  days_supply?: number;
  dispensed_at: string;
  lot_number?: string;
  expiration_date?: string;
  was_substituted: boolean;
  substitution_type?: string;
  substitution_reason?: string;
  pharmacist_notes?: string;
  patient_instructions?: string;
  dispenser_name?: string;
  medication_name?: string;
  created_at: string;
  updated_at: string;
  prescription?: MedicationRequest;
  medication?: Medication;
}

export interface MedicationDispenseCreatePayload {
  prescription_id?: string;
  medication_id?: string;
  quantity_dispensed: number;
  dispense_unit: string;
  days_supply?: number;
  lot_number?: string;
  expiration_date?: string;
  was_substituted?: boolean;
  substitution_type?: string;
  substitution_reason?: string;
  pharmacist_notes?: string;
  patient_instructions?: string;
}

// ============================================================================
// ABDM Digital ABHA ID Card Models
// ============================================================================

export interface AbhaCardDataPayload {
  patient_id: string;
  abha_number: string;
  abha_address: string;
  name: string;
  gender: string;
  date_of_birth?: string | null;
  year_of_birth?: number | null;
  blood_group: string;
  mobile?: string | null;
  address?: string | null;
  district?: string | null;
  state?: string | null;
  pincode?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_relation?: string | null;
  kyc_status: string;
  auth_methods: string[];
}

export interface AbhaCardApiResponse {
  card_data: AbhaCardDataPayload;
  qr_payload: string;
  signature: string;
  issued_at: string;
}

export interface AbhaQrVerificationApiResponse {
  is_valid: boolean;
  message: string;
  claims?: Record<string, any> | null;
  verified_at: string;
}
