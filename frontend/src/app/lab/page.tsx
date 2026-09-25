"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button, Badge, Card, CardTitle, CardDescription } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import {
  TestTube2,
  FileCheck,
  ShieldCheck,
  UploadCloud,
  FileText,
  CheckCircle2,
  Activity,
  Code,
  QrCode,
  AlertCircle,
  Hash,
  Download,
  Building2,
} from "lucide-react";

export default function DiagnosticLabPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 bg-white">
      
      {/* Top Facility Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#e5e7eb]">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-[#111111] text-white flex items-center justify-center font-bold text-base shrink-0">
            <TestTube2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111111]">
                Apollo Diagnostics Central
              </h1>
              <Badge variant="verified">NABL Accredited</Badge>
            </div>
            <p className="text-sm text-[#6b7280]">
              Clinical Pathology & Molecular Diagnostics • HFR:{" "}
              <span className="font-mono text-[#111111]">HFR-DEL-91024</span> • ISO 15189:2022
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="emerald" size="sm">Gateway Online</Badge>
          <Link href="/patient">
            <Button variant="secondary" size="sm">
              Patient Vault
            </Button>
          </Link>
          <Link href="/doctor">
            <Button variant="secondary" size="sm">
              Doctor EMR
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-12">
          <p className="text-sm text-[#6b7280]">
            Diagnostic Gateway initialized. NABL certification active.
          </p>
        </div>
      </div>
    </div>
  );
}
