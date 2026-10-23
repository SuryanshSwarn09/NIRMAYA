"use client";

import React, { useState, useMemo } from "react";
import { Badge, Button } from "@/components/ui";
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ReferenceLine, 
  CartesianGrid 
} from "recharts";
import { VitalsTimeSeriesPoint, evaluateBloodPressure, getVitalBadgeConfig } from "@/lib/vitals";
import { Activity, Heart, ArrowUpRight, ArrowDownRight, Info } from "lucide-react";

export interface BloodPressureChartProps {
  data: VitalsTimeSeriesPoint[];
  className?: string;
  onOpenLogModal?: () => void;
}

export function BloodPressureChart({
  data,
  className = "",
  onOpenLogModal,
}: BloodPressureChartProps) {
  const [timeRange, setTimeRange] = useState<"7D" | "30D" | "90D" | "All">("30D");

  // Filter data based on selected time range
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Ensure chronological order
    const sorted = [...data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    
    if (timeRange === "All") return sorted;
    
    const now = new Date();
    const days = timeRange === "7D" ? 7 : timeRange === "30D" ? 30 : 90;
    const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    
    const filtered = sorted.filter((d) => new Date(d.timestamp) >= cutoff);
    return filtered.length > 0 ? filtered : sorted.slice(-Math.min(sorted.length, days));
  }, [data, timeRange]);

  // Compute statistics
  const stats = useMemo(() => {
    if (filteredData.length === 0) {
      return { latest: null, avgSys: 0, avgDia: 0, maxSys: 0, minSys: 0 };
    }
    const latest = filteredData[filteredData.length - 1];
    const sysVals = filteredData.map((d) => d.systolic || 0).filter((v) => v > 0);
    const diaVals = filteredData.map((d) => d.diastolic || 0).filter((v) => v > 0);

    const avgSys = Math.round(sysVals.reduce((a, b) => a + b, 0) / (sysVals.length || 1));
    const avgDia = Math.round(diaVals.reduce((a, b) => a + b, 0) / (diaVals.length || 1));
    const maxSys = Math.max(...sysVals);
    const minSys = Math.min(...sysVals);

    return { latest, avgSys, avgDia, maxSys, minSys };
  }, [filteredData]);

  const latestEval = stats.latest && stats.latest.systolic && stats.latest.diastolic
    ? evaluateBloodPressure(stats.latest.systolic, stats.latest.diastolic)
    : null;

  return (
    <div className={`p-5 rounded-[16px] bg-white border border-[#e5e7eb] shadow-xs space-y-5 ${className}`}>
      
      {/* 1. Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#f3f4f6]">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-[#f8f9fa] border border-[#e5e7eb] flex items-center justify-center">
              <Activity className="h-4 w-4 text-[#111111]" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#111111] tracking-tight">
                Blood Pressure Telemetry
              </h3>
              <p className="text-[11px] text-[#6b7280]">
                LOINC 85354-9 • Dual Systolic & Diastolic Area Trajectory
              </p>
            </div>
          </div>
        </div>

        {/* Time-Range Selector Pills */}
        <div className="flex items-center gap-1 bg-[#f3f4f6] p-1 rounded-[8px] border border-[#e5e7eb] self-start sm:self-auto">
          {(["7D", "30D", "90D", "All"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setTimeRange(r)}
              className={`px-2.5 py-1 rounded-[6px] text-xs font-semibold transition-all ${
                timeRange === r
                  ? "bg-white text-[#111111] shadow-xs"
                  : "text-[#6b7280] hover:text-[#111111]"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Key Metrics Overview Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Latest Reading
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#111111] tracking-tight">
              {stats.latest ? `${stats.latest.systolic} / ${stats.latest.diastolic}` : "N/A"}
            </span>
            <span className="text-[10px] text-[#6b7280]">mmHg</span>
          </div>
          {latestEval && (
            <Badge 
              variant={latestEval.category === "critical" ? "critical" : latestEval.category === "warning" ? "warning" : "emerald"}
              size="sm"
              className="mt-1"
            >
              {latestEval.label}
            </Badge>
          )}
        </div>

        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Period Average
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#111111] tracking-tight">
              {stats.avgSys} / {stats.avgDia}
            </span>
            <span className="text-[10px] text-[#6b7280]">mmHg</span>
          </div>
          <span className="text-[10px] text-[#6b7280] block mt-1">
            Mean Arterial Baseline
          </span>
        </div>

        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Systolic Peak
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#b91c1c] tracking-tight">
              {stats.maxSys}
            </span>
            <span className="text-[10px] text-[#6b7280]">mmHg</span>
          </div>
          <span className="text-[10px] text-[#6b7280] block mt-1 flex items-center gap-0.5">
            <ArrowUpRight className="h-3 w-3 text-[#ef4444]" /> Max Excursion
          </span>
        </div>

        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Systolic Nadir
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#059669] tracking-tight">
              {stats.minSys}
            </span>
            <span className="text-[10px] text-[#6b7280]">mmHg</span>
          </div>
          <span className="text-[10px] text-[#6b7280] block mt-1 flex items-center gap-0.5">
            <ArrowDownRight className="h-3 w-3 text-[#10b981]" /> Lowest Reading
          </span>
        </div>
      </div>

      {/* 3. Recharts Dual Area/Line Chart */}
      <div className="w-full h-[260px] pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={filteredData}
            margin={{ top: 10, right: 10, left: -15, bottom: 0 }}
          >
            <defs>
              <linearGradient id="systolicGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#111111" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#111111" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="diastolicGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis 
              dataKey="dateLabel" 
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />
            <YAxis 
              domain={[50, 180]} 
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />

            {/* Clinical Threshold Reference Lines */}
            <ReferenceLine 
              y={140} 
              stroke="#ef4444" 
              strokeDasharray="4 4" 
              label={{ value: "Stage 2 (140)", position: "insideTopRight", fill: "#ef4444", fontSize: 10 }}
            />
            <ReferenceLine 
              y={120} 
              stroke="#10b981" 
              strokeDasharray="4 4" 
              label={{ value: "Normal (120)", position: "insideBottomRight", fill: "#10b981", fontSize: 10 }}
            />
            <ReferenceLine 
              y={80} 
              stroke="#059669" 
              strokeDasharray="2 2" 
              label={{ value: "Diastolic Normal (80)", position: "insideBottomRight", fill: "#059669", fontSize: 9 }}
            />

            {/* Custom Tooltip */}
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload as VitalsTimeSeriesPoint;
                  const evalResult = p.systolic && p.diastolic ? evaluateBloodPressure(p.systolic, p.diastolic) : null;
                  return (
                    <div className="p-3 bg-white border border-[#e5e7eb] rounded-[10px] shadow-lg text-xs space-y-1.5">
                      <div className="font-bold text-[#111111]">{p.fullDateTime}</div>
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[#111111]" />
                        <span className="text-[#6b7280]">Systolic:</span>
                        <strong className="text-[#111111] font-mono">{p.systolic} mmHg</strong>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[#3b82f6]" />
                        <span className="text-[#6b7280]">Diastolic:</span>
                        <strong className="text-[#3b82f6] font-mono">{p.diastolic} mmHg</strong>
                      </div>
                      {evalResult && (
                        <div className="pt-1 border-t border-[#f3f4f6]">
                          <Badge 
                            variant={evalResult.category === "critical" ? "critical" : evalResult.category === "warning" ? "warning" : "emerald"}
                            size="sm"
                          >
                            {evalResult.label}
                          </Badge>
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />

            <Area
              type="monotone"
              dataKey="systolic"
              stroke="#111111"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#systolicGradient)"
              activeDot={{ r: 5, fill: "#111111", stroke: "#ffffff", strokeWidth: 2 }}
            />

            <Area
              type="monotone"
              dataKey="diastolic"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#diastolicGradient)"
              activeDot={{ r: 4, fill: "#3b82f6", stroke: "#ffffff", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 4. Clinical Legend & Guideline Note */}
      <div className="pt-2 border-t border-[#f3f4f6] flex flex-wrap items-center justify-between gap-2 text-xs text-[#6b7280]">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#111111]" />
            <span className="font-medium text-[#111111]">Systolic (mmHg)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#3b82f6]" />
            <span className="font-medium text-[#3b82f6]">Diastolic (mmHg)</span>
          </div>
        </div>

        {onOpenLogModal && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onOpenLogModal}
            className="text-xs"
          >
            + Log New BP Reading
          </Button>
        )}
      </div>

    </div>
  );
}
