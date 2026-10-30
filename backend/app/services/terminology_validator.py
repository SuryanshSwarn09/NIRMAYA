"""Medical Ontology Binding Audit & Terminology Validator Service.

Implements standard healthcare terminology validation, concept lookup, fuzzy suggestions,
and full-bundle semantic compliance scoring according to:
- SNOMED-CT (Systematized Nomenclature of Medicine -- Clinical Terms)
- LOINC (Logical Observation Identifiers Names and Codes)
- ICD-10 (International Classification of Diseases, 10th Revision)
- HL7 Standard CodeSystems (ActCode, Observation Category, Condition Clinical Status)
- Unified Code for Units of Measure (UCUM)
"""

from difflib import SequenceMatcher
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.terminology_validator import (
    ConceptAuditItem,
    ConceptBindingStatus,
    ConceptLookupResponse,
    ConceptSuggestion,
    OntologyAuditReport,
    TerminologySystemInfo,
)

logger = logging.getLogger("nirmaya.ontology.validator")

# Canonical System URIs
SYSTEM_SNOMED = "http://snomed.info/sct"
SYSTEM_LOINC = "http://loinc.org"
SYSTEM_ICD10 = "http://hl7.org/fhir/sid/icd-10"
SYSTEM_ICD10_WHO = "http://id.who.int/icd/release/10/2016"
SYSTEM_HL7_ACTCODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
SYSTEM_HL7_OBS_CAT = "http://terminology.hl7.org/CodeSystem/observation-category"
SYSTEM_HL7_COND_STATUS = "http://terminology.hl7.org/CodeSystem/condition-clinical"
SYSTEM_UCUM = "http://unitsofmeasure.org"

# Registered Terminology Metadata
REGISTERED_SYSTEMS: List[TerminologySystemInfo] = [
    TerminologySystemInfo(
        name="SNOMED-CT",
        uri=SYSTEM_SNOMED,
        version="2026-03-India",
        authority="SNOMED International / NRCES India",
        purpose="Comprehensive clinical healthcare terminology covering diagnoses, findings, procedures, and body structures.",
    ),
    TerminologySystemInfo(
        name="LOINC",
        uri=SYSTEM_LOINC,
        version="2.78",
        authority="Regenstrief Institute",
        purpose="Universal code system for laboratory observations, vital signs telemetry, and diagnostic studies.",
    ),
    TerminologySystemInfo(
        name="ICD-10",
        uri=SYSTEM_ICD10,
        version="2016 / 2019",
        authority="World Health Organization (WHO)",
        purpose="Standard diagnostic tool for epidemiology, health management, and clinical morbidity classification.",
    ),
    TerminologySystemInfo(
        name="HL7 ActCode",
        uri=SYSTEM_HL7_ACTCODE,
        version="R4",
        authority="HL7 International",
        purpose="Encounter classifications: ambulatory (AMB), inpatient (IMP), emergency (EMER), and home health (HH).",
    ),
    TerminologySystemInfo(
        name="HL7 Observation Category",
        uri=SYSTEM_HL7_OBS_CAT,
        version="R4",
        authority="HL7 International",
        purpose="High-level grouping for clinical measurements (vital-signs, laboratory, exam).",
    ),
    TerminologySystemInfo(
        name="HL7 Condition Clinical Status",
        uri=SYSTEM_HL7_COND_STATUS,
        version="R4",
        authority="HL7 International",
        purpose="Clinical state of an active, recurring, or resolved medical condition.",
    ),
    TerminologySystemInfo(
        name="UCUM",
        uri=SYSTEM_UCUM,
        version="2.1",
        authority="Regenstrief Institute / UCUM",
        purpose="Harmonized units of measure for laboratory and vital sign quantitative telemetry.",
    ),
]

# Curated SNOMED-CT Concepts
CURATED_SNOMED: Dict[str, Dict[str, str]] = {
    # Clinical Documents
    "371530004": {"display": "Clinical consultation report", "category": "document"},
    "440545006": {"display": "Prescription record", "category": "document"},
    "721981007": {"display": "Diagnostic studies report", "category": "document"},
    "373942005": {"display": "Discharge summary", "category": "document"},
    # Diagnoses & Conditions
    "38341003": {"display": "Hypertension", "category": "condition"},
    "73211009": {"display": "Diabetes mellitus", "category": "condition"},
    "44054006": {"display": "Type 2 diabetes mellitus", "category": "condition"},
    "46635009": {"display": "Type 1 diabetes mellitus", "category": "condition"},
    "195967001": {"display": "Asthma", "category": "condition"},
    "386661006": {"display": "Fever", "category": "condition"},
    "49727002": {"display": "Cough", "category": "condition"},
    "25064002": {"display": "Headache", "category": "condition"},
    "22253000": {"display": "Pain", "category": "condition"},
    "56018004": {"display": "Wheezing", "category": "condition"},
    "84229001": {"display": "Fatigue", "category": "condition"},
    "422587007": {"display": "Nausea", "category": "condition"},
    "62315008": {"display": "Diarrhea", "category": "condition"},
    "38822007": {"display": "Gastroesophageal reflux disease", "category": "condition"},
    "68566005": {"display": "Urinary tract infectious disease", "category": "condition"},
    "132281000119108": {"display": "COVID-19", "category": "condition"},
    # Medications
    "318444007": {"display": "Metformin 500mg tablet", "category": "medication"},
    "387207008": {"display": "Paracetamol", "category": "medication"},
    "372665008": {"display": "Amoxicillin", "category": "medication"},
    "387458008": {"display": "Aspirin", "category": "medication"},
    "387584000": {"display": "Atorvastatin", "category": "medication"},
    "386864001": {"display": "Azithromycin", "category": "medication"},
    "387017005": {"display": "Omeprazole", "category": "medication"},
    "386873009": {"display": "Amlodipine", "category": "medication"},
    "386868003": {"display": "Losartan", "category": "medication"},
}

# Curated LOINC Concepts
CURATED_LOINC: Dict[str, Dict[str, str]] = {
    # Vitals
    "85354-9": {"display": "Blood pressure panel", "category": "vital-signs"},
    "8480-6": {"display": "Systolic blood pressure", "category": "vital-signs"},
    "8462-4": {"display": "Diastolic blood pressure", "category": "vital-signs"},
    "8867-4": {"display": "Heart rate", "category": "vital-signs"},
    "8310-5": {"display": "Body temperature", "category": "vital-signs"},
    "9279-1": {"display": "Respiratory rate", "category": "vital-signs"},
    "2708-6": {"display": "Oxygen saturation in Arterial blood by Pulse oximetry", "category": "vital-signs"},
    "29463-7": {"display": "Body weight", "category": "vital-signs"},
    "8302-2": {"display": "Body height", "category": "vital-signs"},
    "39156-5": {"display": "Body mass index (BMI) [Ratio]", "category": "vital-signs"},
    # Lab Panels & Tests
    "58410-2": {"display": "Complete blood count panel", "category": "laboratory"},
    "718-7": {"display": "Hemoglobin [Mass/volume] in Blood", "category": "laboratory"},
    "4544-3": {"display": "Hematocrit [Volume Fraction] of Blood", "category": "laboratory"},
    "6690-2": {"display": "Leukocytes [#/volume] in Blood", "category": "laboratory"},
    "777-3": {"display": "Platelets [#/volume] in Blood", "category": "laboratory"},
    "2345-7": {"display": "Glucose [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "1558-6": {"display": "Fasting glucose [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "4548-4": {"display": "Hemoglobin A1c/Hemoglobin.total in Blood", "category": "laboratory"},
    "24357-6": {"display": "Urinalysis macro (dipstick) panel", "category": "laboratory"},
    "2085-9": {"display": "Cholesterol in HDL [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "13457-7": {"display": "Cholesterol in LDL [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "2093-3": {"display": "Cholesterol [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "2571-8": {"display": "Triglyceride [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "2160-0": {"display": "Creatinine [Mass/volume] in Serum or Plasma", "category": "laboratory"},
    "3094-0": {"display": "Urea nitrogen [Mass/volume] in Serum or Plasma", "category": "laboratory"},
}

# Curated ICD-10 Concepts
CURATED_ICD10: Dict[str, Dict[str, str]] = {
    "I10": {"display": "Essential (primary) hypertension", "category": "condition"},
    "E11": {"display": "Type 2 diabetes mellitus", "category": "condition"},
    "E11.9": {"display": "Type 2 diabetes mellitus without complications", "category": "condition"},
    "E10": {"display": "Type 1 diabetes mellitus", "category": "condition"},
    "E10.9": {"display": "Type 1 diabetes mellitus without complications", "category": "condition"},
    "J45": {"display": "Asthma", "category": "condition"},
    "J45.9": {"display": "Asthma, unspecified", "category": "condition"},
    "R50.9": {"display": "Fever, unspecified", "category": "condition"},
    "R05": {"display": "Cough", "category": "condition"},
    "R51": {"display": "Headache", "category": "condition"},
    "J06.9": {"display": "Acute upper respiratory infection, unspecified", "category": "condition"},
    "K21.9": {"display": "Gastro-esophageal reflux disease without esophagitis", "category": "condition"},
    "N39.0": {"display": "Urinary tract infection, site not specified", "category": "condition"},
    "U07.1": {"display": "COVID-19, virus identified", "category": "condition"},
}

# Curated HL7 Concepts
CURATED_HL7: Dict[str, Dict[str, Dict[str, str]]] = {
    SYSTEM_HL7_ACTCODE: {
        "AMB": {"display": "ambulatory", "category": "encounter"},
        "IMP": {"display": "inpatient encounter", "category": "encounter"},
        "EMER": {"display": "emergency", "category": "encounter"},
        "HH": {"display": "home health", "category": "encounter"},
    },
    SYSTEM_HL7_OBS_CAT: {
        "vital-signs": {"display": "Vital Signs", "category": "observation"},
        "laboratory": {"display": "Laboratory", "category": "observation"},
        "exam": {"display": "Exam", "category": "observation"},
    },
    SYSTEM_HL7_COND_STATUS: {
        "active": {"display": "Active", "category": "condition-status"},
        "recurrence": {"display": "Recurrence", "category": "condition-status"},
        "relapse": {"display": "Relapse", "category": "condition-status"},
        "remission": {"display": "Remission", "category": "condition-status"},
        "resolved": {"display": "Resolved", "category": "condition-status"},
    },
}


class MedicalOntologyValidatorService:
    """Core service for medical ontology validation, lookup, and bundle auditing."""

    @classmethod
    def get_registered_systems(cls) -> List[TerminologySystemInfo]:
        """Returns the list of officially recognized terminology systems."""
        return REGISTERED_SYSTEMS

    @classmethod
    def lookup_concept(cls, system: str, code: str) -> ConceptLookupResponse:
        """Looks up a concept in the curated ontology registry.

        Parameters:
            system: Terminology system canonical URI.
            code: Concept code.

        Returns:
            ConceptLookupResponse with resolution status and standard display.
        """
        clean_sys = system.strip().lower()
        clean_code = code.strip()

        # 1. SNOMED-CT Lookup
        if clean_sys == SYSTEM_SNOMED.lower():
            if clean_code in CURATED_SNOMED:
                meta = CURATED_SNOMED[clean_code]
                return ConceptLookupResponse(
                    isValid=True,
                    system=SYSTEM_SNOMED,
                    code=clean_code,
                    officialDisplay=meta["display"],
                    category=meta["category"],
                    message=f"Valid SNOMED-CT concept: {meta['display']}",
                )
            # Regex pattern test for valid SNOMED numeric structure (6-18 digits)
            if re.match(r"^\d{6,18}$", clean_code):
                return ConceptLookupResponse(
                    isValid=True,
                    system=SYSTEM_SNOMED,
                    code=clean_code,
                    officialDisplay=None,
                    category="snomed-concept",
                    message="Valid SNOMED-CT format. Concept verified as structurally conforming.",
                )
            return ConceptLookupResponse(
                isValid=False,
                system=SYSTEM_SNOMED,
                code=clean_code,
                officialDisplay=None,
                category=None,
                message=f"Invalid SNOMED-CT code format or unmapped concept: '{clean_code}'.",
            )

        # 2. LOINC Lookup
        if clean_sys == SYSTEM_LOINC.lower():
            if clean_code in CURATED_LOINC:
                meta = CURATED_LOINC[clean_code]
                return ConceptLookupResponse(
                    isValid=True,
                    system=SYSTEM_LOINC,
                    code=clean_code,
                    officialDisplay=meta["display"],
                    category=meta["category"],
                    message=f"Valid LOINC concept: {meta['display']}",
                )
            if re.match(r"^\d{3,5}-\d$", clean_code):
                return ConceptLookupResponse(
                    isValid=True,
                    system=SYSTEM_LOINC,
                    code=clean_code,
                    officialDisplay=None,
                    category="loinc-observation",
                    message="Valid LOINC format. Observation code conforms to standard syntax.",
                )
            return ConceptLookupResponse(
                isValid=False,
                system=SYSTEM_LOINC,
                code=clean_code,
                officialDisplay=None,
                category=None,
                message=f"Invalid LOINC code format or unmapped observation: '{clean_code}'.",
            )

        # 3. ICD-10 Lookup
        if clean_sys in (SYSTEM_ICD10.lower(), SYSTEM_ICD10_WHO.lower()):
            upper_code = clean_code.upper()
            if upper_code in CURATED_ICD10:
                meta = CURATED_ICD10[upper_code]
                return ConceptLookupResponse(
                    isValid=True,
                    system=SYSTEM_ICD10,
                    code=upper_code,
                    officialDisplay=meta["display"],
                    category=meta["category"],
                    message=f"Valid ICD-10 diagnosis: {meta['display']}",
                )
            if re.match(r"^[A-Z]\d{2}(\.\d{1,2})?$", upper_code):
                return ConceptLookupResponse(
                    isValid=True,
                    system=SYSTEM_ICD10,
                    code=upper_code,
                    officialDisplay=None,
                    category="icd10-diagnosis",
                    message="Valid ICD-10 format. Morbidity code conforms to international syntax.",
                )
            return ConceptLookupResponse(
                isValid=False,
                system=SYSTEM_ICD10,
                code=clean_code,
                officialDisplay=None,
                category=None,
                message=f"Invalid ICD-10 code format or unmapped morbidity: '{clean_code}'.",
            )

        # 4. HL7 Standard CodeSystems Lookup
        for hl7_sys, entries in CURATED_HL7.items():
            if clean_sys == hl7_sys.lower():
                if clean_code in entries:
                    meta = entries[clean_code]
                    return ConceptLookupResponse(
                        isValid=True,
                        system=hl7_sys,
                        code=clean_code,
                        officialDisplay=meta["display"],
                        category=meta["category"],
                        message=f"Valid HL7 standard code: {meta['display']}",
                    )
                return ConceptLookupResponse(
                    isValid=False,
                    system=hl7_sys,
                    code=clean_code,
                    officialDisplay=None,
                    category=None,
                    message=f"Unrecognized code '{clean_code}' for standard HL7 system '{hl7_sys}'.",
                )

        # 5. UCUM Lookup
        if clean_sys == SYSTEM_UCUM.lower():
            return ConceptLookupResponse(
                isValid=True,
                system=SYSTEM_UCUM,
                code=clean_code,
                officialDisplay=clean_code,
                category="unit-of-measure",
                message=f"Standard unit of measure: '{clean_code}'.",
            )

        # 6. Institution / NRCES Namespace Check
        if (
            clean_sys.startswith("https://nrces.in/")
            or clean_sys.startswith("https://healthid.ndhm.gov.in/")
            or clean_sys.startswith("https://nirmaya.health/")
        ):
            return ConceptLookupResponse(
                isValid=True,
                system=system,
                code=clean_code,
                officialDisplay=None,
                category="institutional-registry",
                message=f"Accepted national/institutional namespace: '{system}'.",
            )

        # Unrecognized System URI
        return ConceptLookupResponse(
            isValid=False,
            system=system,
            code=clean_code,
            officialDisplay=None,
            category=None,
            message=f"Unrecognized or unauthorized terminology system URI: '{system}'.",
        )

    @classmethod
    def suggest_concepts(
        cls,
        query: str,
        system: Optional[str] = None,
        limit: int = 5,
    ) -> List[ConceptSuggestion]:
        """Provides ranked standard concept suggestions for a natural language term.

        Parameters:
            query: Clinical search string (e.g. 'sugar', 'blood pressure', 'fever').
            system: Optional system URI filter.
            limit: Maximum count of suggestions to return.

        Returns:
            List of ConceptSuggestion objects sorted by descending confidence.
        """
        if not query or not query.strip():
            return []

        search_term = query.strip().lower()
        candidates: List[Tuple[float, ConceptSuggestion]] = []

        # Target pools to search
        pools: List[Tuple[str, Dict[str, Dict[str, str]]]] = []
        if not system or system == SYSTEM_SNOMED:
            pools.append((SYSTEM_SNOMED, CURATED_SNOMED))
        if not system or system == SYSTEM_LOINC:
            pools.append((SYSTEM_LOINC, CURATED_LOINC))
        if not system or system == SYSTEM_ICD10:
            pools.append((SYSTEM_ICD10, CURATED_ICD10))

        for sys_uri, concepts in pools:
            for code, meta in concepts.items():
                display_lower = meta["display"].lower()
                category = meta["category"]

                # 1. Exact match
                if search_term == display_lower or search_term == code:
                    candidates.append(
                        (
                            1.0,
                            ConceptSuggestion(
                                system=sys_uri,
                                code=code,
                                display=meta["display"],
                                category=category,
                                confidence=1.0,
                            ),
                        )
                    )
                    continue

                # 2. Substring match (search_term in display)
                if search_term in display_lower:
                    ratio = len(search_term) / len(display_lower)
                    conf = round(0.75 + (0.20 * ratio), 2)
                    candidates.append(
                        (
                            conf,
                            ConceptSuggestion(
                                system=sys_uri,
                                code=code,
                                display=meta["display"],
                                category=category,
                                confidence=conf,
                            ),
                        )
                    )
                    continue

                # 2b. Inverse substring match (standard display contained in query, e.g. 'fever' in 'suspected typhoid fever')
                if display_lower in search_term:
                    ratio = len(display_lower) / len(search_term)
                    conf = round(0.70 + (0.25 * ratio), 2)
                    candidates.append(
                        (
                            conf,
                            ConceptSuggestion(
                                system=sys_uri,
                                code=code,
                                display=meta["display"],
                                category=category,
                                confidence=conf,
                            ),
                        )
                    )
                    continue

                # 2c. Token-level keyword overlap
                tokens = [w for w in search_term.split() if len(w) > 2]
                token_matched = False
                for tok in tokens:
                    if tok in display_lower:
                        conf = 0.65
                        candidates.append(
                            (
                                conf,
                                ConceptSuggestion(
                                    system=sys_uri,
                                    code=code,
                                    display=meta["display"],
                                    category=category,
                                    confidence=conf,
                                ),
                            )
                        )
                        token_matched = True
                        break
                if token_matched:
                    continue

                # 3. Fuzzy sequence matcher
                similarity = SequenceMatcher(None, search_term, display_lower).ratio()
                if similarity >= 0.55:
                    conf = round(similarity * 0.90, 2)
                    candidates.append(
                        (
                            conf,
                            ConceptSuggestion(
                                system=sys_uri,
                                code=code,
                                display=meta["display"],
                                category=category,
                                confidence=conf,
                            ),
                        )
                    )

        # Sort descending by confidence
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in candidates[:limit]]

    @classmethod
    def audit_bundle_concepts(
        cls,
        bundle_data: Dict[str, Any],
        strict_display_check: bool = False,
    ) -> OntologyAuditReport:
        """Audits all clinical concepts within a FHIR R4 Bundle for ontology compliance.

        Evaluates every coded element across Composition, Condition, Observation,
        DiagnosticReport, MedicationRequest, and Encounter resources.

        Parameters:
            bundle_data: FHIR R4 Bundle dictionary.
            strict_display_check: Whether to strictly flag minor display variances.

        Returns:
            OntologyAuditReport containing granular items, counts, and compliance score.
        """
        audit_items: List[ConceptAuditItem] = []
        entries = bundle_data.get("entry", []) if isinstance(bundle_data, dict) else []
        bundle_id = bundle_data.get("id") if isinstance(bundle_data, dict) else None

        for idx, entry in enumerate(entries):
            res = entry.get("resource")
            if not isinstance(res, dict):
                continue
            rtype = res.get("resourceType", "Resource")
            cls._audit_resource_node(
                node=res,
                path=f"entry[{idx}].resource.{rtype}",
                resource_type=rtype,
                items=audit_items,
                strict_display=strict_display_check,
            )

        # Calculate counts
        fully_bound = sum(1 for it in audit_items if it.status == ConceptBindingStatus.FULLY_BOUND)
        unrecognized = sum(1 for it in audit_items if it.status == ConceptBindingStatus.UNRECOGNIZED_CODE)
        invalid_sys = sum(1 for it in audit_items if it.status == ConceptBindingStatus.INVALID_SYSTEM)
        missing_bind = sum(1 for it in audit_items if it.status == ConceptBindingStatus.MISSING_BINDING)
        display_mismatch = sum(1 for it in audit_items if it.status == ConceptBindingStatus.DISPLAY_MISMATCH)
        total_concepts = len(audit_items)

        # Calculate weighted compliance score
        if total_concepts == 0:
            compliance_score = 100.0
        else:
            weighted_sum = (
                (1.0 * fully_bound)
                + (0.8 * display_mismatch)
                + (0.2 * unrecognized)
                + (0.0 * invalid_sys)
                + (0.0 * missing_bind)
            )
            compliance_score = round((weighted_sum / total_concepts) * 100.0, 1)

        is_compliant = (compliance_score >= 80.0) and (invalid_sys == 0) and (missing_bind == 0)

        # Generate actionable clinical recommendations
        recommendations = cls._generate_recommendations(
            fully_bound=fully_bound,
            unrecognized=unrecognized,
            invalid_sys=invalid_sys,
            missing_bind=missing_bind,
            display_mismatch=display_mismatch,
            compliance_score=compliance_score,
        )

        return OntologyAuditReport(
            bundleId=bundle_id,
            totalConceptsAudited=total_concepts,
            fullyBoundCount=fully_bound,
            unrecognizedCodeCount=unrecognized,
            invalidSystemCount=invalid_sys,
            missingBindingCount=missing_bind,
            displayMismatchCount=display_mismatch,
            complianceScore=compliance_score,
            isCompliant=is_compliant,
            auditItems=audit_items,
            recommendations=recommendations,
        )

    @classmethod
    def _audit_resource_node(
        cls,
        node: Any,
        path: str,
        resource_type: str,
        items: List[ConceptAuditItem],
        strict_display: bool,
    ) -> None:
        """Recursively discovers and audits CodeableConcept and Coding structures."""
        if isinstance(node, dict):
            # Check for CodeableConcept pattern (has 'coding' or 'text')
            is_candidate_concept = (
                "coding" in node
                or (
                    "text" in node
                    and any(k in path.lower() for k in ("code", "clinicalstatus", "verificationstatus", "class", "type"))
                )
            )

            if is_candidate_concept:
                codings = node.get("coding")
                free_text = node.get("text")

                if isinstance(codings, list) and len(codings) > 0:
                    for c_idx, coding in enumerate(codings):
                        if isinstance(coding, dict):
                            cls._evaluate_single_coding(
                                coding=coding,
                                path=f"{path}.coding[{c_idx}]",
                                resource_type=resource_type,
                                items=items,
                                free_text=free_text,
                                strict_display=strict_display,
                            )
                elif free_text and isinstance(free_text, str) and free_text.strip():
                    # Missing binding: has free-text description but ZERO standard codings
                    suggestions = cls.suggest_concepts(query=free_text, limit=3)
                    items.append(
                        ConceptAuditItem(
                            resourceType=resource_type,
                            elementPath=path,
                            system=None,
                            code=None,
                            display=free_text,
                            status=ConceptBindingStatus.MISSING_BINDING,
                            standardDisplay=None,
                            suggestedCodes=suggestions,
                            message=(
                                f"Element contains unstructured text '{free_text}' but lacks "
                                f"standardized SNOMED/LOINC/ICD-10 coding binding."
                            ),
                        )
                    )

            # Recurse into dict children (avoid double-traversing already-audited codings)
            for k, v in node.items():
                if k != "coding":
                    cls._audit_resource_node(
                        node=v,
                        path=f"{path}.{k}",
                        resource_type=resource_type,
                        items=items,
                        strict_display=strict_display,
                    )
        elif isinstance(node, list):
            for i, item in enumerate(node):
                cls._audit_resource_node(
                    node=item,
                    path=f"{path}[{i}]",
                    resource_type=resource_type,
                    items=items,
                    strict_display=strict_display,
                )

    @classmethod
    def _evaluate_single_coding(
        cls,
        coding: Dict[str, Any],
        path: str,
        resource_type: str,
        items: List[ConceptAuditItem],
        free_text: Optional[str],
        strict_display: bool,
    ) -> None:
        """Evaluates an individual coding entry against standard terminologies."""
        system = coding.get("system")
        code = coding.get("code")
        display = coding.get("display")

        # 1. Invalid or missing system URI
        if not system or not str(system).strip():
            query_str = display or free_text or str(code or "")
            suggestions = cls.suggest_concepts(query=query_str, limit=3)
            items.append(
                ConceptAuditItem(
                    resourceType=resource_type,
                    elementPath=path,
                    system=system,
                    code=code,
                    display=display,
                    status=ConceptBindingStatus.INVALID_SYSTEM,
                    standardDisplay=None,
                    suggestedCodes=suggestions,
                    message="Concept is missing a mandatory standard terminology system URI.",
                )
            )
            return

        # Perform concept resolution
        lookup = cls.lookup_concept(system=system, code=str(code or ""))

        # 2. System recognized but code unknown / unmapped
        if not lookup.isValid:
            # Check whether system is recognized
            is_known_system = any(
                s.uri.lower() == system.lower()
                for s in REGISTERED_SYSTEMS
            )
            if is_known_system:
                query_str = display or free_text or ""
                suggestions = cls.suggest_concepts(query=query_str, system=system, limit=3)
                items.append(
                    ConceptAuditItem(
                        resourceType=resource_type,
                        elementPath=path,
                        system=system,
                        code=str(code or ""),
                        display=display,
                        status=ConceptBindingStatus.UNRECOGNIZED_CODE,
                        standardDisplay=None,
                        suggestedCodes=suggestions,
                        message=(
                            f"Code '{code}' is not recognized under standard terminology system '{system}'. "
                            f"{lookup.message}"
                        ),
                    )
                )
            else:
                query_str = display or free_text or ""
                suggestions = cls.suggest_concepts(query=query_str, limit=3)
                items.append(
                    ConceptAuditItem(
                        resourceType=resource_type,
                        elementPath=path,
                        system=system,
                        code=str(code or ""),
                        display=display,
                        status=ConceptBindingStatus.INVALID_SYSTEM,
                        standardDisplay=None,
                        suggestedCodes=suggestions,
                        message=f"Terminology system '{system}' is not authorized under ABDM/NRCES standards.",
                    )
                )
            return

        # 3. Code recognized: Check display consistency
        std_display = lookup.officialDisplay
        if std_display and display:
            sim = SequenceMatcher(None, display.strip().lower(), std_display.strip().lower()).ratio()
            # If similarity is low and strict display check is enabled, or if completely divergent
            if sim < 0.40 or (strict_display and sim < 0.70):
                items.append(
                    ConceptAuditItem(
                        resourceType=resource_type,
                        elementPath=path,
                        system=system,
                        code=str(code),
                        display=display,
                        status=ConceptBindingStatus.DISPLAY_MISMATCH,
                        standardDisplay=std_display,
                        suggestedCodes=[],
                        message=(
                            f"Concept code '{code}' is valid, but declared display '{display}' diverges "
                            f"from official standard nomenclature '{std_display}'."
                        ),
                    )
                )
                return

        # 4. Fully bound concept
        items.append(
            ConceptAuditItem(
                resourceType=resource_type,
                elementPath=path,
                system=system,
                code=str(code),
                display=display or std_display,
                status=ConceptBindingStatus.FULLY_BOUND,
                standardDisplay=std_display,
                suggestedCodes=[],
                message=f"Concept is fully bound and conforms to standard {system} specifications.",
            )
        )

    @classmethod
    def _generate_recommendations(
        cls,
        fully_bound: int,
        unrecognized: int,
        invalid_sys: int,
        missing_bind: int,
        display_mismatch: int,
        compliance_score: float,
    ) -> List[str]:
        """Synthesizes clinical actionable recommendations from audit telemetry."""
        recs: List[str] = []

        if compliance_score >= 95.0 and invalid_sys == 0 and missing_bind == 0:
            recs.append("Bundle exhibits exemplary medical ontology compliance (>95%) across all clinical elements.")
            return recs

        if missing_bind > 0:
            recs.append(
                f"Found {missing_bind} clinical element(s) with free-text descriptions lacking standard code bindings. "
                "Map these elements to standard SNOMED-CT or LOINC codes using the /fhir/ontology/suggest endpoint."
            )

        if invalid_sys > 0:
            recs.append(
                f"Found {invalid_sys} concept(s) referencing non-standard or proprietary terminology systems. "
                "Migrate all clinical codes to canonical URIs: http://snomed.info/sct, http://loinc.org, or http://hl7.org/fhir/sid/icd-10."
            )

        if unrecognized > 0:
            recs.append(
                f"Found {unrecognized} concept code(s) that could not be validated in the standard terminology registry. "
                "Verify codes against official NRCES India value sets."
            )

        if display_mismatch > 0:
            recs.append(
                f"Found {display_mismatch} concept(s) where declared display text diverges from official standard names. "
                "Harmonize display strings with official registry displays to avoid clinical misinterpretation."
            )

        if compliance_score < 80.0:
            recs.append(
                f"Overall compliance score is {compliance_score}% (below ABDM M3 threshold of 80.0%). "
                "Remediate unmapped concepts before transmitting document bundles across national health exchange gateways."
            )

        return recs


medical_ontology_validator = MedicalOntologyValidatorService()
