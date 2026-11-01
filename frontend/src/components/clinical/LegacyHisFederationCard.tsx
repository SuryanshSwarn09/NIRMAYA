"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export interface LegacyServerItem {
  serverId: string;
  displayName: string;
  systemType: "POSTGRES_FDW" | "MYSQL_LEGACY" | "SQLITE_LEGACY";
  host: string;
  port: number;
  database: string;
  status: "READ_ONLY_VERIFIED" | "ONLINE" | "DEGRADED";
  latencyMs: number;
  tablesCount: number;
}

export interface FederatedPatientSummary {
  patientId: string;
  mrnNo: string;
  fullName: string;
  dobStr: string;
  gender: string;
  phone: string;
  abha: string;
  hospital: string;
  serverId: string;
  totalEncounters: number;
  totalObservations: number;
  totalPrescriptions: number;
  lastVisit: string;
  timeline: Array<{
    id: string;
    type: "Encounter" | "Observation" | "MedicationRequest";
    title: string;
    summary: string;
    date: string;
    isCritical?: boolean;
    provenanceHash: string;
  }>;
}

export const INITIAL_SERVERS: LegacyServerItem[] = [
  {
    serverId: "his-delhi-civil-01",
    displayName: "Delhi Civil Hospital (e-Hospital v12)",
    systemType: "POSTGRES_FDW",
    host: "10.0.4.15",
    port: 5432,
    database: "ehospital_delhi_db",
    status: "READ_ONLY_VERIFIED",
    latencyMs: 8.4,
    tablesCount: 4,
  },
  {
    serverId: "his-mumbai-kingedward-02",
    displayName: "King Edward Memorial Hospital Mumbai (Bahmni)",
    systemType: "MYSQL_LEGACY",
    host: "10.0.5.22",
    port: 3306,
    database: "bahmni_kem_db",
    status: "READ_ONLY_VERIFIED",
    latencyMs: 14.2,
    tablesCount: 4,
  },
  {
    serverId: "his-bangalore-victoria-03",
    displayName: "Victoria Hospital Bangalore (MedSys)",
    systemType: "POSTGRES_FDW",
    host: "10.0.6.8",
    port: 5432,
    database: "medsys_victoria_prod",
    status: "READ_ONLY_VERIFIED",
    latencyMs: 11.7,
    tablesCount: 4,
  },
  {
    serverId: "his-rural-phc-alwar-04",
    displayName: "Alwar Rural PHC (Edge SQLite Appliance)",
    systemType: "SQLITE_LEGACY",
    host: "192.168.1.100",
    port: 0,
    database: "/data/phc_alwar_legacy.db",
    status: "READ_ONLY_VERIFIED",
    latencyMs: 3.1,
    tablesCount: 4,
  },
];

export const INITIAL_FEDERATED_PATIENTS: FederatedPatientSummary[] = [
  {
    patientId: "LEGACY-PT-1001",
    mrnNo: "MRN-DEL-2023-8821",
    fullName: "Ramesh Sharma",
    dobStr: "1968-04-12 (56 yrs)",
    gender: "Male",
    phone: "+91 98765 43210",
    abha: "91-1234-5678-9012",
    hospital: "Delhi Civil Hospital",
    serverId: "his-delhi-civil-01",
    totalEncounters: 2,
    totalObservations: 4,
    totalPrescriptions: 3,
    lastVisit: "45 days ago",
    timeline: [
      {
        id: "ENC-DEL-99120",
        type: "Encounter",
        title: "Endocrinology OPD Consultation",
        summary: "Dr. Anita Verma, MD - Type 2 Diabetes Follow-up (ICD-10 E11.9)",
        date: "45 days ago",
        provenanceHash: "b7e289...41a0",
      },
      {
        id: "LAB-DEL-5011",
        type: "Observation",
        title: "Fasting Blood Glucose: 184 mg/dL",
        summary: "LOINC 1558-6 | Ref: 70-99 (Status: High)",
        date: "45 days ago",
        isCritical: true,
        provenanceHash: "c4180d...98e2",
      },
      {
        id: "LAB-DEL-5012",
        type: "Observation",
        title: "Glycated Hemoglobin (HbA1c): 8.4 %",
        summary: "LOINC 4548-4 | Ref: 4.0-5.6 (Status: High)",
        date: "45 days ago",
        isCritical: true,
        provenanceHash: "d8312e...61bf",
      },
      {
        id: "RX-DEL-3011",
        type: "MedicationRequest",
        title: "Rx: Metformin Hydrochloride (500 mg)",
        summary: "BID (Twice daily after meals) for 90 days - Dr. Anita Verma",
        date: "45 days ago",
        provenanceHash: "a1194c...18d7",
      },
      {
        id: "ENC-DEL-98402",
        type: "Encounter",
        title: "Cardiology Emergency Consultation",
        summary: "Dr. Rajesh Gupta, DM - Exertional heaviness (ICD-10 I20.0)",
        date: "120 days ago",
        provenanceHash: "e5012a...77b1",
      },
    ],
  },
  {
    patientId: "LEGACY-PT-1002",
    mrnNo: "MRN-MUM-2024-4109",
    fullName: "Sunita Patel",
    dobStr: "1982-09-24 (42 yrs)",
    gender: "Female",
    phone: "+91 91234 56789",
    abha: "91-4455-6677-8899",
    hospital: "King Edward Memorial Hospital Mumbai",
    serverId: "his-mumbai-kingedward-02",
    totalEncounters: 1,
    totalObservations: 2,
    totalPrescriptions: 2,
    lastVisit: "14 days ago",
    timeline: [
      {
        id: "ENC-KEM-7721",
        type: "Encounter",
        title: "Pulmonary Medicine Consultation",
        summary: "Dr. Pradeep Nair, MD - Nocturnal wheezing (ICD-10 J45.9)",
        date: "14 days ago",
        provenanceHash: "f182c0...44d9",
      },
      {
        id: "LAB-KEM-8821",
        type: "Observation",
        title: "Peak Expiratory Flow Rate: 280 L/min",
        summary: "LOINC 19926-5 | Ref: 380-500 (Status: Low)",
        date: "14 days ago",
        provenanceHash: "9812e1...83f0",
      },
      {
        id: "RX-KEM-4411",
        type: "MedicationRequest",
        title: "Rx: Budesonide + Formoterol Inhaler (200/6 mcg)",
        summary: "2 puffs BID for 60 days - Dr. Pradeep Nair",
        date: "14 days ago",
        provenanceHash: "b823e4...291a",
      },
    ],
  },
  {
    patientId: "LEGACY-PT-1003",
    mrnNo: "MRN-BLR-2022-1923",
    fullName: "Arun Krishnan",
    dobStr: "1955-11-03 (69 yrs)",
    gender: "Male",
    phone: "+91 99887 76655",
    abha: "91-9988-1122-3344",
    hospital: "Victoria Hospital Bangalore",
    serverId: "his-bangalore-victoria-03",
    totalEncounters: 1,
    totalObservations: 3,
    totalPrescriptions: 2,
    lastVisit: "7 days ago",
    timeline: [
      {
        id: "ENC-VIC-3101",
        type: "Encounter",
        title: "Nephrology Consultation",
        summary: "Dr. Meenakshi Sundaram, DM - Stage 3 CKD (ICD-10 N18.3)",
        date: "7 days ago",
        provenanceHash: "7a213e...68bc",
      },
      {
        id: "LAB-VIC-9011",
        type: "Observation",
        title: "Serum Creatinine: 2.3 mg/dL",
        summary: "LOINC 2160-0 | Ref: 0.7-1.3 (Status: Critical High)",
        date: "7 days ago",
        isCritical: true,
        provenanceHash: "419a2e...19cd",
      },
      {
        id: "RX-VIC-6111",
        type: "MedicationRequest",
        title: "Rx: Torsemide (10 mg)",
        summary: "OD in morning for 30 days - Dr. Meenakshi Sundaram",
        date: "7 days ago",
        provenanceHash: "3e9812...55da",
      },
    ],
  },
];

export const LegacyHisFederationCard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"patients" | "servers" | "ddl">("patients");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<FederatedPatientSummary>(INITIAL_FEDERATED_PATIENTS[0]);
  const [viewMode, setViewMode] = useState<"timeline" | "raw" | "fhir">("timeline");
  const [isImporting, setIsImporting] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [servers, setServers] = useState<LegacyServerItem[]>(INITIAL_SERVERS);
  const [testingServerId, setTestingServerId] = useState<string | null>(null);

  const filteredPatients = INITIAL_FEDERATED_PATIENTS.filter(
    (p) =>
      p.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.mrnNo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.hospital.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.phone.includes(searchQuery)
  );

  const handleTestConnection = (serverId: string) => {
    setTestingServerId(serverId);
    setTimeout(() => {
      setServers((prev) =>
        prev.map((s) =>
          s.serverId === serverId ? { ...s, latencyMs: Math.round((Math.random() * 4 + 7) * 10) / 10 } : s
        )
      );
      setTestingServerId(null);
    }, 500);
  };

  const handleImportToVault = () => {
    setIsImporting(true);
    setTimeout(() => {
      setIsImporting(false);
      setImportStatus(
        `Imported ${selectedPatient.fullName} (${selectedPatient.mrnNo}) with 10 resources to sovereign vault.`
      );
      setTimeout(() => setImportStatus(null), 5000);
    }, 700);
  };

  return (
    <Card className="p-6 bg-white border border-gray-200 rounded-xl shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-gray-100">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900 tracking-tight">
              PostgreSQL Foreign Data Wrapper & Legacy HIS Federation
            </h2>
            <Badge variant="verified">postgres_fdw</Badge>
            <Badge variant="neutral">SQL/MED ISO-9075-9</Badge>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Zero-downtime, read-only federation of legacy hospital systems (PostgreSQL, MySQL/Bahmni, SQLite) into HL7 FHIR R4.
          </p>
        </div>

        {/* Telemetry Pills */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <div className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-md flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-gray-600">Active Servers:</span>
            <span className="font-semibold text-gray-900">4 / 4 Online</span>
          </div>
          <div className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-md flex items-center gap-2">
            <span className="text-gray-600">Cache Hit:</span>
            <span className="font-semibold text-gray-900">98.4%</span>
          </div>
          <div className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-md flex items-center gap-2">
            <span className="text-gray-600">Avg Latency:</span>
            <span className="font-semibold text-gray-900">9.3 ms</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-gray-200 mt-4 mb-5">
        <button
          onClick={() => setActiveTab("patients")}
          className={`px-3.5 py-2 text-xs font-medium border-b-2 transition-colors ${
            activeTab === "patients"
              ? "border-gray-900 text-gray-900"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Federated Patient Explorer
        </button>
        <button
          onClick={() => setActiveTab("servers")}
          className={`px-3.5 py-2 text-xs font-medium border-b-2 transition-colors ${
            activeTab === "servers"
              ? "border-gray-900 text-gray-900"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Foreign Servers Fleet (4)
        </button>
        <button
          onClick={() => setActiveTab("ddl")}
          className={`px-3.5 py-2 text-xs font-medium border-b-2 transition-colors ${
            activeTab === "ddl"
              ? "border-gray-900 text-gray-900"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          PostgreSQL 16 SQL/MED DDL
        </button>
      </div>

      {/* Tab 1: Federated Patient Explorer */}
      {activeTab === "patients" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Column: Search & Patient List */}
          <div className="lg:col-span-5 space-y-3">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by MRN, Name, Phone, or Hospital..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-900 focus:bg-white"
              />
            </div>

            <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
              {filteredPatients.map((pt) => {
                const isSelected = selectedPatient.patientId === pt.patientId;
                return (
                  <div
                    key={pt.patientId}
                    onClick={() => setSelectedPatient(pt)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? "bg-gray-50 border-gray-900 ring-1 ring-gray-900"
                        : "bg-white border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-gray-900">{pt.fullName}</span>
                      <Badge variant="neutral">{pt.mrnNo}</Badge>
                    </div>
                    <div className="text-[11px] text-gray-500 mt-1 flex items-center justify-between">
                      <span>{pt.hospital}</span>
                      <span>{pt.lastVisit}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-2 text-[10px] text-gray-600">
                      <span className="px-1.5 py-0.5 bg-gray-100 rounded">
                        {pt.totalEncounters} Encounters
                      </span>
                      <span className="px-1.5 py-0.5 bg-gray-100 rounded">
                        {pt.totalObservations} Labs
                      </span>
                      <span className="px-1.5 py-0.5 bg-gray-100 rounded">
                        {pt.totalPrescriptions} Rx
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Selected Patient Details & Normalized FHIR Timeline */}
          <div className="lg:col-span-7 bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-col justify-between">
            <div>
              {/* Patient Banner */}
              <div className="flex items-start justify-between pb-3 border-b border-gray-200">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-gray-900">
                      {selectedPatient.fullName}
                    </h3>
                    <Badge variant="verified">Read-Only Federated</Badge>
                  </div>
                  <div className="text-xs text-gray-600 mt-0.5 flex items-center gap-3">
                    <span>MRN: <strong className="text-gray-900">{selectedPatient.mrnNo}</strong></span>
                    <span>ABHA: <strong className="text-gray-900">{selectedPatient.abha}</strong></span>
                    <span>DOB: {selectedPatient.dobStr}</span>
                  </div>
                  <div className="text-[11px] text-gray-500 mt-1">
                    Source System: <strong>{selectedPatient.hospital}</strong> ({selectedPatient.serverId})
                  </div>
                </div>

                <Button
                  onClick={handleImportToVault}
                  disabled={isImporting}
                  className="text-xs px-3 py-1.5 bg-gray-900 text-white rounded-md hover:bg-black transition-colors"
                >
                  {isImporting ? "Importing..." : "Import to Native Vault"}
                </Button>
              </div>

              {/* Status Alert */}
              {importStatus && (
                <div className="mt-3 p-2.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-md">
                  {importStatus}
                </div>
              )}

              {/* View Mode Toggle */}
              <div className="flex items-center justify-between mt-4 mb-3">
                <span className="text-xs font-semibold text-gray-800">
                  Federated Clinical Records ({selectedPatient.timeline.length} events)
                </span>
                <div className="flex items-center gap-1 bg-white border border-gray-200 p-0.5 rounded-md text-[11px]">
                  <button
                    onClick={() => setViewMode("timeline")}
                    className={`px-2 py-0.5 rounded ${
                      viewMode === "timeline" ? "bg-gray-900 text-white font-medium" : "text-gray-600"
                    }`}
                  >
                    FHIR Timeline
                  </button>
                  <button
                    onClick={() => setViewMode("raw")}
                    className={`px-2 py-0.5 rounded ${
                      viewMode === "raw" ? "bg-gray-900 text-white font-medium" : "text-gray-600"
                    }`}
                  >
                    Raw SQL Row
                  </button>
                  <button
                    onClick={() => setViewMode("fhir")}
                    className={`px-2 py-0.5 rounded ${
                      viewMode === "fhir" ? "bg-gray-900 text-white font-medium" : "text-gray-600"
                    }`}
                  >
                    FHIR R4 JSON
                  </button>
                </div>
              </div>

              {/* View Mode Content */}
              {viewMode === "timeline" && (
                <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
                  {selectedPatient.timeline.map((entry) => (
                    <div
                      key={entry.id}
                      className="p-3 bg-white rounded-lg border border-gray-200 text-xs space-y-1 shadow-2xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">{entry.title}</span>
                          {entry.isCritical && <Badge variant="critical">Panic Value</Badge>}
                        </div>
                        <Badge variant="neutral">{entry.type}</Badge>
                      </div>
                      <p className="text-gray-600 text-[11px]">{entry.summary}</p>
                      <div className="flex items-center justify-between text-[10px] text-gray-400 pt-1 border-t border-gray-50">
                        <span>Date: {entry.date}</span>
                        <span>SHA-256: {entry.provenanceHash}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {viewMode === "raw" && (
                <pre className="p-3 bg-gray-900 text-gray-100 rounded-lg text-[11px] font-mono overflow-x-auto max-h-[320px]">
{JSON.stringify(
  {
    table: "foreign_his.pt_demographics",
    pt_id: selectedPatient.patientId,
    mrn_no: selectedPatient.mrnNo,
    full_name: selectedPatient.fullName,
    gender_char: selectedPatient.gender[0],
    cell_phone: selectedPatient.phone,
    source_database: selectedPatient.hospital,
    read_only_isolation: "SET TRANSACTION READ ONLY",
  },
  null,
  2
)}
                </pre>
              )}

              {viewMode === "fhir" && (
                <pre className="p-3 bg-gray-900 text-gray-100 rounded-lg text-[11px] font-mono overflow-x-auto max-h-[320px]">
{JSON.stringify(
  {
    resourceType: "Patient",
    id: `fed-${selectedPatient.serverId}-${selectedPatient.patientId.toLowerCase()}`,
    meta: {
      profile: ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"],
      tag: [{ system: "https://nirmaya.gov.in/source-server", code: selectedPatient.serverId }],
    },
    identifier: [
      { use: "usual", type: "MRN", value: selectedPatient.mrnNo },
      { use: "official", type: "ABHA", value: selectedPatient.abha },
    ],
    name: [{ text: selectedPatient.fullName }],
    gender: selectedPatient.gender.toLowerCase(),
  },
  null,
  2
)}
                </pre>
              )}
            </div>

            <div className="pt-3 border-t border-gray-200 text-[11px] text-gray-500 flex items-center justify-between">
              <span>Security: Read-Only Foreign Server Isolation Enforced</span>
              <span>FastAPI Gateway: <strong>/api/v1/his/*</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Foreign Servers Fleet */}
      {activeTab === "servers" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {servers.map((srv) => (
              <div
                key={srv.serverId}
                className="p-4 bg-gray-50 rounded-xl border border-gray-200 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-900">{srv.displayName}</span>
                    <Badge variant={srv.status === "READ_ONLY_VERIFIED" ? "verified" : "warning"}>
                      {srv.status}
                    </Badge>
                  </div>
                  <div className="mt-2 text-xs text-gray-600 space-y-1">
                    <div className="flex justify-between">
                      <span>Server ID:</span>
                      <strong className="text-gray-900 font-mono text-[11px]">{srv.serverId}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Engine:</span>
                      <Badge variant="neutral">{srv.systemType}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Host / DB:</span>
                      <span className="font-mono text-[11px] text-gray-700">
                        {srv.host}:{srv.port} ({srv.database})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tables Mapped:</span>
                      <span className="text-gray-900 font-medium">{srv.tablesCount} Foreign Tables</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-gray-200 flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    Latency: <strong className="text-gray-900">{srv.latencyMs} ms</strong>
                  </span>
                  <Button
                    onClick={() => handleTestConnection(srv.serverId)}
                    disabled={testingServerId === srv.serverId}
                    className="text-[11px] px-2.5 py-1 bg-white border border-gray-300 text-gray-800 rounded hover:bg-gray-100"
                  >
                    {testingServerId === srv.serverId ? "Pinging..." : "Test Ping"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: SQL/MED DDL Generator */}
      {activeTab === "ddl" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>PostgreSQL 16 Foreign Data Wrapper (postgres_fdw) Setup Script</span>
            <span className="font-mono text-gray-500">ISO/IEC 9075-9 SQL/MED</span>
          </div>
          <pre className="p-4 bg-gray-900 text-gray-100 rounded-xl text-xs font-mono overflow-x-auto max-h-[380px]">
{`-- ============================================================================
-- NIRMAYA PostgreSQL Foreign Data Wrapper (postgres_fdw) Federation DDL
-- ISO/IEC 9075-9 SQL/MED Standard Specification
-- ============================================================================

-- 1. Enable postgres_fdw extension
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- 2. Create isolated foreign federation schema
CREATE SCHEMA IF NOT EXISTS foreign_his_delhi;

-- 3. Define foreign server connection
CREATE SERVER IF NOT EXISTS his_delhi_civil_01_server
  FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (
    host '10.0.4.15',
    port '5432',
    dbname 'ehospital_delhi_db',
    fetch_size '100',
    use_remote_estimate 'true'
  );

-- 4. User mapping with read-only credentials
CREATE USER MAPPING IF NOT EXISTS FOR current_user
  SERVER his_delhi_civil_01_server
  OPTIONS (
    user 'readonly_nirmaya_sync',
    password '\${LEGACY_HIS_DB_PASSWORD}'
  );

-- 5. Foreign Tables Declaration
CREATE FOREIGN TABLE IF NOT EXISTS foreign_his_delhi.legacy_patients (
  pt_id VARCHAR(64),
  mrn_no VARCHAR(32),
  full_name VARCHAR(128),
  dob_str VARCHAR(16),
  gender_char CHAR(1),
  cell_phone VARCHAR(20),
  legacy_abha VARCHAR(32),
  created_at TIMESTAMP
)
SERVER his_delhi_civil_01_server
OPTIONS (schema_name 'public', table_name 'pt_demographics');`}
          </pre>
        </div>
      )}
    </Card>
  );
};

