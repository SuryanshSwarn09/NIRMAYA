"""Unit and integration test suite for HL7 FHIR R4 Document Bundle JSON Schema Validator.

Verifies:
- Structural envelope conformity (type="document", valid timestamp, identifier)
- Composition document manifest root enforcement (entry[0] is Composition)
- NRCES India clinical profile detection and mandatory resource cardinality
- Referential integrity for internal urn:uuid and relative ResourceType/id references
- Clinical terminology validation (SNOMED-CT, LOINC, ICD-10, HL7 ActCode)
- Strict mode vs non-strict mode enforcement
- HTTP API endpoints: POST /api/v1/fhir/bundle/validate, GET /api/v1/fhir/bundle/profiles
"""

from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.fhir_validator import (
    BundleProfileType,
    BundleValidationRequest,
    ValidationIssueSeverity,
)
from app.services.fhir_validator import (
    NRCES_PROFILES,
    FHIRR4BundleValidatorService,
    fhir_bundle_validator,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Fixture Generators
# ---------------------------------------------------------------------------

def make_valid_op_consultation_bundle(patient_id: str = "PAT-001", doc_id: str = "DOC-001") -> dict:
    """Constructs a fully conforming NRCES OPConsultationRecord document bundle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    bundle_id = str(uuid.uuid4())
    comp_id = str(uuid.uuid4())
    enc_id = str(uuid.uuid4())
    cond_id = str(uuid.uuid4())
    obs_id = str(uuid.uuid4())

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": now_iso,
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"],
        },
        "identifier": {
            "system": "https://nirmaya.health/bundles/op-consultation",
            "value": bundle_id,
        },
        "type": "document",
        "timestamp": now_iso,
        "entry": [
            {
                "fullUrl": f"urn:uuid:{comp_id}",
                "resource": {
                    "resourceType": "Composition",
                    "id": comp_id,
                    "status": "final",
                    "type": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "371530004",
                                "display": "Clinical consultation report",
                            }
                        ],
                        "text": "Outpatient Consultation Note",
                    },
                    "subject": {
                        "reference": f"Patient/{patient_id}",
                        "display": "Aarav Sharma",
                    },
                    "encounter": {
                        "reference": f"Encounter/{enc_id}",
                    },
                    "date": now_iso,
                    "author": [
                        {
                            "reference": f"Practitioner/{doc_id}",
                            "display": "Dr. Ramesh Verma",
                        }
                    ],
                    "title": "Outpatient Consultation Record - General Medicine",
                },
            },
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": "Aarav Sharma", "family": "Sharma", "given": ["Aarav"]}],
                    "gender": "male",
                    "birthDate": "1988-06-15",
                },
            },
            {
                "fullUrl": f"urn:uuid:{enc_id}",
                "resource": {
                    "resourceType": "Encounter",
                    "id": enc_id,
                    "status": "finished",
                    "class": {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "AMB",
                        "display": "ambulatory",
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                },
            },
            {
                "fullUrl": f"urn:uuid:{doc_id}",
                "resource": {
                    "resourceType": "Practitioner",
                    "id": doc_id,
                    "name": [{"text": "Dr. Ramesh Verma", "family": "Verma", "given": ["Ramesh"]}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{cond_id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": cond_id,
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "38341003",
                                "display": "Hypertension",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                },
            },
            {
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "85354-9",
                                "display": "Blood pressure panel",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                },
            },
        ],
    }


def make_valid_prescription_bundle(patient_id: str = "PAT-002", doc_id: str = "DOC-002") -> dict:
    """Constructs a fully conforming NRCES PrescriptionRecord document bundle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    bundle_id = str(uuid.uuid4())
    comp_id = str(uuid.uuid4())
    med_req_id = str(uuid.uuid4())

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "identifier": {
            "system": "https://nirmaya.health/bundles/prescription",
            "value": bundle_id,
        },
        "type": "document",
        "timestamp": now_iso,
        "entry": [
            {
                "fullUrl": f"urn:uuid:{comp_id}",
                "resource": {
                    "resourceType": "Composition",
                    "id": comp_id,
                    "status": "final",
                    "type": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "440545006",
                                "display": "Prescription record",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "date": now_iso,
                    "title": "Electronic Prescription",
                },
            },
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": "Meera Patel"}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{doc_id}",
                "resource": {
                    "resourceType": "Practitioner",
                    "id": doc_id,
                    "name": [{"text": "Dr. Sunita Rao"}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{med_req_id}",
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": med_req_id,
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "requester": {"reference": f"Practitioner/{doc_id}"},
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "318444007",
                                "display": "Metformin 500mg tablet",
                            }
                        ]
                    },
                },
            },
        ],
    }


def make_valid_diagnostic_report_bundle(patient_id: str = "PAT-003") -> dict:
    """Constructs a fully conforming NRCES DiagnosticReportRecord document bundle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    bundle_id = str(uuid.uuid4())
    comp_id = str(uuid.uuid4())
    report_id = str(uuid.uuid4())
    obs_id = str(uuid.uuid4())

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "identifier": {
            "system": "https://nirmaya.health/bundles/diagnostic-report",
            "value": bundle_id,
        },
        "type": "document",
        "timestamp": now_iso,
        "entry": [
            {
                "fullUrl": f"urn:uuid:{comp_id}",
                "resource": {
                    "resourceType": "Composition",
                    "id": comp_id,
                    "status": "final",
                    "type": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "721981007",
                                "display": "Diagnostic studies report",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "date": now_iso,
                    "title": "Complete Blood Count Lab Panel",
                },
            },
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": "Vikram Singh"}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{report_id}",
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": report_id,
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "58410-2",
                                "display": "Complete blood count panel",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "result": [{"reference": f"Observation/{obs_id}"}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "718-7",
                                "display": "Hemoglobin [Mass/volume] in Blood",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "valueQuantity": {
                        "value": 14.2,
                        "unit": "g/dL",
                        "system": "http://unitsofmeasure.org",
                        "code": "g/dL",
                    },
                },
            },
        ],
    }


def make_valid_discharge_summary_bundle(patient_id: str = "PAT-004", enc_id: str = "ENC-004") -> dict:
    """Constructs a fully conforming NRCES DischargeSummaryRecord document bundle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    bundle_id = str(uuid.uuid4())
    comp_id = str(uuid.uuid4())

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "identifier": {
            "system": "https://nirmaya.health/bundles/discharge-summary",
            "value": bundle_id,
        },
        "type": "document",
        "timestamp": now_iso,
        "entry": [
            {
                "fullUrl": f"urn:uuid:{comp_id}",
                "resource": {
                    "resourceType": "Composition",
                    "id": comp_id,
                    "status": "final",
                    "type": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "373942005",
                                "display": "Discharge summary",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "date": now_iso,
                    "title": "Hospitalization Inpatient Discharge Summary",
                },
            },
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": "Priya Nair"}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{enc_id}",
                "resource": {
                    "resourceType": "Encounter",
                    "id": enc_id,
                    "status": "finished",
                    "class": {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "IMP",
                        "display": "inpatient encounter",
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                },
            },
        ],
    }


# ---------------------------------------------------------------------------
# Positive Unit Tests: 4 NRCES Profile Validations
# ---------------------------------------------------------------------------

class TestFHIRR4BundleValidatorConformingProfiles:
    """Tests that valid bundles conforming to the 4 NRCES India profiles validate with zero errors."""

    def test_valid_op_consultation_record(self):
        bundle = make_valid_op_consultation_bundle()
        response = fhir_bundle_validator.validate_bundle(bundle)

        assert response.isValid is True
        assert response.detectedProfile == BundleProfileType.OP_CONSULTATION.value
        assert response.totalEntries == 6
        assert response.resourceCounts["Composition"] == 1
        assert response.resourceCounts["Patient"] == 1
        assert response.resourceCounts["Encounter"] == 1
        assert response.resourceCounts["Practitioner"] == 1
        assert response.resourceCounts["Condition"] == 1
        assert response.resourceCounts["Observation"] == 1
        errors = [iss for iss in response.issues if iss.severity == ValidationIssueSeverity.ERROR]
        assert len(errors) == 0

    def test_valid_prescription_record(self):
        bundle = make_valid_prescription_bundle()
        response = fhir_bundle_validator.validate_bundle(bundle)

        assert response.isValid is True
        assert response.detectedProfile == BundleProfileType.PRESCRIPTION.value
        assert response.totalEntries == 4
        assert response.resourceCounts["Composition"] == 1
        assert response.resourceCounts["MedicationRequest"] == 1
        errors = [iss for iss in response.issues if iss.severity == ValidationIssueSeverity.ERROR]
        assert len(errors) == 0

    def test_valid_diagnostic_report_record(self):
        bundle = make_valid_diagnostic_report_bundle()
        response = fhir_bundle_validator.validate_bundle(bundle)

        assert response.isValid is True
        assert response.detectedProfile == BundleProfileType.DIAGNOSTIC_REPORT.value
        assert response.totalEntries == 4
        assert response.resourceCounts["DiagnosticReport"] == 1
        assert response.resourceCounts["Observation"] == 1
        errors = [iss for iss in response.issues if iss.severity == ValidationIssueSeverity.ERROR]
        assert len(errors) == 0

    def test_valid_discharge_summary_record(self):
        bundle = make_valid_discharge_summary_bundle()
        response = fhir_bundle_validator.validate_bundle(bundle)

        assert response.isValid is True
        assert response.detectedProfile == BundleProfileType.DISCHARGE_SUMMARY.value
        assert response.totalEntries == 3
        assert response.resourceCounts["Composition"] == 1
        assert response.resourceCounts["Encounter"] == 1
        errors = [iss for iss in response.issues if iss.severity == ValidationIssueSeverity.ERROR]
        assert len(errors) == 0


# ---------------------------------------------------------------------------
# Negative Tests: Structural Envelope Violations
# ---------------------------------------------------------------------------

class TestFHIRR4BundleValidatorStructuralFailures:
    """Tests envelope and syntax validation failures."""

    def test_invalid_root_type(self):
        bundle = make_valid_op_consultation_bundle()
        bundle["resourceType"] = "NotABundle"

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "invalid-resource-type" in codes

    def test_invalid_bundle_type(self):
        bundle = make_valid_op_consultation_bundle()
        bundle["type"] = "searchset"

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "invalid-bundle-type" in codes

    def test_missing_or_empty_entries(self):
        bundle = make_valid_op_consultation_bundle()
        bundle["entry"] = []

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "missing-or-empty-entries" in codes

    def test_invalid_timestamp_format(self):
        bundle = make_valid_op_consultation_bundle()
        bundle["timestamp"] = "not-a-valid-timestamp"

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "invalid-timestamp-format" in codes


# ---------------------------------------------------------------------------
# Negative Tests: Composition Manifest Violations
# ---------------------------------------------------------------------------

class TestFHIRR4BundleValidatorCompositionFailures:
    """Tests Composition resource root requirements."""

    def test_first_entry_not_composition(self):
        bundle = make_valid_op_consultation_bundle()
        # Swap entry 0 and entry 1 (Patient first)
        bundle["entry"][0], bundle["entry"][1] = bundle["entry"][1], bundle["entry"][0]

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "first-entry-not-composition" in codes

    def test_invalid_composition_status(self):
        bundle = make_valid_op_consultation_bundle()
        bundle["entry"][0]["resource"]["status"] = "in-draft-mode-invalid"

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "invalid-composition-status" in codes

    def test_missing_composition_subject(self):
        bundle = make_valid_op_consultation_bundle()
        del bundle["entry"][0]["resource"]["subject"]

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "missing-composition-subject" in codes

    def test_missing_composition_title(self):
        bundle = make_valid_op_consultation_bundle()
        bundle["entry"][0]["resource"]["title"] = "   "

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "missing-composition-title" in codes


# ---------------------------------------------------------------------------
# Negative Tests: Profile Cardinality & Referential Integrity
# ---------------------------------------------------------------------------

class TestFHIRR4BundleValidatorCardinalityAndReferences:
    """Tests missing required resources and dangling pointers."""

    def test_op_consultation_missing_mandatory_encounter(self):
        bundle = make_valid_op_consultation_bundle()
        # Remove Encounter entry
        bundle["entry"] = [e for e in bundle["entry"] if e["resource"]["resourceType"] != "Encounter"]

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "missing-required-resource" in codes

    def test_prescription_missing_mandatory_medication_request(self):
        bundle = make_valid_prescription_bundle()
        # Remove MedicationRequest entry
        bundle["entry"] = [e for e in bundle["entry"] if e["resource"]["resourceType"] != "MedicationRequest"]

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "missing-required-resource" in codes

    def test_dangling_patient_reference(self):
        bundle = make_valid_op_consultation_bundle()
        # Change Composition subject to a non-existent patient ID
        bundle["entry"][0]["resource"]["subject"]["reference"] = "Patient/PAT-DOES-NOT-EXIST"

        response = fhir_bundle_validator.validate_bundle(bundle)
        assert response.isValid is False
        codes = [iss.code for iss in response.issues]
        assert "dangling-reference" in codes

    def test_unrecognized_coding_system_strict_mode(self):
        bundle = make_valid_op_consultation_bundle()
        # Alter Condition coding to an unapproved private ontology
        bundle["entry"][4]["resource"]["code"]["coding"][0]["system"] = "http://proprietary-hospital-code.com/v1"

        # In strict mode, triggers ERROR
        strict_response = fhir_bundle_validator.validate_bundle(bundle, strict_mode=True)
        assert strict_response.isValid is False
        codes = [iss.code for iss in strict_response.issues]
        assert "unrecognized-coding-system" in codes

        # In non-strict mode, triggers WARNING but isValid is True (if no other errors)
        non_strict_response = fhir_bundle_validator.validate_bundle(bundle, strict_mode=False)
        assert non_strict_response.isValid is True
        warning_codes = [iss.code for iss in non_strict_response.issues if iss.severity == ValidationIssueSeverity.WARNING]
        assert "unrecognized-coding-system" in warning_codes


# ---------------------------------------------------------------------------
# Integration Tests: API Endpoints
# ---------------------------------------------------------------------------

class TestFHIRR4BundleValidatorAPI:
    """Tests the REST API routes under /api/v1/fhir/bundle."""

    def test_api_validate_bundle_success(self):
        bundle = make_valid_prescription_bundle()
        payload = {
            "bundle": bundle,
            "expectedProfile": BundleProfileType.PRESCRIPTION.value,
            "strictMode": True,
        }

        response = client.post("/api/v1/fhir/bundle/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is True
        assert data["detectedProfile"] == BundleProfileType.PRESCRIPTION.value
        assert data["totalEntries"] == 4
        assert "MedicationRequest" in data["resourceCounts"]

    def test_api_validate_bundle_malformed(self):
        bundle = make_valid_prescription_bundle()
        bundle["resourceType"] = "CorruptedResource"
        payload = {"bundle": bundle}

        response = client.post("/api/v1/fhir/bundle/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False
        assert len(data["issues"]) > 0

    def test_api_get_supported_profiles(self):
        response = client.get("/api/v1/fhir/bundle/profiles")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4
        profile_ids = [p["profileId"] for p in data["profiles"]]
        assert BundleProfileType.OP_CONSULTATION.value in profile_ids
        assert BundleProfileType.PRESCRIPTION.value in profile_ids
        assert BundleProfileType.DIAGNOSTIC_REPORT.value in profile_ids
        assert BundleProfileType.DISCHARGE_SUMMARY.value in profile_ids

    def test_api_get_profile_detail_found(self):
        response = client.get("/api/v1/fhir/bundle/profiles/OPConsultationRecord")
        assert response.status_code == 200
        data = response.json()
        assert data["profileId"] == "OPConsultationRecord"
        assert data["compositionSnomedCode"] == "371530004"
        assert "Composition" in data["requiredResources"]
        assert "Patient" in data["requiredResources"]
        assert "Encounter" in data["requiredResources"]

    def test_api_get_profile_detail_not_found(self):
        response = client.get("/api/v1/fhir/bundle/profiles/NonExistentProfile123")
        assert response.status_code == 404
        data = response.json()
        error_msg = data.get("message") or data.get("detail", "")
        assert "not found" in error_msg.lower()
