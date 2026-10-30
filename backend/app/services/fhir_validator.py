"""HL7 FHIR Release 4 (R4) Document Bundle JSON Schema Validator & Profile Enforcement Engine.

Validates clinical bundles according to Indian National Resource Centre for EHR Standards (NRCES)
and Ayushman Bharat Digital Mission (ABDM) Milestone 3 specifications:
- Tier 1: Envelope Structure (Bundle type="document", id, timestamp, identifier, entries)
- Tier 2: Document Root (Composition at entry[0], status, subject, title, date)
- Tier 3: Profile Detection & Cardinality (OPConsultation, Prescription, DiagnosticReport, DischargeSummary)
- Tier 4: Referential Integrity (Resolution of internal urn:uuid and relative ResourceType/id references)
- Tier 5: Terminology & Coding Standards (SNOMED CT, LOINC, ICD-10, HL7 ActCode)
"""

from datetime import datetime
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.fhir_validator import (
    BundleProfileType,
    BundleValidationResponse,
    ProfileMetadata,
    ValidationIssue,
    ValidationIssueSeverity,
)

logger = logging.getLogger("nirmaya.fhir.validator")

# Standardized NRCES clinical profile catalogue
NRCES_PROFILES: Dict[str, ProfileMetadata] = {
    BundleProfileType.OP_CONSULTATION.value: ProfileMetadata(
        profileId=BundleProfileType.OP_CONSULTATION.value,
        name="NRCES India Outpatient Consultation Record",
        canonicalUrl="https://nrces.in/ndhm/fhir/r4/StructureDefinition/OPConsultationRecord",
        compositionSnomedCode="371530004",
        compositionDisplay="Clinical consultation report",
        requiredResources=["Composition", "Patient", "Encounter"],
        optionalResources=[
            "Practitioner",
            "Condition",
            "Observation",
            "MedicationRequest",
            "AllergyIntolerance",
            "Procedure",
            "Organization",
        ],
        description="Structured clinical encounter record capturing consultation notes, diagnoses, and vitals telemetry.",
    ),
    BundleProfileType.PRESCRIPTION.value: ProfileMetadata(
        profileId=BundleProfileType.PRESCRIPTION.value,
        name="NRCES India Prescription Record",
        canonicalUrl="https://nrces.in/ndhm/fhir/r4/StructureDefinition/PrescriptionRecord",
        compositionSnomedCode="440545006",
        compositionDisplay="Prescription record",
        requiredResources=["Composition", "Patient", "MedicationRequest"],
        optionalResources=[
            "Practitioner",
            "Medication",
            "Encounter",
            "Condition",
            "Organization",
        ],
        description="Pharmacological order bundle containing active drug instructions, dosage regimens, and provider signatures.",
    ),
    BundleProfileType.DIAGNOSTIC_REPORT.value: ProfileMetadata(
        profileId=BundleProfileType.DIAGNOSTIC_REPORT.value,
        name="NRCES India Diagnostic Report Record",
        canonicalUrl="https://nrces.in/ndhm/fhir/r4/StructureDefinition/DiagnosticReportRecord",
        compositionSnomedCode="721981007",
        compositionDisplay="Diagnostic studies report",
        requiredResources=["Composition", "Patient", "DiagnosticReport"],
        optionalResources=[
            "Observation",
            "Specimen",
            "Organization",
            "Practitioner",
            "Encounter",
        ],
        description="Clinical laboratory or radiology diagnostic report containing quantitative findings and impressions.",
    ),
    BundleProfileType.DISCHARGE_SUMMARY.value: ProfileMetadata(
        profileId=BundleProfileType.DISCHARGE_SUMMARY.value,
        name="NRCES India Discharge Summary Record",
        canonicalUrl="https://nrces.in/ndhm/fhir/r4/StructureDefinition/DischargeSummaryRecord",
        compositionSnomedCode="373942005",
        compositionDisplay="Discharge summary",
        requiredResources=["Composition", "Patient", "Encounter"],
        optionalResources=[
            "Practitioner",
            "Condition",
            "CarePlan",
            "Procedure",
            "MedicationRequest",
            "AllergyIntolerance",
            "Observation",
            "Organization",
        ],
        description="Inpatient hospitalization discharge summary containing course of treatment and discharge instructions.",
    ),
}

# Mapping of SNOMED-CT document codes to profile types
SNOMED_PROFILE_MAP: Dict[str, str] = {
    "371530004": BundleProfileType.OP_CONSULTATION.value,
    "440545006": BundleProfileType.PRESCRIPTION.value,
    "721981007": BundleProfileType.DIAGNOSTIC_REPORT.value,
    "373942005": BundleProfileType.DISCHARGE_SUMMARY.value,
}

# Recognized Standard Terminology Systems
RECOGNIZED_TERMINOLOGY_SYSTEMS = {
    "http://snomed.info/sct",
    "http://loinc.org",
    "http://hl7.org/fhir/sid/icd-10",
    "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "http://terminology.hl7.org/CodeSystem/observation-category",
    "http://terminology.hl7.org/CodeSystem/medicationrequest-category",
    "http://unitsofmeasure.org",
}

VALID_COMPOSITION_STATUSES = {"preliminary", "final", "amended", "entered-in-error"}


class FHIRR4BundleValidatorService:
    """Core validation service for HL7 FHIR R4 Document Bundles."""

    @classmethod
    def get_supported_profiles(cls) -> List[ProfileMetadata]:
        """Returns catalog of all registered NRCES clinical profiles."""
        return list(NRCES_PROFILES.values())

    @classmethod
    def validate_bundle(
        cls,
        bundle_data: Dict[str, Any],
        expected_profile: Optional[BundleProfileType] = None,
        strict_mode: bool = True,
    ) -> BundleValidationResponse:
        """Validates a complete FHIR R4 document bundle against NRCES India specifications.

        Parameters:
            bundle_data: Raw bundle dict payload.
            expected_profile: Optional expected profile type to enforce.
            strict_mode: Whether to treat unmapped terminologies as errors vs warnings.

        Returns:
            BundleValidationResponse containing isValid flag, profile, resource counts, and issues.
        """
        issues: List[ValidationIssue] = []

        # 1. Structural & Envelope Validation
        structural_ok = cls._validate_structure(bundle_data, issues)
        if not structural_ok:
            return cls._build_response(
                bundle_data=bundle_data,
                detected_profile=BundleProfileType.GENERIC_DOCUMENT.value,
                issues=issues,
                resource_counts={},
            )

        entries = bundle_data.get("entry", [])
        bundle_id = bundle_data.get("id")

        # 2. Document Root Composition Validation
        composition_ok, detected_profile = cls._validate_composition(
            first_entry=entries[0] if entries else {},
            bundle_meta=bundle_data.get("meta", {}),
            issues=issues,
        )

        profile_to_enforce = expected_profile.value if expected_profile else detected_profile

        if expected_profile and detected_profile != BundleProfileType.GENERIC_DOCUMENT.value:
            if expected_profile.value != detected_profile:
                issues.append(
                    ValidationIssue(
                        severity=ValidationIssueSeverity.ERROR,
                        code="profile-mismatch",
                        location="entry[0].resource.Composition.type",
                        message=(
                            f"Bundle Composition specifies profile '{detected_profile}', "
                            f"but expected profile was '{expected_profile.value}'."
                        ),
                    )
                )

        # 3. Resource Counts & Profile Cardinality
        resource_counts: Dict[str, int] = {}
        for idx, entry in enumerate(entries):
            res = entry.get("resource")
            if isinstance(res, dict):
                rtype = res.get("resourceType", "Unknown")
                resource_counts[rtype] = resource_counts.get(rtype, 0) + 1
            else:
                issues.append(
                    ValidationIssue(
                        severity=ValidationIssueSeverity.ERROR,
                        code="invalid-entry-resource",
                        location=f"entry[{idx}]",
                        message="Entry is missing a valid 'resource' object.",
                    )
                )

        cls._validate_profile_cardinality(
            profile_name=profile_to_enforce,
            resource_counts=resource_counts,
            issues=issues,
        )

        # 4. Referential Integrity Validation
        cls._validate_referential_integrity(entries=entries, issues=issues)

        # 5. Coding & Terminology System Validation
        cls._validate_coding_terminologies(
            entries=entries,
            issues=issues,
            strict_mode=strict_mode,
        )

        return cls._build_response(
            bundle_data=bundle_data,
            detected_profile=profile_to_enforce,
            issues=issues,
            resource_counts=resource_counts,
        )

    @classmethod
    def _validate_structure(
        cls,
        bundle: Dict[str, Any],
        issues: List[ValidationIssue],
    ) -> bool:
        """Validates top-level envelope schema of the FHIR R4 Bundle."""
        if not isinstance(bundle, dict):
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="invalid-json-root",
                    location="root",
                    message="FHIR Bundle payload must be a JSON object.",
                )
            )
            return False

        # resourceType
        resource_type = bundle.get("resourceType")
        if resource_type != "Bundle":
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="invalid-resource-type",
                    location="resourceType",
                    message=f"Root resourceType must be 'Bundle', received '{resource_type}'.",
                )
            )

        # type == "document"
        bundle_type = bundle.get("type")
        if bundle_type != "document":
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="invalid-bundle-type",
                    location="type",
                    message=f"Bundle type must be 'document' for clinical exchange, received '{bundle_type}'.",
                )
            )

        # id
        if not bundle.get("id"):
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.WARNING,
                    code="missing-bundle-id",
                    location="id",
                    message="Bundle resource should have a non-empty logical 'id'.",
                )
            )

        # timestamp
        timestamp = bundle.get("timestamp")
        if not timestamp:
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="missing-bundle-timestamp",
                    location="timestamp",
                    message="FHIR R4 Document Bundle must declare an instantaneous 'timestamp'.",
                )
            )
        else:
            try:
                # Accept ISO 8601 timestamps
                clean_ts = timestamp.replace("Z", "+00:00")
                datetime.fromisoformat(clean_ts)
            except Exception:
                issues.append(
                    ValidationIssue(
                        severity=ValidationIssueSeverity.ERROR,
                        code="invalid-timestamp-format",
                        location="timestamp",
                        message=f"Bundle timestamp '{timestamp}' is not a valid ISO 8601 instant.",
                    )
                )

        # identifier
        identifier = bundle.get("identifier")
        if not identifier or not isinstance(identifier, dict) or not identifier.get("value"):
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.WARNING,
                    code="missing-bundle-identifier",
                    location="identifier",
                    message="Document Bundle should contain an authoritative business identifier with a system and value.",
                )
            )

        # entry
        entries = bundle.get("entry")
        if not isinstance(entries, list) or len(entries) == 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="missing-or-empty-entries",
                    location="entry",
                    message="FHIR R4 Document Bundle must contain at least one entry.",
                )
            )
            return False

        return True

    @classmethod
    def _validate_composition(
        cls,
        first_entry: Dict[str, Any],
        bundle_meta: Dict[str, Any],
        issues: List[ValidationIssue],
    ) -> Tuple[bool, str]:
        """Enforces that the first entry is a valid Composition document manifest."""
        res = first_entry.get("resource")
        if not isinstance(res, dict) or res.get("resourceType") != "Composition":
            actual_type = res.get("resourceType") if isinstance(res, dict) else "Unknown"
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="first-entry-not-composition",
                    location="entry[0].resource",
                    message=(
                        f"First entry in a FHIR R4 Document Bundle MUST be a 'Composition' resource, "
                        f"found '{actual_type}'."
                    ),
                )
            )
            return False, BundleProfileType.GENERIC_DOCUMENT.value

        # Composition.status
        status = res.get("status")
        if not status or status not in VALID_COMPOSITION_STATUSES:
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="invalid-composition-status",
                    location="entry[0].resource.Composition.status",
                    message=(
                        f"Composition.status must be one of {sorted(list(VALID_COMPOSITION_STATUSES))}, "
                        f"found '{status}'."
                    ),
                )
            )

        # Composition.subject
        subject = res.get("subject")
        if not isinstance(subject, dict) or not subject.get("reference"):
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="missing-composition-subject",
                    location="entry[0].resource.Composition.subject",
                    message="Composition resource must have a 'subject' referencing the patient.",
                )
            )

        # Composition.date
        comp_date = res.get("date")
        if not comp_date:
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="missing-composition-date",
                    location="entry[0].resource.Composition.date",
                    message="Composition resource must declare a clinical document 'date'.",
                )
            )

        # Composition.title
        title = res.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationIssueSeverity.ERROR,
                    code="missing-composition-title",
                    location="entry[0].resource.Composition.title",
                    message="Composition resource must declare a non-empty human-readable 'title'.",
                )
            )

        # Profile detection via Composition.type coding
        detected_profile = BundleProfileType.GENERIC_DOCUMENT.value
        comp_type = res.get("type", {})
        codings = comp_type.get("coding", []) if isinstance(comp_type, dict) else []

        for coding in codings:
            if isinstance(coding, dict):
                code = str(coding.get("code", "")).strip()
                if code in SNOMED_PROFILE_MAP:
                    detected_profile = SNOMED_PROFILE_MAP[code]
                    break

        # Fallback profile detection via bundle meta.profile canonical URLs
        if detected_profile == BundleProfileType.GENERIC_DOCUMENT.value:
            profiles = bundle_meta.get("profile", []) if isinstance(bundle_meta, dict) else []
            for prof_url in profiles:
                for p_name, meta in NRCES_PROFILES.items():
                    if meta.canonicalUrl in prof_url:
                        detected_profile = p_name
                        break

        return True, detected_profile

    @classmethod
    def _validate_profile_cardinality(
        cls,
        profile_name: str,
        resource_counts: Dict[str, int],
        issues: List[ValidationIssue],
    ) -> None:
        """Verifies that all mandatory resources required by the target profile exist."""
        profile_spec = NRCES_PROFILES.get(profile_name)
        if not profile_spec:
            # Generic document bundle without specific cardinality requirements
            return

        for req in profile_spec.requiredResources:
            count = resource_counts.get(req, 0)
            if count < 1:
                issues.append(
                    ValidationIssue(
                        severity=ValidationIssueSeverity.ERROR,
                        code="missing-required-resource",
                        location=f"bundle.entry.{req}",
                        message=(
                            f"Profile '{profile_name}' requires at least one '{req}' resource, "
                            f"but 0 were found in the bundle."
                        ),
                    )
                )

    @classmethod
    def _validate_referential_integrity(
        cls,
        entries: List[Dict[str, Any]],
        issues: List[ValidationIssue],
    ) -> None:
        """Verifies that all internal resource references resolve to declared bundle targets."""
        declared_targets: Set[str] = set()

        # Phase A: Collect all valid targets
        for entry in entries:
            full_url = entry.get("fullUrl")
            if full_url:
                declared_targets.add(full_url.strip())

            res = entry.get("resource")
            if isinstance(res, dict):
                rid = res.get("id")
                rtype = res.get("resourceType")
                if rid:
                    declared_targets.add(f"{rtype}/{rid}")
                    declared_targets.add(str(rid))

        # Phase B: Inspect all references in resources
        for idx, entry in enumerate(entries):
            res = entry.get("resource")
            if not isinstance(res, dict):
                continue
            rtype = res.get("resourceType", "Resource")
            cls._check_references_recursive(
                node=res,
                path=f"entry[{idx}].resource.{rtype}",
                declared_targets=declared_targets,
                issues=issues,
            )

    @classmethod
    def _check_references_recursive(
        cls,
        node: Any,
        path: str,
        declared_targets: Set[str],
        issues: List[ValidationIssue],
    ) -> None:
        """Recursively checks any 'reference' field within nested structures."""
        if isinstance(node, dict):
            # Check if this node is a FHIR Reference
            if "reference" in node and isinstance(node["reference"], str):
                ref_str = node["reference"].strip()
                # External absolute HTTP/HTTPS URLs are allowed external references
                is_external = ref_str.startswith("http://") or ref_str.startswith("https://")
                if not is_external and ref_str not in declared_targets:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationIssueSeverity.ERROR,
                            code="dangling-reference",
                            location=f"{path}.reference",
                            message=(
                                f"Referenced target '{ref_str}' could not be resolved to any "
                                f"declared entry id or fullUrl in this bundle."
                            ),
                        )
                    )

            # Recurse into dict values
            for k, v in node.items():
                cls._check_references_recursive(
                    node=v,
                    path=f"{path}.{k}",
                    declared_targets=declared_targets,
                    issues=issues,
                )
        elif isinstance(node, list):
            for i, item in enumerate(node):
                cls._check_references_recursive(
                    node=item,
                    path=f"{path}[{i}]",
                    declared_targets=declared_targets,
                    issues=issues,
                )

    @classmethod
    def _validate_coding_terminologies(
        cls,
        entries: List[Dict[str, Any]],
        issues: List[ValidationIssue],
        strict_mode: bool,
    ) -> None:
        """Verifies that all coded concepts use recognized clinical terminologies."""
        for idx, entry in enumerate(entries):
            res = entry.get("resource")
            if not isinstance(res, dict):
                continue
            rtype = res.get("resourceType", "Resource")
            cls._check_codings_recursive(
                node=res,
                path=f"entry[{idx}].resource.{rtype}",
                issues=issues,
                strict_mode=strict_mode,
            )

    @classmethod
    def _check_codings_recursive(
        cls,
        node: Any,
        path: str,
        issues: List[ValidationIssue],
        strict_mode: bool,
    ) -> None:
        """Finds any 'coding' list and verifies system/code conformity."""
        if isinstance(node, dict):
            if "coding" in node and isinstance(node["coding"], list):
                for c_idx, coding in enumerate(node["coding"]):
                    if not isinstance(coding, dict):
                        continue
                    system = coding.get("system")
                    code = coding.get("code")

                    c_path = f"{path}.coding[{c_idx}]"

                    if not system:
                        issues.append(
                            ValidationIssue(
                                severity=(
                                    ValidationIssueSeverity.ERROR
                                    if strict_mode
                                    else ValidationIssueSeverity.WARNING
                                ),
                                code="missing-coding-system",
                                location=c_path,
                                message="Coded concept is missing a mandatory 'system' URI.",
                            )
                        )
                    elif not cls._is_acceptable_system(system):
                        issues.append(
                            ValidationIssue(
                                severity=(
                                    ValidationIssueSeverity.ERROR
                                    if strict_mode
                                    else ValidationIssueSeverity.WARNING
                                ),
                                code="unrecognized-coding-system",
                                location=f"{c_path}.system",
                                message=(
                                    f"Coding system '{system}' is not recognized under standard "
                                    f"NRCES/HL7 registries (expected SNOMED CT, LOINC, ICD-10, or ActCode)."
                                ),
                            )
                        )

                    if not code or not str(code).strip():
                        issues.append(
                            ValidationIssue(
                                severity=ValidationIssueSeverity.ERROR,
                                code="missing-coding-code",
                                location=f"{c_path}.code",
                                message="Coded concept contains a system but is missing the 'code' value.",
                            )
                        )

            # Recurse dict
            for k, v in node.items():
                cls._check_codings_recursive(
                    node=v,
                    path=f"{path}.{k}",
                    issues=issues,
                    strict_mode=strict_mode,
                )
        elif isinstance(node, list):
            for i, item in enumerate(node):
                cls._check_codings_recursive(
                    node=item,
                    path=f"{path}[{i}]",
                    issues=issues,
                    strict_mode=strict_mode,
                )

    @staticmethod
    def _is_acceptable_system(system: str) -> bool:
        """Checks if a coding system URI is a recognized standard or registered local namespace."""
        if system in RECOGNIZED_TERMINOLOGY_SYSTEMS:
            return True
        # Allow Indian NRCES, NHA, and NIRMAYA institutional URIs
        if (
            system.startswith("https://nrces.in/")
            or system.startswith("https://healthid.ndhm.gov.in/")
            or system.startswith("https://nirmaya.health/")
            or system.startswith("http://terminology.hl7.org/")
        ):
            return True
        return False

    @classmethod
    def _build_response(
        cls,
        bundle_data: Dict[str, Any],
        detected_profile: str,
        issues: List[ValidationIssue],
        resource_counts: Dict[str, int],
    ) -> BundleValidationResponse:
        """Constructs standardized BundleValidationResponse."""
        error_count = sum(1 for iss in issues if iss.severity == ValidationIssueSeverity.ERROR)
        warning_count = sum(1 for iss in issues if iss.severity == ValidationIssueSeverity.WARNING)
        is_valid = (error_count == 0)

        entries = bundle_data.get("entry", []) if isinstance(bundle_data, dict) else []
        bundle_id = bundle_data.get("id") if isinstance(bundle_data, dict) else None

        if is_valid:
            summary = (
                f"Bundle conforms to profile '{detected_profile}' with {len(entries)} entries. "
                f"Found 0 errors and {warning_count} warning(s)."
            )
        else:
            summary = (
                f"Bundle failed validation for profile '{detected_profile}' with {error_count} error(s) "
                f"and {warning_count} warning(s)."
            )

        return BundleValidationResponse(
            isValid=is_valid,
            bundleId=bundle_id,
            detectedProfile=detected_profile,
            totalEntries=len(entries),
            resourceCounts=resource_counts,
            issues=issues,
            summary=summary,
        )


fhir_bundle_validator = FHIRR4BundleValidatorService()
