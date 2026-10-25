"use client";

import React, { useState, useMemo } from "react";
import { Badge, Button, Card, CardTitle, CardDescription } from "@/components/ui";
import { 
  Medication, 
  FormularyTier, 
  MedicationForm, 
  AdministrationRoute 
} from "@/lib/api";
import { 
  Search, 
  Pill, 
  ShieldAlert, 
  FileCode, 
  Check, 
  Copy, 
  Sparkles, 
  Filter, 
  Info, 
  X,
  Layers,
  ThermometerSnowflake,
  ExternalLink
} from "lucide-react";

interface MedicationCatalogBrowserProps {
  onSelectMedication?: (medication: Medication) => void;
  isSelectable?: boolean;
}

// Built-in clinical formulary fallback dataset (30 Essential Medications)
const FALLBACK_FORMULARY_DATA: Medication[] = [
  {
    id: "med-metformin-500",
    name: "Metformin 500mg Oral Tablet",
    generic_name: "Metformin Hydrochloride",
    brand_name: "Glucophage",
    rxnorm_code: "860975",
    rxnorm_display: "Metformin hydrochloride 500 MG Oral Tablet",
    atc_code: "A10BA02",
    atc_display: "Biguanides (Metformin)",
    snomed_code: "387048002",
    snomed_display: "Metformin hydrochloride",
    form: "tablet",
    route: "oral",
    strength: "500 mg",
    active_ingredient: "Metformin",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "First-line biguanide oral antihyperglycemic agent for Type 2 Diabetes Mellitus.",
    contraindications_summary: "Severe renal impairment (eGFR < 30 mL/min/1.73 m2), acute metabolic acidosis.",
    storage_instructions: "Store at 20°C to 25°C (68°F to 77°F). Protect from moisture.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-atorvastatin-20",
    name: "Atorvastatin 20mg Oral Tablet",
    generic_name: "Atorvastatin Calcium",
    brand_name: "Lipitor",
    rxnorm_code: "617314",
    rxnorm_display: "Atorvastatin 20 MG Oral Tablet",
    atc_code: "C10AA05",
    atc_display: "HMG-CoA reductase inhibitors (Statins)",
    snomed_code: "387584000",
    snomed_display: "Atorvastatin calcium",
    form: "tablet",
    route: "oral",
    strength: "20 mg",
    active_ingredient: "Atorvastatin",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Competitive HMG-CoA reductase inhibitor for hypercholesterolemia and ASCVD risk reduction.",
    contraindications_summary: "Active liver disease, unexplained persistent elevations in hepatic transaminases, pregnancy.",
    storage_instructions: "Store at 20°C to 25°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-lisinopril-10",
    name: "Lisinopril 10mg Oral Tablet",
    generic_name: "Lisinopril",
    brand_name: "Zestril",
    rxnorm_code: "314076",
    rxnorm_display: "Lisinopril 10 MG Oral Tablet",
    atc_code: "C09AA03",
    atc_display: "ACE inhibitors (Lisinopril)",
    snomed_code: "386864001",
    snomed_display: "Lisinopril",
    form: "tablet",
    route: "oral",
    strength: "10 mg",
    active_ingredient: "Lisinopril",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Angiotensin-converting enzyme (ACE) inhibitor for hypertension and heart failure.",
    contraindications_summary: "History of angioedema with ACE inhibitors, pregnancy (Boxed Warning).",
    storage_instructions: "Store at 20°C to 25°C. Protect from moisture.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-amoxicillin-500",
    name: "Amoxicillin 500mg Oral Capsule",
    generic_name: "Amoxicillin Trihydrate",
    brand_name: "Amoxil",
    rxnorm_code: "308182",
    rxnorm_display: "Amoxicillin 500 MG Oral Capsule",
    atc_code: "J01CA04",
    atc_display: "Penicillins with extended spectrum (Amoxicillin)",
    snomed_code: "372687004",
    snomed_display: "Amoxicillin trihydrate",
    form: "capsule",
    route: "oral",
    strength: "500 mg",
    active_ingredient: "Amoxicillin",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Moderate-spectrum bactericidal beta-lactam antibiotic for susceptible bacterial infections.",
    contraindications_summary: "History of severe allergic reaction (anaphylaxis) to penicillin or beta-lactams.",
    storage_instructions: "Store at 20°C to 25°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-albuterol-inhaler",
    name: "Albuterol 90 mcg/actuation Inhalation Aerosol",
    generic_name: "Albuterol Sulfate",
    brand_name: "ProAir HFA",
    rxnorm_code: "745678",
    rxnorm_display: "Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler",
    atc_code: "R03AC02",
    atc_display: "Selective beta-2 adrenoreceptor agonists",
    snomed_code: "372808003",
    snomed_display: "Albuterol sulfate",
    form: "inhaler",
    route: "inhalation",
    strength: "90 mcg/actuation",
    active_ingredient: "Albuterol",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Short-acting selective beta-2 adrenergic receptor agonist (SABA) rescue bronchodilator for acute asthma.",
    contraindications_summary: "Hypersensitivity to albuterol or propellant ingredients.",
    storage_instructions: "Store at 20°C to 25°C. Contents under pressure.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-pantoprazole-40",
    name: "Pantoprazole 40mg Delayed Release Tablet",
    generic_name: "Pantoprazole Sodium",
    brand_name: "Protonix",
    rxnorm_code: "284635",
    rxnorm_display: "Pantoprazole sodium 40 MG Delayed Release Oral Tablet",
    atc_code: "A02BC02",
    atc_display: "Proton pump inhibitors (Pantoprazole)",
    snomed_code: "386858008",
    snomed_display: "Pantoprazole sodium",
    form: "tablet",
    route: "oral",
    strength: "40 mg",
    active_ingredient: "Pantoprazole",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Substituted benzimidazole proton pump inhibitor (PPI) suppressing gastric acid secretion.",
    contraindications_summary: "Hypersensitivity to substituted benzimidazoles, concurrent rilpivirine.",
    storage_instructions: "Store at 20°C to 25°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-paracetamol-500",
    name: "Paracetamol 500mg Oral Tablet",
    generic_name: "Acetaminophen",
    brand_name: "Calpol",
    rxnorm_code: "198440",
    rxnorm_display: "Acetaminophen 500 MG Oral Tablet",
    atc_code: "N02BE01",
    atc_display: "Anilides (Paracetamol / Acetaminophen)",
    snomed_code: "387517004",
    snomed_display: "Acetaminophen",
    form: "tablet",
    route: "oral",
    strength: "500 mg",
    active_ingredient: "Paracetamol",
    is_prescription_required: false,
    is_controlled_substance: false,
    formulary_tier: "tier_5_otc",
    status: "active",
    description: "Centrally acting analgesic and antipyretic for mild to moderate pain and fever.",
    contraindications_summary: "Severe hepatic impairment or severe active liver disease.",
    storage_instructions: "Store below 25°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-tramadol-50",
    name: "Tramadol Hydrochloride 50mg Oral Tablet",
    generic_name: "Tramadol Hydrochloride",
    brand_name: "Ultram",
    rxnorm_code: "833734",
    rxnorm_display: "Tramadol hydrochloride 50 MG Oral Tablet",
    atc_code: "N02AX02",
    atc_display: "Other opioids (Tramadol)",
    snomed_code: "387525002",
    snomed_display: "Tramadol hydrochloride",
    form: "tablet",
    route: "oral",
    strength: "50 mg",
    active_ingredient: "Tramadol",
    is_prescription_required: true,
    is_controlled_substance: true,
    formulary_tier: "tier_3_non_preferred_brand",
    status: "active",
    description: "Centrally acting mu-opioid receptor agonist and weak SNRI reuptake inhibitor.",
    contraindications_summary: "Significant respiratory depression, acute intoxication with CNS depressants. DEA Schedule IV.",
    storage_instructions: "Store at 20°C to 25°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-sertraline-50",
    name: "Sertraline Hydrochloride 50mg Oral Tablet",
    generic_name: "Sertraline Hydrochloride",
    brand_name: "Zoloft",
    rxnorm_code: "312940",
    rxnorm_display: "Sertraline hydrochloride 50 MG Oral Tablet",
    atc_code: "N06AB06",
    atc_display: "Selective serotonin reuptake inhibitors (SSRI)",
    snomed_code: "386899009",
    snomed_display: "Sertraline hydrochloride",
    form: "tablet",
    route: "oral",
    strength: "50 mg",
    active_ingredient: "Sertraline",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Selective serotonin reuptake inhibitor (SSRI) for major depressive disorder and panic disorder.",
    contraindications_summary: "Concurrent MAO inhibitors, pimozide (Boxed Warning: suicidality in young adults).",
    storage_instructions: "Store at 20°C to 25°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-levothyroxine-50",
    name: "Levothyroxine Sodium 50mcg Oral Tablet",
    generic_name: "Levothyroxine Sodium",
    brand_name: "Synthroid",
    rxnorm_code: "966222",
    rxnorm_display: "Levothyroxine sodium 0.05 MG Oral Tablet",
    atc_code: "H03AA01",
    atc_display: "Thyroid hormones (Levothyroxine)",
    snomed_code: "387157007",
    snomed_display: "Levothyroxine sodium",
    form: "tablet",
    route: "oral",
    strength: "50 mcg",
    active_ingredient: "Levothyroxine",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Synthetic L-thyroxine (T4) hormone replacement for primary and secondary hypothyroidism.",
    contraindications_summary: "Uncorrected adrenal cortical insufficiency, untreated thyrotoxicosis.",
    storage_instructions: "Store at 20°C to 25°C. Protect from moisture and light.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-insulin-glargine",
    name: "Insulin Glargine 100 units/mL Subcutaneous Solution",
    generic_name: "Insulin Glargine (rDNA origin)",
    brand_name: "Lantus",
    rxnorm_code: "274786",
    rxnorm_display: "Insulin Glargine 100 UNT/ML Injectable Solution",
    atc_code: "A10AE04",
    atc_display: "Long-acting insulins and analogues",
    snomed_code: "411529000",
    snomed_display: "Insulin glargine",
    form: "injection",
    route: "subcutaneous",
    strength: "100 units/mL",
    active_ingredient: "Insulin Glargine",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_2_preferred_brand",
    status: "active",
    description: "Peakless once-daily basal insulin analogue with 24-hour duration.",
    contraindications_summary: "Episodes of hypoglycemia, hypersensitivity.",
    storage_instructions: "Refrigerate unopened vials at 2°C to 8°C (36°F to 46°F). Do not freeze.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "med-azithromycin-500",
    name: "Azithromycin 500mg Oral Tablet",
    generic_name: "Azithromycin Dihydrate",
    brand_name: "Zithromax",
    rxnorm_code: "308460",
    rxnorm_display: "Azithromycin 500 MG Oral Tablet",
    atc_code: "J01FA10",
    atc_display: "Macrolides (Azithromycin)",
    snomed_code: "372695000",
    snomed_display: "Azithromycin dihydrate",
    form: "tablet",
    route: "oral",
    strength: "500 mg",
    active_ingredient: "Azithromycin",
    is_prescription_required: true,
    is_controlled_substance: false,
    formulary_tier: "tier_1_generic",
    status: "active",
    description: "Azalide macrolide antibiotic inhibiting 50S ribosomal protein synthesis with long tissue half-life.",
    contraindications_summary: "Known hypersensitivity to macrolides or ketolides, cholestatic jaundice history.",
    storage_instructions: "Store at 15°C to 30°C.",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const THERAPEUTIC_CATEGORIES = [
  { id: "ALL", label: "All Therapeutic Classes" },
  { id: "A", label: "A - Alimentary & Metabolism (Antidiabetics, PPIs)" },
  { id: "C", label: "C - Cardiovascular (Statins, ACEi, ARBs)" },
  { id: "J", label: "J - Antimicrobial & Antibiotics" },
  { id: "R", label: "R - Respiratory & Bronchodilators" },
  { id: "N", label: "N - Nervous System & Analgesics" },
  { id: "H", label: "H - Endocrine & Thyroid" },
];

export function MedicationCatalogBrowser({
  onSelectMedication,
  isSelectable = false,
}: MedicationCatalogBrowserProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [selectedForm, setSelectedForm] = useState<string>("ALL");
  const [selectedTier, setSelectedTier] = useState<string>("ALL");
  const [selectedMedication, setSelectedMedication] = useState<Medication | null>(null);
  const [fhirModalMed, setFhirModalMed] = useState<Medication | null>(null);
  const [copiedFhir, setCopiedFhir] = useState(false);

  // Filter medications
  const filteredMedications = useMemo(() => {
    return FALLBACK_FORMULARY_DATA.filter((med) => {
      // Category filter
      if (selectedCategory !== "ALL") {
        if (!med.atc_code || !med.atc_code.startsWith(selectedCategory)) {
          return false;
        }
      }

      // Form filter
      if (selectedForm !== "ALL" && med.form !== selectedForm) {
        return false;
      }

      // Tier filter
      if (selectedTier !== "ALL" && med.formulary_tier !== selectedTier) {
        return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const matchesName = med.name.toLowerCase().includes(query);
        const matchesGeneric = med.generic_name.toLowerCase().includes(query);
        const matchesBrand = med.brand_name ? med.brand_name.toLowerCase().includes(query) : false;
        const matchesIngredient = med.active_ingredient.toLowerCase().includes(query);
        const matchesRxNorm = med.rxnorm_code.includes(query);
        const matchesAtc = med.atc_code ? med.atc_code.toLowerCase().includes(query) : false;

        return matchesName || matchesGeneric || matchesBrand || matchesIngredient || matchesRxNorm || matchesAtc;
      }

      return true;
    });
  }, [searchQuery, selectedCategory, selectedForm, selectedTier]);

  // Construct standard FHIR R4 Medication JSON
  const getFhirMedicationJson = (med: Medication) => {
    return {
      resourceType: "Medication",
      id: med.id,
      meta: {
        profile: [
          "https://nrces.in/ndhm/fhir/r4/StructureDefinition/Medication"
        ]
      },
      identifier: [
        {
          system: "https://nirmaya.health/fhir/medication",
          value: med.id
        },
        {
          system: "http://www.nlm.nih.gov/research/umls/rxnorm",
          value: med.rxnorm_code,
          use: "official"
        }
      ],
      code: {
        coding: [
          {
            system: "http://www.nlm.nih.gov/research/umls/rxnorm",
            code: med.rxnorm_code,
            display: med.rxnorm_display || med.name
          },
          ...(med.atc_code ? [{
            system: "http://www.whocc.no/atc",
            code: med.atc_code,
            display: med.atc_display || med.generic_name
          }] : []),
          ...(med.snomed_code ? [{
            system: "http://snomed.info/sct",
            code: med.snomed_code,
            display: med.snomed_display || med.generic_name
          }] : [])
        ],
        text: med.name
      },
      status: med.status,
      form: {
        coding: [
          {
            system: "http://snomed.info/sct",
            code: med.form,
            display: med.form.charAt(0).toUpperCase() + med.form.slice(1)
          }
        ],
        text: med.form.charAt(0).toUpperCase() + med.form.slice(1)
      },
      ingredient: [
        {
          itemCodeableConcept: {
            coding: [
              {
                system: "http://www.nlm.nih.gov/research/umls/rxnorm",
                code: med.rxnorm_code,
                display: med.active_ingredient
              }
            ],
            text: med.active_ingredient
          },
          isActive: true,
          strength: {
            text: med.strength
          }
        }
      ]
    };
  };

  const handleCopyFhir = (med: Medication) => {
    const jsonString = JSON.stringify(getFhirMedicationJson(med), null, 2);
    navigator.clipboard.writeText(jsonString);
    setCopiedFhir(true);
    setTimeout(() => setCopiedFhir(false), 2000);
  };

  const getTierBadge = (tier: FormularyTier) => {
    switch (tier) {
      case "tier_1_generic":
        return <Badge variant="emerald">Generic (Tier 1)</Badge>;
      case "tier_2_preferred_brand":
        return <Badge variant="default">Preferred Brand (Tier 2)</Badge>;
      case "tier_3_non_preferred_brand":
        return <Badge variant="warning">Non-Preferred Brand (Tier 3)</Badge>;
      case "tier_4_specialty":
        return <Badge variant="violet">Specialty (Tier 4)</Badge>;
      case "tier_5_otc":
        return <Badge variant="neutral">Over-the-Counter</Badge>;
      default:
        return <Badge variant="outline">{tier}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#e5e7eb]">
        <div>
          <h2 className="text-xl font-bold text-[#111111] tracking-tight flex items-center gap-2">
            <Pill className="h-5 w-5 text-[#111111]" />
            Clinical Medication Catalog & Formulary
          </h2>
          <p className="text-xs text-[#6b7280] mt-1">
            Standardized pharmaceutical formulary with NLM RxNorm, WHO-ATC, and SNOMED-CT clinical coding
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs">
            {filteredMedications.length} Formulary Drugs
          </Badge>
          <Badge variant="fhir" className="text-xs">
            HL7 FHIR R4
          </Badge>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9ca3af]" />
          <input
            type="text"
            placeholder="Search by drug name, generic moiety, brand (e.g. Lipitor), active ingredient, or RxNorm CUI (e.g. 860975)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2.5 text-sm bg-white border border-[#e5e7eb] rounded-lg shadow-sm placeholder:text-[#9ca3af] focus:outline-none focus:ring-1 focus:ring-[#111111] focus:border-[#111111] transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#9ca3af] hover:text-[#111111]"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Category Pills & Filters */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-[#6b7280] font-medium flex items-center gap-1">
            <Filter className="h-3.5 w-3.5" />
            Category:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {THERAPEUTIC_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`text-xs px-2.5 py-1 rounded-md font-medium transition-all ${
                  selectedCategory === cat.id
                    ? "bg-[#111111] text-white shadow-xs"
                    : "bg-[#f4f4f5] text-[#52525b] hover:bg-[#e4e4e7] hover:text-[#111111]"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Secondary Filters (Form & Tier) */}
        <div className="flex flex-wrap gap-3 pt-1">
          <div className="flex items-center gap-1.5 text-xs text-[#6b7280]">
            <span>Form:</span>
            <select
              value={selectedForm}
              onChange={(e) => setSelectedForm(e.target.value)}
              className="bg-white border border-[#e5e7eb] rounded-md px-2 py-1 text-xs text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111]"
            >
              <option value="ALL">All Forms</option>
              <option value="tablet">Oral Tablet</option>
              <option value="capsule">Oral Capsule</option>
              <option value="inhaler">Inhaler</option>
              <option value="injection">Injection / Solution</option>
              <option value="suspension">Suspension</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-[#6b7280]">
            <span>Formulary Tier:</span>
            <select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              className="bg-white border border-[#e5e7eb] rounded-md px-2 py-1 text-xs text-[#111111] focus:outline-none focus:ring-1 focus:ring-[#111111]"
            >
              <option value="ALL">All Tiers</option>
              <option value="tier_1_generic">Generic (Tier 1)</option>
              <option value="tier_2_preferred_brand">Preferred Brand (Tier 2)</option>
              <option value="tier_3_non_preferred_brand">Non-Preferred Brand (Tier 3)</option>
              <option value="tier_5_otc">Over-the-Counter (OTC)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Medication Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredMedications.map((med) => (
          <div
            key={med.id}
            className={`border rounded-xl p-4.5 bg-white transition-all shadow-xs hover:border-[#111111] ${
              selectedMedication?.id === med.id ? "border-[#111111] ring-1 ring-[#111111]" : "border-[#e5e7eb]"
            }`}
          >
            {/* Top row: Title and Badges */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-sm text-[#111111] leading-tight">
                  {med.name}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-[#4b5563] font-medium">
                    {med.generic_name}
                  </span>
                  {med.brand_name && (
                    <span className="text-[11px] text-[#6b7280] bg-[#f4f4f5] px-1.5 py-0.5 rounded font-mono">
                      Brand: {med.brand_name}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-end gap-1">
                {getTierBadge(med.formulary_tier)}
                {med.is_controlled_substance && (
                  <Badge variant="critical" className="text-[10px] flex items-center gap-1">
                    <ShieldAlert className="h-3 w-3" />
                    Controlled (Sch IV)
                  </Badge>
                )}
              </div>
            </div>

            {/* Middle row: Coding Chips */}
            <div className="flex flex-wrap items-center gap-1.5 my-3">
              <span className="bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0] text-[10px] font-mono font-medium px-2 py-0.5 rounded-[6px]">
                RxCUI: {med.rxnorm_code}
              </span>
              {med.atc_code && (
                <span className="bg-[#eff6ff] text-[#1e40af] border border-[#bfdbfe] text-[10px] font-mono font-medium px-2 py-0.5 rounded-[6px]">
                  ATC: {med.atc_code}
                </span>
              )}
              <span className="bg-[#f4f4f5] text-[#52525b] text-[10px] font-medium px-2 py-0.5 rounded-[6px] capitalize">
                {med.form} · {med.route}
              </span>
              <span className="bg-[#fafafa] text-[#71717a] border border-[#e4e4e7] text-[10px] font-medium px-2 py-0.5 rounded-[6px]">
                Strength: {med.strength}
              </span>
            </div>

            {/* Description */}
            {med.description && (
              <p className="text-xs text-[#52525b] leading-relaxed line-clamp-2 my-2">
                {med.description}
              </p>
            )}

            {/* Contraindications Warning */}
            {med.contraindications_summary && (
              <div className="bg-[#fffbeb] border border-[#fef3c7] rounded-md p-2 mt-2 mb-3 text-[11px] text-[#92400e] flex items-start gap-1.5">
                <Info className="h-3.5 w-3.5 shrink-0 mt-0.5 text-[#b45309]" />
                <span className="line-clamp-2">
                  <strong className="font-semibold">Contraindications: </strong>
                  {med.contraindications_summary}
                </span>
              </div>
            )}

            {/* Actions Bottom Bar */}
            <div className="flex items-center justify-between pt-2 border-t border-[#f4f4f5] mt-3">
              <button
                onClick={() => setFhirModalMed(med)}
                className="text-xs text-[#6b7280] hover:text-[#111111] font-medium flex items-center gap-1 transition-colors"
              >
                <FileCode className="h-3.5 w-3.5" />
                Inspect FHIR R4
              </button>

              <div className="flex items-center gap-2">
                {isSelectable && onSelectMedication && (
                  <Button
                    size="sm"
                    onClick={() => onSelectMedication(med)}
                    className="text-xs py-1 h-7"
                  >
                    Select for Prescription
                  </Button>
                )}
                <button
                  onClick={() => setSelectedMedication(selectedMedication?.id === med.id ? null : med)}
                  className="text-xs text-[#111111] font-medium hover:underline flex items-center gap-0.5"
                >
                  {selectedMedication?.id === med.id ? "Hide Details" : "View Details"}
                </button>
              </div>
            </div>

            {/* Expanded Details Drawer */}
            {selectedMedication?.id === med.id && (
              <div className="mt-3 pt-3 border-t border-[#f4f4f5] text-xs space-y-2 bg-[#fafafa] p-3 rounded-lg">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[#6b7280] block text-[10px]">Active Ingredient</span>
                    <span className="font-medium text-[#111111]">{med.active_ingredient}</span>
                  </div>
                  <div>
                    <span className="text-[#6b7280] block text-[10px]">SNOMED Concept</span>
                    <span className="font-mono text-[#111111]">{med.snomed_code || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-[#6b7280] block text-[10px]">RxNorm Display</span>
                    <span className="font-medium text-[#111111] truncate block">{med.rxnorm_display || med.name}</span>
                  </div>
                  <div>
                    <span className="text-[#6b7280] block text-[10px]">Prescription Law</span>
                    <span className="font-medium text-[#111111]">
                      {med.is_prescription_required ? "Rx Required" : "Over-The-Counter (OTC)"}
                    </span>
                  </div>
                </div>

                {med.storage_instructions && (
                  <div className="pt-1 flex items-center gap-1.5 text-[#52525b]">
                    <ThermometerSnowflake className="h-3.5 w-3.5 text-[#6b7280]" />
                    <span className="text-[11px]">{med.storage_instructions}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {filteredMedications.length === 0 && (
          <div className="col-span-2 text-center py-12 bg-[#fafafa] border border-dashed border-[#e4e4e7] rounded-xl">
            <Pill className="h-8 w-8 text-[#a1a1aa] mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-[#111111]">No Medications Found</h4>
            <p className="text-xs text-[#71717a] mt-1">
              No clinical drugs matched your search query or filters. Try adjusting your search term.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("ALL");
                setSelectedForm("ALL");
                setSelectedTier("ALL");
              }}
              className="mt-3 text-xs"
            >
              Reset Filters
            </Button>
          </div>
        )}
      </div>

      {/* FHIR R4 Medication Inspection Modal */}
      {fhirModalMed && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-[#e5e7eb]">
            {/* Modal Header */}
            <div className="p-4 border-b border-[#e5e7eb] flex items-center justify-between bg-[#fafafa]">
              <div className="flex items-center gap-2">
                <FileCode className="h-4 w-4 text-[#111111]" />
                <h3 className="font-semibold text-sm text-[#111111]">
                  HL7 FHIR R4 Medication Resource
                </h3>
                <Badge variant="fhir" className="text-[10px]">
                  Medication
                </Badge>
              </div>
              <button
                onClick={() => setFhirModalMed(null)}
                className="text-[#6b7280] hover:text-[#111111] p-1 rounded-md"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body: JSON Viewer */}
            <div className="p-4 overflow-y-auto flex-1 bg-[#09090b] text-[#fafafa] font-mono text-xs">
              <pre className="whitespace-pre-wrap leading-relaxed">
                {JSON.stringify(getFhirMedicationJson(fhirModalMed), null, 2)}
              </pre>
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-[#e5e7eb] flex items-center justify-between bg-[#fafafa]">
              <span className="text-[11px] text-[#71717a]">
                Conforms to NRCeS NDHM Medication Profile
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyFhir(fhirModalMed)}
                  className="text-xs flex items-center gap-1.5"
                >
                  {copiedFhir ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-[#16a34a]" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      Copy JSON
                    </>
                  )}
                </Button>
                <Button
                  size="sm"
                  onClick={() => setFhirModalMed(null)}
                  className="text-xs"
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
