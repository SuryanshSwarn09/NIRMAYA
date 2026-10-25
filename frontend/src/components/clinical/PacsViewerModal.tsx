"use client";

import React, { useState, useEffect, useRef } from "react";
import { Badge, Button } from "@/components/ui";
import {
  X,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Sliders,
  Maximize2,
  Minimize2,
  ChevronLeft,
  ChevronRight,
  FileCode,
  Download,
  Activity,
  Layers,
  Ruler,
  Info,
  CheckCircle2,
  FileText,
  Scan,
} from "lucide-react";

export type WindowPreset = "default" | "lung" | "bone" | "soft-tissue" | "inverted";

export interface DicomSlice {
  sliceNumber: number;
  instanceUid: string;
  graphicType: "chest-xray" | "ecg-rhythm" | "head-ct" | "echo-doppler";
  caption: string;
}

export interface DicomSeries {
  seriesInstanceUid: string;
  seriesNumber: number;
  modality: "CR" | "DX" | "CT" | "ECG" | "US";
  seriesDescription: string;
  bodyPartExamined: string;
  slices: DicomSlice[];
}

export interface DicomStudy {
  studyInstanceUid: string;
  accessionNumber: string;
  patientId: string;
  patientName: string;
  patientAgeGender?: string;
  studyDate: string;
  studyTime: string;
  modality: string;
  studyDescription: string;
  referringPhysician: string;
  institutionName: string;
  series: DicomSeries[];
  radiologistReport?: {
    radiologistName: string;
    radiologistReg: string;
    findings: string;
    impression: string;
    status: "preliminary" | "final";
  };
}

export const SAMPLE_STUDIES: Record<string, DicomStudy> = {
  "chest-xray": {
    studyInstanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219001",
    accessionNumber: "ACC-2026-XRAY-4491",
    patientId: "pat-arun-patel",
    patientName: "Arun Patel",
    patientAgeGender: "48Y / M",
    studyDate: "2026-10-24",
    studyTime: "09:30:15 IST",
    modality: "CR",
    studyDescription: "Chest X-Ray 2 Views (PA & Lateral)",
    referringPhysician: "Dr. Ananya Sharma (MCI-2015-84920)",
    institutionName: "NIRMAYA Apex Imaging Center, Bengaluru",
    series: [
      {
        seriesInstanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219001.1",
        seriesNumber: 1,
        modality: "CR",
        seriesDescription: "Posteroanterior (PA) Erect View",
        bodyPartExamined: "CHEST",
        slices: [
          {
            sliceNumber: 1,
            instanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219001.1.1",
            graphicType: "chest-xray",
            caption: "Chest PA View: Trachea midline, clear costophrenic angles, CTR 0.44",
          },
        ],
      },
    ],
    radiologistReport: {
      radiologistName: "Dr. Vikram Sethi, MD Radiodiagnosis",
      radiologistReg: "KMC-41982",
      findings:
        "The cardiac silhouette is within normal limits for size (Cardiothoracic ratio = 0.44). The mediastinal contours, aortic arch, and pulmonary hilar structures are unremarkable. Both lung fields demonstrate clear bronchovascular markings with no evidence of focal consolidation, parenchymal mass, or pleural effusion. Costophrenic and cardiophrenic angles are acute and well defined. Osseous thoracic cage and bilateral clavicles are intact.",
      impression:
        "Normal posteroanterior chest radiograph. No acute cardiopulmonary pathology or active infiltrative process.",
      status: "final",
    },
  },
  "ecg-rhythm": {
    studyInstanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219002",
    accessionNumber: "ACC-2026-ECG-1104",
    patientId: "pat-arun-patel",
    patientName: "Arun Patel",
    patientAgeGender: "48Y / M",
    studyDate: "2026-10-24",
    studyTime: "09:45:00 IST",
    modality: "ECG",
    studyDescription: "12-Lead Electrocardiogram Diagnostic Strip",
    referringPhysician: "Dr. Ananya Sharma (MCI-2015-84920)",
    institutionName: "NIRMAYA Apex Imaging Center, Bengaluru",
    series: [
      {
        seriesInstanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219002.1",
        seriesNumber: 1,
        modality: "ECG",
        seriesDescription: "Standard 12-Lead Rhythm Strip (25mm/s, 10mm/mV)",
        bodyPartExamined: "HEART",
        slices: [
          {
            sliceNumber: 1,
            instanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219002.1.1",
            graphicType: "ecg-rhythm",
            caption: "Normal Sinus Rhythm: HR 72 bpm, PR 156 ms, QRS 84 ms, QTc 412 ms",
          },
        ],
      },
    ],
    radiologistReport: {
      radiologistName: "Dr. Rajesh K. Nair, DM Cardiology",
      radiologistReg: "KMC-33108",
      findings:
        "Normal sinus rhythm at 72 beats per minute. Normal P-wave morphology and PR interval of 156 milliseconds. Normal QRS axis and duration (84 ms) without intraventricular conduction delay. No pathological Q waves, ST segment elevation, or T wave inversions across precordial (V1-V6) or limb leads (I, II, III, aVR, aVL, aVF). Corrected QT interval (Bazett formula) measured at 412 ms.",
      impression:
        "Normal 12-lead electrocardiogram. Regular sinus rhythm without evidence of myocardial ischemia or chamber hypertrophy.",
      status: "final",
    },
  },
  "head-ct": {
    studyInstanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219003",
    accessionNumber: "ACC-2026-CT-8832",
    patientId: "pat-arun-patel",
    patientName: "Arun Patel",
    patientAgeGender: "48Y / M",
    studyDate: "2026-10-23",
    studyTime: "14:15:20 IST",
    modality: "CT",
    studyDescription: "Computed Tomography (CT) Head & Brain Axial",
    referringPhysician: "Dr. Ananya Sharma (MCI-2015-84920)",
    institutionName: "NIRMAYA Apex Imaging Center, Bengaluru",
    series: [
      {
        seriesInstanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219003.1",
        seriesNumber: 1,
        modality: "CT",
        seriesDescription: "Axial Brain Non-Contrast Thin Slices (3.0mm)",
        bodyPartExamined: "HEAD",
        slices: [
          {
            sliceNumber: 1,
            instanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219003.1.1",
            graphicType: "head-ct",
            caption: "Axial Slice at Level of Lateral Ventricles & Basal Ganglia",
          },
          {
            sliceNumber: 2,
            instanceUid: "1.2.840.113619.2.55.3.604681313.731.1698219003.1.2",
            graphicType: "head-ct",
            caption: "Axial Slice at Centrum Semiovale & Superior Frontal Convexity",
          },
        ],
      },
    ],
    radiologistReport: {
      radiologistName: "Dr. Vikram Sethi, MD Radiodiagnosis",
      radiologistReg: "KMC-41982",
      findings:
        "Non-contrast axial CT images through the neurocranium show standard attenuation values throughout the cerebral hemispheres, basal ganglia, and cerebellum. Ventricular system, basal cisterns, and cortical sulci are symmetrical and age appropriate. No evidence of acute intracranial hemorrhage, mass effect, or midline shift. Gray-white differentiation is preserved.",
      impression:
        "Normal non-contrast head CT study. No acute intracranial hemorrhage or territorial infarction.",
      status: "final",
    },
  },
};

interface PacsViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  studyKey?: string;
  initialStudy?: DicomStudy;
}

export const PacsViewerModal: React.FC<PacsViewerModalProps> = ({
  isOpen,
  onClose,
  studyKey = "chest-xray",
  initialStudy,
}) => {
  const activeStudy: DicomStudy =
    initialStudy || SAMPLE_STUDIES[studyKey] || SAMPLE_STUDIES["chest-xray"];

  const [activeSeriesIndex, setActiveSeriesIndex] = useState(0);
  const [activeSliceIndex, setActiveSliceIndex] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [windowPreset, setWindowPreset] = useState<WindowPreset>("default");
  const [showMetadataDrawer, setShowMetadataDrawer] = useState(false);
  const [showReportDrawer, setShowReportDrawer] = useState(false);
  const [isCaliperActive, setIsCaliperActive] = useState(false);
  const [caliperPoints, setCaliperPoints] = useState<
    { x: number; y: number }[]
  >([]);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Reset view controls on study or series change
    setZoomLevel(1);
    setRotation(0);
    setWindowPreset("default");
    setIsCaliperActive(false);
    setCaliperPoints([]);
  }, [studyKey, activeSeriesIndex]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === "Escape") {
        if (showMetadataDrawer) setShowMetadataDrawer(false);
        else if (showReportDrawer) setShowReportDrawer(false);
        else onClose();
      } else if (e.key === "ArrowRight") {
        handleNextSlice();
      } else if (e.key === "ArrowLeft") {
        handlePrevSlice();
      } else if (e.key === "+" || e.key === "=") {
        handleZoomIn();
      } else if (e.key === "-") {
        handleZoomOut();
      } else if (e.key === "r" || e.key === "R") {
        handleRotate();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, showMetadataDrawer, showReportDrawer, activeSliceIndex]);

  if (!isOpen) return null;

  const currentSeries = activeStudy.series[activeSeriesIndex] || activeStudy.series[0];
  const currentSlice =
    currentSeries?.slices[activeSliceIndex] || currentSeries?.slices[0];
  const totalSlices = currentSeries?.slices?.length || 1;

  const handleZoomIn = () => setZoomLevel((z) => Math.min(3, +(z + 0.25).toFixed(2)));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(0.5, +(z - 0.25).toFixed(2)));
  const handleResetZoom = () => {
    setZoomLevel(1);
    setRotation(0);
    setWindowPreset("default");
    setCaliperPoints([]);
  };

  const handleRotate = () => setRotation((r) => (r + 90) % 360);

  const handlePrevSlice = () => {
    if (activeSliceIndex > 0) setActiveSliceIndex(activeSliceIndex - 1);
  };

  const handleNextSlice = () => {
    if (activeSliceIndex < totalSlices - 1) setActiveSliceIndex(activeSliceIndex + 1);
  };

  const handleViewportClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isCaliperActive) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(e.clientX - rect.left);
    const y = Math.round(e.clientY - rect.top);

    if (caliperPoints.length >= 2) {
      setCaliperPoints([{ x, y }]);
    } else {
      setCaliperPoints((prev) => [...prev, { x, y }]);
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // Contrast preset filter classes
  const getFilterClass = (preset: WindowPreset) => {
    switch (preset) {
      case "lung":
        return "contrast-150 brightness-110 hue-rotate-15";
      case "bone":
        return "contrast-200 brightness-95 saturate-0";
      case "soft-tissue":
        return "contrast-125 brightness-105";
      case "inverted":
        return "invert contrast-125";
      case "default":
      default:
        return "contrast-100 brightness-100";
    }
  };

  const calculateDistance = () => {
    if (caliperPoints.length < 2) return null;
    const p1 = caliperPoints[0];
    const p2 = caliperPoints[1];
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const pixels = Math.sqrt(dx * dx + dy * dy);
    // Estimated DICOM pixel pitch approximation (0.28 mm / px)
    const mm = (pixels * 0.28).toFixed(1);
    return { pixels: Math.round(pixels), mm };
  };

  const distanceInfo = calculateDistance();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        ref={containerRef}
        className="bg-[#0f1115] text-[#f3f4f6] rounded-[8px] w-full max-w-6xl h-[92vh] flex flex-col overflow-hidden border border-[#27272a] shadow-2xl"
      >
        {/* PACS Studio Header Bar */}
        <div className="bg-[#18181b] border-b border-[#27272a] px-4 py-2.5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Scan className="h-5 w-5 text-emerald-400" />
              <span className="font-semibold text-sm tracking-tight text-white font-mono">
                NIRMAYA PACS Studio
              </span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-xs text-[#a1a1aa] border-l border-[#27272a] pl-3">
              <span className="text-white font-medium">{activeStudy.patientName}</span>
              <span>•</span>
              <span className="font-mono">{activeStudy.patientId}</span>
              <span>•</span>
              <span>{activeStudy.patientAgeGender}</span>
              <span>•</span>
              <Badge variant="outline" size="sm" className="font-mono uppercase text-[#e4e4e7] border-[#3f3f46]">
                {activeStudy.modality}
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowReportDrawer(false);
                setShowMetadataDrawer(!showMetadataDrawer);
              }}
              className="text-xs bg-[#27272a] text-[#f4f4f5] border-[#3f3f46] hover:bg-[#3f3f46] flex items-center gap-1.5"
            >
              <FileCode className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">DICOM Tags</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowMetadataDrawer(false);
                setShowReportDrawer(!showReportDrawer);
              }}
              className="text-xs bg-[#27272a] text-[#f4f4f5] border-[#3f3f46] hover:bg-[#3f3f46] flex items-center gap-1.5"
            >
              <FileText className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Radiology Report</span>
            </Button>

            <button
              onClick={toggleFullscreen}
              className="p-1.5 text-[#a1a1aa] hover:text-white rounded-[6px] hover:bg-[#27272a] transition-colors"
              title="Toggle Fullscreen"
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-[#a1a1aa] hover:text-white rounded-[6px] hover:bg-[#27272a] transition-colors"
              title="Close PACS Viewer (Esc)"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Viewport Action Toolbar */}
        <div className="bg-[#141518] border-b border-[#27272a] px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0">
          {/* Left: Windowing Presets */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[#a1a1aa] text-[11px] font-medium uppercase tracking-wider mr-1">
              Window:
            </span>
            {(
              [
                { id: "default", label: "Native" },
                { id: "lung", label: "Lung" },
                { id: "bone", label: "Bone" },
                { id: "soft-tissue", label: "Soft Tissue" },
                { id: "inverted", label: "Inverted" },
              ] as const
            ).map((preset) => (
              <button
                key={preset.id}
                onClick={() => setWindowPreset(preset.id)}
                className={`px-2.5 py-1 rounded-[6px] font-medium transition-colors ${
                  windowPreset === preset.id
                    ? "bg-white text-[#111111]"
                    : "bg-[#27272a] text-[#d4d4d8] hover:bg-[#3f3f46]"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Center: Zoom / Rotate / Caliper Controls */}
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-[#27272a] rounded-[8px] p-0.5 border border-[#3f3f46]">
              <button
                onClick={handleZoomOut}
                className="p-1.5 text-[#d4d4d8] hover:text-white rounded-[6px] hover:bg-[#3f3f46]"
                title="Zoom Out (-)"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span className="px-2 font-mono text-[11px] text-[#f4f4f5] select-none">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-1.5 text-[#d4d4d8] hover:text-white rounded-[6px] hover:bg-[#3f3f46]"
                title="Zoom In (+)"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
            </div>

            <button
              onClick={handleRotate}
              className="p-1.5 bg-[#27272a] text-[#d4d4d8] hover:text-white border border-[#3f3f46] rounded-[8px] hover:bg-[#3f3f46] flex items-center gap-1 px-2.5"
              title="Rotate 90 degrees (R)"
            >
              <RotateCw className="h-3.5 w-3.5" />
              <span className="font-mono text-[11px]">{rotation}°</span>
            </button>

            <button
              onClick={() => {
                setIsCaliperActive(!isCaliperActive);
                setCaliperPoints([]);
              }}
              className={`p-1.5 border rounded-[8px] flex items-center gap-1.5 px-2.5 transition-colors ${
                isCaliperActive
                  ? "bg-emerald-950/80 border-emerald-500 text-emerald-300 font-semibold"
                  : "bg-[#27272a] border-[#3f3f46] text-[#d4d4d8] hover:bg-[#3f3f46]"
              }`}
              title="Toggle Digital Caliper Measurement"
            >
              <Ruler className="h-3.5 w-3.5" />
              <span>Caliper</span>
            </button>

            <button
              onClick={handleResetZoom}
              className="px-2 py-1 text-[11px] text-[#a1a1aa] hover:text-white hover:underline"
            >
              Reset
            </button>
          </div>

          {/* Right: Slice Stepper */}
          {totalSlices > 1 && (
            <div className="flex items-center gap-2">
              <button
                disabled={activeSliceIndex === 0}
                onClick={handlePrevSlice}
                className="p-1 text-[#d4d4d8] hover:text-white disabled:opacity-30 rounded-[6px] hover:bg-[#27272a]"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="font-mono text-xs text-[#a1a1aa]">
                Slice {activeSliceIndex + 1} of {totalSlices}
              </span>
              <button
                disabled={activeSliceIndex === totalSlices - 1}
                onClick={handleNextSlice}
                className="p-1 text-[#d4d4d8] hover:text-white disabled:opacity-30 rounded-[6px] hover:bg-[#27272a]"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Viewport Core Layout */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Main Visual Display Area */}
          <div
            onClick={handleViewportClick}
            className={`flex-1 flex items-center justify-center bg-[#07080a] relative overflow-hidden select-none ${
              isCaliperActive ? "cursor-crosshair" : "cursor-default"
            }`}
          >
            {/* Viewport HUD Overlays */}
            <div className="absolute top-3 left-3 z-10 pointer-events-none space-y-1 text-left font-mono text-[11px] text-[#a1a1aa] bg-black/40 backdrop-blur-xs p-2 rounded-[6px] border border-white/5">
              <p className="text-white font-semibold">{activeStudy.studyDescription}</p>
              <p>Series: {currentSeries.seriesDescription}</p>
              <p>Modality: {currentSeries.modality} • SOP: {currentSlice.instanceUid.slice(-12)}</p>
              <p>Window: {windowPreset.toUpperCase()}</p>
            </div>

            <div className="absolute top-3 right-3 z-10 pointer-events-none text-right font-mono text-[11px] text-[#a1a1aa] bg-black/40 backdrop-blur-xs p-2 rounded-[6px] border border-white/5">
              <p className="text-emerald-400 font-semibold">{activeStudy.institutionName}</p>
              <p>Acc: {activeStudy.accessionNumber}</p>
              <p>Acq: {activeStudy.studyDate} {activeStudy.studyTime}</p>
              <p>Zoom: {Math.round(zoomLevel * 100)}%</p>
            </div>

            {/* Caliper HUD Indicator */}
            {isCaliperActive && (
              <div className="absolute bottom-3 left-3 z-10 font-mono text-xs text-emerald-300 bg-emerald-950/80 border border-emerald-600/50 p-2 rounded-[6px] backdrop-blur-xs">
                {caliperPoints.length === 0 && (
                  <span>Click first point on image to begin caliper measurement</span>
                )}
                {caliperPoints.length === 1 && (
                  <span>Click second point to measure distance</span>
                )}
                {distanceInfo && (
                  <div className="space-y-0.5">
                    <p className="font-bold">Distance: {distanceInfo.mm} mm</p>
                    <p className="text-[10px] text-emerald-400">({distanceInfo.pixels} px @ 0.28mm/px scale)</p>
                  </div>
                )}
              </div>
            )}

            {/* Image / Graphic Canvas */}
            <div
              style={{
                transform: `scale(${zoomLevel}) rotate(${rotation}deg)`,
                transition: "transform 150ms ease-out",
              }}
              className={`relative max-w-full max-h-full flex items-center justify-center ${getFilterClass(
                windowPreset
              )}`}
            >
              {currentSlice.graphicType === "chest-xray" && (
                <ChestXRayGraphic />
              )}
              {currentSlice.graphicType === "ecg-rhythm" && (
                <EcgRhythmGraphic />
              )}
              {currentSlice.graphicType === "head-ct" && (
                <HeadCtGraphic sliceNumber={currentSlice.sliceNumber} />
              )}
              {currentSlice.graphicType === "echo-doppler" && (
                <EchoDopplerGraphic />
              )}
            </div>

            {/* Interactive Caliper Overlay SVG */}
            {isCaliperActive && caliperPoints.length > 0 && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none z-20">
                {caliperPoints.map((p, idx) => (
                  <g key={idx}>
                    <circle cx={p.x} cy={p.y} r={4} fill="#10b981" />
                    <circle cx={p.x} cy={p.y} r={8} stroke="#10b981" strokeWidth={1} fill="none" />
                  </g>
                ))}
                {caliperPoints.length === 2 && (
                  <>
                    <line
                      x1={caliperPoints[0].x}
                      y1={caliperPoints[0].y}
                      x2={caliperPoints[1].x}
                      y2={caliperPoints[1].y}
                      stroke="#10b981"
                      strokeWidth={1.5}
                      strokeDasharray="4,4"
                    />
                    <text
                      x={(caliperPoints[0].x + caliperPoints[1].x) / 2 + 10}
                      y={(caliperPoints[0].y + caliperPoints[1].y) / 2 - 10}
                      fill="#10b981"
                      fontSize={12}
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {distanceInfo?.mm} mm
                    </text>
                  </>
                )}
              </svg>
            )}

            {/* Bottom Caption Pill */}
            <div className="absolute bottom-3 right-3 z-10 pointer-events-none font-mono text-[11px] text-[#a1a1aa] bg-black/50 backdrop-blur-xs px-2.5 py-1 rounded-[6px] border border-white/5">
              {currentSlice.caption}
            </div>
          </div>

          {/* Slide-Over Drawer: DICOM Tags */}
          {showMetadataDrawer && (
            <div className="w-80 md:w-96 bg-[#141518] border-l border-[#27272a] p-4 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-[#27272a]">
                  <div className="flex items-center gap-2">
                    <FileCode className="h-4 w-4 text-emerald-400" />
                    <h4 className="font-semibold text-xs tracking-wide text-white uppercase">
                      DICOM 3.0 Header Tags
                    </h4>
                  </div>
                  <button
                    onClick={() => setShowMetadataDrawer(false)}
                    className="text-[#a1a1aa] hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <DicomTagRow tag="(0010,0010)" name="Patient's Name" value={activeStudy.patientName} />
                  <DicomTagRow tag="(0010,0020)" name="Patient ID" value={activeStudy.patientId} />
                  <DicomTagRow tag="(0008,0020)" name="Study Date" value={activeStudy.studyDate} />
                  <DicomTagRow tag="(0008,0030)" name="Study Time" value={activeStudy.studyTime} />
                  <DicomTagRow tag="(0008,0050)" name="Accession Number" value={activeStudy.accessionNumber} />
                  <DicomTagRow tag="(0008,0060)" name="Modality" value={activeStudy.modality} />
                  <DicomTagRow tag="(0008,0080)" name="Institution Name" value={activeStudy.institutionName} />
                  <DicomTagRow tag="(0008,0090)" name="Referring Physician" value={activeStudy.referringPhysician} />
                  <DicomTagRow tag="(0008,1030)" name="Study Description" value={activeStudy.studyDescription} />
                  <DicomTagRow tag="(0020,000D)" name="Study Instance UID" value={activeStudy.studyInstanceUid} />
                  <DicomTagRow tag="(0020,000E)" name="Series Instance UID" value={currentSeries.seriesInstanceUid} />
                  <DicomTagRow tag="(0008,0018)" name="SOP Instance UID" value={currentSlice.instanceUid} />
                  <DicomTagRow tag="(0028,0004)" name="Photometric Interp." value="MONOCHROME2" />
                  <DicomTagRow tag="(0002,0010)" name="Transfer Syntax" value="1.2.840.10008.1.2.1 (Explicit VR LE)" />
                </div>

                <div className="p-2.5 bg-[#18181b] rounded-[6px] border border-[#27272a] text-[11px] font-mono text-[#a1a1aa] space-y-1">
                  <p className="text-white font-semibold">WADO-RS Endpoint:</p>
                  <p className="break-all text-[10px] text-emerald-400">
                    /dicom-web/studies/{activeStudy.studyInstanceUid.slice(0, 24)}.../series/{currentSeries.seriesInstanceUid.slice(0, 18)}.../instances/{currentSlice.instanceUid.slice(0, 18)}...
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-[#27272a]">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const dataStr =
                      "data:text/json;charset=utf-8," +
                      encodeURIComponent(JSON.stringify(activeStudy, null, 2));
                    const dlAnchor = document.createElement("a");
                    dlAnchor.setAttribute("href", dataStr);
                    dlAnchor.setAttribute(
                      "download",
                      `dicom-metadata-${activeStudy.accessionNumber}.json`
                    );
                    dlAnchor.click();
                  }}
                  className="w-full text-xs bg-[#27272a] text-white border-[#3f3f46] hover:bg-[#3f3f46] flex items-center justify-center gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download DICOM Metadata (JSON)
                </Button>
              </div>
            </div>
          )}

          {/* Slide-Over Drawer: Radiology Diagnostic Report */}
          {showReportDrawer && activeStudy.radiologistReport && (
            <div className="w-80 md:w-96 bg-[#141518] border-l border-[#27272a] p-4 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
              <div className="space-y-4 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-[#27272a]">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-emerald-400" />
                    <h4 className="font-semibold text-xs tracking-wide text-white uppercase">
                      Radiology Report
                    </h4>
                  </div>
                  <button
                    onClick={() => setShowReportDrawer(false)}
                    className="text-[#a1a1aa] hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="flex items-center justify-between p-2 bg-[#18181b] rounded-[6px] border border-[#27272a]">
                  <div>
                    <p className="text-[11px] text-[#a1a1aa]">Reading Radiologist</p>
                    <p className="font-semibold text-white">
                      {activeStudy.radiologistReport.radiologistName}
                    </p>
                    <p className="text-[10px] text-[#a1a1aa]">
                      Reg: {activeStudy.radiologistReport.radiologistReg}
                    </p>
                  </div>
                  <Badge variant="emerald" size="sm" className="font-mono uppercase">
                    {activeStudy.radiologistReport.status}
                  </Badge>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-semibold text-white tracking-wide uppercase text-[11px]">
                    Clinical Findings Narrative:
                  </h5>
                  <p className="text-[#d4d4d8] leading-relaxed text-xs p-3 bg-[#18181b] rounded-[6px] border border-[#27272a]">
                    {activeStudy.radiologistReport.findings}
                  </p>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-semibold text-emerald-400 tracking-wide uppercase text-[11px]">
                    Impression & Conclusion:
                  </h5>
                  <p className="text-white font-medium leading-relaxed text-xs p-3 bg-emerald-950/40 border border-emerald-600/40 rounded-[6px]">
                    {activeStudy.radiologistReport.impression}
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-[#27272a]">
                <div className="flex items-center gap-2 text-[11px] text-emerald-400">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>Digitally attested via HPR Key Pair</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const DicomTagRow: React.FC<{ tag: string; name: string; value: string }> = ({
  tag,
  name,
  value,
}) => (
  <div className="flex flex-col border-b border-[#27272a] pb-1.5">
    <div className="flex items-center justify-between text-[10px] text-[#71717a]">
      <span>{name}</span>
      <span className="text-[#a1a1aa]">{tag}</span>
    </div>
    <span className="text-[#f4f4f5] text-[11px] truncate" title={value}>
      {value}
    </span>
  </div>
);

// High-Fidelity Diagnostic Graphics

const ChestXRayGraphic: React.FC = () => (
  <svg
    viewBox="0 0 600 700"
    className="w-[380px] sm:w-[480px] md:w-[540px] h-auto drop-shadow-2xl select-none"
  >
    <defs>
      <radialGradient id="lungVascularGrad" cx="50%" cy="45%" r="60%">
        <stop offset="0%" stopColor="#15171d" />
        <stop offset="45%" stopColor="#0c0d11" />
        <stop offset="100%" stopColor="#030304" />
      </radialGradient>
      <linearGradient id="boneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#d1d5db" stopOpacity="0.85" />
        <stop offset="100%" stopColor="#9ca3af" stopOpacity="0.45" />
      </linearGradient>
      <linearGradient id="cardiacGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#e5e7eb" stopOpacity="0.75" />
        <stop offset="100%" stopColor="#9ca3af" stopOpacity="0.55" />
      </linearGradient>
    </defs>

    {/* Background Cassette */}
    <rect width="600" height="700" rx="8" fill="#050608" />

    {/* Soft Tissue Contour */}
    <path
      d="M100 120 C100 80, 200 40, 300 40 C400 40, 500 80, 500 120 C540 220, 550 480, 510 650 C440 680, 160 680, 90 650 C50 480, 60 220, 100 120 Z"
      fill="url(#lungVascularGrad)"
      stroke="#1f2937"
      strokeWidth="2"
    />

    {/* Right Lung Field */}
    <path
      d="M140 180 C180 140, 260 140, 270 200 C275 350, 270 480, 260 520 C230 540, 160 530, 130 500 C115 420, 115 280, 140 180 Z"
      fill="#080a0e"
      stroke="#374151"
      strokeWidth="1.5"
    />

    {/* Left Lung Field */}
    <path
      d="M460 180 C420 140, 340 140, 330 200 C325 350, 340 460, 350 515 C380 540, 440 530, 470 500 C485 420, 485 280, 460 180 Z"
      fill="#080a0e"
      stroke="#374151"
      strokeWidth="1.5"
    />

    {/* Trachea Air Column */}
    <rect x="294" y="60" width="12" height="150" rx="4" fill="#000000" stroke="#4b5563" strokeWidth="1" />

    {/* Clavicles */}
    <path
      d="M120 135 Q210 160, 290 150"
      stroke="url(#boneGrad)"
      strokeWidth="14"
      strokeLinecap="round"
      fill="none"
    />
    <path
      d="M480 135 Q390 160, 310 150"
      stroke="url(#boneGrad)"
      strokeWidth="14"
      strokeLinecap="round"
      fill="none"
    />

    {/* Rib Cage Skeletons */}
    {[0, 1, 2, 3, 4, 5, 6].map((i) => {
      const yOffset = 180 + i * 45;
      const arc = 35 + i * 6;
      return (
        <g key={i}>
          {/* Right Rib */}
          <path
            d={`M285 ${yOffset} Q${160 - arc} ${yOffset + 25}, 125 ${yOffset + 50}`}
            stroke="url(#boneGrad)"
            strokeWidth="8"
            strokeLinecap="round"
            fill="none"
            opacity="0.6"
          />
          {/* Left Rib */}
          <path
            d={`M315 ${yOffset} Q${440 + arc} ${yOffset + 25}, 475 ${yOffset + 50}`}
            stroke="url(#boneGrad)"
            strokeWidth="8"
            strokeLinecap="round"
            fill="none"
            opacity="0.6"
          />
        </g>
      );
    })}

    {/* Mediastinal Cardiac Silhouette */}
    <path
      d="M280 230 C280 200, 320 200, 320 250 C335 300, 410 430, 375 515 C340 540, 260 540, 230 500 C215 440, 255 350, 280 230 Z"
      fill="url(#cardiacGrad)"
      stroke="#e5e7eb"
      strokeWidth="1"
      opacity="0.85"
    />

    {/* Diaphragmatic Domes */}
    <path
      d="M90 535 Q190 490, 270 525"
      stroke="#9ca3af"
      strokeWidth="4"
      fill="none"
    />
    <path
      d="M330 525 Q410 495, 510 540"
      stroke="#9ca3af"
      strokeWidth="4"
      fill="none"
    />

    {/* Costophrenic Angle Sharp Markers */}
    <circle cx="108" cy="530" r="3" fill="#10b981" />
    <circle cx="492" cy="535" r="3" fill="#10b981" />

    {/* Anatomical Orientation Marker (R) */}
    <text x="50" y="90" fill="#e5e7eb" fontSize="28" fontWeight="bold" fontFamily="sans-serif">
      R
    </text>
  </svg>
);

const EcgRhythmGraphic: React.FC = () => (
  <svg
    viewBox="0 0 900 450"
    className="w-[450px] sm:w-[650px] md:w-[750px] h-auto drop-shadow-2xl select-none"
  >
    {/* Millimeter Grid Background (25mm/s, 10mm/mV standard) */}
    <rect width="900" height="450" rx="8" fill="#1c0707" />
    <defs>
      <pattern id="smallGrid" width="10" height="10" patternUnits="userSpaceOnUse">
        <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#7f1d1d" strokeWidth="0.5" opacity="0.3" />
      </pattern>
      <pattern id="largeGrid" width="50" height="50" patternUnits="userSpaceOnUse">
        <rect width="50" height="50" fill="url(#smallGrid)" />
        <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#b91c1c" strokeWidth="1" opacity="0.45" />
      </pattern>
    </defs>
    <rect width="900" height="450" fill="url(#largeGrid)" />

    {/* Calibration Pulse (10mm = 1mV) */}
    <path
      d="M30 250 L60 250 L60 170 L90 170 L90 250 L120 250"
      fill="none"
      stroke="#38bdf8"
      strokeWidth="2.5"
    />
    <text x="45" y="275" fill="#38bdf8" fontSize="11" fontFamily="monospace">
      1 mV / 10 mm
    </text>

    {/* Lead II Continuous Rhythm Waveform */}
    <path
      d="
        M120 250
        L150 250 Q160 235, 170 250 L185 250
        L190 260 L200 120 L210 280 L215 250
        L230 250 Q250 215, 270 250 L300 250

        L330 250 Q340 235, 350 250 L365 250
        L370 260 L380 120 L390 280 L395 250
        L410 250 Q430 215, 450 250 L480 250

        L510 250 Q520 235, 530 250 L545 250
        L550 260 L560 120 L570 280 L575 250
        L590 250 Q610 215, 630 250 L660 250

        L690 250 Q700 235, 710 250 L725 250
        L730 260 L740 120 L750 280 L755 250
        L770 250 Q790 215, 810 250 L870 250
      "
      fill="none"
      stroke="#22c55e"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    {/* Lead Annotations */}
    <text x="35" y="50" fill="#f87171" fontSize="16" fontWeight="bold" fontFamily="sans-serif">
      LEAD II • Standard Diagnostic Strip (25 mm/s)
    </text>
    <text x="35" y="75" fill="#a1a1aa" fontSize="12" fontFamily="monospace">
      HR: 72 bpm • PR: 156 ms • QRS: 84 ms • QT/QTc: 388/412 ms • P-QRS-T Normal
    </text>
  </svg>
);

const HeadCtGraphic: React.FC<{ sliceNumber: number }> = ({ sliceNumber }) => (
  <svg
    viewBox="0 0 500 500"
    className="w-[340px] sm:w-[440px] h-auto drop-shadow-2xl select-none"
  >
    {/* Cranial Bone Calvarium */}
    <rect width="500" height="500" rx="8" fill="#040507" />

    {/* Calvarium Cortical Bone Ring */}
    <ellipse
      cx="250"
      cy="250"
      rx="190"
      ry="215"
      fill="#18181b"
      stroke="#f4f4f5"
      strokeWidth="14"
    />

    {/* Brain Parenchyma (Soft Tissue HU 35-40) */}
    <ellipse cx="250" cy="250" rx="178" ry="203" fill="#27272a" />

    {/* Interhemispheric Falx Cerebri Midline */}
    <line x1="250" y1="50" x2="250" y2="450" stroke="#3f3f46" strokeWidth="2.5" />

    {/* Lateral Ventricles (CSF HU 0-10) */}
    {sliceNumber === 1 ? (
      <g fill="#09090b" stroke="#3f3f46" strokeWidth="1.5">
        {/* Right Anterior Horn */}
        <path d="M244 190 Q225 210, 230 250 Q240 260, 245 220 Z" />
        {/* Left Anterior Horn */}
        <path d="M256 190 Q275 210, 270 250 Q260 260, 255 220 Z" />
        {/* Third Ventricle Midline Slit */}
        <line x1="250" y1="260" x2="250" y2="285" stroke="#09090b" strokeWidth="4" />
      </g>
    ) : (
      <g fill="#09090b" stroke="#3f3f46" strokeWidth="1.5">
        {/* Superior Centrum Semiovale sulcal pattern */}
        <path d="M190 200 Q210 240, 240 220" fill="none" stroke="#3f3f46" strokeWidth="2" />
        <path d="M310 200 Q290 240, 260 220" fill="none" stroke="#3f3f46" strokeWidth="2" />
      </g>
    )}

    {/* Orientation Letters */}
    <text x="35" y="255" fill="#e5e7eb" fontSize="18" fontWeight="bold">
      R
    </text>
    <text x="455" y="255" fill="#e5e7eb" fontSize="18" fontWeight="bold">
      L
    </text>
    <text x="245" y="35" fill="#e5e7eb" fontSize="18" fontWeight="bold">
      A
    </text>
    <text x="245" y="485" fill="#e5e7eb" fontSize="18" fontWeight="bold">
      P
    </text>
  </svg>
);

const EchoDopplerGraphic: React.FC = () => (
  <svg
    viewBox="0 0 500 450"
    className="w-[340px] sm:w-[440px] h-auto drop-shadow-2xl select-none"
  >
    <rect width="500" height="450" rx="8" fill="#040507" />
    {/* Ultrasound Sector Fan Beam */}
    <path
      d="M250 40 L70 410 A230 230 0 0 0 430 410 Z"
      fill="#18181b"
      stroke="#3f3f46"
      strokeWidth="2"
    />
    {/* Apical 4-Chamber Structure */}
    <path
      d="M200 240 Q250 220, 300 240 Q280 340, 250 360 Q220 340, 200 240 Z"
      fill="#09090b"
      stroke="#52525b"
      strokeWidth="1.5"
    />
    {/* Interventricular Septum */}
    <line x1="250" y1="230" x2="250" y2="360" stroke="#71717a" strokeWidth="3" />
    {/* Color Doppler Flow Jet */}
    <ellipse cx="270" cy="270" rx="20" ry="30" fill="#38bdf8" opacity="0.6" />
    <ellipse cx="230" cy="270" rx="18" ry="25" fill="#ef4444" opacity="0.5" />
    <text x="40" y="70" fill="#38bdf8" fontSize="12" fontFamily="monospace">
      APICAL 4-CHAMBER • COLOR DOPPLER
    </text>
  </svg>
);
