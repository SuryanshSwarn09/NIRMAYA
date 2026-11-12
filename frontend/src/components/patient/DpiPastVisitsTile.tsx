"use client";

import React, { useState } from "react";
import { CitizenVisitReportItem } from "@/lib/api";
import { useAccessibility } from "@/context/AccessibilityContext";


interface DpiPastVisitsTileProps {
  visits: CitizenVisitReportItem[];
  patientName: string;
}

export const DpiPastVisitsTile: React.FC<DpiPastVisitsTileProps> = ({
  visits,
  patientName,
}) => {
  const { t, locale } = useAccessibility();
  const [filter, setFilter] = useState<"all" | "prescription" | "diagnostic">("all");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const filteredItems = visits.filter((item) => {
    if (filter === "prescription") return item.item_type === "prescription";
    if (filter === "diagnostic") return item.item_type === "diagnostic_report";
    return true;
  });

  const handleDownload = (item: CitizenVisitReportItem) => {
    setDownloadingId(item.id);
    // Simulate generation and download of signed FHIR bundle/PDF
    setTimeout(() => {
      const element = document.createElement("a");
      const file = new Blob(
        [
          JSON.stringify(
            {
              format: "ABDM-FHIR-R4-RECORD",
              recordId: item.id,
              patient: patientName,
              doctor: item.doctor_name,
              facility: item.facility_name,
              diagnosis: item.plain_diagnosis,
              date: item.encounter_date,
              digitalSignatureSeal: item.digital_signature_seal || "SHA256:AUTHENTIC-RECORD",
              issuedAt: new Date().toISOString(),
            },
            null,
            2
          ),
        ],
        { type: "application/json" }
      );
      element.href = URL.createObjectURL(file);
      element.download = `${item.id}-clinical-summary.json`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      setDownloadingId(null);
    }, 450);
  };

  return (
    <section
      aria-labelledby="tile-visits-title"
      className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md"
    >
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white">
              3
            </span>
            <h2 id="tile-visits-title" className="text-base font-semibold text-gray-900">
              {t("citizen.tile3.title", "Tile 3: Past Consultations & Reports")}
            </h2>
          </div>
          <p className="mt-1 text-xs text-gray-500">
            {t("citizen.tile3.desc", "Doctor visits and 1-click verifiable signed prescription PDFs.")}
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center rounded-lg border border-gray-200 bg-gray-50 p-1 text-xs">
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`rounded-md px-3 py-1 font-medium transition cursor-pointer ${
              filter === "all"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {locale === "hi" ? "सभी" : "All"} ({visits.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter("prescription")}
            className={`rounded-md px-3 py-1 font-medium transition cursor-pointer ${
              filter === "prescription"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {locale === "hi" ? "पर्चे" : "Prescriptions"}
          </button>
          <button
            type="button"
            onClick={() => setFilter("diagnostic")}
            className={`rounded-md px-3 py-1 font-medium transition cursor-pointer ${
              filter === "diagnostic"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {locale === "hi" ? "रिपोर्ट्स" : "Reports"}
          </button>
        </div>
      </div>

      {/* Content Feed */}
      <div className="mt-4 divide-y divide-gray-100">
        {filteredItems.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm font-medium text-gray-600">No records found for this category</p>
            <p className="mt-1 text-xs text-gray-400">
              Consultations from registered ABDM facilities will automatically appear here.
            </p>
          </div>
        ) : (
          filteredItems.map((item) => (
            <article key={item.id} className="py-3.5 first:pt-1 last:pb-1">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${
                        item.item_type === "prescription"
                          ? "bg-gray-100 text-gray-800 border border-gray-200"
                          : "bg-blue-50 text-blue-800 border border-blue-200"
                      }`}
                    >
                      {item.item_type === "prescription" ? "Prescription" : "Diagnostic Report"}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">
                      {item.encounter_date}
                    </span>
                    {item.digital_signature_seal && (
                      <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 border border-emerald-200">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Digitally Signed
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-semibold text-gray-900">
                    {item.plain_diagnosis}
                  </h3>

                  <div className="flex flex-wrap items-center gap-x-3 text-xs text-gray-600">
                    <span>{item.doctor_name}</span>
                    <span>•</span>
                    <span className="text-gray-500">{item.facility_name}</span>
                  </div>

                  {item.summary && (
                    <p className="text-xs text-gray-600 bg-gray-50 rounded p-2 mt-1">
                      {item.summary}
                    </p>
                  )}
                </div>

                {/* Action CTA */}
                <div className="mt-2 sm:mt-0 flex-shrink-0">
                  <button
                    type="button"
                    onClick={() => handleDownload(item)}
                    disabled={downloadingId === item.id}
                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition active:scale-95 disabled:opacity-50"
                  >
                    <svg className="h-3.5 w-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    {downloadingId === item.id
                      ? "Downloading..."
                      : item.item_type === "prescription"
                      ? "Download Signed Rx"
                      : "Download Report"}
                  </button>
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
};
