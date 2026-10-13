"""Medication catalog, clinical formulary query engine, and starter seed service.

Provides business logic for searching medications by brand/generic name, RxNorm CUI,
WHO-ATC classification, dosage form, administration route, and insurance formulary tiers.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.models.enums import (
    AdministrationRoute,
    FormularyTier,
    MedicationForm,
    MedicationStatus,
)
from app.models.medication import Medication
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    TherapeuticClassSummary,
)


# ============================================================================
# Curated Standard Clinical Formulary Seeds (30 Essential Medications)
# ============================================================================

CLINICAL_FORMULARY_SEEDS: List[Dict[str, Any]] = [
    # --- Antidiabetics (ATC: A10) ---
    {
        "name": "Metformin 500mg Oral Tablet",
        "generic_name": "Metformin Hydrochloride",
        "brand_name": "Glucophage",
        "rxnorm_code": "860975",
        "rxnorm_display": "Metformin hydrochloride 500 MG Oral Tablet",
        "atc_code": "A10BA02",
        "atc_display": "Biguanides (Metformin)",
        "snomed_code": "387048002",
        "snomed_display": "Metformin hydrochloride",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "500 mg",
        "active_ingredient": "Metformin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "First-line biguanide oral antihyperglycemic agent for Type 2 Diabetes Mellitus.",
        "contraindications_summary": "Severe renal impairment (eGFR < 30 mL/min/1.73 m2), acute metabolic acidosis.",
        "storage_instructions": "Store at 20°C to 25°C (68°F to 77°F). Protect from moisture.",
    },
    {
        "name": "Metformin 1000mg Extended Release Tablet",
        "generic_name": "Metformin Hydrochloride",
        "brand_name": "Glucophage XR",
        "rxnorm_code": "861004",
        "rxnorm_display": "Metformin hydrochloride 1000 MG Extended Release Oral Tablet",
        "atc_code": "A10BA02",
        "atc_display": "Biguanides (Metformin XR)",
        "snomed_code": "387048002",
        "snomed_display": "Metformin hydrochloride",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "1000 mg",
        "active_ingredient": "Metformin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Extended-release formulation of metformin for once-daily evening dosing.",
        "contraindications_summary": "Severe renal impairment, acute metabolic acidosis.",
        "storage_instructions": "Store at 20°C to 25°C. Avoid excessive heat.",
    },
    {
        "name": "Glimepiride 2mg Oral Tablet",
        "generic_name": "Glimepiride",
        "brand_name": "Amaryl",
        "rxnorm_code": "197734",
        "rxnorm_display": "Glimepiride 2 MG Oral Tablet",
        "atc_code": "A10BB12",
        "atc_display": "Sulfonylureas (Glimepiride)",
        "snomed_code": "386967008",
        "snomed_display": "Glimepiride",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "2 mg",
        "active_ingredient": "Glimepiride",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Second-generation sulfonylurea insulin secretagogue for Type 2 Diabetes.",
        "contraindications_summary": "Hypersensitivity to sulfonylureas, diabetic ketoacidosis.",
        "storage_instructions": "Store at 15°C to 30°C.",
    },
    {
        "name": "Sitagliptin 100mg Oral Tablet",
        "generic_name": "Sitagliptin Phosphate",
        "brand_name": "Januvia",
        "rxnorm_code": "665042",
        "rxnorm_display": "Sitagliptin 100 MG Oral Tablet",
        "atc_code": "A10BH01",
        "atc_display": "Dipeptidyl peptidase 4 (DPP-4) inhibitors",
        "snomed_code": "423588008",
        "snomed_display": "Sitagliptin phosphate",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "100 mg",
        "active_ingredient": "Sitagliptin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_2_PREFERRED_BRAND,
        "description": "DPP-4 enzyme inhibitor that increases active incretin hormones.",
        "contraindications_summary": "History of serious hypersensitivity or acute pancreatitis.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Insulin Glargine 100 units/mL Subcutaneous Solution",
        "generic_name": "Insulin Glargine (rDNA origin)",
        "brand_name": "Lantus",
        "rxnorm_code": "274786",
        "rxnorm_display": "Insulin Glargine 100 UNT/ML Injectable Solution",
        "atc_code": "A10AE04",
        "atc_display": "Long-acting insulins and analogues",
        "snomed_code": "411529000",
        "snomed_display": "Insulin glargine",
        "form": MedicationForm.INJECTION,
        "route": AdministrationRoute.SUBCUTANEOUS,
        "strength": "100 units/mL",
        "active_ingredient": "Insulin Glargine",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_2_PREFERRED_BRAND,
        "description": "Peakless once-daily basal insulin analogue with 24-hour duration.",
        "contraindications_summary": "Episodes of hypoglycemia, hypersensitivity.",
        "storage_instructions": "Refrigerate unopened vials at 2°C to 8°C (36°F to 46°F). Do not freeze.",
    },

    # --- Cardiovascular & Antihypertensive (ATC: C07, C08, C09, C10) ---
    {
        "name": "Atorvastatin 20mg Oral Tablet",
        "generic_name": "Atorvastatin Calcium",
        "brand_name": "Lipitor",
        "rxnorm_code": "617314",
        "rxnorm_display": "Atorvastatin 20 MG Oral Tablet",
        "atc_code": "C10AA05",
        "atc_display": "HMG-CoA reductase inhibitors (Statins)",
        "snomed_code": "387584000",
        "snomed_display": "Atorvastatin calcium",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "20 mg",
        "active_ingredient": "Atorvastatin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Competitive HMG-CoA reductase inhibitor for hypercholesterolemia and ASCVD risk reduction.",
        "contraindications_summary": "Active liver disease, unexplained persistent elevations in hepatic transaminases, pregnancy.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Atorvastatin 40mg Oral Tablet",
        "generic_name": "Atorvastatin Calcium",
        "brand_name": "Lipitor",
        "rxnorm_code": "617318",
        "rxnorm_display": "Atorvastatin 40 MG Oral Tablet",
        "atc_code": "C10AA05",
        "atc_display": "HMG-CoA reductase inhibitors (Statins)",
        "snomed_code": "387584000",
        "snomed_display": "Atorvastatin calcium",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "40 mg",
        "active_ingredient": "Atorvastatin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "High-intensity statin therapy dose for established atherosclerotic cardiovascular disease.",
        "contraindications_summary": "Active liver disease, pregnancy, concurrent strong CYP3A4 inhibitors.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Lisinopril 10mg Oral Tablet",
        "generic_name": "Lisinopril",
        "brand_name": "Zestril",
        "rxnorm_code": "314076",
        "rxnorm_display": "Lisinopril 10 MG Oral Tablet",
        "atc_code": "C09AA03",
        "atc_display": "ACE inhibitors (Lisinopril)",
        "snomed_code": "386864001",
        "snomed_display": "Lisinopril",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "10 mg",
        "active_ingredient": "Lisinopril",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Angiotensin-converting enzyme (ACE) inhibitor for hypertension and heart failure.",
        "contraindications_summary": "History of angioedema with ACE inhibitors, pregnancy (Boxed Warning), coadministration with aliskiren in diabetes.",
        "storage_instructions": "Store at 20°C to 25°C. Protect from moisture and excessive light.",
    },
    {
        "name": "Amlodipine 5mg Oral Tablet",
        "generic_name": "Amlodipine Besylate",
        "brand_name": "Norvasc",
        "rxnorm_code": "197361",
        "rxnorm_display": "Amlodipine 5 MG Oral Tablet",
        "atc_code": "C08CA01",
        "atc_display": "Dihydropyridine calcium channel blockers",
        "snomed_code": "386864001",
        "snomed_display": "Amlodipine besylate",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "5 mg",
        "active_ingredient": "Amlodipine",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Dihydropyridine calcium channel blocker for essential hypertension and chronic stable angina.",
        "contraindications_summary": "Severe hypotension, cardiogenic shock, hypersensitivity.",
        "storage_instructions": "Store at 15°C to 30°C.",
    },
    {
        "name": "Losartan Potassium 50mg Oral Tablet",
        "generic_name": "Losartan Potassium",
        "brand_name": "Cozaar",
        "rxnorm_code": "979482",
        "rxnorm_display": "Losartan potassium 50 MG Oral Tablet",
        "atc_code": "C09CA01",
        "atc_display": "Angiotensin II receptor blockers (ARBs)",
        "snomed_code": "372658007",
        "snomed_display": "Losartan potassium",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "50 mg",
        "active_ingredient": "Losartan",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Selective AT1 angiotensin receptor antagonist for hypertension and diabetic nephropathy.",
        "contraindications_summary": "Pregnancy (Boxed Warning), concurrent aliskiren in diabetic patients.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Metoprolol Tartrate 50mg Oral Tablet",
        "generic_name": "Metoprolol Tartrate",
        "brand_name": "Lopressor",
        "rxnorm_code": "866414",
        "rxnorm_display": "Metoprolol tartrate 50 MG Oral Tablet",
        "atc_code": "C07AB02",
        "atc_display": "Beta blocking agents, selective (Metoprolol)",
        "snomed_code": "372826007",
        "snomed_display": "Metoprolol tartrate",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "50 mg",
        "active_ingredient": "Metoprolol",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Cardioselective beta-1 adrenergic receptor blocker for hypertension and post-MI angina.",
        "contraindications_summary": "Sinus bradycardia, heart block greater than first degree, cardiogenic shock.",
        "storage_instructions": "Store at 15°C to 30°C.",
    },
    {
        "name": "Telmisartan 40mg Oral Tablet",
        "generic_name": "Telmisartan",
        "brand_name": "Micardis",
        "rxnorm_code": "316672",
        "rxnorm_display": "Telmisartan 40 MG Oral Tablet",
        "atc_code": "C09CA07",
        "atc_display": "Angiotensin II receptor blockers (Telmisartan)",
        "snomed_code": "386884002",
        "snomed_display": "Telmisartan",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "40 mg",
        "active_ingredient": "Telmisartan",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Long-acting ARB with 24-hour hemodynamic control and PPAR-gamma agonist activity.",
        "contraindications_summary": "Pregnancy (Boxed Warning), bilateral renal artery stenosis.",
        "storage_instructions": "Store at 25°C in original blister pack.",
    },

    # --- Antimicrobials & Antibiotics (ATC: J01) ---
    {
        "name": "Amoxicillin 500mg Oral Capsule",
        "generic_name": "Amoxicillin Trihydrate",
        "brand_name": "Amoxil",
        "rxnorm_code": "308182",
        "rxnorm_display": "Amoxicillin 500 MG Oral Capsule",
        "atc_code": "J01CA04",
        "atc_display": "Penicillins with extended spectrum (Amoxicillin)",
        "snomed_code": "372687004",
        "snomed_display": "Amoxicillin trihydrate",
        "form": MedicationForm.CAPSULE,
        "route": AdministrationRoute.ORAL,
        "strength": "500 mg",
        "active_ingredient": "Amoxicillin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Moderate-spectrum bactericidal beta-lactam antibiotic for susceptible bacterial infections.",
        "contraindications_summary": "History of severe allergic reaction (anaphylaxis) to penicillin or beta-lactams.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Amoxicillin-Clavulanate 875mg/125mg Oral Tablet",
        "generic_name": "Amoxicillin Trihydrate and Clavulanate Potassium",
        "brand_name": "Augmentin",
        "rxnorm_code": "308191",
        "rxnorm_display": "Amoxicillin 875 MG / Clavulanate Potassium 125 MG Oral Tablet",
        "atc_code": "J01CR02",
        "atc_display": "Combinations of penicillins, including beta-lactamase inhibitors",
        "snomed_code": "372687004",
        "snomed_display": "Amoxicillin with clavulanic acid",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "875 mg / 125 mg",
        "active_ingredient": "Amoxicillin / Clavulanic Acid",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Beta-lactam antibiotic combined with beta-lactamase inhibitor for resistant infections.",
        "contraindications_summary": "History of amoxicillin-clavulanate-associated cholestatic jaundice or hepatic dysfunction.",
        "storage_instructions": "Store at 20°C to 25°C in tightly closed moisture-resistant container.",
    },
    {
        "name": "Azithromycin 500mg Oral Tablet",
        "generic_name": "Azithromycin Dihydrate",
        "brand_name": "Zithromax",
        "rxnorm_code": "308460",
        "rxnorm_display": "Azithromycin 500 MG Oral Tablet",
        "atc_code": "J01FA10",
        "atc_display": "Macrolides (Azithromycin)",
        "snomed_code": "372695000",
        "snomed_display": "Azithromycin dihydrate",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "500 mg",
        "active_ingredient": "Azithromycin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Azalide macrolide antibiotic inhibiting 50S ribosomal protein synthesis with long tissue half-life.",
        "contraindications_summary": "Known hypersensitivity to macrolides or ketolides, cholestatic jaundice history.",
        "storage_instructions": "Store at 15°C to 30°C.",
    },
    {
        "name": "Ciprofloxacin 500mg Oral Tablet",
        "generic_name": "Ciprofloxacin Hydrochloride",
        "brand_name": "Cipro",
        "rxnorm_code": "309309",
        "rxnorm_display": "Ciprofloxacin 500 MG Oral Tablet",
        "atc_code": "J01MA02",
        "atc_display": "Fluoroquinolones (Ciprofloxacin)",
        "snomed_code": "372722005",
        "snomed_display": "Ciprofloxacin hydrochloride",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "500 mg",
        "active_ingredient": "Ciprofloxacin",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Broad-spectrum fluoroquinolone inhibiting bacterial DNA gyrase and topoisomerase IV.",
        "contraindications_summary": "Concurrent tizanidine, myasthenia gravis (Boxed Warning: tendinitis and tendon rupture).",
        "storage_instructions": "Store below 30°C.",
    },
    {
        "name": "Doxycycline Hyclate 100mg Oral Capsule",
        "generic_name": "Doxycycline Hyclate",
        "brand_name": "Vibramycin",
        "rxnorm_code": "310025",
        "rxnorm_display": "Doxycycline hyclate 100 MG Oral Capsule",
        "atc_code": "J01AA02",
        "atc_display": "Tetracyclines (Doxycycline)",
        "snomed_code": "372750005",
        "snomed_display": "Doxycycline hyclate",
        "form": MedicationForm.CAPSULE,
        "route": AdministrationRoute.ORAL,
        "strength": "100 mg",
        "active_ingredient": "Doxycycline",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Synthetic tetracycline derivative active against a broad range of gram-positive and gram-negative bacteria.",
        "contraindications_summary": "Hypersensitivity to tetracyclines, pregnancy and young children (tooth discoloration).",
        "storage_instructions": "Store at 20°C to 25°C. Protect from light.",
    },

    # --- Respiratory & Bronchodilators (ATC: R03) ---
    {
        "name": "Albuterol 90 mcg/actuation Inhalation Aerosol",
        "generic_name": "Albuterol Sulfate",
        "brand_name": "ProAir HFA",
        "rxnorm_code": "745678",
        "rxnorm_display": "Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler",
        "atc_code": "R03AC02",
        "atc_display": "Selective beta-2 adrenoreceptor agonists (Salbutamol)",
        "snomed_code": "372808003",
        "snomed_display": "Albuterol sulfate",
        "form": MedicationForm.INHALER,
        "route": AdministrationRoute.INHALATION,
        "strength": "90 mcg/actuation",
        "active_ingredient": "Albuterol",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Short-acting selective beta-2 adrenergic receptor agonist (SABA) rescue bronchodilator for acute asthma.",
        "contraindications_summary": "Hypersensitivity to albuterol or propellant ingredients.",
        "storage_instructions": "Store at 20°C to 25°C. Contents under pressure.",
    },
    {
        "name": "Budesonide 0.5mg/2mL Inhalation Suspension",
        "generic_name": "Budesonide",
        "brand_name": "Pulmicort Respules",
        "rxnorm_code": "308889",
        "rxnorm_display": "Budesonide 0.25 MG/ML Inhalation Suspension",
        "atc_code": "R03BA02",
        "atc_display": "Glucocorticoids (Budesonide)",
        "snomed_code": "372814008",
        "snomed_display": "Budesonide",
        "form": MedicationForm.SUSPENSION,
        "route": AdministrationRoute.INHALATION,
        "strength": "0.5 mg / 2 mL",
        "active_ingredient": "Budesonide",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_2_PREFERRED_BRAND,
        "description": "Potent non-halogenated synthetic corticosteroid for maintenance treatment of asthma.",
        "contraindications_summary": "Primary treatment of status asthmaticus, hypersensitivity.",
        "storage_instructions": "Store upright at 20°C to 25°C in aluminum foil envelope.",
    },
    {
        "name": "Montelukast 10mg Oral Tablet",
        "generic_name": "Montelukast Sodium",
        "brand_name": "Singulair",
        "rxnorm_code": "311956",
        "rxnorm_display": "Montelukast 10 MG Oral Tablet",
        "atc_code": "R03DC03",
        "atc_display": "Leukotriene receptor antagonists",
        "snomed_code": "386847000",
        "snomed_display": "Montelukast sodium",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "10 mg",
        "active_ingredient": "Montelukast",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Cysteinyl leukotriene receptor antagonist for prophylaxis and chronic treatment of asthma.",
        "contraindications_summary": "Hypersensitivity (Boxed Warning: neuropsychiatric events).",
        "storage_instructions": "Store at 20°C to 25°C. Protect from moisture and light.",
    },

    # --- Gastrointestinal & Antiulcer (ATC: A02, A04) ---
    {
        "name": "Pantoprazole 40mg Delayed Release Tablet",
        "generic_name": "Pantoprazole Sodium",
        "brand_name": "Protonix",
        "rxnorm_code": "284635",
        "rxnorm_display": "Pantoprazole sodium 40 MG Delayed Release Oral Tablet",
        "atc_code": "A02BC02",
        "atc_display": "Proton pump inhibitors (Pantoprazole)",
        "snomed_code": "386858008",
        "snomed_display": "Pantoprazole sodium",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "40 mg",
        "active_ingredient": "Pantoprazole",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Substituted benzimidazole proton pump inhibitor (PPI) suppressing gastric acid secretion.",
        "contraindications_summary": "Hypersensitivity to substituted benzimidazoles, concurrent rilpivirine.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Omeprazole 20mg Delayed Release Capsule",
        "generic_name": "Omeprazole",
        "brand_name": "Prilosec",
        "rxnorm_code": "312153",
        "rxnorm_display": "Omeprazole 20 MG Delayed Release Oral Capsule",
        "atc_code": "A02BC01",
        "atc_display": "Proton pump inhibitors (Omeprazole)",
        "snomed_code": "386857003",
        "snomed_display": "Omeprazole",
        "form": MedicationForm.CAPSULE,
        "route": AdministrationRoute.ORAL,
        "strength": "20 mg",
        "active_ingredient": "Omeprazole",
        "is_prescription_required": False,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_5_OTC,
        "description": "Irreversible inhibitor of gastric H+/K+-ATPase proton pump for GERD and peptic ulcers.",
        "contraindications_summary": "Hypersensitivity to PPIs, concurrent clopidogrel (CYP2C19 interaction caution).",
        "storage_instructions": "Store at 15°C to 30°C in dry container.",
    },
    {
        "name": "Ondansetron 4mg Oral Disintegrating Tablet",
        "generic_name": "Ondansetron",
        "brand_name": "Zofran ODT",
        "rxnorm_code": "312170",
        "rxnorm_display": "Ondansetron 4 MG Disintegrating Oral Tablet",
        "atc_code": "A04AA01",
        "atc_display": "Serotonin (5HT3) antagonists (Ondansetron)",
        "snomed_code": "372844007",
        "snomed_display": "Ondansetron",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.SUBLINGUAL,
        "strength": "4 mg",
        "active_ingredient": "Ondansetron",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Selective 5-HT3 receptor antagonist antiemetic for chemotherapy-induced or postoperative nausea.",
        "contraindications_summary": "Concurrent apomorphine, congenital long QT syndrome.",
        "storage_instructions": "Store at 2°C to 30°C.",
    },

    # --- Analgesics & Anti-Inflammatory (ATC: N02, M01) ---
    {
        "name": "Paracetamol 500mg Oral Tablet",
        "generic_name": "Acetaminophen",
        "brand_name": "Calpol",
        "rxnorm_code": "198440",
        "rxnorm_display": "Acetaminophen 500 MG Oral Tablet",
        "atc_code": "N02BE01",
        "atc_display": "Anilides (Paracetamol / Acetaminophen)",
        "snomed_code": "387517004",
        "snomed_display": "Acetaminophen",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "500 mg",
        "active_ingredient": "Paracetamol",
        "is_prescription_required": False,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_5_OTC,
        "description": "Centrally acting analgesic and antipyretic for mild to moderate pain and fever.",
        "contraindications_summary": "Severe hepatic impairment or severe active liver disease.",
        "storage_instructions": "Store below 25°C.",
    },
    {
        "name": "Ibuprofen 400mg Oral Tablet",
        "generic_name": "Ibuprofen",
        "brand_name": "Advil",
        "rxnorm_code": "197806",
        "rxnorm_display": "Ibuprofen 400 MG Oral Tablet",
        "atc_code": "M01AE01",
        "atc_display": "Propionic acid derivatives (Ibuprofen)",
        "snomed_code": "387207008",
        "snomed_display": "Ibuprofen",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "400 mg",
        "active_ingredient": "Ibuprofen",
        "is_prescription_required": False,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_5_OTC,
        "description": "Non-steroidal anti-inflammatory drug (NSAID) inhibiting cyclooxygenase COX-1 and COX-2.",
        "contraindications_summary": "Active peptic ulcer, third trimester of pregnancy, perioperative CABG pain.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Tramadol Hydrochloride 50mg Oral Tablet",
        "generic_name": "Tramadol Hydrochloride",
        "brand_name": "Ultram",
        "rxnorm_code": "833734",
        "rxnorm_display": "Tramadol hydrochloride 50 MG Oral Tablet",
        "atc_code": "N02AX02",
        "atc_display": "Other opioids (Tramadol)",
        "snomed_code": "387525002",
        "snomed_display": "Tramadol hydrochloride",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "50 mg",
        "active_ingredient": "Tramadol",
        "is_prescription_required": True,
        "is_controlled_substance": True,
        "formulary_tier": FormularyTier.TIER_3_NON_PREFERRED_BRAND,
        "description": "Centrally acting mu-opioid receptor agonist and weak SNRI reuptake inhibitor.",
        "contraindications_summary": "Significant respiratory depression, acute intoxication with CNS depressants, concurrent MAOIs.",
        "storage_instructions": "Store at 20°C to 25°C. DEA Schedule IV controlled substance.",
    },

    # --- Central Nervous System & Psychiatric (ATC: N05, N06) ---
    {
        "name": "Sertraline Hydrochloride 50mg Oral Tablet",
        "generic_name": "Sertraline Hydrochloride",
        "brand_name": "Zoloft",
        "rxnorm_code": "312940",
        "rxnorm_display": "Sertraline hydrochloride 50 MG Oral Tablet",
        "atc_code": "N06AB06",
        "atc_display": "Selective serotonin reuptake inhibitors (SSRI)",
        "snomed_code": "386899009",
        "snomed_display": "Sertraline hydrochloride",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "50 mg",
        "active_ingredient": "Sertraline",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Selective serotonin reuptake inhibitor (SSRI) for major depressive disorder and panic disorder.",
        "contraindications_summary": "Concurrent MAO inhibitors, pimozide (Boxed Warning: suicidality in young adults).",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Escitalopram 10mg Oral Tablet",
        "generic_name": "Escitalopram Oxalate",
        "brand_name": "Lexapro",
        "rxnorm_code": "352272",
        "rxnorm_display": "Escitalopram 10 MG Oral Tablet",
        "atc_code": "N06AB10",
        "atc_display": "Selective serotonin reuptake inhibitors (Escitalopram)",
        "snomed_code": "386898001",
        "snomed_display": "Escitalopram oxalate",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "10 mg",
        "active_ingredient": "Escitalopram",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Pure S-enantiomer SSRI for major depressive disorder and generalized anxiety disorder (GAD).",
        "contraindications_summary": "Concomitant MAOIs, pimozide, QT prolongation history.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },
    {
        "name": "Alprazolam 0.5mg Oral Tablet",
        "generic_name": "Alprazolam",
        "brand_name": "Xanax",
        "rxnorm_code": "197319",
        "rxnorm_display": "Alprazolam 0.5 MG Oral Tablet",
        "atc_code": "N05BA12",
        "atc_display": "Benzodiazepine derivatives (Alprazolam)",
        "snomed_code": "387143003",
        "snomed_display": "Alprazolam",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "0.5 mg",
        "active_ingredient": "Alprazolam",
        "is_prescription_required": True,
        "is_controlled_substance": True,
        "formulary_tier": FormularyTier.TIER_3_NON_PREFERRED_BRAND,
        "description": "Short-acting triazolobenzodiazepine enhancing GABA inhibitory neurotransmission for panic disorder.",
        "contraindications_summary": "Acute narrow-angle glaucoma, concurrent ketoconazole/itraconazole. DEA Schedule IV.",
        "storage_instructions": "Store at 20°C to 25°C.",
    },

    # --- Endocrine & Thyroid (ATC: H03) ---
    {
        "name": "Levothyroxine Sodium 50mcg Oral Tablet",
        "generic_name": "Levothyroxine Sodium",
        "brand_name": "Synthroid",
        "rxnorm_code": "966222",
        "rxnorm_display": "Levothyroxine sodium 0.05 MG Oral Tablet",
        "atc_code": "H03AA01",
        "atc_display": "Thyroid hormones (Levothyroxine)",
        "snomed_code": "387157007",
        "snomed_display": "Levothyroxine sodium",
        "form": MedicationForm.TABLET,
        "route": AdministrationRoute.ORAL,
        "strength": "50 mcg",
        "active_ingredient": "Levothyroxine",
        "is_prescription_required": True,
        "is_controlled_substance": False,
        "formulary_tier": FormularyTier.TIER_1_GENERIC,
        "description": "Synthetic L-thyroxine (T4) hormone replacement for primary and secondary hypothyroidism.",
        "contraindications_summary": "Uncorrected adrenal cortical insufficiency, untreated thyrotoxicosis.",
        "storage_instructions": "Store at 20°C to 25°C. Protect from moisture and light.",
    },
]


# ============================================================================
# Medication Service Layer Functions
# ============================================================================

async def get_medication_by_id(
    db: AsyncSession,
    medication_id: str,
) -> Medication:
    """Retrieve an individual medication by UUID id or RxNorm CUI code."""
    stmt = select(Medication).where(
        or_(
            Medication.id == medication_id,
            Medication.rxnorm_code == medication_id,
        )
    )
    result = await db.scalar(stmt)
    if not result:
        raise EntityNotFoundException("Medication", medication_id)
    return result


async def search_medications(
    db: AsyncSession,
    q: Optional[str] = None,
    form: Optional[MedicationForm] = None,
    route: Optional[AdministrationRoute] = None,
    tier: Optional[FormularyTier] = None,
    atc_prefix: Optional[str] = None,
    is_prescription_required: Optional[bool] = None,
    is_controlled_substance: Optional[bool] = None,
    status: Optional[MedicationStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Medication], int]:
    """Search and filter the medication catalog with pagination and clinical filters."""
    query = select(Medication)
    count_query = select(func.count(Medication.id))

    filters = []

    # Text search across names, ingredients, codes
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        text_clause = or_(
            func.lower(Medication.name).like(term),
            func.lower(Medication.generic_name).like(term),
            func.lower(Medication.brand_name).like(term),
            func.lower(Medication.active_ingredient).like(term),
            Medication.rxnorm_code.like(term),
            Medication.atc_code.like(term),
        )
        filters.append(text_clause)

    if form:
        filters.append(Medication.form == form)

    if route:
        filters.append(Medication.route == route)

    if tier:
        filters.append(Medication.formulary_tier == tier)

    if atc_prefix and atc_prefix.strip():
        prefix_clean = atc_prefix.strip().upper()
        filters.append(Medication.atc_code.startswith(prefix_clean))

    if is_prescription_required is not None:
        filters.append(Medication.is_prescription_required == is_prescription_required)

    if is_controlled_substance is not None:
        filters.append(Medication.is_controlled_substance == is_controlled_substance)

    if status:
        filters.append(Medication.status == status)

    if filters:
        for f in filters:
            query = query.where(f)
            count_query = count_query.where(f)

    # Ordering: sort by name alphabetically
    query = query.order_by(Medication.name.asc()).limit(limit).offset(offset)

    total_count = await db.scalar(count_query) or 0
    items = list((await db.scalars(query)).all())

    return items, total_count


async def create_medication(
    db: AsyncSession,
    payload: MedicationCreate,
) -> Medication:
    """Create a new medication catalog entry in the formulary."""
    med = Medication(**payload.model_dump())
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med


async def update_medication(
    db: AsyncSession,
    medication_id: str,
    payload: MedicationUpdate,
) -> Medication:
    """Update properties of an existing medication in the formulary."""
    med = await get_medication_by_id(db, medication_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(med, field, value)

    await db.commit()
    await db.refresh(med)
    return med


async def get_therapeutic_classes(db: AsyncSession) -> List[TherapeuticClassSummary]:
    """Aggregate medication counts by high-level WHO-ATC therapeutic classification categories."""
    atc_category_names = {
        "A": "Alimentary tract and metabolism",
        "B": "Blood and blood forming organs",
        "C": "Cardiovascular system",
        "D": "Dermatologicals",
        "G": "Genito-urinary system and sex hormones",
        "H": "Systemic hormonal preparations, excl. sex hormones",
        "J": "Antiinfectives for systemic use",
        "L": "Antineoplastic and immunomodulating agents",
        "M": "Musculo-skeletal system",
        "N": "Nervous system",
        "P": "Antiparasitic products, insecticides and repellents",
        "R": "Respiratory system",
        "S": "Sensory organs",
        "V": "Various",
    }

    # Query distinct ATC codes in catalog
    stmt = select(Medication.atc_code).where(Medication.atc_code.isnot(None))
    results = (await db.scalars(stmt)).all()

    counts: Dict[str, int] = {}
    for code in results:
        if code and len(code) >= 1:
            prefix = code[0].upper()
            counts[prefix] = counts.get(prefix, 0) + 1

    summaries = []
    for prefix, count in sorted(counts.items()):
        name = atc_category_names.get(prefix, f"Category {prefix}")
        summaries.append(
            TherapeuticClassSummary(
                atc_prefix=prefix,
                name=name,
                medication_count=count,
            )
        )

    return summaries


async def seed_medications_if_empty(db: AsyncSession) -> int:
    """Populate initial clinical formulary seeds if the medication table is empty."""
    existing_count = await db.scalar(select(func.count(Medication.id))) or 0
    if existing_count > 0:
        return 0

    seeded = 0
    for seed_data in CLINICAL_FORMULARY_SEEDS:
        med = Medication(**seed_data)
        db.add(med)
        seeded += 1

    await db.commit()
    return seeded
