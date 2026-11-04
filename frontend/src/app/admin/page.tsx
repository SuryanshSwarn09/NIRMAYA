"use client";

import React from "react";
import Link from "next/link";
import { 
  ShieldCheck, 
  Server, 
  Terminal, 
  Activity, 
  Layers, 
  Lock, 
  ArrowLeft,
  Database
} from "lucide-react";
import { Badge, Button } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import {
  AbdmGatewayStatusCard,
  AuditLedgerVerificationCard,
  SecurityScanReportCard,
  AsvsComplianceShieldCard,
  AdministrativeHierarchyViewerCard,
  ChainOfCommandDelegationCard,
  TerritorialCommandCenterCard,
  ContainerRuntimeCard,
  FrontendContainerCard,
  DockerOrchestrationCard,
  EdgeNodeSyncCard,
  LegacyHisFederationCard,
  AcademicMonographViewerCard,
  PerformanceBenchmarkCard,
  InteractiveDemoSandboxCard,
  SystemAuditLicenseCard,
  ProductionReleaseCard,
} from "@/components/clinical";

export default function AdminConsolePage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-[#fafafa] pb-16">
      {/* 1. Administrator Header Strip */}
      <header className="border-b border-[#e5e7eb] bg-white sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-1.5 rounded-lg border border-[#e5e7eb] hover:bg-[#f9fafb] text-[#6b7280] hover:text-[#111111] transition-colors"
              title="Return to Home"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-[#111111] tracking-tight">
                  National Administrative & DevOps Command Center
                </h1>
                <Badge variant="critical" size="sm">Super Admin</Badge>
                <Badge variant="verified" size="sm">CIS Hardened</Badge>
              </div>
              <p className="text-xs text-[#6b7280]">
                Infrastructure telemetry, Docker topology, LGD hierarchy, security audits & monograph repository
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden md:flex flex-col text-right">
              <span className="text-xs font-semibold text-[#111111]">
                {user?.fullName || "System Administrator"}
              </span>
              <span className="text-[10px] text-[#6b7280] font-mono">
                {user?.email || "admin@nirmaya.health"}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Main Administrative Console Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Top Metric Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-[#e5e7eb] bg-white">
            <div className="text-xs font-medium text-[#6b7280] flex items-center gap-1.5">
              <Server className="h-3.5 w-3.5 text-[#111111]" />
              Topology
            </div>
            <div className="mt-1.5 text-lg font-bold text-[#111111]">5 Microservices</div>
            <div className="text-[11px] text-[#059669]">Docker Compose Active</div>
          </div>

          <div className="p-4 rounded-xl border border-[#e5e7eb] bg-white">
            <div className="text-xs font-medium text-[#6b7280] flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-[#111111]" />
              OWASP ASVS
            </div>
            <div className="mt-1.5 text-lg font-bold text-[#111111]">Level 2 Certified</div>
            <div className="text-[11px] text-[#059669]">18/18 Controls Green</div>
          </div>

          <div className="p-4 rounded-xl border border-[#e5e7eb] bg-white">
            <div className="text-xs font-medium text-[#6b7280] flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-[#111111]" />
              Gateway Shield
            </div>
            <div className="mt-1.5 text-lg font-bold text-[#111111]">50,000 req/s</div>
            <div className="text-[11px] text-[#059669]">Anti-Brute Force Active</div>
          </div>

          <div className="p-4 rounded-xl border border-[#e5e7eb] bg-white">
            <div className="text-xs font-medium text-[#6b7280] flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5 text-[#111111]" />
              Database Engine
            </div>
            <div className="mt-1.5 text-lg font-bold text-[#111111]">PostgreSQL 16</div>
            <div className="text-[11px] text-[#059669]">ltree + GiST Indexed</div>
          </div>
        </div>

        {/* 3. Production Release & Monograph Showcase */}
        <ProductionReleaseCard />
        <AcademicMonographViewerCard />

        {/* 4. Security, Compliance & Audit Trail */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SecurityScanReportCard />
          <AsvsComplianceShieldCard />
        </div>

        {/* 5. Cryptographic Ledger & ABDM Gateway */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AuditLedgerVerificationCard />
          <AbdmGatewayStatusCard />
        </div>

        {/* 6. Administrative Hierarchy & Command Center */}
        <AdministrativeHierarchyViewerCard />
        <ChainOfCommandDelegationCard />
        <TerritorialCommandCenterCard />

        {/* 7. Container Runtime & Infrastructure Telemetry */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ContainerRuntimeCard />
          <FrontendContainerCard />
        </div>

        {/* 8. Docker Topology & Edge Federation */}
        <DockerOrchestrationCard />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EdgeNodeSyncCard />
          <LegacyHisFederationCard />
        </div>

        {/* 9. Performance Benchmarks & License Compliance */}
        <PerformanceBenchmarkCard />
        <SystemAuditLicenseCard />
        <InteractiveDemoSandboxCard />
      </main>
    </div>
  );
}

