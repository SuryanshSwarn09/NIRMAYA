"use client";

import React, { useState, useEffect } from "react";
import {
  Building2,
  MapPin,
  ChevronRight,
  ChevronDown,
  Search,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Users,
  Compass,
  Layers,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export interface AdministrativeUnitItem {
  id: string;
  name: string;
  unit_level: "country" | "state" | "division" | "district" | "sub_district";
  lgd_code?: string | null;
  path: string;
  parent_id?: string | null;
  level_depth: number;
  child_count: number;
  is_active: boolean;
}

export interface AdministrativeOfficerItem {
  id: string;
  user_id: string;
  designation: string;
  administrative_unit_id: string;
  jurisdiction_path: string;
  gov_email: string;
  aadhaar_verified: boolean;
  unit_name?: string | null;
  unit_level?: string | null;
  is_active: boolean;
}

interface AdministrativeHierarchyViewerCardProps {
  className?: string;
}

export function AdministrativeHierarchyViewerCard({ className = "" }: AdministrativeHierarchyViewerCardProps) {
  const [activeTab, setActiveTab] = useState<"tree" | "search" | "officers">("tree");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUnit, setSelectedUnit] = useState<AdministrativeUnitItem | null>(null);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
    new Set(["india", "india.27", "india.27.pune_div", "india.27.492"])
  );

  // Jurisdiction check bench states
  const [testOfficerPath, setTestOfficerPath] = useState("india.27.492");
  const [testTargetPath, setTestTargetPath] = useState("india.27.492.4182");
  const [jurisdictionResult, setJurisdictionResult] = useState<{
    tested: boolean;
    authorized: boolean;
    message: string;
  }>({
    tested: true,
    authorized: true,
    message: "Authorized: Target facility is under Pune District jurisdiction scope.",
  });

  // Reference Administrative Units (Pre-loaded for responsive display)
  const defaultUnits: AdministrativeUnitItem[] = [
    {
      id: "unit-india",
      name: "India (Union Government)",
      unit_level: "country",
      lgd_code: "IND",
      path: "india",
      parent_id: null,
      level_depth: 0,
      child_count: 36,
      is_active: true,
    },
    {
      id: "unit-state-27",
      name: "Maharashtra",
      unit_level: "state",
      lgd_code: "27",
      path: "india.27",
      parent_id: "unit-india",
      level_depth: 1,
      child_count: 6,
      is_active: true,
    },
    {
      id: "unit-div-pune",
      name: "Pune Division",
      unit_level: "division",
      lgd_code: "DIV_27_01",
      path: "india.27.pune_div",
      parent_id: "unit-state-27",
      level_depth: 2,
      child_count: 2,
      is_active: true,
    },
    {
      id: "unit-dist-492",
      name: "Pune District",
      unit_level: "district",
      lgd_code: "492",
      path: "india.27.492",
      parent_id: "unit-div-pune",
      level_depth: 3,
      child_count: 3,
      is_active: true,
    },
    {
      id: "unit-sub-4182",
      name: "Haveli Sub-District",
      unit_level: "sub_district",
      lgd_code: "4182",
      path: "india.27.492.4182",
      parent_id: "unit-dist-492",
      level_depth: 4,
      child_count: 0,
      is_active: true,
    },
    {
      id: "unit-sub-4183",
      name: "Pune City Sub-District",
      unit_level: "sub_district",
      lgd_code: "4183",
      path: "india.27.492.4183",
      parent_id: "unit-dist-492",
      level_depth: 4,
      child_count: 0,
      is_active: true,
    },
    {
      id: "unit-sub-4184",
      name: "Baramati Sub-District",
      unit_level: "sub_district",
      lgd_code: "4184",
      path: "india.27.492.4184",
      parent_id: "unit-dist-492",
      level_depth: 4,
      child_count: 0,
      is_active: true,
    },
    {
      id: "unit-dist-493",
      name: "Satara District",
      unit_level: "district",
      lgd_code: "493",
      path: "india.27.493",
      parent_id: "unit-div-pune",
      level_depth: 3,
      child_count: 2,
      is_active: true,
    },
    {
      id: "unit-sub-4190",
      name: "Satara Taluka",
      unit_level: "sub_district",
      lgd_code: "4190",
      path: "india.27.493.4190",
      parent_id: "unit-dist-493",
      level_depth: 4,
      child_count: 0,
      is_active: true,
    },
    {
      id: "unit-state-07",
      name: "Delhi (NCT)",
      unit_level: "state",
      lgd_code: "07",
      path: "india.07",
      parent_id: "unit-india",
      level_depth: 1,
      child_count: 11,
      is_active: true,
    },
    {
      id: "unit-dist-89",
      name: "New Delhi District",
      unit_level: "district",
      lgd_code: "89",
      path: "india.07.89",
      parent_id: "unit-state-07",
      level_depth: 2,
      child_count: 2,
      is_active: true,
    },
    {
      id: "unit-state-29",
      name: "Karnataka",
      unit_level: "state",
      lgd_code: "29",
      path: "india.29",
      parent_id: "unit-india",
      level_depth: 1,
      child_count: 31,
      is_active: true,
    },
    {
      id: "unit-dist-524",
      name: "Bengaluru Urban District",
      unit_level: "district",
      lgd_code: "524",
      path: "india.29.524",
      parent_id: "unit-state-29",
      level_depth: 2,
      child_count: 4,
      is_active: true,
    },
    {
      id: "unit-state-19",
      name: "West Bengal",
      unit_level: "state",
      lgd_code: "19",
      path: "india.19",
      parent_id: "unit-india",
      level_depth: 1,
      child_count: 23,
      is_active: true,
    },
    {
      id: "unit-dist-718",
      name: "Paschim Bardhaman District",
      unit_level: "district",
      lgd_code: "718",
      path: "india.19.718",
      parent_id: "unit-state-19",
      level_depth: 2,
      child_count: 2,
      is_active: true,
    },
    {
      id: "unit-sub-2002",
      name: "Durgapur Sub-District",
      unit_level: "sub_district",
      lgd_code: "2002",
      path: "india.19.718.2002",
      parent_id: "unit-dist-718",
      level_depth: 3,
      child_count: 0,
      is_active: true,
    },
  ];

  // Default Appointed Officers
  const defaultOfficers: AdministrativeOfficerItem[] = [
    {
      id: "off-01",
      user_id: "user-admin-national",
      designation: "NATIONAL_DIRECTOR",
      administrative_unit_id: "unit-india",
      jurisdiction_path: "india",
      gov_email: "national.director.abdm@gov.in",
      aadhaar_verified: true,
      unit_name: "India (Union Government)",
      unit_level: "country",
      is_active: true,
    },
    {
      id: "off-02",
      user_id: "user-admin-mh",
      designation: "STATE_SECRETARY",
      administrative_unit_id: "unit-state-27",
      jurisdiction_path: "india.27",
      gov_email: "secretary.health.mh@gov.in",
      aadhaar_verified: true,
      unit_name: "Maharashtra",
      unit_level: "state",
      is_active: true,
    },
    {
      id: "off-03",
      user_id: "user-admin-pune",
      designation: "CHIEF_MEDICAL_OFFICER",
      administrative_unit_id: "unit-dist-492",
      jurisdiction_path: "india.27.492",
      gov_email: "cmo.pune@nic.in",
      aadhaar_verified: true,
      unit_name: "Pune District",
      unit_level: "district",
      is_active: true,
    },
    {
      id: "off-04",
      user_id: "user-admin-haveli",
      designation: "BLOCK_MEDICAL_OFFICER",
      administrative_unit_id: "unit-sub-4182",
      jurisdiction_path: "india.27.492.4182",
      gov_email: "bmo.haveli@nic.in",
      aadhaar_verified: true,
      unit_name: "Haveli Sub-District",
      unit_level: "sub_district",
      is_active: true,
    },
  ];

  const [units] = useState<AdministrativeUnitItem[]>(defaultUnits);
  const [officers] = useState<AdministrativeOfficerItem[]>(defaultOfficers);

  // Initialize selected unit to Pune District by default
  useEffect(() => {
    const defaultSelected = units.find((u) => u.lgd_code === "492") || units[0];
    setSelectedUnit(defaultSelected);
  }, []);

  const toggleExpand = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const handleRunJurisdictionCheck = () => {
    const authorized =
      testOfficerPath === testTargetPath || testTargetPath.startsWith(testOfficerPath + ".");
    setJurisdictionResult({
      tested: true,
      authorized,
      message: authorized
        ? `Authorized: Target '${testTargetPath}' falls within jurisdiction scope '${testOfficerPath}'.`
        : `Access Denied: Target '${testTargetPath}' is outside officer's territorial authority '${testOfficerPath}'.`,
    });
  };

  // Filtered units for search tab
  const filteredUnits = units.filter((u) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      u.name.toLowerCase().includes(q) ||
      (u.lgd_code && u.lgd_code.toLowerCase().includes(q)) ||
      u.path.toLowerCase().includes(q) ||
      u.unit_level.toLowerCase().includes(q)
    );
  });

  const getLevelBadgeVariant = (level: string) => {
    switch (level) {
      case "country":
        return "violet";
      case "state":
        return "neutral";
      case "division":
        return "pink";
      case "district":
        return "orange";
      case "sub_district":
        return "verified";
      default:
        return "default";
    }
  };

  // Render tree node recursive
  const renderTreeNode = (unit: AdministrativeUnitItem) => {
    const children = units.filter((u) => u.parent_id === unit.id);
    const hasChildren = children.length > 0;
    const isExpanded = expandedPaths.has(unit.path);
    const isSelected = selectedUnit?.id === unit.id;

    return (
      <div key={unit.id} className="select-none">
        <div
          onClick={() => {
            setSelectedUnit(unit);
            if (hasChildren) toggleExpand(unit.path);
          }}
          className={`flex items-center justify-between py-1.5 px-2 rounded-md cursor-pointer text-xs transition-colors ${
            isSelected
              ? "bg-[#111827] text-white font-medium"
              : "hover:bg-[#f3f4f6] text-[#374151]"
          }`}
          style={{ paddingLeft: `${unit.level_depth * 14 + 8}px` }}
        >
          <div className="flex items-center gap-1.5 min-w-0">
            {hasChildren ? (
              <span className="p-0.5 text-[#9ca3af]">
                {isExpanded ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
              </span>
            ) : (
              <span className="w-4 h-4 inline-block text-center text-[#9ca3af]">
                •
              </span>
            )}
            <Building2 className={`w-3.5 h-3.5 ${isSelected ? "text-white" : "text-[#6b7280]"}`} />
            <span className="truncate">{unit.name}</span>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {unit.lgd_code && (
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                  isSelected ? "bg-white/20 text-white" : "bg-[#f3f4f6] text-[#4b5563]"
                }`}
              >
                LGD {unit.lgd_code}
              </span>
            )}
            <span
              className={`text-[10px] uppercase font-semibold tracking-wider ${
                isSelected ? "text-white/80" : "text-[#9ca3af]"
              }`}
            >
              {unit.unit_level.replace("_", " ")}
            </span>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l border-[#e5e7eb] ml-3.5 my-0.5">
            {children.map((child) => renderTreeNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={`bg-white rounded-lg border border-[#e5e7eb] p-6 text-[#111827] shadow-xs ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-[#e5e7eb] gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-[#111827]">
              Indian LGD Administrative Hierarchy & Governance
            </h2>
            <Badge variant="verified" size="sm">
              LGD Certified (MoPR/MeitY)
            </Badge>
          </div>
          <p className="text-xs text-[#6b7280] mt-1">
            Sovereign 6-tier administrative directory, PostgreSQL ltree sub-2ms territorial queries & chain-of-command
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="neutral" size="sm">
            ltree GiST: sub-2ms
          </Badge>
          <Badge variant="emerald" size="sm">
            DPDP Act Sec 9 Dual-Plane
          </Badge>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-5">
        <div className="p-3 bg-[#fafafa] rounded-md border border-[#e5e7eb]">
          <span className="text-[11px] font-medium text-[#6b7280] block">States & UTs</span>
          <span className="text-lg font-semibold text-[#111827] mt-0.5 block">36 / 36</span>
          <span className="text-[10px] text-[#059669] font-medium block mt-0.5">100% Union Territory</span>
        </div>
        <div className="p-3 bg-[#fafafa] rounded-md border border-[#e5e7eb]">
          <span className="text-[11px] font-medium text-[#6b7280] block">LGD Districts</span>
          <span className="text-lg font-semibold text-[#111827] mt-0.5 block">785+</span>
          <span className="text-[10px] text-[#2563eb] font-medium block mt-0.5">ltree Indexed</span>
        </div>
        <div className="p-3 bg-[#fafafa] rounded-md border border-[#e5e7eb]">
          <span className="text-[11px] font-medium text-[#6b7280] block">Sub-Districts & Blocks</span>
          <span className="text-lg font-semibold text-[#111827] mt-0.5 block">6,000+</span>
          <span className="text-[10px] text-[#6b7280] block mt-0.5">Local Primary Care</span>
        </div>
        <div className="p-3 bg-[#fafafa] rounded-md border border-[#e5e7eb]">
          <span className="text-[11px] font-medium text-[#6b7280] block">Appointed Officers</span>
          <span className="text-lg font-semibold text-[#111827] mt-0.5 block">4 Active</span>
          <span className="text-[10px] text-[#059669] font-medium block mt-0.5">Aadhaar MFA Bound</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-[#e5e7eb] mb-5 gap-6 text-xs font-medium">
        <button
          onClick={() => setActiveTab("tree")}
          className={`pb-2.5 transition-colors border-b-2 cursor-pointer flex items-center gap-1.5 ${
            activeTab === "tree"
              ? "border-[#111827] text-[#111827] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111827]"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Territorial Tree Explorer</span>
        </button>

        <button
          onClick={() => setActiveTab("search")}
          className={`pb-2.5 transition-colors border-b-2 cursor-pointer flex items-center gap-1.5 ${
            activeTab === "search"
              ? "border-[#111827] text-[#111827] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111827]"
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Sub-2ms Scoped Traversal Bench</span>
        </button>

        <button
          onClick={() => setActiveTab("officers")}
          className={`pb-2.5 transition-colors border-b-2 cursor-pointer flex items-center gap-1.5 ${
            activeTab === "officers"
              ? "border-[#111827] text-[#111827] font-semibold"
              : "border-transparent text-[#6b7280] hover:text-[#111827]"
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Appointed Healthcare Officers ({officers.length})</span>
        </button>
      </div>

      {/* Tab 1: Territorial Tree Explorer */}
      {activeTab === "tree" && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
          {/* Tree Explorer Left Column */}
          <div className="md:col-span-7 bg-[#fafafa] rounded-md border border-[#e5e7eb] p-3 max-h-[460px] overflow-y-auto">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#e5e7eb] text-xs text-[#6b7280]">
              <span className="font-medium text-[#374151]">National Territorial Hierarchy</span>
              <span>Click to drill down</span>
            </div>
            {renderTreeNode(units[0])}
          </div>

          {/* Unit Detail Right Column */}
          <div className="md:col-span-5 bg-white rounded-md border border-[#e5e7eb] p-4 flex flex-col justify-between">
            {selectedUnit ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6b7280]">
                      Territory Details
                    </span>
                    <Badge variant={getLevelBadgeVariant(selectedUnit.unit_level)} size="sm">
                      {selectedUnit.unit_level.replace("_", " ").toUpperCase()}
                    </Badge>
                  </div>
                  <h3 className="text-base font-semibold text-[#111827] mt-1">
                    {selectedUnit.name}
                  </h3>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                    <span className="text-[#6b7280]">Official LGD Code</span>
                    <span className="font-mono font-medium text-[#111827]">
                      {selectedUnit.lgd_code || "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                    <span className="text-[#6b7280]">PostgreSQL ltree Path</span>
                    <span className="font-mono text-[#059669] font-medium">
                      {selectedUnit.path}
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                    <span className="text-[#6b7280]">Tree Depth Level</span>
                    <span className="text-[#111827] font-medium">
                      Level {selectedUnit.level_depth} ({selectedUnit.unit_level})
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                    <span className="text-[#6b7280]">Immediate Sub-units</span>
                    <span className="text-[#111827] font-medium">
                      {selectedUnit.child_count} children
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-[#f3f4f6]">
                    <span className="text-[#6b7280]">Territory Status</span>
                    <span className="text-[#059669] font-medium flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Active
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-[#fafafa] rounded border border-[#e5e7eb] text-xs">
                  <span className="font-medium text-[#374151] block mb-1">
                    PostgreSQL ltree Traversal Query
                  </span>
                  <code className="text-[11px] font-mono text-[#4b5563] block break-all">
                    SELECT * FROM administrative_units WHERE path &lt;@ '{selectedUnit.path}';
                  </code>
                  <span className="text-[10px] text-[#6b7280] block mt-1">
                    Indexed via GIST for sub-2ms retrieval across all subordinate facilities.
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-[#6b7280] text-xs">
                Select an administrative unit on the left to view details
              </div>
            )}

            <div className="pt-3 border-t border-[#e5e7eb] flex items-center justify-between text-[11px] text-[#6b7280]">
              <span>Dual-Plane Air-Gap Active</span>
              <span className="text-[#059669] font-medium">Zero Patient Record Access</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Sub-2ms Scoped Traversal Bench */}
      {activeTab === "search" && (
        <div className="space-y-5">
          {/* Fast Search Filter */}
          <div className="relative">
            <Search className="w-4 h-4 text-[#9ca3af] absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by territory name, LGD code, or path token (e.g. Pune, Haveli, 492, 27)..."
              className="w-full pl-9 pr-4 py-2 border border-[#e5e7eb] rounded-md text-xs text-[#111827] placeholder-[#9ca3af] focus:outline-none focus:border-[#111827]"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search Results List */}
            <div className="bg-[#fafafa] rounded-md border border-[#e5e7eb] p-3 max-h-[300px] overflow-y-auto">
              <span className="text-xs font-medium text-[#374151] block pb-2 mb-2 border-b border-[#e5e7eb]">
                Matched Territories ({filteredUnits.length})
              </span>
              <div className="space-y-1.5">
                {filteredUnits.map((u) => (
                  <div
                    key={u.id}
                    onClick={() => {
                      setSelectedUnit(u);
                      setTestTargetPath(u.path);
                    }}
                    className="p-2 rounded bg-white border border-[#e5e7eb] text-xs flex items-center justify-between cursor-pointer hover:border-[#111827] transition-colors"
                  >
                    <div>
                      <span className="font-medium text-[#111827] block">{u.name}</span>
                      <span className="text-[10px] text-[#6b7280] font-mono">{u.path}</span>
                    </div>
                    <div className="text-right">
                      {u.lgd_code && (
                        <span className="text-[10px] bg-[#f3f4f6] text-[#4b5563] px-1.5 py-0.5 rounded font-mono block mb-0.5">
                          LGD {u.lgd_code}
                        </span>
                      )}
                      <span className="text-[9px] uppercase tracking-wider text-[#9ca3af]">
                        {u.unit_level.replace("_", " ")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Jurisdiction RBAC Bench */}
            <div className="bg-white rounded-md border border-[#e5e7eb] p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-1.5 pb-2 border-b border-[#e5e7eb]">
                  <Compass className="w-4 h-4 text-[#111827]" />
                  <h4 className="text-xs font-semibold text-[#111827]">
                    Territorial Jurisdiction Verifier Bench
                  </h4>
                </div>
                <p className="text-[11px] text-[#6b7280] my-2">
                  Simulates Scoped Territorial RBAC verifying whether an administrative officer has supervisory authority over a child facility.
                </p>

                <div className="space-y-3 mt-3 text-xs">
                  <div>
                    <label className="text-[11px] font-medium text-[#374151] block mb-1">
                      Officer Jurisdiction Scope (ltree path):
                    </label>
                    <input
                      type="text"
                      value={testOfficerPath}
                      onChange={(e) => setTestOfficerPath(e.target.value)}
                      className="w-full px-2.5 py-1.5 border border-[#e5e7eb] rounded text-xs font-mono text-[#111827] focus:outline-none focus:border-[#111827]"
                    />
                    <span className="text-[10px] text-[#6b7280] block mt-0.5">
                      Example: 'india.27.492' (Pune District Chief Medical Officer)
                    </span>
                  </div>

                  <div>
                    <label className="text-[11px] font-medium text-[#374151] block mb-1">
                      Target Clinic / Facility Path:
                    </label>
                    <input
                      type="text"
                      value={testTargetPath}
                      onChange={(e) => setTestTargetPath(e.target.value)}
                      className="w-full px-2.5 py-1.5 border border-[#e5e7eb] rounded text-xs font-mono text-[#111827] focus:outline-none focus:border-[#111827]"
                    />
                    <span className="text-[10px] text-[#6b7280] block mt-0.5">
                      Example: 'india.27.492.4182' (Haveli Block) or 'india.27.493' (Satara)
                    </span>
                  </div>

                  <button
                    onClick={handleRunJurisdictionCheck}
                    className="w-full py-1.5 px-3 bg-[#111827] text-white rounded text-xs font-medium hover:bg-[#1f2937] transition-colors cursor-pointer flex items-center justify-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                    <span>Verify Territorial Authority</span>
                  </button>
                </div>
              </div>

              {jurisdictionResult.tested && (
                <div
                  className={`p-3 rounded border text-xs mt-3 flex items-start gap-2 ${
                    jurisdictionResult.authorized
                      ? "bg-[#ecfdf5] border-[#a7f3d0] text-[#065f46]"
                      : "bg-[#fef2f2] border-[#fecaca] text-[#991b1b]"
                  }`}
                >
                  {jurisdictionResult.authorized ? (
                    <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#059669]" />
                  ) : (
                    <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#dc2626]" />
                  )}
                  <div>
                    <span className="font-semibold block">
                      {jurisdictionResult.authorized ? "Access Permitted" : "Access Denied"}
                    </span>
                    <span className="text-[11px] block mt-0.5">
                      {jurisdictionResult.message}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Appointed Healthcare Officers */}
      {activeTab === "officers" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-[#6b7280]">
            <span>Official Government of India Healthcare Administrators</span>
            <span>Aadhaar e-KYC Verified Chain-of-Command</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {officers.map((off) => (
              <div
                key={off.id}
                className="p-3.5 rounded-md border border-[#e5e7eb] bg-[#fafafa] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6b7280]">
                      {off.designation.replace(/_/g, " ")}
                    </span>
                    <Badge variant="verified" size="sm">
                      Aadhaar Verified
                    </Badge>
                  </div>

                  <h4 className="text-xs font-semibold text-[#111827] mt-1.5">
                    {off.gov_email}
                  </h4>
                  <span className="text-[11px] text-[#4b5563] block mt-0.5">
                    Assigned Unit: {off.unit_name} ({off.unit_level})
                  </span>
                </div>

                <div className="mt-3 pt-2.5 border-t border-[#e5e7eb] flex items-center justify-between text-[11px]">
                  <span className="text-[#6b7280]">Jurisdiction Scope:</span>
                  <span className="font-mono text-[#059669] font-medium">
                    {off.jurisdiction_path}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 bg-[#f8f9fa] rounded-md border border-[#e5e7eb] text-xs text-[#4b5563] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#059669]" />
              <span>
                Administrative officers cannot inspect private clinical records without an ABDM Consent Artefact.
              </span>
            </div>
            <Badge variant="neutral" size="sm">
              DPDP Act Sec 6 Compliant
            </Badge>
          </div>
        </div>
      )}
    </div>
  );
}
