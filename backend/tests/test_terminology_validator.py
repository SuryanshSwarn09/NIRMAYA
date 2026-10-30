"""Unit and integration test suite for Medical Ontology Binding Audit & Terminology Validator.

Verifies:
- Standard clinical terminology lookup (SNOMED-CT, LOINC, ICD-10, HL7 ActCode, UCUM)
- Clinical concept suggestion engine (exact, substring, and fuzzy matching)
- Full-bundle semantic ontology auditing and compliance scoring
- Categorization of concept binding statuses (FULLY_BOUND, UNRECOGNIZED_CODE, INVALID_SYSTEM, MISSING_BINDING, DISPLAY_MISMATCH)
- Recommendation synthesis for clinical remediations
- REST API routes: POST /api/v1/fhir/ontology/audit, GET /api/v1/fhir/ontology/lookup,
  GET /api/v1/fhir/ontology/suggest, GET /api/v1/fhir/ontology/systems
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.terminology_validator import (
    ConceptBindingStatus,
)
from app.services.terminology_validator import (
    SYSTEM_HL7_ACTCODE,
    SYSTEM_ICD10,
    SYSTEM_LOINC,
    SYSTEM_SNOMED,
    SYSTEM_UCUM,
    medical_ontology_validator,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Fixtures: Bundle Generators
# ---------------------------------------------------------------------------

def make_fully_bound_clinical_bundle() -> dict:
    """Creates a bundle where 100% of clinical concepts map to authentic standards."""
    now_iso = datetime.now(timezone.utc).isoformat()
    bundle_id = str(uuid.uuid4())
    comp_id = str(uuid.uuid4())
    enc_id = str(uuid.uuid4())
    cond_id = str(uuid.uuid4())
    obs_id = str(uuid.uuid4())

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
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
                                "system": SYSTEM_SNOMED,
                                "code": "371530004",
                                "display": "Clinical consultation report",
                            }
                        ]
                    },
                    "subject": {"reference": "Patient/PAT-001"},
                    "date": now_iso,
                    "title": "General Consultation Report",
                },
            },
            {
                "fullUrl": f"urn:uuid:{enc_id}",
                "resource": {
                    "resourceType": "Encounter",
                    "id": enc_id,
                    "status": "finished",
                    "class": {
                        "system": SYSTEM_HL7_ACTCODE,
                        "code": "AMB",
                        "display": "ambulatory",
                    },
                    "subject": {"reference": "Patient/PAT-001"},
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
                                "display": "Active",
                            }
                        ]
                    },
                    "code": {
                        "coding": [
                            {
                                "system": SYSTEM_SNOMED,
                                "code": "38341003",
                                "display": "Hypertension",
                            }
                        ]
                    },
                    "subject": {"reference": "Patient/PAT-001"},
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
                                "system": SYSTEM_LOINC,
                                "code": "85354-9",
                                "display": "Blood pressure panel",
                            }
                        ]
                    },
                    "subject": {"reference": "Patient/PAT-001"},
                },
            },
        ],
    }


# ---------------------------------------------------------------------------
# Unit Tests: Concept Lookup Engine
# ---------------------------------------------------------------------------

class TestMedicalOntologyLookup:
    """Tests concept lookup against curated terminology dictionaries."""

    def test_lookup_valid_snomed_concept(self):
        result = medical_ontology_validator.lookup_concept(SYSTEM_SNOMED, "38341003")
        assert result.isValid is True
        assert result.code == "38341003"
        assert result.officialDisplay == "Hypertension"
        assert result.category == "condition"

    def test_lookup_valid_loinc_concept(self):
        result = medical_ontology_validator.lookup_concept(SYSTEM_LOINC, "718-7")
        assert result.isValid is True
        assert result.code == "718-7"
        assert "Hemoglobin" in result.officialDisplay
        assert result.category == "laboratory"

    def test_lookup_valid_icd10_concept(self):
        result = medical_ontology_validator.lookup_concept(SYSTEM_ICD10, "E11.9")
        assert result.isValid is True
        assert result.code == "E11.9"
        assert "Type 2 diabetes" in result.officialDisplay

    def test_lookup_valid_hl7_actcode(self):
        result = medical_ontology_validator.lookup_concept(SYSTEM_HL7_ACTCODE, "AMB")
        assert result.isValid is True
        assert result.officialDisplay == "ambulatory"

    def test_lookup_valid_ucum_unit(self):
        result = medical_ontology_validator.lookup_concept(SYSTEM_UCUM, "g/dL")
        assert result.isValid is True
        assert result.category == "unit-of-measure"

    def test_lookup_regex_structural_fallback_snomed(self):
        # 8-digit numeric code not explicitly in curated subset, but structurally valid SNOMED
        result = medical_ontology_validator.lookup_concept(SYSTEM_SNOMED, "99988877")
        assert result.isValid is True
        assert "conforming" in result.message.lower()

    def test_lookup_invalid_snomed_code(self):
        # Alphabetic string in SNOMED
        result = medical_ontology_validator.lookup_concept(SYSTEM_SNOMED, "NOT-NUMERIC")
        assert result.isValid is False
        assert "invalid" in result.message.lower()

    def test_lookup_invalid_loinc_code(self):
        result = medical_ontology_validator.lookup_concept(SYSTEM_LOINC, "invalid-loinc")
        assert result.isValid is False

    def test_lookup_unrecognized_system_uri(self):
        result = medical_ontology_validator.lookup_concept("http://unknown-hospital-system.org/v1", "123")
        assert result.isValid is False
        assert "unrecognized" in result.message.lower()


# ---------------------------------------------------------------------------
# Unit Tests: Concept Suggestion Engine
# ---------------------------------------------------------------------------

class TestMedicalOntologySuggestions:
    """Tests natural language clinical concept suggestion generator."""

    def test_suggest_exact_match(self):
        suggestions = medical_ontology_validator.suggest_concepts(query="hypertension")
        assert len(suggestions) > 0
        codes = [s.code for s in suggestions]
        assert "38341003" in codes or "I10" in codes
        top = suggestions[0]
        assert top.confidence >= 0.90

    def test_suggest_substring_match(self):
        suggestions = medical_ontology_validator.suggest_concepts(query="hemoglobin")
        assert len(suggestions) > 0
        displays = [s.display.lower() for s in suggestions]
        assert any("hemoglobin" in d for d in displays)

    def test_suggest_with_system_filter(self):
        suggestions = medical_ontology_validator.suggest_concepts(
            query="diabetes",
            system=SYSTEM_SNOMED,
        )
        assert len(suggestions) > 0
        for s in suggestions:
            assert s.system == SYSTEM_SNOMED

    def test_suggest_empty_query(self):
        suggestions = medical_ontology_validator.suggest_concepts(query="   ")
        assert suggestions == []


# ---------------------------------------------------------------------------
# Unit Tests: Full-Bundle Semantic Ontology Auditing
# ---------------------------------------------------------------------------

class TestMedicalOntologyBundleAudit:
    """Tests bundle-wide ontology audit, compliance score calculation, and item classification."""

    def test_audit_fully_bound_bundle(self):
        bundle = make_fully_bound_clinical_bundle()
        report = medical_ontology_validator.audit_bundle_concepts(bundle)

        assert report.totalConceptsAudited >= 4
        assert report.fullyBoundCount == report.totalConceptsAudited
        assert report.unrecognizedCodeCount == 0
        assert report.invalidSystemCount == 0
        assert report.missingBindingCount == 0
        assert report.displayMismatchCount == 0
        assert report.complianceScore == 100.0
        assert report.isCompliant is True
        assert len(report.recommendations) > 0

    def test_audit_unrecognized_code(self):
        bundle = make_fully_bound_clinical_bundle()
        # Set invalid code in Condition
        bundle["entry"][2]["resource"]["code"]["coding"][0]["code"] = "ABC_INVALID_999"

        report = medical_ontology_validator.audit_bundle_concepts(bundle)
        assert report.unrecognizedCodeCount == 1
        assert report.complianceScore < 100.0
        unrec_items = [it for it in report.auditItems if it.status == ConceptBindingStatus.UNRECOGNIZED_CODE]
        assert len(unrec_items) == 1
        assert len(unrec_items[0].suggestedCodes) > 0

    def test_audit_invalid_system_uri(self):
        bundle = make_fully_bound_clinical_bundle()
        # Set proprietary unapproved system URI
        bundle["entry"][2]["resource"]["code"]["coding"][0]["system"] = "http://my-custom-codes.org"

        report = medical_ontology_validator.audit_bundle_concepts(bundle)
        assert report.invalidSystemCount == 1
        assert report.isCompliant is False
        inv_items = [it for it in report.auditItems if it.status == ConceptBindingStatus.INVALID_SYSTEM]
        assert len(inv_items) == 1

    def test_audit_missing_binding_free_text_only(self):
        bundle = make_fully_bound_clinical_bundle()
        # Replace coding with pure text description
        bundle["entry"][2]["resource"]["code"] = {"text": "Suspected Typhoid Fever"}

        report = medical_ontology_validator.audit_bundle_concepts(bundle)
        assert report.missingBindingCount == 1
        assert report.isCompliant is False
        missing_items = [it for it in report.auditItems if it.status == ConceptBindingStatus.MISSING_BINDING]
        assert len(missing_items) == 1
        assert missing_items[0].display == "Suspected Typhoid Fever"
        # Provides suggestions
        assert len(missing_items[0].suggestedCodes) > 0

    def test_audit_display_mismatch(self):
        bundle = make_fully_bound_clinical_bundle()
        # Code is 38341003 (Hypertension) but user wrote 'High Blood Sugar & Glucose'
        bundle["entry"][2]["resource"]["code"]["coding"][0]["display"] = "High Blood Sugar & Glucose"

        report = medical_ontology_validator.audit_bundle_concepts(bundle, strict_display_check=True)
        assert report.displayMismatchCount == 1
        mismatch_items = [it for it in report.auditItems if it.status == ConceptBindingStatus.DISPLAY_MISMATCH]
        assert len(mismatch_items) == 1
        assert mismatch_items[0].standardDisplay == "Hypertension"


# ---------------------------------------------------------------------------
# Integration Tests: REST API Routes (/api/v1/fhir/ontology)
# ---------------------------------------------------------------------------

class TestMedicalOntologyAPI:
    """Tests the REST API endpoints under /api/v1/fhir/ontology."""

    def test_api_audit_bundle_endpoint(self):
        bundle = make_fully_bound_clinical_bundle()
        payload = {"bundle": bundle, "strictDisplayCheck": False}

        response = client.post("/api/v1/fhir/ontology/audit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["complianceScore"] == 100.0
        assert data["isCompliant"] is True
        assert data["totalConceptsAudited"] >= 4

    def test_api_lookup_endpoint_valid(self):
        response = client.get(
            "/api/v1/fhir/ontology/lookup",
            params={"system": SYSTEM_LOINC, "code": "85354-9"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is True
        assert data["officialDisplay"] == "Blood pressure panel"

    def test_api_lookup_endpoint_invalid(self):
        response = client.get(
            "/api/v1/fhir/ontology/lookup",
            params={"system": SYSTEM_LOINC, "code": "not-a-code"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False

    def test_api_suggest_endpoint(self):
        response = client.get(
            "/api/v1/fhir/ontology/suggest",
            params={"query": "asthma", "limit": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert len(data["suggestions"]) <= 3
        codes = [s["code"] for s in data["suggestions"]]
        assert "195967001" in codes or "J45" in codes

    def test_api_systems_catalog_endpoint(self):
        response = client.get("/api/v1/fhir/ontology/systems")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 7
        uris = [s["uri"] for s in data["systems"]]
        assert SYSTEM_SNOMED in uris
        assert SYSTEM_LOINC in uris
        assert SYSTEM_ICD10 in uris
        assert SYSTEM_HL7_ACTCODE in uris
