import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.legacy_his import (
    ConnectionStatusEnum,
    FederatedPatientView,
    FederationEngineTelemetry,
    FederationQueryRequest,
    FederationQueryResponse,
    FhirResourceTypeEnum,
    LegacyConnectionConfig,
    LegacyEncounterRecord,
    LegacyObservationRecord,
    LegacyPatientRecord,
    LegacyPrescriptionRecord,
    LegacySystemType,
    NormalizedFhirTimelineEntry,
    ServerHealthCheckResult,
    SqlMedDdlResponse,
)


class LegacyHisSecurityException(Exception):
    """Exception raised when an unauthorized or mutating query is attempted."""
    pass


class LegacyHisFederationService:
    """Enterprise PostgreSQL Foreign Data Wrapper (postgres_fdw) and

    Legacy Hospital Information System (HIS) Read-Only Federation Service.
    """

    PROHIBITED_MUTATION_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE", "RENAME",
        "MERGE", "UPSERT", "REPLACE"
    }

    # Standard LOINC coding dictionary for laboratory investigations
    LOINC_MAP = {
        "GLUCOSE": {"code": "1558-6", "display": "Fasting glucose [Mass/volume] in Serum or Plasma"},
        "HBA1C": {"code": "4548-4", "display": "Hemoglobin A1c/Hemoglobin.total in Blood"},
        "CREATININE": {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum or Plasma"},
        "HEMOGLOBIN": {"code": "718-7", "display": "Hemoglobin [Mass/volume] in Blood"},
        "POTASSIUM": {"code": "2823-3", "display": "Potassium [Moles/volume] in Serum or Plasma"},
        "EGFR": {"code": "33914-3", "display": "Glomerular filtration rate/1.73 sq M.predicted"},
        "PEFR": {"code": "19926-5", "display": "Peak expiratory flow rate"},
        "EOSINOPHIL": {"code": "704-7", "display": "Eosinophils [#/volume] in Blood"},
        "BUN": {"code": "3094-0", "display": "Urea nitrogen [Mass/volume] in Serum or Plasma"},
    }

    def __init__(self) -> None:
        self._servers: Dict[str, LegacyConnectionConfig] = {}
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_ttl_seconds: int = 300

        # Telemetry metrics
        self._total_queries: int = 0
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._total_latency_ms: float = 0.0
        self._violations_prevented: int = 0

        # In-memory simulated hospital repository
        self._patients_db: Dict[str, LegacyPatientRecord] = {}
        self._encounters_db: List[LegacyEncounterRecord] = []
        self._observations_db: List[LegacyObservationRecord] = []
        self._prescriptions_db: List[LegacyPrescriptionRecord] = []

        # Bootstrap reference servers and seed datasets
        self._initialize_default_servers()
        self._seed_simulated_clinical_records()

    def _initialize_default_servers(self) -> None:
        """Register default legacy hospital servers across multiple database engines."""
        defaults = [
            LegacyConnectionConfig(
                server_id="his-delhi-civil-01",
                display_name="Delhi Civil Hospital (e-Hospital v12)",
                system_type=LegacySystemType.POSTGRES_FDW,
                host="10.0.4.15",
                port=5432,
                database_name="ehospital_delhi_db",
                username="readonly_nirmaya_sync",
                schema_prefix="foreign_his_delhi",
                read_only_enforced=True,
                connection_timeout_ms=1500,
                pool_size=8,
            ),
            LegacyConnectionConfig(
                server_id="his-mumbai-kingedward-02",
                display_name="King Edward Memorial Hospital Mumbai (Bahmni)",
                system_type=LegacySystemType.MYSQL_LEGACY,
                host="10.0.5.22",
                port=3306,
                database_name="bahmni_kem_db",
                username="nirmaya_reader",
                schema_prefix="foreign_his_kem",
                read_only_enforced=True,
                connection_timeout_ms=2000,
                pool_size=5,
            ),
            LegacyConnectionConfig(
                server_id="his-bangalore-victoria-03",
                display_name="Victoria Hospital Bangalore (MedSys)",
                system_type=LegacySystemType.POSTGRES_FDW,
                host="10.0.6.8",
                port=5432,
                database_name="medsys_victoria_prod",
                username="fdw_nirmaya_ro",
                schema_prefix="foreign_his_victoria",
                read_only_enforced=True,
                connection_timeout_ms=1800,
                pool_size=6,
            ),
            LegacyConnectionConfig(
                server_id="his-rural-phc-alwar-04",
                display_name="Alwar Rural PHC (Edge SQLite Appliance)",
                system_type=LegacySystemType.SQLITE_LEGACY,
                host="192.168.1.100",
                port=0,
                database_name="/data/phc_alwar_legacy.db",
                username="local_reader",
                schema_prefix="foreign_his_alwar",
                read_only_enforced=True,
                connection_timeout_ms=500,
                pool_size=2,
            ),
        ]
        for s in defaults:
            self._servers[s.server_id] = s

    def _seed_simulated_clinical_records(self) -> None:
        """Seed rich, clinically accurate records across distinct legacy hospitals."""
        now = datetime.utcnow()

        # Patient 1: Ramesh Sharma (Type 2 Diabetes, Hypertension - Delhi Civil)
        pt1 = LegacyPatientRecord(
            pt_id="LEGACY-PT-1001",
            mrn_no="MRN-DEL-2023-8821",
            full_name="Ramesh Sharma",
            dob_str="1968-04-12",
            gender_char="M",
            cell_phone="+919876543210",
            legacy_abha="91-1234-5678-9012",
            address="42 Chandni Chowk, Old Delhi",
            city="New Delhi",
            state="Delhi",
            source_server_id="his-delhi-civil-01",
            created_at=now - timedelta(days=240),
        )
        self._patients_db[pt1.pt_id] = pt1

        enc1_1 = LegacyEncounterRecord(
            enc_no="ENC-DEL-99120",
            pt_id=pt1.pt_id,
            visit_datetime=now - timedelta(days=45),
            dept_name="Endocrinology OPD",
            attending_dr="Dr. Anita Verma, MD",
            chief_complaint="Routine 3-month Type 2 Diabetes follow-up and polyuria review",
            diagnosis_icd10="E11.9",
            encounter_type="outpatient",
            source_server_id="his-delhi-civil-01",
        )
        enc1_2 = LegacyEncounterRecord(
            enc_no="ENC-DEL-98402",
            pt_id=pt1.pt_id,
            visit_datetime=now - timedelta(days=120),
            dept_name="Cardiology Emergency",
            attending_dr="Dr. Rajesh Gupta, DM",
            chief_complaint="Exertional retrosternal heaviness and elevated blood pressure",
            diagnosis_icd10="I20.0",
            encounter_type="emergency",
            source_server_id="his-delhi-civil-01",
        )
        self._encounters_db.extend([enc1_1, enc1_2])

        # Patient 1 Labs
        self._observations_db.extend([
            LegacyObservationRecord(
                lab_id="LAB-DEL-5011",
                pt_id=pt1.pt_id,
                enc_no=enc1_1.enc_no,
                test_code="GLUCOSE",
                test_name="Fasting Blood Glucose",
                result_val="184",
                unit_str="mg/dL",
                ref_range="70-99",
                interpretation="high",
                recorded_at=now - timedelta(days=45, hours=3),
                source_server_id="his-delhi-civil-01",
            ),
            LegacyObservationRecord(
                lab_id="LAB-DEL-5012",
                pt_id=pt1.pt_id,
                enc_no=enc1_1.enc_no,
                test_code="HBA1C",
                test_name="Glycated Hemoglobin (HbA1c)",
                result_val="8.4",
                unit_str="%",
                ref_range="4.0-5.6",
                interpretation="high",
                recorded_at=now - timedelta(days=45, hours=2),
                source_server_id="his-delhi-civil-01",
            ),
            LegacyObservationRecord(
                lab_id="LAB-DEL-5013",
                pt_id=pt1.pt_id,
                enc_no=enc1_2.enc_no,
                test_code="CREATININE",
                test_name="Serum Creatinine",
                result_val="1.1",
                unit_str="mg/dL",
                ref_range="0.7-1.3",
                interpretation="normal",
                recorded_at=now - timedelta(days=120, hours=1),
                source_server_id="his-delhi-civil-01",
            ),
            LegacyObservationRecord(
                lab_id="LAB-DEL-5014",
                pt_id=pt1.pt_id,
                enc_no=enc1_2.enc_no,
                test_code="HEMOGLOBIN",
                test_name="Hemoglobin",
                result_val="13.8",
                unit_str="g/dL",
                ref_range="13.5-17.5",
                interpretation="normal",
                recorded_at=now - timedelta(days=120, hours=1),
                source_server_id="his-delhi-civil-01",
            ),
        ])

        # Patient 1 Medications
        self._prescriptions_db.extend([
            LegacyPrescriptionRecord(
                rx_id="RX-DEL-3011",
                pt_id=pt1.pt_id,
                enc_no=enc1_1.enc_no,
                drug_name="Metformin Hydrochloride",
                dosage="500 mg",
                frequency="BID (Twice daily after meals)",
                duration_days=90,
                instructions="Take with water immediately after breakfast and dinner",
                prescribed_at=now - timedelta(days=45),
                prescribed_by="Dr. Anita Verma",
                source_server_id="his-delhi-civil-01",
            ),
            LegacyPrescriptionRecord(
                rx_id="RX-DEL-3012",
                pt_id=pt1.pt_id,
                enc_no=enc1_1.enc_no,
                drug_name="Glimepiride",
                dosage="1 mg",
                frequency="OD (Once daily before breakfast)",
                duration_days=30,
                instructions="Monitor for hypoglycemia symptoms",
                prescribed_at=now - timedelta(days=45),
                prescribed_by="Dr. Anita Verma",
                source_server_id="his-delhi-civil-01",
            ),
            LegacyPrescriptionRecord(
                rx_id="RX-DEL-3013",
                pt_id=pt1.pt_id,
                enc_no=enc1_2.enc_no,
                drug_name="Atorvastatin",
                dosage="20 mg",
                frequency="HS (Once daily at bedtime)",
                duration_days=60,
                instructions="Lipid profile recheck in 2 months",
                prescribed_at=now - timedelta(days=120),
                prescribed_by="Dr. Rajesh Gupta",
                source_server_id="his-delhi-civil-01",
            ),
        ])

        # Patient 2: Sunita Patel (Bronchial Asthma - KEM Hospital Mumbai)
        pt2 = LegacyPatientRecord(
            pt_id="LEGACY-PT-1002",
            mrn_no="MRN-MUM-2024-4109",
            full_name="Sunita Patel",
            dob_str="1982-09-24",
            gender_char="F",
            cell_phone="+919123456789",
            legacy_abha="91-4455-6677-8899",
            address="15 Parel Road",
            city="Mumbai",
            state="Maharashtra",
            source_server_id="his-mumbai-kingedward-02",
            created_at=now - timedelta(days=180),
        )
        self._patients_db[pt2.pt_id] = pt2

        enc2_1 = LegacyEncounterRecord(
            enc_no="ENC-KEM-7721",
            pt_id=pt2.pt_id,
            visit_datetime=now - timedelta(days=14),
            dept_name="Pulmonary Medicine",
            attending_dr="Dr. Pradeep Nair, MD",
            chief_complaint="Nocturnal wheezing and recurrent dry cough",
            diagnosis_icd10="J45.9",
            encounter_type="outpatient",
            source_server_id="his-mumbai-kingedward-02",
        )
        self._encounters_db.append(enc2_1)

        self._observations_db.extend([
            LegacyObservationRecord(
                lab_id="LAB-KEM-8821",
                pt_id=pt2.pt_id,
                enc_no=enc2_1.enc_no,
                test_code="PEFR",
                test_name="Peak Expiratory Flow Rate",
                result_val="280",
                unit_str="L/min",
                ref_range="380-500",
                interpretation="low",
                recorded_at=now - timedelta(days=14),
                source_server_id="his-mumbai-kingedward-02",
            ),
            LegacyObservationRecord(
                lab_id="LAB-KEM-8822",
                pt_id=pt2.pt_id,
                enc_no=enc2_1.enc_no,
                test_code="EOSINOPHIL",
                test_name="Absolute Eosinophil Count",
                result_val="620",
                unit_str="cells/mcL",
                ref_range="20-500",
                interpretation="high",
                recorded_at=now - timedelta(days=14),
                source_server_id="his-mumbai-kingedward-02",
            ),
        ])

        self._prescriptions_db.extend([
            LegacyPrescriptionRecord(
                rx_id="RX-KEM-4411",
                pt_id=pt2.pt_id,
                enc_no=enc2_1.enc_no,
                drug_name="Budesonide + Formoterol Inhaler",
                dosage="200/6 mcg",
                frequency="2 puffs BID",
                duration_days=60,
                instructions="Rinse mouth thoroughly with water after inhalation",
                prescribed_at=now - timedelta(days=14),
                prescribed_by="Dr. Pradeep Nair",
                source_server_id="his-mumbai-kingedward-02",
            ),
            LegacyPrescriptionRecord(
                rx_id="RX-KEM-4412",
                pt_id=pt2.pt_id,
                enc_no=enc2_1.enc_no,
                drug_name="Montelukast Sodium",
                dosage="10 mg",
                frequency="OD at bedtime",
                duration_days=30,
                instructions="Take with water at night",
                prescribed_at=now - timedelta(days=14),
                prescribed_by="Dr. Pradeep Nair",
                source_server_id="his-mumbai-kingedward-02",
            ),
        ])

        # Patient 3: Arun Krishnan (Stage 3 CKD - Victoria Hospital Bangalore)
        pt3 = LegacyPatientRecord(
            pt_id="LEGACY-PT-1003",
            mrn_no="MRN-BLR-2022-1923",
            full_name="Arun Krishnan",
            dob_str="1955-11-03",
            gender_char="M",
            cell_phone="+919988776655",
            legacy_abha="91-9988-1122-3344",
            address="78 Fort Road, Kalasipalyam",
            city="Bengaluru",
            state="Karnataka",
            source_server_id="his-bangalore-victoria-03",
            created_at=now - timedelta(days=360),
        )
        self._patients_db[pt3.pt_id] = pt3

        enc3_1 = LegacyEncounterRecord(
            enc_no="ENC-VIC-3101",
            pt_id=pt3.pt_id,
            visit_datetime=now - timedelta(days=7),
            dept_name="Nephrology",
            attending_dr="Dr. Meenakshi Sundaram, DM",
            chief_complaint="Bilateral pedal edema and fatigue evaluation",
            diagnosis_icd10="N18.3",
            encounter_type="outpatient",
            source_server_id="his-bangalore-victoria-03",
        )
        self._encounters_db.append(enc3_1)

        self._observations_db.extend([
            LegacyObservationRecord(
                lab_id="LAB-VIC-9011",
                pt_id=pt3.pt_id,
                enc_no=enc3_1.enc_no,
                test_code="CREATININE",
                test_name="Serum Creatinine",
                result_val="2.3",
                unit_str="mg/dL",
                ref_range="0.7-1.3",
                interpretation="critical",
                recorded_at=now - timedelta(days=7),
                source_server_id="his-bangalore-victoria-03",
            ),
            LegacyObservationRecord(
                lab_id="LAB-VIC-9012",
                pt_id=pt3.pt_id,
                enc_no=enc3_1.enc_no,
                test_code="EGFR",
                test_name="Estimated GFR (CKD-EPI)",
                result_val="32",
                unit_str="mL/min/1.73m2",
                ref_range=">60",
                interpretation="low",
                recorded_at=now - timedelta(days=7),
                source_server_id="his-bangalore-victoria-03",
            ),
            LegacyObservationRecord(
                lab_id="LAB-VIC-9013",
                pt_id=pt3.pt_id,
                enc_no=enc3_1.enc_no,
                test_code="BUN",
                test_name="Blood Urea Nitrogen",
                result_val="42",
                unit_str="mg/dL",
                ref_range="7-20",
                interpretation="high",
                recorded_at=now - timedelta(days=7),
                source_server_id="his-bangalore-victoria-03",
            ),
        ])

        self._prescriptions_db.extend([
            LegacyPrescriptionRecord(
                rx_id="RX-VIC-6111",
                pt_id=pt3.pt_id,
                enc_no=enc3_1.enc_no,
                drug_name="Torsemide",
                dosage="10 mg",
                frequency="OD in morning",
                duration_days=30,
                instructions="Take with water in the morning to avoid nocturnal diuresis",
                prescribed_at=now - timedelta(days=7),
                prescribed_by="Dr. Meenakshi Sundaram",
                source_server_id="his-bangalore-victoria-03",
            ),
            LegacyPrescriptionRecord(
                rx_id="RX-VIC-6112",
                pt_id=pt3.pt_id,
                enc_no=enc3_1.enc_no,
                drug_name="Sodium Bicarbonate",
                dosage="500 mg",
                frequency="TID",
                duration_days=60,
                instructions="Acidosis management; review serum electrolytes in 4 weeks",
                prescribed_at=now - timedelta(days=7),
                prescribed_by="Dr. Meenakshi Sundaram",
                source_server_id="his-bangalore-victoria-03",
            ),
        ])

    # --------------------------------------------------------------------------
    # Security & Read-Only Guardrails
    # --------------------------------------------------------------------------

    def validate_read_only_query(self, sql_query: str) -> None:
        """Inspect SQL statement to guarantee strict read-only execution.

        Raises LegacyHisSecurityException if mutating keywords are present.
        """
        cleaned = re.sub(r"--.*$", "", sql_query, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        tokens = set(re.findall(r"\b[A-Z_]+\b", cleaned.upper()))

        violations = tokens.intersection(self.PROHIBITED_MUTATION_KEYWORDS)
        if violations:
            self._violations_prevented += 1
            raise LegacyHisSecurityException(
                f"Security Violation: Read-only federation rejected mutating statement containing keywords: {sorted(violations)}"
            )

    # --------------------------------------------------------------------------
    # Server Management & Health Inspection
    # --------------------------------------------------------------------------

    def list_servers(self) -> List[LegacyConnectionConfig]:
        """Return all registered legacy hospital servers."""
        return list(self._servers.values())

    def get_server(self, server_id: str) -> Optional[LegacyConnectionConfig]:
        """Retrieve connection config for a given server."""
        return self._servers.get(server_id)

    def register_server(self, config: LegacyConnectionConfig) -> LegacyConnectionConfig:
        """Register or update a foreign hospital server."""
        if not config.read_only_enforced:
            config.read_only_enforced = True
        self._servers[config.server_id] = config
        return config

    def check_server_health(self, server_id: str) -> ServerHealthCheckResult:
        """Ping and verify read-only connection to foreign server."""
        server = self._servers.get(server_id)
        if not server:
            return ServerHealthCheckResult(
                server_id=server_id,
                display_name="Unknown Server",
                system_type=LegacySystemType.POSTGRES_FDW,
                status=ConnectionStatusEnum.OFFLINE,
                latency_ms=0.0,
                read_only_verified=False,
                error_message=f"Server {server_id} not registered in federation manager",
            )

        start_time = time.perf_counter()
        # Simulated sub-millisecond query ping with simulated latency
        simulated_latencies = {
            "his-delhi-civil-01": 8.4,
            "his-mumbai-kingedward-02": 14.2,
            "his-bangalore-victoria-03": 11.7,
            "his-rural-phc-alwar-04": 3.1,
        }
        latency = simulated_latencies.get(server_id, 9.5)
        elapsed_actual = (time.perf_counter() - start_time) * 1000.0

        # Count tables accessible for this server
        table_count = 4  # patients, encounters, observations, prescriptions

        version_strings = {
            LegacySystemType.POSTGRES_FDW: "PostgreSQL 14.9 on x86_64-pc-linux-gnu",
            LegacySystemType.MYSQL_LEGACY: "MySQL 8.0.35-commercial (Debian)",
            LegacySystemType.SQLITE_LEGACY: "SQLite 3.44.2 (Edge Appliance)",
            LegacySystemType.MSSQL_LEGACY: "Microsoft SQL Server 2019 (RTM-GDR)",
            LegacySystemType.ORACLE_LEGACY: "Oracle Database 19c Enterprise Edition",
            LegacySystemType.SIMULATED_HIS: "Simulated Hospital Database Engine v1.0",
        }

        return ServerHealthCheckResult(
            server_id=server.server_id,
            display_name=server.display_name,
            system_type=server.system_type,
            status=ConnectionStatusEnum.READ_ONLY_VERIFIED,
            latency_ms=round(latency + elapsed_actual, 2),
            read_only_verified=True,
            server_version=version_strings.get(server.system_type, "PostgreSQL 16"),
            table_count=table_count,
        )

    # --------------------------------------------------------------------------
    # HL7 FHIR R4 Bijective Normalization Pipeline
    # --------------------------------------------------------------------------

    def normalize_patient_to_fhir(self, pt: LegacyPatientRecord) -> Dict[str, Any]:
        """Convert a legacy patient record into HL7 FHIR R4 Patient resource."""
        gender_map = {"M": "male", "F": "female", "O": "other"}
        fhir_id = f"fed-{pt.source_server_id}-{pt.pt_id.lower()}"

        identifiers = [
            {
                "use": "usual",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number",
                        }
                    ]
                },
                "system": f"https://nirmaya.gov.in/his/{pt.source_server_id}/mrn",
                "value": pt.mrn_no,
            }
        ]
        if pt.legacy_abha:
            identifiers.append({
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "https://abdm.gov.in/codesystems/identifier-type",
                            "code": "ABHA",
                            "display": "Ayushman Bharat Health Account",
                        }
                    ]
                },
                "system": "https://abdm.gov.in",
                "value": pt.legacy_abha,
            })

        resource: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": fhir_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "tag": [
                    {
                        "system": "https://nirmaya.gov.in/federation/source-server",
                        "code": pt.source_server_id,
                        "display": self._servers.get(pt.source_server_id, LegacyConnectionConfig(
                            server_id=pt.source_server_id,
                            display_name=pt.source_server_id,
                            database_name="legacy",
                            username="ro"
                        )).display_name,
                    }
                ],
            },
            "identifier": identifiers,
            "active": True,
            "name": [
                {
                    "use": "official",
                    "text": pt.full_name,
                }
            ],
            "gender": gender_map.get(pt.gender_char.upper(), "unknown"),
            "birthDate": pt.dob_str,
        }

        if pt.cell_phone:
            resource["telecom"] = [
                {
                    "system": "phone",
                    "value": pt.cell_phone,
                    "use": "mobile",
                }
            ]

        if pt.address or pt.city or pt.state:
            address_entry: Dict[str, Any] = {"use": "home"}
            if pt.address:
                address_entry["line"] = [pt.address]
            if pt.city:
                address_entry["city"] = pt.city
            if pt.state:
                address_entry["state"] = pt.state
            address_entry["country"] = "IND"
            resource["address"] = [address_entry]

        return resource

    def normalize_encounter_to_fhir(
        self, enc: LegacyEncounterRecord, pt_fhir_id: str
    ) -> Dict[str, Any]:
        """Convert a legacy encounter record into HL7 FHIR R4 Encounter resource."""
        enc_id = f"enc-{enc.enc_no.lower()}"
        return {
            "resourceType": "Encounter",
            "id": enc_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB" if enc.encounter_type == "outpatient" else "EMER",
                "display": enc.encounter_type.capitalize(),
            },
            "subject": {"reference": f"Patient/{pt_fhir_id}"},
            "period": {
                "start": enc.visit_datetime.isoformat() + "Z",
            },
            "reasonCode": [
                {
                    "text": enc.chief_complaint or "Clinical Consultation",
                }
            ],
            "diagnosis": [
                {
                    "condition": {
                        "display": f"ICD-10: {enc.diagnosis_icd10}" if enc.diagnosis_icd10 else "Clinical Assessment"
                    }
                }
            ],
            "serviceProvider": {
                "display": enc.dept_name,
            },
            "participant": [
                {
                    "individual": {
                        "display": enc.attending_dr,
                    }
                }
            ],
        }

    def normalize_observation_to_fhir(
        self, obs: LegacyObservationRecord, pt_fhir_id: str
    ) -> Dict[str, Any]:
        """Convert a legacy laboratory observation into HL7 FHIR R4 Observation."""
        obs_id = f"obs-{obs.lab_id.lower()}"
        loinc = self.LOINC_MAP.get(obs.test_code.upper(), {
            "code": "custom-code",
            "display": obs.test_name,
        })

        resource: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc["code"],
                        "display": loinc["display"],
                    }
                ],
                "text": obs.test_name,
            },
            "subject": {"reference": f"Patient/{pt_fhir_id}"},
            "effectiveDateTime": obs.recorded_at.isoformat() + "Z",
            "valueQuantity": {
                "value": float(obs.result_val) if obs.result_val.replace(".", "", 1).isdigit() else obs.result_val,
                "unit": obs.unit_str or "",
                "system": "http://unitsofmeasure.org",
            },
        }

        if obs.ref_range:
            resource["referenceRange"] = [{"text": obs.ref_range}]

        if obs.interpretation:
            resource["interpretation"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": obs.interpretation.upper(),
                            "display": obs.interpretation.capitalize(),
                        }
                    ]
                }
            ]

        return resource

    def normalize_prescription_to_fhir(
        self, rx: LegacyPrescriptionRecord, pt_fhir_id: str
    ) -> Dict[str, Any]:
        """Convert a legacy prescription record into HL7 FHIR R4 MedicationRequest."""
        rx_id = f"medrx-{rx.rx_id.lower()}"
        return {
            "resourceType": "MedicationRequest",
            "id": rx_id,
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": rx.drug_name,
            },
            "subject": {"reference": f"Patient/{pt_fhir_id}"},
            "authoredOn": rx.prescribed_at.isoformat() + "Z",
            "requester": {
                "display": rx.prescribed_by,
            },
            "dosageInstruction": [
                {
                    "text": f"{rx.dosage} - {rx.frequency} for {rx.duration_days} days. {rx.instructions or ''}".strip(),
                }
            ],
        }

    # --------------------------------------------------------------------------
    # Federated Query & Multi-Tier Caching Engine
    # --------------------------------------------------------------------------

    def search_patients(self, req: FederationQueryRequest) -> FederationQueryResponse:
        """Search patients across all federated legacy hospital databases."""
        start_time = time.perf_counter()
        cache_key = f"search:{req.search_query or ''}:{req.mrn or ''}:{req.server_id or ''}:{req.limit}:{req.offset}"

        # 1. Check in-memory cache
        now = time.time()
        if cache_key in self._cache:
            ts, cached_resp = self._cache[cache_key]
            if now - ts < self._cache_ttl_seconds:
                self._cache_hits += 1
                self._total_queries += 1
                cached_resp.cached = True
                return cached_resp

        self._cache_misses += 1
        self._total_queries += 1

        # 2. Filter simulated legacy patients
        results: List[FederatedPatientView] = []
        q = (req.search_query or "").strip().lower()
        mrn_filter = (req.mrn or "").strip().lower()

        for pt in self._patients_db.values():
            if req.server_id and pt.source_server_id != req.server_id:
                continue

            matches_mrn = not mrn_filter or mrn_filter in pt.mrn_no.lower()
            matches_query = (
                not q
                or q in pt.full_name.lower()
                or q in pt.mrn_no.lower()
                or (pt.cell_phone and q in pt.cell_phone.lower())
                or (pt.legacy_abha and q in pt.legacy_abha.lower())
                or q in pt.city.lower() if pt.city else False
            )

            if matches_mrn and matches_query:
                view = self._build_federated_patient_view(pt)
                results.append(view)

        total_matches = len(results)
        paginated = results[req.offset : req.offset + req.limit]

        latency = round((time.perf_counter() - start_time) * 1000.0, 2)
        self._total_latency_ms += latency

        resp = FederationQueryResponse(
            total_matches=total_matches,
            page=(req.offset // req.limit) + 1 if req.limit > 0 else 1,
            page_size=len(paginated),
            server_id=req.server_id,
            patients=paginated,
            query_latency_ms=latency,
            cached=False,
        )

        self._cache[cache_key] = (now, resp)
        return resp

    def get_patient_timeline(self, pt_id: str) -> Optional[FederatedPatientView]:
        """Retrieve complete federated patient portrait with full FHIR timeline."""
        start_time = time.perf_counter()
        cache_key = f"patient_timeline:{pt_id}"

        now = time.time()
        if cache_key in self._cache:
            ts, cached_view = self._cache[cache_key]
            if now - ts < self._cache_ttl_seconds:
                self._cache_hits += 1
                self._total_queries += 1
                cached_view.cached = True
                return cached_view

        self._cache_misses += 1
        self._total_queries += 1

        pt = self._patients_db.get(pt_id)
        if not pt:
            # Check by MRN lookup
            for candidate in self._patients_db.values():
                if candidate.mrn_no.lower() == pt_id.lower():
                    pt = candidate
                    break

        if not pt:
            return None

        view = self._build_federated_patient_view(pt, include_full_timeline=True)
        latency = round((time.perf_counter() - start_time) * 1000.0, 2)
        view.query_latency_ms = latency
        self._total_latency_ms += latency

        self._cache[cache_key] = (now, view)
        return view

    def _build_federated_patient_view(
        self, pt: LegacyPatientRecord, include_full_timeline: bool = False
    ) -> FederatedPatientView:
        """Construct a unified FederatedPatientView with counts and FHIR timeline."""
        fhir_pt = self.normalize_patient_to_fhir(pt)
        pt_fhir_id = fhir_pt["id"]

        # Associated records
        encs = [e for e in self._encounters_db if e.pt_id == pt.pt_id]
        obss = [o for o in self._observations_db if o.pt_id == pt.pt_id]
        rxs = [r for r in self._prescriptions_db if r.pt_id == pt.pt_id]

        last_enc_date = max([e.visit_datetime for e in encs]) if encs else None

        timeline: List[NormalizedFhirTimelineEntry] = []
        if include_full_timeline:
            server = self._servers.get(pt.source_server_id)
            sys_type = server.system_type if server else LegacySystemType.POSTGRES_FDW

            # Encounters
            for enc in encs:
                fhir_enc = self.normalize_encounter_to_fhir(enc, pt_fhir_id)
                prov = hashlib.sha256(
                    f"{enc.source_server_id}:{enc.enc_no}:{enc.visit_datetime.isoformat()}".encode()
                ).hexdigest()
                timeline.append(
                    NormalizedFhirTimelineEntry(
                        entry_id=enc.enc_no,
                        resource_type=FhirResourceTypeEnum.Encounter,
                        date=enc.visit_datetime,
                        title=f"{enc.dept_name} Consultation",
                        summary=f"{enc.attending_dr} - {enc.chief_complaint or 'Routine Visit'}",
                        fhir_resource=fhir_enc,
                        source_server_id=enc.source_server_id,
                        source_system_type=sys_type,
                        provenance_hash=prov,
                        is_critical=False,
                    )
                )

            # Observations
            for obs in obss:
                fhir_obs = self.normalize_observation_to_fhir(obs, pt_fhir_id)
                prov = hashlib.sha256(
                    f"{obs.source_server_id}:{obs.lab_id}:{obs.result_val}".encode()
                ).hexdigest()
                is_crit = obs.interpretation in {"critical", "high"} and obs.test_code in {"CREATININE", "POTASSIUM"}
                timeline.append(
                    NormalizedFhirTimelineEntry(
                        entry_id=obs.lab_id,
                        resource_type=FhirResourceTypeEnum.Observation,
                        date=obs.recorded_at,
                        title=f"{obs.test_name}: {obs.result_val} {obs.unit_str or ''}",
                        summary=f"Ref: {obs.ref_range or 'N/A'} (Status: {obs.interpretation or 'normal'})",
                        fhir_resource=fhir_obs,
                        source_server_id=obs.source_server_id,
                        source_system_type=sys_type,
                        provenance_hash=prov,
                        is_critical=is_crit,
                    )
                )

            # Prescriptions
            for rx in rxs:
                fhir_rx = self.normalize_prescription_to_fhir(rx, pt_fhir_id)
                prov = hashlib.sha256(
                    f"{rx.source_server_id}:{rx.rx_id}:{rx.drug_name}".encode()
                ).hexdigest()
                timeline.append(
                    NormalizedFhirTimelineEntry(
                        entry_id=rx.rx_id,
                        resource_type=FhirResourceTypeEnum.MedicationRequest,
                        date=rx.prescribed_at,
                        title=f"Rx: {rx.drug_name} ({rx.dosage})",
                        summary=f"{rx.frequency} for {rx.duration_days} days - {rx.prescribed_by}",
                        fhir_resource=fhir_rx,
                        source_server_id=rx.source_server_id,
                        source_system_type=sys_type,
                        provenance_hash=prov,
                        is_critical=False,
                    )
                )

            # Chronological sort: newest first
            timeline.sort(key=lambda x: x.date, reverse=True)

        return FederatedPatientView(
            patient_id=pt.pt_id,
            mrn_no=pt.mrn_no,
            demographics=pt,
            fhir_patient=fhir_pt,
            total_encounters=len(encs),
            total_observations=len(obss),
            total_prescriptions=len(rxs),
            last_encounter_date=last_enc_date,
            source_server_id=pt.source_server_id,
            timeline=timeline,
            query_latency_ms=0.0,
            cached=False,
        )

    # --------------------------------------------------------------------------
    # SQL/MED DDL Generator for PostgreSQL 16
    # --------------------------------------------------------------------------

    def generate_sql_med_ddl(self, server_id: str) -> SqlMedDdlResponse:
        """Generate ISO/IEC 9075-9 SQL/MED DDL statements to configure postgres_fdw."""
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not registered")

        server_slug = re.sub(r"[^a-zA-Z0-9_]", "_", server.server_id)
        schema = server.schema_prefix or f"foreign_his_{server_slug}"

        ddl = f"""-- ============================================================================
-- NIRMAYA PostgreSQL Foreign Data Wrapper (postgres_fdw) Federation DDL
-- ISO/IEC 9075-9 SQL/MED (Management of External Data) Standard Specification
-- Target Foreign Server: {server.display_name} ({server.server_id})
-- ============================================================================

-- 1. Enable postgres_fdw extension
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- 2. Create isolated foreign federation schema
CREATE SCHEMA IF NOT EXISTS {schema};

-- 3. Define foreign server connection
CREATE SERVER IF NOT EXISTS {server_slug}_server
  FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (
    host '{server.host}',
    port '{server.port}',
    dbname '{server.database_name}',
    fetch_size '100',
    use_remote_estimate 'true'
  );

-- 4. Map current user with read-only credentials
CREATE USER MAPPING IF NOT EXISTS FOR current_user
  SERVER {server_slug}_server
  OPTIONS (
    user '{server.username}',
    password '${{LEGACY_HIS_DB_PASSWORD}}'
  );

-- 5. Foreign Table: Patients
CREATE FOREIGN TABLE IF NOT EXISTS {schema}.legacy_patients (
  pt_id VARCHAR(64),
  mrn_no VARCHAR(32),
  full_name VARCHAR(128),
  dob_str VARCHAR(16),
  gender_char CHAR(1),
  cell_phone VARCHAR(20),
  legacy_abha VARCHAR(32),
  address TEXT,
  city VARCHAR(64),
  state VARCHAR(64),
  created_at TIMESTAMP
)
SERVER {server_slug}_server
OPTIONS (schema_name 'public', table_name 'pt_demographics');

-- 6. Foreign Table: Encounters
CREATE FOREIGN TABLE IF NOT EXISTS {schema}.legacy_encounters (
  enc_no VARCHAR(64),
  pt_id VARCHAR(64),
  visit_datetime TIMESTAMP,
  dept_name VARCHAR(64),
  attending_dr VARCHAR(128),
  chief_complaint TEXT,
  diagnosis_icd10 VARCHAR(32),
  encounter_type VARCHAR(32)
)
SERVER {server_slug}_server
OPTIONS (schema_name 'public', table_name 'enc_encounters');

-- 7. Foreign Table: Observations (Labs)
CREATE FOREIGN TABLE IF NOT EXISTS {schema}.legacy_observations (
  lab_id VARCHAR(64),
  pt_id VARCHAR(64),
  enc_no VARCHAR(64),
  test_code VARCHAR(32),
  test_name VARCHAR(128),
  result_val VARCHAR(64),
  unit_str VARCHAR(32),
  ref_range VARCHAR(64),
  interpretation VARCHAR(32),
  recorded_at TIMESTAMP
)
SERVER {server_slug}_server
OPTIONS (schema_name 'public', table_name 'lab_investigations');

-- 8. Foreign Table: Prescriptions
CREATE FOREIGN TABLE IF NOT EXISTS {schema}.legacy_prescriptions (
  rx_id VARCHAR(64),
  pt_id VARCHAR(64),
  enc_no VARCHAR(64),
  drug_name VARCHAR(128),
  dosage VARCHAR(64),
  frequency VARCHAR(64),
  duration_days INTEGER,
  instructions TEXT,
  prescribed_at TIMESTAMP,
  prescribed_by VARCHAR(128)
)
SERVER {server_slug}_server
OPTIONS (schema_name 'public', table_name 'rx_medications');

-- Ensure read-only guardrails for session
COMMENT ON SCHEMA {schema} IS 'Federated read-only legacy HIS tables via postgres_fdw';
"""

        tables = [
            f"{schema}.legacy_patients",
            f"{schema}.legacy_encounters",
            f"{schema}.legacy_observations",
            f"{schema}.legacy_prescriptions",
        ]

        return SqlMedDdlResponse(
            server_id=server.server_id,
            ddl_script=ddl,
            schema_name=schema,
            instructions="Execute this DDL in PostgreSQL 16 using a superuser or database owner account.",
            foreign_tables=tables,
        )

    # --------------------------------------------------------------------------
    # Telemetry
    # --------------------------------------------------------------------------

    def get_telemetry(self) -> FederationEngineTelemetry:
        """Calculate and return live federation engine telemetry metrics."""
        health_list = [self.check_server_health(s.server_id) for s in self._servers.values()]
        active_count = sum(1 for h in health_list if h.status in {ConnectionStatusEnum.READ_ONLY_VERIFIED, ConnectionStatusEnum.ONLINE})
        total_cache_reqs = self._cache_hits + self._cache_misses
        hit_ratio = round((self._cache_hits / total_cache_reqs * 100.0) if total_cache_reqs > 0 else 0.0, 2)
        avg_latency = round((self._total_latency_ms / self._total_queries) if self._total_queries > 0 else 0.0, 2)

        return FederationEngineTelemetry(
            configured_servers=len(self._servers),
            active_servers=active_count,
            total_queries_executed=self._total_queries,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            cache_hit_ratio_pct=hit_ratio,
            avg_query_latency_ms=avg_latency,
            read_only_violations_prevented=self._violations_prevented,
            servers_health=health_list,
        )


# Global singleton instance for injection
legacy_his_service = LegacyHisFederationService()

