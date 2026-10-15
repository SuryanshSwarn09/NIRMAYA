"use client";

import React, { useState } from "react";
import { Badge, Button } from "@/components/ui";
import { apiClient } from "@/lib/api";
import type { MedicationRequest, MedicationDispense } from "@/lib/api";
import {
  Pill,
  CheckCircle2,
  AlertTriangle,
  X,
  Package,
  Calendar,
  Layers,
  ArrowRight,
  ShieldCheck,
  FileCheck,
  Building2,
  Clock,
  Sparkles,
  Info,
} from "lucide-react";

export interface PharmacyDispenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  prescription: MedicationRequest | null;
  onDispenseSuccess?: (dispense: MedicationDispense) => void;
}

const COMMON_SUBSTITUTION_REASONS = [
  "Formulary tier-1 generic equivalent supplied",
  "Prescribed brand formulation temporarily unavailable",
  "Patient requested lower-cost bioequivalent generic",
  "Institutional formulary substitution protocol followed",
];

export const PharmacyDispenseModal: React.FC<PharmacyDispenseModalProps> = ({
  isOpen,
  onClose,
  prescription,
  onDispenseSuccess,
}) => {
  const [quantity, setQuantity] = useState<number>(
    prescription?.dispense_quantity || 30
  );
  const [dispenseUnit, setDispenseUnit] = useState<string>(
    prescription?.dispense_unit || "tablets"
  );
  const [daysSupply, setDaysSupply] = useState<number>(
    prescription?.expected_supply_duration_days || 30
  );
  const [lotNumber, setLotNumber] = useState<string>("LOT-2026-X01");
  const [expirationDate, setExpirationDate] = useState<string>("2028-06-30");
  const [wasSubstituted, setWasSubstituted] = useState<boolean>(false);
  const [substitutionReason, setSubstitutionReason] = useState<string>(
    "Formulary tier-1 generic equivalent supplied"
  );
  const [pharmacistNotes, setPharmacistNotes] = useState<string>("");
  const [patientInstructions, setPatientInstructions] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [dispenseSuccess, setDispenseSuccess] = useState<MedicationDispense | null>(null);

  if (!isOpen || !prescription) {
    return null;
  }

  const allowSub = prescription.allow_generic_substitution !== false;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!lotNumber.trim()) {
      setErrorMessage("Batch lot number is required for pharmaceutical tracking.");
      return;
    }

    if (!expirationDate) {
      setErrorMessage("Batch expiration date is required.");
      return;
    }

    if (quantity <= 0) {
      setErrorMessage("Quantity dispensed must be greater than zero.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        prescription_id: prescription.id,
        quantity_dispensed: quantity,
        dispense_unit: dispenseUnit,
        days_supply: daysSupply,
        lot_number: lotNumber.trim(),
        expiration_date: expirationDate,
        was_substituted: wasSubstituted,
        substitution_type: wasSubstituted ? "G" : undefined,
        substitution_reason: wasSubstituted ? substitutionReason : undefined,
        pharmacist_notes: pharmacistNotes.trim() || undefined,
        patient_instructions: patientInstructions.trim() || undefined,
      };

      const result = await apiClient.dispensePrescription(prescription.id, payload);
      setDispenseSuccess(result);
      if (onDispenseSuccess) {
        onDispenseSuccess(result);
      }
    } catch (err: unknown) {
      console.error("Dispense failed:", err);
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to fulfill prescription. Please verify authorization and repeat quotas.";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetAndClose = () => {
    setDispenseSuccess(null);
    setErrorMessage(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-neutral-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-neutral-200 overflow-hidden max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-neutral-100 flex items-center justify-between bg-neutral-50/70">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-neutral-900 text-white flex items-center justify-center shadow-xs">
              <Package className="w-5 h-5 text-neutral-100" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-neutral-900 tracking-tight">
                Pharmacy Fulfillment & Dispense
              </h3>
              <p className="text-xs text-neutral-500">
                ABDM & HL7 FHIR R4 MedicationDispense record
              </p>
            </div>
          </div>
          <button
            onClick={handleResetAndClose}
            className="text-neutral-400 hover:text-neutral-700 p-1.5 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {dispenseSuccess ? (
            /* Success confirmation screen */
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto shadow-xs">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-neutral-900">
                  Prescription Successfully Dispensed
                </h4>
                <p className="text-xs text-neutral-500 mt-1">
                  Dispensation number has been registered in the longitudinal vault
                </p>
              </div>

              <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-4 text-left max-w-md mx-auto space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-neutral-500">Dispense Number:</span>
                  <span className="font-mono font-semibold text-neutral-900">
                    {dispenseSuccess.dispense_number}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500">Medication:</span>
                  <span className="font-medium text-neutral-900">
                    {dispenseSuccess.medication_name || prescription.medication?.name || "Medication"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500">Quantity & Days:</span>
                  <span className="text-neutral-900 font-medium">
                    {dispenseSuccess.quantity_dispensed} {dispenseSuccess.dispense_unit} ({dispenseSuccess.days_supply} days supply)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500">Batch Lot & Expiry:</span>
                  <span className="font-mono text-neutral-900">
                    {dispenseSuccess.lot_number} • Exp: {dispenseSuccess.expiration_date}
                  </span>
                </div>
                {dispenseSuccess.was_substituted && (
                  <div className="flex justify-between pt-1 border-t border-neutral-200">
                    <span className="text-amber-800 font-medium">Generic Substitution:</span>
                    <span className="text-amber-900 italic font-mono text-[11px]">
                      {dispenseSuccess.substitution_reason || "Generic applied"}
                    </span>
                  </div>
                )}
              </div>

              <div className="pt-2">
                <Button
                  onClick={handleResetAndClose}
                  className="bg-neutral-900 text-white hover:bg-neutral-800 text-xs px-6"
                >
                  Close & Refresh Dashboard
                </Button>
              </div>
            </div>
          ) : (
            /* Dispensation fulfillment form */
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Prescription Context Banner */}
              <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] text-neutral-500">
                    RX ID: {prescription.id.slice(0, 13)}...
                  </span>
                  <Badge
                    variant={allowSub ? "outline" : "warning"}
                    className={
                      allowSub
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px]"
                        : "bg-amber-50 text-amber-800 border-amber-200 text-[10px]"
                    }
                  >
                    {allowSub ? "Substitution Permitted" : "Dispense As Written (DAW)"}
                  </Badge>
                </div>

                <div className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-white border border-neutral-200 text-neutral-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Pill className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-neutral-900">
                      {prescription.medication?.name || "Catalog Drug"}
                    </h4>
                    <p className="text-neutral-600 mt-0.5">{prescription.dosage_text}</p>
                    <div className="flex items-center gap-3 text-neutral-500 text-[11px] mt-1">
                      <span>Prescribed: {prescription.dispense_quantity || 30} {prescription.dispense_unit || "tablets"}</span>
                      <span>•</span>
                      <span>Repeats Allowed: {prescription.number_of_repeats_allowed}</span>
                    </div>
                  </div>
                </div>
              </div>

              {errorMessage && (
                <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-900 rounded-xl p-3 text-xs animate-in fade-in">
                  <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">Dispensation Rejected:</span>
                    <p className="mt-0.5">{errorMessage}</p>
                  </div>
                </div>
              )}

              {/* Dispensation Parameters */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="text-neutral-700 font-medium block mb-1">
                    Quantity to Dispense *
                  </label>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    className="w-full p-2 rounded-lg border border-neutral-300 focus:outline-none focus:ring-1 focus:ring-neutral-900 text-xs"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    required
                  />
                </div>

                <div>
                  <label className="text-neutral-700 font-medium block mb-1">
                    Dispense Unit *
                  </label>
                  <input
                    type="text"
                    className="w-full p-2 rounded-lg border border-neutral-300 focus:outline-none focus:ring-1 focus:ring-neutral-900 text-xs"
                    value={dispenseUnit}
                    onChange={(e) => setDispenseUnit(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="text-neutral-700 font-medium block mb-1">
                    Batch Lot Number *
                  </label>
                  <input
                    type="text"
                    className="w-full p-2 rounded-lg border border-neutral-300 focus:outline-none focus:ring-1 focus:ring-neutral-900 text-xs font-mono"
                    placeholder="e.g. LOT-2026-X42"
                    value={lotNumber}
                    onChange={(e) => setLotNumber(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="text-neutral-700 font-medium block mb-1">
                    Batch Expiration Date *
                  </label>
                  <input
                    type="date"
                    className="w-full p-2 rounded-lg border border-neutral-300 focus:outline-none focus:ring-1 focus:ring-neutral-900 text-xs"
                    value={expirationDate}
                    onChange={(e) => setExpirationDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Generic Substitution Governance */}
              <div className="border border-neutral-200 rounded-xl p-3 bg-neutral-50/50 space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-neutral-800">
                    <input
                      type="checkbox"
                      disabled={!allowSub}
                      checked={wasSubstituted}
                      onChange={(e) => setWasSubstituted(e.target.checked)}
                      className="rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900 w-4 h-4 disabled:opacity-50"
                    />
                    <span>Dispense with Generic / Bioequivalent Substitution</span>
                  </label>
                </div>

                {!allowSub && (
                  <p className="text-[11px] text-amber-800 bg-amber-50 p-2 rounded-lg border border-amber-200/80">
                    ⚠️ The prescriber has explicitly restricted this prescription to "Dispense As
                    Written". Generic substitution is prohibited by clinical policy.
                  </p>
                )}

                {wasSubstituted && allowSub && (
                  <div className="pt-1.5 space-y-2">
                    <label className="text-neutral-600 block text-[11px]">
                      Substitution Reason:
                    </label>
                    <select
                      className="w-full text-xs p-2 rounded-lg border border-neutral-300 bg-white focus:outline-none focus:ring-1 focus:ring-neutral-900"
                      value={substitutionReason}
                      onChange={(e) => setSubstitutionReason(e.target.value)}
                    >
                      {COMMON_SUBSTITUTION_REASONS.map((r, i) => (
                        <option key={i} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Pharmacist Clinical Notes */}
              <div className="space-y-1 text-xs">
                <label className="text-neutral-700 font-medium block">
                  Pharmacist Dispensation Notes (Optional)
                </label>
                <textarea
                  rows={2}
                  className="w-full p-2 rounded-lg border border-neutral-300 focus:outline-none focus:ring-1 focus:ring-neutral-900 placeholder:text-neutral-400 text-xs"
                  placeholder="e.g. First fill dispensed. Patient counseled on hydration and timing..."
                  value={pharmacistNotes}
                  onChange={(e) => setPharmacistNotes(e.target.value)}
                />
              </div>

              {/* Footer Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-neutral-100">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleResetAndClose}
                  className="text-xs text-neutral-700"
                >
                  Cancel
                </Button>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-neutral-900 text-white hover:bg-neutral-800 text-xs gap-1.5 px-4"
                >
                  {isSubmitting ? (
                    <>Fulfilling Dispensation...</>
                  ) : (
                    <>
                      Confirm & Fulfill Dispense
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
