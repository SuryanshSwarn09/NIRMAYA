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
import { 
  VitalsTimeSeriesPoint, 
  evaluateHeartRate, 
  evaluateSpo2, 
  evaluateBmi, 
  evaluateTemperature 
} from "@/lib/vitals";
import { Heart, Activity, Wind, Scale, Thermometer, ArrowUpRight, ArrowDownRight } from "lucide-react";

export type MetricType = "heartRate" | "spo2" | "weight" | "temperature";

export interface VitalsMetricChartProps {
  data: VitalsTimeSeriesPoint[];
  initialMetric?: MetricType;
  className?: string;
  onOpenLogModal?: () => void;
}

interface MetricConfig {
  id: MetricType;
  title: string;
  loinc: string;
  unit: string;
  dataKey: keyof VitalsTimeSeriesPoint;
  strokeColor: string;
  gradientColor: string;
  yDomain: [number, number];
  referenceLines: Array<{ y: number; label: string; stroke: string }>;
  evaluator: (val: number) => { label: string; category: "normal" | "elevated" | "warning" | "critical" };
  icon: React.ElementType;
}

const METRIC_CONFIGS: Record<MetricType, MetricConfig> = {
  heartRate: {
    id: "heartRate",
    title: "Resting Heart Rate",
    loinc: "LOINC 8867-4",
    unit: "BPM",
    dataKey: "heartRate",
    strokeColor: "#e11d48",
    gradientColor: "#f43f5e",
    yDomain: [40, 140],
    referenceLines: [
      { y: 100, label: "Tachycardia (100)", stroke: "#ef4444" },
      { y: 60, label: "Normal Baseline (60)", stroke: "#10b981" },
    ],
    evaluator: (val) => evaluateHeartRate(val),
    icon: Heart,
  },
  spo2: {
    id: "spo2",
    title: "Blood Oxygen Saturation (SpO2)",
    loinc: "LOINC 2708-6",
    unit: "%",
    dataKey: "spo2",
    strokeColor: "#0284c7",
    gradientColor: "#38bdf8",
    yDomain: [88, 100],
    referenceLines: [
      { y: 95, label: "Normal Threshold (95%)", stroke: "#10b981" },
      { y: 90, label: "Hypoxia Alert (90%)", stroke: "#ef4444" },
    ],
    evaluator: (val) => evaluateSpo2(val),
    icon: Wind,
  },
  weight: {
    id: "weight",
    title: "Body Weight & Mass Index",
    loinc: "LOINC 29463-7",
    unit: "kg",
    dataKey: "weight",
    strokeColor: "#059669",
    gradientColor: "#34d399",
    yDomain: [50, 100],
    referenceLines: [
      { y: 72, label: "Target Weight (72 kg)", stroke: "#10b981" },
    ],
    evaluator: (val) => evaluateBmi(Number((val / (1.75 * 1.75)).toFixed(1))),
    icon: Scale,
  },
  temperature: {
    id: "temperature",
    title: "Body Temperature",
    loinc: "LOINC 8310-5",
    unit: "°F",
    dataKey: "temperature",
    strokeColor: "#d97706",
    gradientColor: "#fbbf24",
    yDomain: [96, 104],
    referenceLines: [
      { y: 100.4, label: "Fever Threshold (100.4°F)", stroke: "#ef4444" },
      { y: 98.6, label: "Normal (98.6°F)", stroke: "#10b981" },
    ],
    evaluator: (val) => evaluateTemperature(val),
    icon: Thermometer,
  },
};

export function VitalsMetricChart({
  data,
  initialMetric = "heartRate",
  className = "",
  onOpenLogModal,
}: VitalsMetricChartProps) {
  const [activeMetric, setActiveMetric] = useState<MetricType>(initialMetric);
  const [timeRange, setTimeRange] = useState<"7D" | "30D" | "90D" | "All">("30D");

  const config = METRIC_CONFIGS[activeMetric];
  const Icon = config.icon;

  // Filter chronologically
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    const sorted = [...data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    
    if (timeRange === "All") return sorted;
    const now = new Date();
    const days = timeRange === "7D" ? 7 : timeRange === "30D" ? 30 : 90;
    const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    
    const filtered = sorted.filter((d) => new Date(d.timestamp) >= cutoff);
    return filtered.length > 0 ? filtered : sorted.slice(-Math.min(sorted.length, days));
  }, [data, timeRange]);

  // Compute metric stats
  const stats = useMemo(() => {
    const values = filteredData
      .map((d) => d[config.dataKey] as number | undefined)
      .filter((v): v is number => typeof v === "number" && v > 0);

    if (values.length === 0) {
      return { latest: null, avg: 0, max: 0, min: 0 };
    }

    const latest = values[values.length - 1];
    const avg = Number((values.reduce((a, b) => a + b, 0) / values.length).toFixed(1));
    const max = Math.max(...values);
    const min = Math.min(...values);

    return { latest, avg, max, min };
  }, [filteredData, config.dataKey]);

  const latestEval = stats.latest ? config.evaluator(stats.latest) : null;

  return (
    <div className={`p-5 rounded-[16px] bg-white border border-[#e5e7eb] shadow-xs space-y-5 ${className}`}>
      
      {/* 1. Header: Metric Switcher Pills & Time Range */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#f3f4f6]">
        
        {/* Metric Selector Tabs */}
        <div className="flex flex-wrap items-center gap-1.5">
          {(["heartRate", "spo2", "weight", "temperature"] as MetricType[]).map((m) => {
            const mConfig = METRIC_CONFIGS[m];
            const MIcon = mConfig.icon;
            const isSelected = activeMetric === m;
            return (
              <button
                key={m}
                type="button"
                onClick={() => setActiveMetric(m)}
                className={`py-1.5 px-3 rounded-[8px] text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  isSelected
                    ? "bg-[#111111] text-white shadow-xs"
                    : "bg-[#f8f9fa] text-[#4b5563] hover:bg-[#f3f4f6] border border-[#e5e7eb]"
                }`}
              >
                <MIcon className={`h-3.5 w-3.5 ${isSelected ? "text-white" : "text-[#6b7280]"}`} />
                <span>{m === "heartRate" ? "Pulse" : m === "spo2" ? "SpO2" : m === "weight" ? "Weight / BMI" : "Temperature"}</span>
              </button>
            );
          })}
        </div>

        {/* Time-Range Selector */}
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

      {/* 2. Metric Title & Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Latest Reading
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#111111] tracking-tight">
              {stats.latest !== null ? stats.latest : "N/A"}
            </span>
            <span className="text-[10px] text-[#6b7280]">{config.unit}</span>
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
              {stats.avg}
            </span>
            <span className="text-[10px] text-[#6b7280]">{config.unit}</span>
          </div>
          <span className="text-[10px] text-[#6b7280] block mt-1">
            Mean Measurement
          </span>
        </div>

        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Peak Measurement
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#b91c1c] tracking-tight">
              {stats.max}
            </span>
            <span className="text-[10px] text-[#6b7280]">{config.unit}</span>
          </div>
          <span className="text-[10px] text-[#6b7280] block mt-1 flex items-center gap-0.5">
            <ArrowUpRight className="h-3 w-3 text-[#ef4444]" /> High Excursion
          </span>
        </div>

        <div className="p-3 bg-[#f8f9fa] rounded-[10px] border border-[#e5e7eb] space-y-0.5">
          <span className="text-[10px] uppercase font-bold text-[#6b7280] tracking-wider block">
            Lowest Reading
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-bold text-[#059669] tracking-tight">
              {stats.min}
            </span>
            <span className="text-[10px] text-[#6b7280]">{config.unit}</span>
          </div>
          <span className="text-[10px] text-[#6b7280] block mt-1 flex items-center gap-0.5">
            <ArrowDownRight className="h-3 w-3 text-[#10b981]" /> Baseline Nadir
          </span>
        </div>
      </div>

      {/* 3. Recharts Area Chart */}
      <div className="w-full h-[240px] pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={filteredData}
            margin={{ top: 10, right: 10, left: -15, bottom: 0 }}
          >
            <defs>
              <linearGradient id={`${activeMetric}Gradient`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={config.gradientColor} stopOpacity={0.25} />
                <stop offset="95%" stopColor={config.gradientColor} stopOpacity={0.0} />
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
              domain={config.yDomain} 
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />

            {/* Reference Threshold Lines */}
            {config.referenceLines.map((ref, idx) => (
              <ReferenceLine
                key={idx}
                y={ref.y}
                stroke={ref.stroke}
                strokeDasharray="4 4"
                label={{ value: ref.label, position: "insideTopRight", fill: ref.stroke, fontSize: 10 }}
              />
            ))}

            {/* Tooltip */}
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload as VitalsTimeSeriesPoint;
                  const val = p[config.dataKey] as number | undefined;
                  const evalRes = val ? config.evaluator(val) : null;
                  return (
                    <div className="p-3 bg-white border border-[#e5e7eb] rounded-[10px] shadow-lg text-xs space-y-1.5">
                      <div className="font-bold text-[#111111]">{p.fullDateTime}</div>
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: config.strokeColor }} />
                        <span className="text-[#6b7280]">{config.title}:</span>
                        <strong className="text-[#111111] font-mono">{val} {config.unit}</strong>
                      </div>
                      {evalRes && (
                        <div className="pt-1 border-t border-[#f3f4f6]">
                          <Badge 
                            variant={evalRes.category === "critical" ? "critical" : evalRes.category === "warning" ? "warning" : "emerald"}
                            size="sm"
                          >
                            {evalRes.label}
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
              dataKey={config.dataKey as string}
              stroke={config.strokeColor}
              strokeWidth={2.5}
              fillOpacity={1}
              fill={`url(#${activeMetric}Gradient)`}
              activeDot={{ r: 5, fill: config.strokeColor, stroke: "#ffffff", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 4. Footer & Quick Logging Action */}
      <div className="pt-2 border-t border-[#f3f4f6] flex flex-wrap items-center justify-between gap-2 text-xs text-[#6b7280]">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" style={{ color: config.strokeColor }} />
          <span>{config.title} • {config.loinc}</span>
        </div>

        {onOpenLogModal && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onOpenLogModal}
            className="text-xs"
          >
            + Log New Observation
          </Button>
        )}
      </div>

    </div>
  );
}
