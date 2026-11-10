"""Pydantic v2 schemas for the Strict CoWIN/DigiLocker 3-Tile Citizen Portal.

Defines schemas for:
- Tile 1: My Health ID (ABHA Card, demographic details, OPD Counter QR)
- Tile 2: Active Medicines (Daily plain-language schedule without Latin abbreviations)
- Tile 3: Doctor Visits & Reports (Chronological consultations, plain diagnoses, signed PDFs)
- Aggregated 3-Tile Response for adult self or dependent profiles
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CitizenHealthIdSummary(BaseModel):
    """Tile 1: Clean summary representing citizen's official ABHA health card."""
    patient_id: str = Field(description="Patient Profile UUID")
    abha_number: str = Field(description="14-digit ABHA ID formatted or raw", example="91-8472-1048-2190")
    formatted_abha_number: str = Field(default="", description="14-digit ABHA ID formatted with hyphens", example="91-8472-1048-2190")
    abha_address: str = Field(description="Reserved @abdm handle", example="arun.patel@abdm")
    name: str = Field(description="Certified legal full name", example="Arun Kumar Patel")
    full_name: str = Field(default="", description="Alias for legal full name", example="Arun Kumar Patel")
    gender: str = Field(description="Gender (male, female, other)", example="male")
    date_of_birth: str = Field(description="Date of birth in YYYY-MM-DD format", example="1988-06-15")
    age: int = Field(default=34, description="Calculated patient age in years", example=34)
    blood_group: Optional[str] = Field(default="O+", description="Blood group if recorded", example="O+")
    masked_mobile: Optional[str] = Field(default="+91 ******4821", description="Masked registered phone number")
    mobile_masked: Optional[str] = Field(default="+91 ******4821", description="Alias for masked phone number")
    qr_code_payload: str = Field(description="Scannable ABDM-compliant payload for hospital scanner cameras")
    is_active: bool = Field(default=True, description="Active registration status")
    is_dependent: bool = Field(default=False, description="Whether this is a dependent child or senior")
    relationship_to_guardian: Optional[str] = Field(default=None, description="Relationship if dependent (e.g. Son, Mother)")

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.full_name:
            self.full_name = self.name
        if not self.formatted_abha_number:
            raw = self.abha_number.replace("-", "")
            if len(raw) == 14:
                self.formatted_abha_number = f"{raw[:2]}-{raw[2:6]}-{raw[6:10]}-{raw[10:14]}"
            else:
                self.formatted_abha_number = self.abha_number
        if not self.mobile_masked and self.masked_mobile:
            self.mobile_masked = self.masked_mobile


class PlainScheduleItem(BaseModel):
    """Plain-language time-of-day intake indicators eliminating Latin abbreviations."""
    slot: str = Field(default="morning", description="Time slot indicator: morning, afternoon, night, as_needed")
    label: str = Field(default="Morning", description="User facing slot label", example="Morning")
    dose: str = Field(default="1 tablet", description="Dosage quantity for this slot", example="1 tablet")
    time_hint: str = Field(default="With breakfast", description="Plain timing instruction", example="With breakfast")
    taken_today: bool = Field(default=False, description="Intake compliance tracker")
    morning: bool = Field(default=False, description="Take in morning (breakfast)")
    afternoon: bool = Field(default=False, description="Take in afternoon (lunch)")
    night: bool = Field(default=False, description="Take at night (dinner)")
    time_description: str = Field(
        default="",
        description="Plain language timing description",
        example="Morning & Night after meals",
    )

    model_config = ConfigDict(from_attributes=True)


class CitizenActiveMedicineItem(BaseModel):
    """Tile 2: Plain language active prescription item with intake indicators and refill alerts."""
    medicine_id: str = Field(description="Medication identifier")
    id: str = Field(default="", description="Alias for medicine_id")
    name: str = Field(description="Trade or generic medication name", example="Paracetamol")
    brand_name: str = Field(default="", description="Brand name", example="Paracetamol 650")
    generic_name: str = Field(default="", description="Generic chemical salt name", example="Paracetamol")
    dosage_form: str = Field(description="Dosage form (Tablet, Capsule, Syrup, Drops)", example="Tablet")
    strength: str = Field(description="Strength concentration", example="650mg")
    dosage_display: str = Field(default="", description="Formatted strength and form display", example="650mg Tablet")
    schedule: PlainScheduleItem = Field(description="Visual time-of-day schedule")
    plain_schedule: List[PlainScheduleItem] = Field(default_factory=list, description="List of scheduled doses")
    frequency_badge: str = Field(default="Daily", description="Plain schedule badge", example="Twice Daily")
    plain_instruction: str = Field(
        description="Clear plain-language instruction for patient",
        example="Take 1 tablet after food with a glass of water",
    )
    instructions: str = Field(default="", description="Alias for plain_instruction")
    remaining_days: int = Field(description="Days remaining in active course", example=3)
    days_remaining: int = Field(default=3, description="Alias for remaining_days", example=3)
    total_days: int = Field(description="Total prescribed course length in days", example=5)
    course_duration_days: int = Field(default=5, description="Alias for total_days", example=5)
    refill_due_date: Optional[str] = Field(default=None, description="Date when refill is due (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="Course completion date")
    is_refill_urgent: bool = Field(default=False, description="Flag indicating course expiring within 48 hours")
    refill_needed: bool = Field(default=False, description="Whether refill should be ordered now")
    refill_urgency: str = Field(default="none", description="Refill urgency status: none, soon, urgent")
    prescribed_by: str = Field(description="Doctor full name", example="Dr. Ananya Sharma")
    prescribing_doctor: str = Field(default="", description="Alias for prescribed_by")
    hospital_name: str = Field(default="AIIMS New Delhi", description="Prescribing hospital or clinic")
    prescribed_at: str = Field(description="Date prescribed (YYYY-MM-DD)", example="2026-11-06")
    prescribed_on: str = Field(default="", description="Alias for prescribed_at")

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.medicine_id
        if not self.brand_name:
            self.brand_name = self.name
        if not self.generic_name:
            self.generic_name = self.name
        if not self.dosage_display:
            self.dosage_display = f"{self.strength} {self.dosage_form}"
        if not self.instructions:
            self.instructions = self.plain_instruction
        self.days_remaining = self.remaining_days
        self.course_duration_days = self.total_days
        if not self.prescribing_doctor:
            self.prescribing_doctor = self.prescribed_by
        if not self.prescribed_on:
            self.prescribed_on = self.prescribed_at
        if not self.end_date and self.refill_due_date:
            self.end_date = self.refill_due_date


class CitizenVisitReportItem(BaseModel):
    """Tile 3: Chronological consultation visit with plain-language diagnosis and signed PDF."""
    encounter_id: str = Field(description="Clinical encounter UUID")
    id: str = Field(default="", description="Alias for encounter_id")
    item_type: str = Field(default="prescription", description="Item category: prescription | diagnostic_report")
    visit_date: str = Field(description="Consultation date in YYYY-MM-DD format", example="2026-11-05")
    encounter_date: str = Field(default="", description="Alias for visit_date")
    doctor_name: str = Field(description="Attending practitioner name", example="Dr. Ananya Sharma")
    facility_name: str = Field(description="Healthcare facility or hospital", example="AIIMS New Delhi")
    department: str = Field(default="General OPD", description="Clinical specialty or department", example="Cardiology OPD")
    plain_diagnosis: str = Field(
        description="Plain language diagnosis understandable by citizens",
        example="Mild High Blood Pressure",
    )
    clinical_diagnosis: str = Field(
        default="",
        description="Formal ICD-10 medical diagnostic terminology",
        example="Essential (primary) hypertension [I10]",
    )
    summary: str = Field(default="", description="Plain clinical summary of encounter")
    signed_prescription_hash: str = Field(description="Cryptographic SHA-256 hash of digital signature")
    digital_signature_seal: Optional[str] = Field(default=None, description="Alias for cryptographic signature seal")
    signed_prescription_url: Optional[str] = Field(
        default=None,
        description="Direct link to download tamper-evident signed prescription PDF",
    )
    document_url: Optional[str] = Field(default=None, description="Alias for signed prescription download link")
    lab_reports_count: int = Field(default=0, description="Number of diagnostic lab reports attached")
    lab_reports: List[Dict[str, Any]] = Field(default_factory=list, description="Summary list of diagnostic reports")

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.encounter_id
        if not self.encounter_date:
            self.encounter_date = self.visit_date
        if not self.summary:
            self.summary = self.clinical_diagnosis or self.plain_diagnosis
        if not self.digital_signature_seal:
            self.digital_signature_seal = self.signed_prescription_hash
        if not self.document_url and self.signed_prescription_url:
            self.document_url = self.signed_prescription_url


class HospitalCheckInQrResponse(BaseModel):
    """Payload representing high-contrast scannable QR code for OPD fast-track check-in."""
    token_id: str = Field(default="", description="Ephemeral check-in token UUID")
    token: str = Field(default="", description="Alias for token_id")
    patient_id: str = Field(description="Patient Profile UUID")
    abha_number: str = Field(description="Patient ABHA number")
    patient_name: str = Field(default="", description="Patient certified full name")
    qr_data_string: str = Field(default="", description="High-contrast scannable payload")
    qr_payload: str = Field(default="", description="Alias for qr_data_string")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp")
    expires_at: datetime = Field(description="Expiration timestamp (60 minutes validity)")
    ttl_seconds: int = Field(default=3600, description="Remaining validity window in seconds")
    facility_context: Optional[str] = Field(default=None, description="Target hospital or OPD desk code")
    counter_instructions: str = Field(
        default="Present this high-contrast QR code to the hospital OPD counter scanner for instant fast-track registration.",
        description="Instructions for citizen",
    )

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.token:
            self.token = self.token_id
        if not self.token_id:
            self.token_id = self.token
        if not self.qr_payload:
            self.qr_payload = self.qr_data_string
        if not self.qr_data_string:
            self.qr_data_string = self.qr_payload


class CitizenThreeTileResponse(BaseModel):
    """Unified container returning all 3 tiles for active patient or dependent profile."""
    patient_id: str = Field(description="Patient Profile UUID")
    patient_name: str = Field(description="Patient full name")
    context_type: str = Field(
        default="self",
        description="Context selector: self | pediatric_minor | geriatric_senior",
    )
    health_id_tile: CitizenHealthIdSummary = Field(description="Tile 1: Official ABHA ID Card and OPD QR")
    medicines_tile: List[CitizenActiveMedicineItem] = Field(description="Tile 2: Plain language active prescriptions")
    visits_tile: List[CitizenVisitReportItem] = Field(description="Tile 3: Chronological doctor consultations")
    active_medicines_tile: List[CitizenActiveMedicineItem] = Field(default_factory=list, description="Alias for medicines_tile")
    visits_and_reports_tile: List[CitizenVisitReportItem] = Field(default_factory=list, description="Alias for visits_tile")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Aggregation timestamp",
    )
    cache_hit: bool = Field(default=False, description="Whether returned from in-memory cache")

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.active_medicines_tile:
            self.active_medicines_tile = self.medicines_tile
        if not self.visits_and_reports_tile:
            self.visits_and_reports_tile = self.visits_tile
