"use client";

import React, { useState, useMemo } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { ClinicalCondition, ConditionSeverity, ClinicalStatus } from "@/lib/api";
import { PatientConditionCard } from "./PatientConditionCard";
import { PatientConditionUpdateModal } from "./PatientConditionUpdateModal";
import { 
  AlertCircle, 
  Search, 
  Filter, 
  Activity, 
  Sparkles, 
  CheckCircle2, 
  ShieldCheck, 
  Clock, 
  RefreshCw,
  FolderHeart,
  Plus
} from "lucide-react";

export interface PatientProblemsTabProps {
  conditions: ClinicalCondition[];
  loading?: boolean;
  onRefresh?: () => void;
  onViewFhir?: (condition: ClinicalCondition) => void;
  onConditionUpdated?: (
    conditionId: string, 
    updateData: {
      severity: ConditionSeverity;
      trend: "improved" | "stable" | "worsened";
      patientNote: string;
      flagForReview: boolean;
    }
  ) => Promise<void> | void;
}

export function PatientProblemsTab({
  conditions,
  loading = false,
  onRefresh,
  onViewFhir,
  onConditionUpdated,
}: PatientProblemsTabProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "chronic" | "resolved">("all");
  const [severityFilter, setSeverityFilter] = useState<"all" | "severe" | "moderate" | "mild">("all");
  const [selectedConditionForUpdate, setSelectedConditionForUpdate] = useState<ClinicalCondition | null>(null);

  // Compute summary metrics
  const activeCount = useMemo(() => {
    return conditions.filter((c) => c.clinical_status === "active").length;
  }, [conditions]);

  const chronicCount = useMemo(() => {
    return conditions.filter((c) => c.category === "chronic-condition").length;
  }, [conditions]);

  const resolvedCount = useMemo(() => {
    return conditions.filter((c) => c.clinical_status === "resolved").length;
  }, [conditions]);

  // Filtered conditions list
  const filteredConditions = useMemo(() => {
    return conditions.filter((c) => {
      // Search matching
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesName = c.code_display.toLowerCase().includes(q);
        const matchesCode = c.code_value.toLowerCase().includes(q);
        const matchesNote = c.note ? c.note.toLowerCase().includes(q) : false;
        if (!matchesName && !matchesCode && !matchesNote) return false;
      }

      // Status matching
      if (statusFilter === "active" && c.clinical_status !== "active") return false;
      if (statusFilter === "resolved" && c.clinical_status !== "resolved") return false;
      if (statusFilter === "chronic" && c.category !== "chronic-condition") return false;

      // Severity matching
      if (severityFilter !== "all" && c.severity !== severityFilter) return false;

      return true;
    });
  }, [conditions, searchQuery, statusFilter, severityFilter]);

  const handleOpenUpdateModal = (condition: ClinicalCondition) => {
    setSelectedConditionForUpdate(condition);
  };

  const handleCloseUpdateModal = () => {
    setSelectedConditionForUpdate(null);
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      
      {/* 1. Summary Health Metrics Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-[12px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
          <span className="text-[11px] uppercase font-bold tracking-wider text-[#6b7280] block">
            Active Diagnoses
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#111111]">{activeCount}</span>
            <Badge variant="emerald" size="sm">Under Management</Badge>
          </div>
        </div>

        <div className="p-4 rounded-[12px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
          <span className="text-[11px] uppercase font-bold tracking-wider text-[#6b7280] block">
            Chronic Conditions
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#d97706]">{chronicCount}</span>
            <Badge variant="warning" size="sm">Longitudinal</Badge>
          </div>
        </div>

        <div className="p-4 rounded-[12px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
          <span className="text-[11px] uppercase font-bold tracking-wider text-[#6b7280] block">
            Resolved / Remission
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#059669]">{resolvedCount}</span>
            <Badge variant="verified" size="sm">Clinically Clear</Badge>
          </div>
        </div>

        <div className="p-4 rounded-[12px] bg-[#f8f9fa] border border-[#e5e7eb] space-y-1">
          <span className="text-[11px] uppercase font-bold tracking-wider text-[#6b7280] block">
            Standard Ontology
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-bold text-[#111111]">SNOMED-CT</span>
            <Badge variant="fhir" size="sm">HL7 FHIR R4</Badge>
          </div>
        </div>
      </div>

      {/* 2. Interactive Search & Filter Controls */}
      <div className="p-4 bg-white rounded-[14px] border border-[#e5e7eb] shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          
          {/* Search bar */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9ca3af]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search diagnoses by name, SNOMED or ICD code..."
              className="w-full pl-9 pr-4 py-2 rounded-[8px] bg-[#f8f9fa] border border-[#e5e7eb] text-xs text-[#111111] placeholder:text-[#9ca3af] focus:outline-hidden focus:ring-2 focus:ring-[#111111]"
            />
          </div>

          {/* Action Button: Refresh */}
          {onRefresh && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
              className="text-xs flex items-center gap-1.5 shrink-0"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Records</span>
            </Button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[#f3f4f6]">
          {/* Status Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto py-1">
            <span className="text-xs font-semibold text-[#6b7280] mr-1">Status:</span>
            {[
              { id: "all", label: "All Problems" },
              { id: "active", label: "Active" },
              { id: "chronic", label: "Chronic Illness" },
              { id: "resolved", label: "Resolved" },
            ].map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setStatusFilter(f.id as any)}
                className={`px-3 py-1 rounded-[6px] text-xs font-semibold transition-all ${
                  statusFilter === f.id
                    ? "bg-[#111111] text-white"
                    : "bg-[#f3f4f6] text-[#4b5563] hover:text-[#111111]"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Severity Dropdown */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-[#6b7280] font-semibold">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as any)}
              className="px-2.5 py-1 rounded-[6px] bg-[#f3f4f6] border border-[#e5e7eb] text-xs font-medium text-[#111111] focus:outline-hidden"
            >
              <option value="all">All Severities</option>
              <option value="severe">Severe</option>
              <option value="moderate">Moderate</option>
              <option value="mild">Mild</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. Problem List Grid */}
      {filteredConditions.length > 0 ? (
        <div className="space-y-4">
          {filteredConditions.map((cond) => (
            <PatientConditionCard
              key={cond.id}
              condition={cond}
              onViewFhir={onViewFhir}
              onOpenUpdateModal={handleOpenUpdateModal}
            />
          ))}
        </div>
      ) : (
        <div className="p-8 rounded-[14px] bg-white border border-[#e5e7eb] text-center space-y-3">
          <div className="h-12 w-12 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] flex items-center justify-center mx-auto text-[#9ca3af]">
            <FolderHeart className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-[#111111]">No conditions match your filters</h4>
            <p className="text-xs text-[#6b7280] mt-1">
              {searchQuery.trim()
                ? `No diagnoses found matching "${searchQuery}". Clear your search query to see all records.`
                : "No clinical conditions recorded in this classification."}
            </p>
          </div>
          {(searchQuery || statusFilter !== "all" || severityFilter !== "all") && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("all");
                setSeverityFilter("all");
              }}
              className="text-xs"
            >
              Reset All Filters
            </Button>
          )}
        </div>
      )}

      {/* 4. Condition Symptom Update Modal */}
      <PatientConditionUpdateModal
        isOpen={Boolean(selectedConditionForUpdate)}
        onClose={handleCloseUpdateModal}
        condition={selectedConditionForUpdate}
        onSubmitUpdate={async (condId, updateData) => {
          if (onConditionUpdated) {
            await onConditionUpdated(condId, updateData);
          }
        }}
      />

    </div>
  );
}
