/**
 * NIRMAYA Navigation Registry and Route Definitions
 */

export interface NavItem {
  title: string;
  href: string;
  badge?: string;
  badgeVariant?: "default" | "verified" | "pending" | "critical" | "fhir" | "abdm";
  description: string;
  role: "public" | "patient" | "doctor" | "lab";
  iconName: "ShieldCheck" | "Stethoscope" | "FlaskConical" | "Database" | "Layers" | "Activity";
}

export const MAIN_NAV_ITEMS: NavItem[] = [
  {
    title: "Patient Vault",
    href: "/patient",
    badge: "Vault",
    badgeVariant: "verified",
    description: "Self-sovereign longitudinal health records & appointment booking",
    role: "patient",
    iconName: "ShieldCheck",
  },
  {
    title: "Provider EMR",
    href: "/doctor",
    badge: "EMR",
    badgeVariant: "fhir",
    description: "Clinical encounters, vitals recording & e-prescriptions",
    role: "doctor",
    iconName: "Stethoscope",
  },
  {
    title: "Diagnostic Gateway",
    href: "/lab",
    badge: "Lab",
    badgeVariant: "abdm",
    description: "Direct upload of test observations & digitally stamped reports",
    role: "lab",
    iconName: "FlaskConical",
  },
  {
    title: "FHIR Standards",
    href: "/fhir",
    badge: "R4",
    badgeVariant: "fhir",
    description: "Interactive HL7 FHIR R4 schema explorer & bundle validator",
    role: "public",
    iconName: "Database",
  },
];

export const FOOTER_SECTIONS = [
  {
    title: "Healthcare Pillars",
    links: [
      { label: "Patient Health Vault", href: "/patient" },
      { label: "Provider (Doctor) EMR", href: "/doctor" },
      { label: "Diagnostic Lab Gateway", href: "/lab" },
      { label: "Longitudinal Timeline", href: "/patient#timeline" },
    ],
  },
  {
    title: "Standards & Compliance",
    links: [
      { label: "HL7 FHIR Release 4", href: "/fhir" },
      { label: "ABDM / ABHA Sandbox", href: "https://sandbox.abdm.gov.in/" },
      { label: "LOINC Clinical Terms", href: "https://loinc.org/" },
      { label: "SNOMED CT Ontology", href: "https://www.snomed.org/" },
    ],
  },
  {
    title: "Academic Project",
    links: [
      { label: "System Architecture", href: "https://github.com/SuryanshSwarn09/NIRMAYA" },
      { label: "GitBook Documentation", href: "https://github.com/SuryanshSwarn09/NIRMAYA/tree/main/docs" },
      { label: "FastAPI Swagger Docs", href: "http://localhost:8000/docs" },
      { label: "Daily Development Log", href: "https://github.com/SuryanshSwarn09/NIRMAYA/blob/main/docs/CHANGELOG.md" },
    ],
  },
];
