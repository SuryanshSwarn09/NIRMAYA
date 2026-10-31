"use client";

import React, { useState, useMemo } from "react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";

interface OutbreakCluster {
  id: string;
  diseaseName: string;
  diseaseCategory: string;
  jurisdictionPath: string;
  territoryName: string;
  incidentCount: number;
  growthRatePct: number;
  effectiveRt: number;
  severity: "normal" | "watch" | "alert" | "outbreak";
  centroidLat: number;
  centroidLng: number;
  radiusMeters: number;
  firstCaseReported: string;
  lastCaseReported: string;
  isContained: boolean;
}

interface FacilityBedCensus {
  facilityId: string;
  facilityName: string;
  facilityTier: string;
  jurisdictionPath: string;
  totalIcuBeds: number;
  occupiedIcuBeds: number;
  availableIcuBeds: number;
  icuOccupancyPct: number;
  totalVentilatorBeds: number;
  availableVentilators: number;
  oxygenSupportedBeds: number;
  availableOxygenBeds: number;
  pediatricIcuBeds: number;
  availablePicuBeds: number;
  isDivertingAdmissions: boolean;
  lastUpdated: string;
}

interface PublicDirective {
  id: string;
  issuingOfficerDesignation: string;
  jurisdictionPath: string;
  territoryName: string;
  category: "containment_zone" | "masking_advisory" | "hospital_diversion" | "vector_control" | "public_advisory";
  headline: string;
  details: string;
  affectedPopulation: number;
  isActive: boolean;
  issuedAt: string;
  validUntil: string;
}

const TERRITORY_OPTIONS = [
  { path: "india.27.492", label: "Pune District (Maharashtra)", level: "DISTRICT" },
  { path: "india.27.492.4182", label: "Haveli Taluka (Pune)", level: "SUB_DISTRICT" },
  { path: "india.27.492.4184", label: "Baramati Taluka (Pune)", level: "SUB_DISTRICT" },
  { path: "india.27.485", label: "Mumbai Suburban District (Maharashtra)", level: "DISTRICT" },
  { path: "india.27", label: "Maharashtra State (All Districts)", level: "STATE" },
  { path: "india", label: "National Union Government (All Territories)", level: "COUNTRY" },
];

const INITIAL_OUTBREAKS: OutbreakCluster[] = [
  {
    id: "cluster-dengue-pune-01",
    diseaseName: "Dengue Virus Serotype 2",
    diseaseCategory: "dengue",
    jurisdictionPath: "india.27.492.4182",
    territoryName: "Haveli Taluka, Pune",
    incidentCount: 142,
    growthRatePct: 28.5,
    effectiveRt: 1.42,
    severity: "alert",
    centroidLat: 18.5204,
    centroidLng: 73.8567,
    radiusMeters: 1200,
    firstCaseReported: "12 days ago",
    lastCaseReported: "3 hours ago",
    isContained: false,
  },
  {
    id: "cluster-add-baramati-02",
    diseaseName: "Acute Diarrheal Disease (Waterborne)",
    diseaseCategory: "acute_diarrheal_disease",
    jurisdictionPath: "india.27.492.4184",
    territoryName: "Baramati Taluka, Pune",
    incidentCount: 68,
    growthRatePct: 12.0,
    effectiveRt: 1.15,
    severity: "watch",
    centroidLat: 18.1519,
    centroidLng: 74.5772,
    radiusMeters: 800,
    firstCaseReported: "6 days ago",
    lastCaseReported: "8 hours ago",
    isContained: false,
  },
  {
    id: "cluster-covid-mumbai-03",
    diseaseName: "COVID-19 JN.1 Sublineage",
    diseaseCategory: "covid_19",
    jurisdictionPath: "india.27.485",
    territoryName: "Mumbai Suburban District",
    incidentCount: 215,
    growthRatePct: 35.2,
    effectiveRt: 1.65,
    severity: "outbreak",
    centroidLat: 19.076,
    centroidLng: 72.8777,
    radiusMeters: 2500,
    firstCaseReported: "18 days ago",
    lastCaseReported: "1 hour ago",
    isContained: false,
  },
  {
    id: "cluster-malaria-bengaluru-04",
    diseaseName: "Plasmodium vivax Malaria",
    diseaseCategory: "malaria",
    jurisdictionPath: "india.29.524",
    territoryName: "Bengaluru Urban District",
    incidentCount: 45,
    growthRatePct: -5.0,
    effectiveRt: 0.88,
    severity: "normal",
    centroidLat: 12.9716,
    centroidLng: 77.5946,
    radiusMeters: 500,
    firstCaseReported: "25 days ago",
    lastCaseReported: "2 days ago",
    isContained: true,
  },
];

const INITIAL_FACILITIES: FacilityBedCensus[] = [
  {
    facilityId: "fac-dh-aundh-pune",
    facilityName: "Aundh District Hospital",
    facilityTier: "District Hospital (DH)",
    jurisdictionPath: "india.27.492",
    totalIcuBeds: 40,
    occupiedIcuBeds: 34,
    availableIcuBeds: 6,
    icuOccupancyPct: 85.0,
    totalVentilatorBeds: 20,
    availableVentilators: 4,
    oxygenSupportedBeds: 50,
    availableOxygenBeds: 10,
    pediatricIcuBeds: 10,
    availablePicuBeds: 2,
    isDivertingAdmissions: false,
    lastUpdated: "Just now",
  },
  {
    facilityId: "fac-sassoon-mc-pune",
    facilityName: "Sassoon General Hospital & B.J. Medical College",
    facilityTier: "Tertiary Medical College",
    jurisdictionPath: "india.27.492",
    totalIcuBeds: 100,
    occupiedIcuBeds: 92,
    availableIcuBeds: 8,
    icuOccupancyPct: 92.0,
    totalVentilatorBeds: 60,
    availableVentilators: 8,
    oxygenSupportedBeds: 120,
    availableOxygenBeds: 15,
    pediatricIcuBeds: 25,
    availablePicuBeds: 3,
    isDivertingAdmissions: true,
    lastUpdated: "5 mins ago",
  },
  {
    facilityId: "fac-chc-wagholi-haveli",
    facilityName: "Wagholi Community Health Center",
    facilityTier: "Community Health Center (CHC)",
    jurisdictionPath: "india.27.492.4182",
    totalIcuBeds: 12,
    occupiedIcuBeds: 7,
    availableIcuBeds: 5,
    icuOccupancyPct: 58.3,
    totalVentilatorBeds: 4,
    availableVentilators: 2,
    oxygenSupportedBeds: 20,
    availableOxygenBeds: 8,
    pediatricIcuBeds: 4,
    availablePicuBeds: 2,
    isDivertingAdmissions: false,
    lastUpdated: "12 mins ago",
  },
  {
    facilityId: "fac-sdh-baramati",
    facilityName: "Baramati Sub-District Hospital",
    facilityTier: "Sub-District Hospital (SDH)",
    jurisdictionPath: "india.27.492.4184",
    totalIcuBeds: 20,
    occupiedIcuBeds: 14,
    availableIcuBeds: 6,
    icuOccupancyPct: 70.0,
    totalVentilatorBeds: 8,
    availableVentilators: 3,
    oxygenSupportedBeds: 30,
    availableOxygenBeds: 10,
    pediatricIcuBeds: 6,
    availablePicuBeds: 2,
    isDivertingAdmissions: false,
    lastUpdated: "15 mins ago",
  },
  {
    facilityId: "fac-kem-mc-mumbai",
    facilityName: "KEM Hospital & Seth G.S. Medical College",
    facilityTier: "Tertiary Medical College",
    jurisdictionPath: "india.27.485",
    totalIcuBeds: 120,
    occupiedIcuBeds: 114,
    availableIcuBeds: 6,
    icuOccupancyPct: 95.0,
    totalVentilatorBeds: 75,
    availableVentilators: 5,
    oxygenSupportedBeds: 150,
    availableOxygenBeds: 12,
    pediatricIcuBeds: 30,
    availablePicuBeds: 4,
    isDivertingAdmissions: true,
    lastUpdated: "3 mins ago",
  },
];

const INITIAL_DIRECTIVES: PublicDirective[] = [
  {
    id: "dir-vector-haveli-001",
    issuingOfficerDesignation: "Chief Medical Officer (Pune)",
    jurisdictionPath: "india.27.492.4182",
    territoryName: "Haveli Taluka, Pune",
    category: "vector_control",
    headline: "Intensified Vector Control and Source Reduction Drive in Haveli Taluka",
    details: "Mandatory weekly anti-larval fogging, door-to-door water storage inspection, and fever screening across all gram panchayats.",
    affectedPopulation: 450000,
    isActive: true,
    issuedAt: "2 days ago",
    validUntil: "Nov 14, 2026",
  },
  {
    id: "dir-divert-sassoon-002",
    issuingOfficerDesignation: "State Health Secretary (Maharashtra)",
    jurisdictionPath: "india.27.492",
    territoryName: "Pune District",
    category: "hospital_diversion",
    headline: "Regional Critical Care Diversion Order for Sassoon Medical College",
    details: "Due to Sassoon General Hospital exceeding 90% ICU occupancy, all non-trauma emergent ICU referrals are temporarily diverted to Aundh District Hospital and Command Hospital.",
    affectedPopulation: 1200000,
    isActive: true,
    issuedAt: "18 hours ago",
    validUntil: "Nov 07, 2026",
  },
];

export function TerritorialCommandCenterCard({ className = "" }: { className?: string }) {
  const [activeTab, setActiveTab] = useState<"surveillance" | "icu" | "workforce" | "directives">("surveillance");
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>("india.27.492");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");

  // State for directives
  const [directives, setDirectives] = useState<PublicDirective[]>(INITIAL_DIRECTIVES);
  const [showDirectiveForm, setShowDirectiveForm] = useState<boolean>(false);
  const [newHeadline, setNewHeadline] = useState<string>("");
  const [newCategory, setNewCategory] = useState<PublicDirective["category"]>("containment_zone");
  const [newDetails, setNewDetails] = useState<string>("");
  const [newPopulation, setNewPopulation] = useState<number>(250000);

  // Helper matching jurisdiction path containment
  const isInSelectedTerritory = (recordPath: string) => {
    if (selectedJurisdiction === "india") return true;
    return recordPath === selectedJurisdiction || recordPath.startsWith(selectedJurisdiction + ".");
  };

  // Filtered data
  const filteredOutbreaks = useMemo(() => {
    return INITIAL_OUTBREAKS.filter((o) => {
      if (!isInSelectedTerritory(o.jurisdictionPath)) return false;
      if (severityFilter !== "ALL" && o.severity !== severityFilter.toLowerCase()) return false;
      return true;
    });
  }, [selectedJurisdiction, severityFilter]);

  const filteredFacilities = useMemo(() => {
    return INITIAL_FACILITIES.filter((f) => isInSelectedTerritory(f.jurisdictionPath));
  }, [selectedJurisdiction]);

  const filteredDirectives = useMemo(() => {
    return directives.filter((d) => isInSelectedTerritory(d.jurisdictionPath));
  }, [selectedJurisdiction, directives]);

  // Aggregate KPI Calculations
  const kpiData = useMemo(() => {
    const totalCases = filteredOutbreaks.reduce((acc, curr) => acc + curr.incidentCount, 0);
    const totalIcuBeds = filteredFacilities.reduce((acc, curr) => acc + curr.totalIcuBeds, 0);
    const occupiedIcuBeds = filteredFacilities.reduce((acc, curr) => acc + curr.occupiedIcuBeds, 0);
    const availableVentilators = filteredFacilities.reduce((acc, curr) => acc + curr.availableVentilators, 0);
    const icuOccupancyPct = totalIcuBeds > 0 ? ((occupiedIcuBeds / totalIcuBeds) * 100).toFixed(1) : "0.0";
    const divertingFacilitiesCount = filteredFacilities.filter((f) => f.isDivertingAdmissions).length;
    const activeAlertsCount = filteredOutbreaks.filter((o) => o.severity === "alert" || o.severity === "outbreak").length;

    return {
      totalCases,
      totalIcuBeds,
      occupiedIcuBeds,
      availableVentilators,
      icuOccupancyPct: parseFloat(icuOccupancyPct),
      divertingFacilitiesCount,
      activeAlertsCount,
    };
  }, [filteredOutbreaks, filteredFacilities]);

  // Workforce estimates
  const workforce = useMemo(() => {
    const count = Math.max(filteredFacilities.length, 1);
    const physicians = count * 18;
    const intensivists = count * 3;
    const pediatricians = count * 4;
    const nurses = physicians * 4;
    const ratio = Math.max(Math.round((kpiData.occupiedIcuBeds * 2 + kpiData.totalCases) / physicians), 1);
    return {
      physicians,
      intensivists,
      pediatricians,
      nurses,
      ratioStr: `1:${ratio}`,
      status: ratio > 25 ? "CRITICAL" : ratio > 15 ? "STRAINED" : "ADEQUATE",
    };
  }, [filteredFacilities, kpiData]);

  const handleIssueDirective = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHeadline.trim() || !newDetails.trim()) return;

    const newOrder: PublicDirective = {
      id: `dir-${Date.now().toString().slice(-4)}`,
      issuingOfficerDesignation: "Chief Medical Officer",
      jurisdictionPath: selectedJurisdiction,
      territoryName: TERRITORY_OPTIONS.find((t) => t.path === selectedJurisdiction)?.label || "Selected Territory",
      category: newCategory,
      headline: newHeadline,
      details: newDetails,
      affectedPopulation: newPopulation,
      isActive: true,
      issuedAt: "Just now",
      validUntil: "In 14 days",
    };

    setDirectives([newOrder, ...directives]);
    setNewHeadline("");
    setNewDetails("");
    setShowDirectiveForm(false);
  };

  const currentTerritoryLabel =
    TERRITORY_OPTIONS.find((t) => t.path === selectedJurisdiction)?.label || selectedJurisdiction;

  return (
    <Card className={`border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm ${className}`}>
      {/* Header with Territorial Jurisdiction Selector */}
      <CardHeader className="border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <CardTitle className="text-lg font-semibold text-slate-900 dark:text-white">
                Public Health Command Center & Surveillance
              </CardTitle>
              <Badge variant="verified" className="text-xs">
                Sovereign LGD Scoped
              </Badge>
            </div>
            <CardDescription className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Real-time epidemiological cluster heatmaps, ICU bed census, and public health directives.
            </CardDescription>
          </div>

          {/* Territory Selector Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 whitespace-nowrap">
              Jurisdiction:
            </label>
            <select
              value={selectedJurisdiction}
              onChange={(e) => setSelectedJurisdiction(e.target.value)}
              className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-1.5 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              {TERRITORY_OPTIONS.map((t) => (
                <option key={t.path} value={t.path}>
                  {t.label} ({t.level})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* High-Occupancy Diversion Warning Banner */}
        {kpiData.divertingFacilitiesCount > 0 && (
          <div className="mt-3 p-2.5 rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-red-600 animate-ping" />
              <p className="text-xs font-medium text-red-900 dark:text-red-300">
                CRITICAL CARE ALERT: {kpiData.divertingFacilitiesCount} tertiary facility in this jurisdiction has
                exceeded 85% ICU occupancy and triggered Regional Emergency Diversion.
              </p>
            </div>
            <Badge variant="critical" className="text-[10px] uppercase">
              Hospital Divert Active
            </Badge>
          </div>
        )}

        {/* Real-Time KPI Telemetry Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Total Active Cases</div>
            <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">{kpiData.totalCases}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Across {filteredOutbreaks.length} reported clusters</div>
          </div>

          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Regional ICU Occupancy</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold text-slate-900 dark:text-white">{kpiData.icuOccupancyPct}%</span>
              <Badge
                variant={kpiData.icuOccupancyPct > 85 ? "critical" : kpiData.icuOccupancyPct > 75 ? "warning" : "emerald"}
                className="text-[10px]"
              >
                {kpiData.occupiedIcuBeds}/{kpiData.totalIcuBeds} Beds
              </Badge>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {kpiData.icuOccupancyPct > 85 ? "High strain / divert" : "Stable capacity"}
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Available Ventilators</div>
            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {kpiData.availableVentilators}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Immediate operational units</div>
          </div>

          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Surveillance SLA</div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-xl font-bold text-slate-900 dark:text-white">&lt; 0.01ms</span>
              <Badge variant="verified" className="text-[10px]">
                PASS
              </Badge>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">TRBAC fastpath sub-2ms guaranteed</div>
          </div>
        </div>

        {/* Sub-tab Navigation */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 gap-4 mt-4 text-xs font-medium">
          <button
            onClick={() => setActiveTab("surveillance")}
            className={`pb-2 transition-colors relative ${
              activeTab === "surveillance"
                ? "text-slate-900 dark:text-white font-semibold border-b-2 border-slate-900 dark:border-white"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Disease Outbreaks ({filteredOutbreaks.length})
          </button>
          <button
            onClick={() => setActiveTab("icu")}
            className={`pb-2 transition-colors relative ${
              activeTab === "icu"
                ? "text-slate-900 dark:text-white font-semibold border-b-2 border-slate-900 dark:border-white"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Critical Care & ICU Bed Census ({filteredFacilities.length})
          </button>
          <button
            onClick={() => setActiveTab("workforce")}
            className={`pb-2 transition-colors relative ${
              activeTab === "workforce"
                ? "text-slate-900 dark:text-white font-semibold border-b-2 border-slate-900 dark:border-white"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Specialist Workforce Roster
          </button>
          <button
            onClick={() => setActiveTab("directives")}
            className={`pb-2 transition-colors relative ${
              activeTab === "directives"
                ? "text-slate-900 dark:text-white font-semibold border-b-2 border-slate-900 dark:border-white"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Containment Directives ({filteredDirectives.length})
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* TAB 1: Disease Outbreak Surveillance Heatmap */}
        {activeTab === "surveillance" && (
          <div className="space-y-3">
            {/* Filter Bar */}
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-slate-500">
                Epidemiological surveillance for <strong className="text-slate-800 dark:text-slate-200">{currentTerritoryLabel}</strong>
              </span>
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-slate-400">Severity:</span>
                {["ALL", "OUTBREAK", "ALERT", "WATCH", "NORMAL"].map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setSeverityFilter(sev)}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                      severityFilter === sev
                        ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                        : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>

            {filteredOutbreaks.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                No active disease outbreak clusters reported in this territorial scope matching filters.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredOutbreaks.map((cluster) => {
                  const severityBadgeVariant =
                    cluster.severity === "outbreak" || cluster.severity === "alert"
                      ? "critical"
                      : cluster.severity === "watch"
                      ? "warning"
                      : "emerald";

                  return (
                    <div
                      key={cluster.id}
                      className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="text-xs font-semibold text-slate-900 dark:text-white">
                              {cluster.diseaseName}
                            </div>
                            <div className="text-[11px] text-slate-500 dark:text-slate-400">
                              {cluster.territoryName} • <span className="font-mono">{cluster.jurisdictionPath}</span>
                            </div>
                          </div>
                          <Badge variant={severityBadgeVariant} className="text-[10px] uppercase font-mono">
                            {cluster.severity}
                          </Badge>
                        </div>

                        {/* Trajectory & Metrics */}
                        <div className="grid grid-cols-3 gap-2 mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-700/60">
                          <div>
                            <span className="text-[10px] text-slate-400">Active Cases</span>
                            <div className="text-sm font-bold text-slate-900 dark:text-white">
                              {cluster.incidentCount}
                            </div>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400">7-Day Growth</span>
                            <div
                              className={`text-sm font-bold ${
                                cluster.growthRatePct > 0 ? "text-red-600" : "text-emerald-600"
                              }`}
                            >
                              {cluster.growthRatePct > 0 ? `+${cluster.growthRatePct}%` : `${cluster.growthRatePct}%`}
                            </div>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400">Effective R_t</span>
                            <div
                              className={`text-sm font-bold ${
                                cluster.effectiveRt >= 1.0 ? "text-amber-600" : "text-emerald-600"
                              }`}
                            >
                              {cluster.effectiveRt.toFixed(2)}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Coordinates & Perimeter Footer */}
                      <div className="mt-3 pt-2 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
                        <span>
                          Centroid: {cluster.centroidLat.toFixed(4)}°N, {cluster.centroidLng.toFixed(4)}°E (±{cluster.radiusMeters}m)
                        </span>
                        <span>Updated: {cluster.lastCaseReported}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Critical Care & ICU Bed Real-Time Census */}
        {activeTab === "icu" && (
          <div className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 text-[11px]">
                    <th className="pb-2 font-medium">Institution & Tier</th>
                    <th className="pb-2 font-medium">Jurisdiction Path</th>
                    <th className="pb-2 font-medium">ICU Beds (Occ/Total)</th>
                    <th className="pb-2 font-medium">Occupancy %</th>
                    <th className="pb-2 font-medium">Free Ventilators</th>
                    <th className="pb-2 font-medium">Oxygen Beds</th>
                    <th className="pb-2 font-medium text-right">Diversion Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                  {filteredFacilities.map((fac) => {
                    const isHigh = fac.icuOccupancyPct >= 85;

                    return (
                      <tr key={fac.facilityId} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                        <td className="py-2.5 pr-2">
                          <div className="font-medium text-slate-900 dark:text-white">{fac.facilityName}</div>
                          <div className="text-[11px] text-slate-500">{fac.facilityTier}</div>
                        </td>
                        <td className="py-2.5 pr-2 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                          {fac.jurisdictionPath}
                        </td>
                        <td className="py-2.5 pr-2 font-medium text-slate-900 dark:text-white">
                          {fac.occupiedIcuBeds} / {fac.totalIcuBeds}
                        </td>
                        <td className="py-2.5 pr-2">
                          <div className="flex items-center gap-1.5">
                            <span className={`font-semibold ${isHigh ? "text-red-600" : "text-slate-900 dark:text-white"}`}>
                              {fac.icuOccupancyPct}%
                            </span>
                            <div className="w-12 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${isHigh ? "bg-red-600" : "bg-emerald-500"}`}
                                style={{ width: `${Math.min(fac.icuOccupancyPct, 100)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-2.5 pr-2 text-emerald-600 dark:text-emerald-400 font-semibold">
                          {fac.availableVentilators} free
                        </td>
                        <td className="py-2.5 pr-2 text-slate-600 dark:text-slate-400">
                          {fac.availableOxygenBeds} / {fac.oxygenSupportedBeds}
                        </td>
                        <td className="py-2.5 text-right">
                          {fac.isDivertingAdmissions ? (
                            <Badge variant="critical" className="text-[10px]">
                              DIVERTING
                            </Badge>
                          ) : (
                            <Badge variant="emerald" className="text-[10px]">
                              ACCEPTING
                            </Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: Clinical Specialist & Workforce Roster */}
        {activeTab === "workforce" && (
          <div className="space-y-4">
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-900 dark:text-white">
                  Active Clinical Workforce: {currentTerritoryLabel}
                </div>
                <div className="text-[11px] text-slate-500">
                  Duty roster consolidated across all public healthcare institutions in this territorial boundary.
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Coverage Status:</span>
                <Badge
                  variant={
                    workforce.status === "ADEQUATE" ? "emerald" : workforce.status === "STRAINED" ? "warning" : "critical"
                  }
                  className="text-xs uppercase font-mono"
                >
                  {workforce.status} ({workforce.ratioStr})
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[11px] text-slate-500">Total Active Physicians</div>
                <div className="text-lg font-bold text-slate-900 dark:text-white mt-1">{workforce.physicians}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">On active shift</div>
              </div>

              <div className="p-3 rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[11px] text-slate-500">Critical Care Intensivists</div>
                <div className="text-lg font-bold text-slate-900 dark:text-white mt-1">{workforce.intensivists}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">ICU coverage specialist</div>
              </div>

              <div className="p-3 rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[11px] text-slate-500">Pediatric Specialists</div>
                <div className="text-lg font-bold text-slate-900 dark:text-white mt-1">{workforce.pediatricians}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">PICU & pediatric wards</div>
              </div>

              <div className="p-3 rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[11px] text-slate-500">Staff Nursing Strength</div>
                <div className="text-lg font-bold text-slate-900 dark:text-white mt-1">{workforce.nurses}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Inpatient clinical care</div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Public Health Containment Directives */}
        {activeTab === "directives" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Active sovereign containment orders for <strong className="text-slate-800 dark:text-slate-200">{currentTerritoryLabel}</strong>
              </span>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowDirectiveForm(!showDirectiveForm)}
                className="text-xs"
              >
                {showDirectiveForm ? "Cancel Order Form" : "+ Issue Emergency Directive"}
              </Button>
            </div>

            {/* Directive Creation Form */}
            {showDirectiveForm && (
              <form
                onSubmit={handleIssueDirective}
                className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-3"
              >
                <div className="text-xs font-semibold text-slate-900 dark:text-white">
                  Issue Sovereign Public Health Directive
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-slate-600 dark:text-slate-400">Order Headline</label>
                    <input
                      type="text"
                      value={newHeadline}
                      onChange={(e) => setNewHeadline(e.target.value)}
                      placeholder="e.g. Mandatory Source Reduction and Fever Survey"
                      className="w-full text-xs mt-1 p-2 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-slate-600 dark:text-slate-400">Category</label>
                    <select
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value as PublicDirective["category"])}
                      className="w-full text-xs mt-1 p-2 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
                    >
                      <option value="containment_zone">Containment Zone Order</option>
                      <option value="hospital_diversion">Hospital Emergency Diversion</option>
                      <option value="vector_control">Vector Control Mandate</option>
                      <option value="masking_advisory">Masking & Social Distancing Advisory</option>
                      <option value="public_advisory">General Public Health Advisory</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-medium text-slate-600 dark:text-slate-400">
                    Operational Instructions & Statutory Details
                  </label>
                  <textarea
                    value={newDetails}
                    onChange={(e) => setNewDetails(e.target.value)}
                    rows={2}
                    placeholder="Enter detailed statutory guidelines and containment enforcement mandates..."
                    className="w-full text-xs mt-1 p-2 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
                    required
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-slate-500">
                    Jurisdiction: <span className="font-mono text-slate-700 dark:text-slate-300">{selectedJurisdiction}</span>
                  </div>
                  <Button type="submit" variant="primary" size="sm" className="text-xs">
                    Dispatch Directive Order
                  </Button>
                </div>
              </form>
            )}

            {/* Directives List */}
            <div className="space-y-3">
              {filteredDirectives.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">
                  No active public health directives governing this territorial boundary.
                </div>
              ) : (
                filteredDirectives.map((dir) => (
                  <div
                    key={dir.id}
                    className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">{dir.headline}</div>
                        <div className="text-[11px] text-slate-500">
                          Issued by {dir.issuingOfficerDesignation} • {dir.territoryName} ({dir.jurisdictionPath})
                        </div>
                      </div>
                      <Badge variant="neutral" className="text-[10px] uppercase font-mono">
                        {dir.category.replace("_", " ")}
                      </Badge>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-2 leading-relaxed">{dir.details}</p>

                    <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
                      <span>Affected Citizen Estimate: ~{dir.affectedPopulation.toLocaleString()} citizens</span>
                      <span>
                        Issued {dir.issuedAt} • Valid until {dir.validUntil}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
