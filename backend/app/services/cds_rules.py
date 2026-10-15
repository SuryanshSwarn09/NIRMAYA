"""Clinical Decision Support (CDS) Rules and Pharmacological Interaction Matrix.

Defines the knowledge base and rule evaluation engines for:
1. Drug-Drug Interactions (DDI) with severity grading (Critical, Major, Moderate).
2. Drug-Allergy & Cross-Sensitivity Detection (Beta-lactams, Sulfas, NSAIDs).
3. Drug-Condition Contraindications (Renal Disease, Peptic Ulcer, Severe Asthma).
"""

from dataclasses import dataclass
from typing import List, Optional, Set

from app.models.enums import CDSAlertType, CDSSeverity


@dataclass(frozen=True)
class DrugDrugInteractionRule:
    """Pharmacological interaction rule between two drug substance classes."""

    rule_id: str
    substance_a: str
    matches_a: List[str]
    substance_b: str
    matches_b: List[str]
    severity: CDSSeverity
    title: str
    mechanism: str
    recommendation: str


@dataclass(frozen=True)
class AllergyRule:
    """Allergy and hypersensitivity cross-reactivity rule."""

    allergen_family: str
    allergen_keywords: List[str]
    drug_keywords: List[str]
    severity: CDSSeverity
    title: str
    mechanism: str
    recommendation: str


@dataclass(frozen=True)
class ConditionContraindicationRule:
    """Clinical condition contraindication rule."""

    condition_keywords: List[str]
    drug_keywords: List[str]
    severity: CDSSeverity
    title: str
    mechanism: str
    recommendation: str


# ==============================================================================
# 1. CURATED CLINICAL DRUG-DRUG INTERACTION (DDI) RULES MATRIX
# ==============================================================================

DDI_RULES: List[DrugDrugInteractionRule] = [
    # 1. Warfarin + Aspirin / NSAIDs
    DrugDrugInteractionRule(
        rule_id="DDI-001",
        substance_a="Warfarin",
        matches_a=["warfarin", "coumadin", "jantoven"],
        substance_b="NSAIDs / Antiplatelets",
        matches_b=[
            "aspirin",
            "ibuprofen",
            "diclofenac",
            "naproxen",
            "ketorolac",
            "indomethacin",
            "meloxicam",
            "piroxicam",
            "celecoxib",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Critical Hemorrhage Risk: Warfarin & NSAID/Aspirin",
        mechanism=(
            "Concurrent administration of Warfarin with NSAIDs or Aspirin causes synergistic "
            "inhibition of platelet aggregation and induces gastric mucosal injury, dramatically "
            "elevating the risk of fatal gastrointestinal and systemic hemorrhage."
        ),
        recommendation=(
            "Avoid concurrent administration. If analgesic therapy is required, prefer Acetaminophen/Paracetamol "
            "or non-NSAID options with strict International Normalized Ratio (INR) monitoring."
        ),
    ),
    # 2. ACE Inhibitors / ARBs + Potassium-Sparing Diuretics
    DrugDrugInteractionRule(
        rule_id="DDI-002",
        substance_a="ACE Inhibitors / ARBs",
        matches_a=[
            "ramipril",
            "enalapril",
            "lisinopril",
            "captopril",
            "benazepril",
            "losartan",
            "telmisartan",
            "valsartan",
            "candesartan",
            "olmesartan",
        ],
        substance_b="Potassium-Sparing Diuretics & Aldosterone Antagonists",
        matches_b=[
            "spironolactone",
            "eplerenone",
            "amiloride",
            "triamterene",
            "potassium chloride",
        ],
        severity=CDSSeverity.MAJOR,
        title="Severe Hyperkalemia Risk: Renin-Angiotensin Blocker & Potassium-Sparing Agent",
        mechanism=(
            "Combining ACE inhibitors or Angiotensin Receptor Blockers (ARBs) with potassium-sparing diuretics "
            "blocks aldosterone-mediated renal potassium excretion, inducing life-threatening hyperkalemia "
            "and fatal cardiac arrhythmias."
        ),
        recommendation=(
            "Monitor serum potassium and creatinine within 1-2 weeks of co-administration. Avoid concurrent "
            "routine potassium supplements unless hypokalemia is clinically documented."
        ),
    ),
    # 3. Metformin + Iodinated Radiocontrast
    DrugDrugInteractionRule(
        rule_id="DDI-003",
        substance_a="Metformin",
        matches_a=["metformin", "glucophage", "glycomet"],
        substance_b="Iodinated Radiocontrast Agents",
        matches_b=[
            "iodinated",
            "iohexol",
            "iopamidol",
            "iodixanol",
            "contrast",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Fatal Lactic Acidosis Risk: Metformin & Iodinated Contrast",
        mechanism=(
            "Intravascular administration of iodinated radiocontrast media can trigger acute contrast-induced "
            "nephropathy (CIN), impairing metformin renal clearance and precipitating fatal metformin-associated "
            "lactic acidosis (MALA)."
        ),
        recommendation=(
            "Withhold metformin at the time of or prior to iodinated radiocontrast imaging. Re-evaluate renal function "
            "(eGFR) 48 hours post-procedure before resuming metformin therapy."
        ),
    ),
    # 4. Clopidogrel + Omeprazole / Esomeprazole
    DrugDrugInteractionRule(
        rule_id="DDI-004",
        substance_a="Clopidogrel",
        matches_a=["clopidogrel", "plavix"],
        substance_b="CYP2C19 Inhibiting Proton Pump Inhibitors",
        matches_b=["omeprazole", "esomeprazole", "prilosec", "nexium"],
        severity=CDSSeverity.MAJOR,
        title="Reduced Antiplatelet Efficacy: Clopidogrel & Omeprazole",
        mechanism=(
            "Omeprazole and esomeprazole competitively inhibit cytochrome P450 2C19 (CYP2C19), the principal hepatic "
            "enzyme required to bioactivate clopidogrel into its active thiol metabolite, increasing the risk of recurrent "
            "thrombosis and stent occlusion."
        ),
        recommendation=(
            "Avoid omeprazole/esomeprazole with clopidogrel. Consider alternative gastroprotective agents that have "
            "minimal CYP2C19 inhibition, such as Pantoprazole or H2-receptor antagonists (Famotidine)."
        ),
    ),
    # 5. SSRIs / SNRIs + Tramadol
    DrugDrugInteractionRule(
        rule_id="DDI-005",
        substance_a="Serotonergic Antidepressants (SSRIs / SNRIs)",
        matches_a=[
            "fluoxetine",
            "sertraline",
            "paroxetine",
            "citalopram",
            "escitalopram",
            "venlafaxine",
            "duloxetine",
        ],
        substance_b="Tramadol",
        matches_b=["tramadol", "ultram"],
        severity=CDSSeverity.MAJOR,
        title="Serotonin Syndrome & Seizure Risk: SSRI/SNRI & Tramadol",
        mechanism=(
            "Tramadol inhibits serotonin and norepinephrine reuptake. Concurrent use with SSRIs or SNRIs synergistically "
            "enhances central serotonergic transmission, triggering life-threatening Serotonin Syndrome and significantly "
            "lowering the seizure threshold."
        ),
        recommendation=(
            "Exercise extreme caution or select an alternative analgesic. Counsel patient to immediately report neuromuscular "
            "hyperactivity (clonus, hyperreflexia), autonomic instability (hyperthermia, tachycardia), or altered mental status."
        ),
    ),
    # 6. Statins + Strong CYP3A4 Inhibitors
    DrugDrugInteractionRule(
        rule_id="DDI-006",
        substance_a="CYP3A4-Metabolized Statins",
        matches_a=["simvastatin", "atorvastatin", "lovastatin"],
        substance_b="Strong CYP3A4 Inhibitors (Macrolides / Azoles)",
        matches_b=[
            "clarithromycin",
            "erythromycin",
            "ketoconazole",
            "itraconazole",
            "voriconazole",
            "posaconazole",
        ],
        severity=CDSSeverity.MAJOR,
        title="Severe Rhabdomyolysis Risk: Statin & Strong CYP3A4 Inhibitor",
        mechanism=(
            "Potent CYP3A4 inhibitors markedly increase systemic exposure to CYP3A4-metabolized statins by blocking hepatic "
            "clearance, substantially raising the risk of severe skeletal muscle toxicity and acute rhabdomyolysis."
        ),
        recommendation=(
            "Temporarily suspend simvastatin or atorvastatin during short-course macrolide or azole antifungal therapy, "
            "or switch to a non-CYP3A4 statin (such as Rosuvastatin or Pravastatin) with dose limits."
        ),
    ),
    # 7. Methotrexate + Penicillins / NSAIDs
    DrugDrugInteractionRule(
        rule_id="DDI-007",
        substance_a="Methotrexate",
        matches_a=["methotrexate", "trexall"],
        substance_b="Penicillins & NSAIDs",
        matches_b=[
            "amoxicillin",
            "ampicillin",
            "penicillin",
            "piperacillin",
            "ibuprofen",
            "naproxen",
            "diclofenac",
            "indomethacin",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Severe Bone Marrow Toxicity Risk: Methotrexate & Penicillins/NSAIDs",
        mechanism=(
            "Penicillins and NSAIDs compete with methotrexate for renal organic anion transporter (OAT) tubular secretion, "
            "causing acute methotrexate retention, prolonged serum half-life, and potentially fatal myelosuppression, pancytopenia, "
            "and mucosal ulceration."
        ),
        recommendation=(
            "Avoid concurrent administration. If antibiotic coverage is required in a patient on methotrexate, choose non-penicillin "
            "classes, and strictly monitor complete blood counts and renal function."
        ),
    ),
    # 8. Levothyroxine + Multivalent Cations (Calcium / Iron)
    DrugDrugInteractionRule(
        rule_id="DDI-008",
        substance_a="Levothyroxine",
        matches_a=["levothyroxine", "eltroxin", "synthroid"],
        substance_b="Multivalent Cation Supplements",
        matches_b=[
            "calcium carbonate",
            "calcium",
            "ferrous sulfate",
            "ferrous fumarate",
            "iron",
            "aluminum hydroxide",
            "sucralfate",
        ],
        severity=CDSSeverity.MODERATE,
        title="Reduced Absorption: Levothyroxine & Calcium/Iron Cations",
        mechanism=(
            "Multivalent metal cations form insoluble, non-absorbable chelates with levothyroxine within the gastrointestinal "
            "tract, substantially impairing thyroid hormone bioavailability and precipitating clinical hypothyroidism."
        ),
        recommendation=(
            "Separate administration times by at least 4 hours. Instruct patient to take Levothyroxine on an empty stomach "
            "in the morning and mineral supplements later in the afternoon."
        ),
    ),
    # 9. Digoxin + Amiodarone
    DrugDrugInteractionRule(
        rule_id="DDI-009",
        substance_a="Digoxin",
        matches_a=["digoxin", "lanoxin"],
        substance_b="P-Glycoprotein Inhibitors (Amiodarone / Verapamil)",
        matches_b=["amiodarone", "cordarone", "verapamil"],
        severity=CDSSeverity.MAJOR,
        title="Severe Digitalis Toxicity Risk: Digoxin & Amiodarone/Verapamil",
        mechanism=(
            "Amiodarone and Verapamil inhibit P-glycoprotein (P-gp) and renal tubular clearance of digoxin, typically doubling "
            "digoxin serum concentrations and precipitating fatal ventricular arrhythmias and heart block."
        ),
        recommendation=(
            "Empirically reduce digoxin dose by 50% upon initiating amiodarone. Frequently monitor serum digoxin levels, "
            "potassium, and ECG for signs of digitalis toxicity."
        ),
    ),
    # 10. Fluoroquinolones + Theophylline
    DrugDrugInteractionRule(
        rule_id="DDI-010",
        substance_a="Fluoroquinolones",
        matches_a=["ciprofloxacin", "cipro", "norfloxacin", "enoxacin"],
        substance_b="Theophylline",
        matches_b=["theophylline", "theobid", "theo-24", "aminophylline"],
        severity=CDSSeverity.MAJOR,
        title="Severe Neurotoxicity Risk: Ciprofloxacin & Theophylline",
        mechanism=(
            "Ciprofloxacin is a potent inhibitor of hepatic cytochrome P450 1A2 (CYP1A2), significantly decreasing theophylline "
            "metabolic clearance and leading to severe toxic theophylline accumulation, nausea, tachycardia, and grand mal seizures."
        ),
        recommendation=(
            "Avoid co-administration when possible. If ciprofloxacin is mandatory, decrease theophylline dose by 50% "
            "and conduct daily serum theophylline level monitoring."
        ),
    ),
]


# ==============================================================================
# 2. ALLERGY & CROSS-REACTIVITY RULES
# ==============================================================================

ALLERGY_RULES: List[AllergyRule] = [
    AllergyRule(
        allergen_family="Beta-Lactam / Penicillin",
        allergen_keywords=["penicillin", "amoxicillin", "ampicillin", "beta-lactam", "penam"],
        drug_keywords=[
            "amoxicillin",
            "ampicillin",
            "penicillin",
            "piperacillin",
            "augmentin",
            "amoxicillin-clavulanate",
            "cloxacillin",
            "flucloxacillin",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Severe Penicillin / Beta-Lactam Hypersensitivity Risk",
        mechanism=(
            "Patient has a documented beta-lactam / penicillin allergy. Administration of penicillin-class "
            "antibiotics carries high risk of type I IgE-mediated anaphylaxis, angioedema, and bronchospasm."
        ),
        recommendation=(
            "Discontinue candidate drug. Prescribe a non-beta-lactam alternative antibiotic "
            "(e.g., Macrolides such as Azithromycin, Fluoroquinolones, or Glycopeptides depending on infection)."
        ),
    ),
    AllergyRule(
        allergen_family="Sulfonamide",
        allergen_keywords=["sulfa", "sulfonamide", "bactrim", "septra"],
        drug_keywords=[
            "sulfamethoxazole",
            "trimethoprim-sulfamethoxazole",
            "co-trimoxazole",
            "sulfasalazine",
            "sulfadiazine",
            "celecoxib",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Severe Sulfonamide Hypersensitivity Risk",
        mechanism=(
            "Patient has a documented sulfonamide allergy. Administration of sulfa antibiotics or derivatives "
            "carries risk of severe cutaneous adverse reactions (SCAR), including Stevens-Johnson Syndrome (SJS) "
            "and Toxic Epidermal Necrolysis (TEN)."
        ),
        recommendation=(
            "Do not administer sulfonamide-containing agents. Select alternative antimicrobial therapy."
        ),
    ),
    AllergyRule(
        allergen_family="NSAID / Aspirin",
        allergen_keywords=["aspirin", "nsaid", "ibuprofen", "diclofenac", "naproxen"],
        drug_keywords=[
            "aspirin",
            "ibuprofen",
            "diclofenac",
            "naproxen",
            "ketorolac",
            "indomethacin",
            "meloxicam",
            "piroxicam",
            "celecoxib",
        ],
        severity=CDSSeverity.MAJOR,
        title="NSAID Hypersensitivity Cross-Reactivity Risk",
        mechanism=(
            "Patient has a documented hypersensitivity to NSAIDs or Aspirin. Administration can trigger "
            "aspirin-exacerbated respiratory disease (AERD), severe bronchospasm, or generalized urticaria."
        ),
        recommendation=(
            "Avoid all cyclooxygenase-1 (COX-1) inhibitors. Use Acetaminophen/Paracetamol for mild pain or "
            "consult clinical specialist for desensitization protocols."
        ),
    ),
]


# ==============================================================================
# 3. CONDITION CONTRAINDICATION RULES
# ==============================================================================

CONDITION_RULES: List[ConditionContraindicationRule] = [
    # 1. Chronic Kidney Disease / Renal Failure + NSAIDs
    ConditionContraindicationRule(
        condition_keywords=[
            "chronic kidney disease",
            "ckd",
            "renal failure",
            "renal impairment",
            "kidney injury",
            "nephropathy",
            "end stage renal",
        ],
        drug_keywords=[
            "ibuprofen",
            "diclofenac",
            "naproxen",
            "ketorolac",
            "indomethacin",
            "meloxicam",
            "piroxicam",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Acute Renal Decompensation: NSAID in Chronic Kidney Disease",
        mechanism=(
            "NSAIDs inhibit renal prostaglandin E2 synthesis, precipitating severe afferent arteriolar "
            "vasoconstriction, acute reduction in glomerular filtration rate (GFR), and accelerated renal failure."
        ),
        recommendation=(
            "Strictly avoid systemic NSAIDs in patients with renal impairment. Use non-nephrotoxic alternatives "
            "(e.g., Acetaminophen/Paracetamol with appropriate dosage limits)."
        ),
    ),
    # 2. Peptic Ulcer Disease + NSAIDs / Systemic Corticosteroids
    ConditionContraindicationRule(
        condition_keywords=[
            "peptic ulcer",
            "gastric ulcer",
            "duodenal ulcer",
            "gi bleeding",
            "gastrointestinal hemorrhage",
            "hematemesis",
            "melena",
        ],
        drug_keywords=[
            "aspirin",
            "ibuprofen",
            "diclofenac",
            "naproxen",
            "ketorolac",
            "prednisolone",
            "dexamethasone",
            "hydrocortisone",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Gastrointestinal Perforation & Bleeding Risk: Peptic Ulcer Disease",
        mechanism=(
            "Cyclooxygenase-1 inhibition decreases protective gastric mucus and bicarbonate secretion, "
            "while corticosteroids impair mucosal healing, dramatically increasing the risk of active ulcer "
            "perforation and life-threatening gastrointestinal hemorrhage."
        ),
        recommendation=(
            "Contraindicated in active peptic ulcer disease. If anti-inflammatory therapy is critical, "
            "provide aggressive proton pump inhibitor (PPI) co-therapy under gastroenterology supervision."
        ),
    ),
    # 3. Severe Asthma + Non-Selective Beta-Blockers
    ConditionContraindicationRule(
        condition_keywords=[
            "asthma",
            "bronchospasm",
            "reactive airway",
            "bronchial asthma",
        ],
        drug_keywords=[
            "propranolol",
            "timolol",
            "nadolol",
            "sotalol",
            "carvedilol",
            "labetalol",
        ],
        severity=CDSSeverity.CRITICAL,
        title="Fatal Bronchospasm Risk: Non-Selective Beta-Blocker in Asthma",
        mechanism=(
            "Non-selective beta-adrenergic antagonists block bronchial beta-2 receptors, eliminating sympathetic "
            "bronchodilation and triggering severe, refractory bronchospasm that is poorly responsive to beta-agonist rescue."
        ),
        recommendation=(
            "Contraindicated in patients with active asthma or history of severe bronchospasm. Select cardioselective "
            "beta-1 blockers (e.g. Bisoprolol, Metoprolol) with extreme caution, or alternative antihypertensive classes."
        ),
    ),
]


# ==============================================================================
# 4. RULE EVALUATION ENGINE
# ==============================================================================

def normalize_text(text: Optional[str]) -> str:
    """Normalize drug or condition text for fuzzy lowercase matching."""
    if not text:
        return ""
    return text.strip().lower()


def evaluate_drug_drug_interactions(
    candidate_drug_name: str,
    active_drug_names: List[str],
) -> List[dict]:
    """Evaluate a candidate medication against active patient medications for known DDIs."""
    alerts: List[dict] = []
    cand_norm = normalize_text(candidate_drug_name)

    for active_med in active_drug_names:
        act_norm = normalize_text(active_med)
        if not act_norm or act_norm == cand_norm:
            continue

        for rule in DDI_RULES:
            # Check candidate in group A and active in group B
            cand_in_a = any(m in cand_norm for m in rule.matches_a)
            act_in_b = any(m in act_norm for m in rule.matches_b)

            # Check candidate in group B and active in group A
            cand_in_b = any(m in cand_norm for m in rule.matches_b)
            act_in_a = any(m in act_norm for m in rule.matches_a)

            if (cand_in_a and act_in_b) or (cand_in_b and act_in_a):
                alerts.append({
                    "rule_id": rule.rule_id,
                    "alert_type": CDSAlertType.DRUG_DRUG.value,
                    "severity": rule.severity.value,
                    "title": rule.title,
                    "offending_entity": active_med,
                    "mechanism": rule.mechanism,
                    "recommendation": rule.recommendation,
                })

    return alerts


def evaluate_allergy_cross_sensitivity(
    candidate_drug_name: str,
    patient_allergies: List[str],
) -> List[dict]:
    """Evaluate candidate medication against patient documented allergies."""
    alerts: List[dict] = []
    cand_norm = normalize_text(candidate_drug_name)

    for allergy in patient_allergies:
        all_norm = normalize_text(allergy)
        if not all_norm:
            continue

        for rule in ALLERGY_RULES:
            allergy_match = any(k in all_norm for k in rule.allergen_keywords)
            drug_match = any(k in cand_norm for k in rule.drug_keywords)

            if allergy_match and drug_match:
                alerts.append({
                    "rule_id": f"ALLERGY-{rule.allergen_family.replace(' ', '-').upper()}",
                    "alert_type": CDSAlertType.DRUG_ALLERGY.value,
                    "severity": rule.severity.value,
                    "title": rule.title,
                    "offending_entity": allergy,
                    "mechanism": rule.mechanism,
                    "recommendation": rule.recommendation,
                })

    return alerts


def evaluate_condition_contraindications(
    candidate_drug_name: str,
    active_conditions: List[str],
) -> List[dict]:
    """Evaluate candidate medication against patient active clinical conditions."""
    alerts: List[dict] = []
    cand_norm = normalize_text(candidate_drug_name)

    for condition in active_conditions:
        cond_norm = normalize_text(condition)
        if not cond_norm:
            continue

        for idx, rule in enumerate(CONDITION_RULES, start=1):
            cond_match = any(k in cond_norm for k in rule.condition_keywords)
            drug_match = any(k in cand_norm for k in rule.drug_keywords)

            if cond_match and drug_match:
                alerts.append({
                    "rule_id": f"COND-{idx:03d}",
                    "alert_type": CDSAlertType.DRUG_CONDITION.value,
                    "severity": rule.severity.value,
                    "title": rule.title,
                    "offending_entity": condition,
                    "mechanism": rule.mechanism,
                    "recommendation": rule.recommendation,
                })

    return alerts
