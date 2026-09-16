import Link from "next/link";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui";
import { 
  ShieldCheck, 
  Activity, 
  FileSpreadsheet, 
  Stethoscope, 
  FlaskConical, 
  Lock, 
  Share2, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Layers,
  Sparkles,
  ExternalLink
} from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-16 lg:space-y-24 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-12 lg:pt-16 lg:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-50 dark:bg-sky-950/60 border border-sky-200 dark:border-sky-800/80 text-xs font-semibold text-sky-800 dark:text-sky-300 shadow-sm">
              <Layers className="h-4 w-4 text-sky-600 dark:text-sky-400" />
              <span>Ayushman Bharat Digital Mission (ABDM) Compatible Architecture</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.12]">
              Unifying Clinical Data Across the{" "}
              <span className="bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 bg-clip-text text-transparent">
                Healthcare Continuum
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
              NIRMAYA bridges patient health records, provider encounters, and diagnostic laboratories 
              into an interoperable, standard-compliant HL7 FHIR R4 network with consent-driven data ownership.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link href="/patient">
                <Button variant="emerald" size="lg">
                  Access Patient Vault
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/doctor">
                <Button variant="primary" size="lg">
                  <Stethoscope className="h-4 w-4" />
                  Provider EMR Console
                </Button>
              </Link>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline" size="lg">
                  <Database className="h-4 w-4" />
                  FastAPI Swagger
                  <ExternalLink className="h-3.5 w-3.5 opacity-60" />
                </Button>
              </a>
            </div>

            {/* Checklist of Enterprise Guarantees */}
            <div className="pt-8 border-t border-slate-200/80 dark:border-slate-800/80 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs font-medium text-slate-600 dark:text-slate-400">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Zero Data Silos</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Longitudinal History</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>ABHA Identity Linked</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>HL7 FHIR R4 Bundles</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Consent-Driven HIP/HIU</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Sub-ms API Telemetry</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Network Pillars */}
      <section className="py-12 bg-white dark:bg-slate-900/40 border-y border-slate-200/80 dark:border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
            <Badge variant="fhir">Interoperable Ecosystem</Badge>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Three Pillars of the NIRMAYA Network
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-sm sm:text-base">
              Engineered with discrete role permissions, guaranteed data integrity, and compliance at every touchpoint.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Pillar 1: Patient Vault */}
            <Card className="hover:shadow-lg transition-all duration-200 hover:-translate-y-1 flex flex-col justify-between">
              <CardHeader>
                <div className="h-12 w-12 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 flex items-center justify-center mb-4">
                  <ShieldCheck className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between">
                  <CardTitle>Patient Health Vault</CardTitle>
                  <Badge variant="verified">Self-Sovereign</Badge>
                </div>
                <CardDescription>
                  Longitudinal health record locker with full patient consent control.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <div className="flex items-start gap-2">
                  <Activity className="h-4 w-4 text-emerald-600 mt-0.5" />
                  <span>Consolidated timeline of prescriptions, labs, and diagnoses.</span>
                </div>
                <div className="flex items-start gap-2">
                  <Lock className="h-4 w-4 text-emerald-600 mt-0.5" />
                  <span>Granular doctor-level time-bound access delegation.</span>
                </div>
              </CardContent>
              <CardFooter>
                <Link href="/patient" className="w-full">
                  <Button variant="ghost" size="sm" className="w-full justify-between">
                    <span>Enter Vault Portal</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>

            {/* Pillar 2: Doctor EMR */}
            <Card className="hover:shadow-lg transition-all duration-200 hover:-translate-y-1 flex flex-col justify-between">
              <CardHeader>
                <div className="h-12 w-12 rounded-xl bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-400 flex items-center justify-center mb-4">
                  <Stethoscope className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between">
                  <CardTitle>Provider (Doctor) EMR</CardTitle>
                  <Badge variant="fhir">Clinical EMR</Badge>
                </div>
                <CardDescription>
                  High-efficiency clinical workspace for encounter notes and prescriptions.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <div className="flex items-start gap-2">
                  <Share2 className="h-4 w-4 text-sky-600 mt-0.5" />
                  <span>Instant access to verified patient past medical history.</span>
                </div>
                <div className="flex items-start gap-2">
                  <FileSpreadsheet className="h-4 w-4 text-sky-600 mt-0.5" />
                  <span>Structured e-prescriptions generating FHIR MedicationRequests.</span>
                </div>
              </CardContent>
              <CardFooter>
                <Link href="/doctor" className="w-full">
                  <Button variant="ghost" size="sm" className="w-full justify-between">
                    <span>Open EMR Console</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>

            {/* Pillar 3: Diagnostic Gateway */}
            <Card className="hover:shadow-lg transition-all duration-200 hover:-translate-y-1 flex flex-col justify-between">
              <CardHeader>
                <div className="h-12 w-12 rounded-xl bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 flex items-center justify-center mb-4">
                  <FlaskConical className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between">
                  <CardTitle>Diagnostic Gateway</CardTitle>
                  <Badge variant="abdm">Lab Portal</Badge>
                </div>
                <CardDescription>
                  Direct ingest portal for accredited laboratories and imaging centers.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <div className="flex items-start gap-2">
                  <Activity className="h-4 w-4 text-indigo-600 mt-0.5" />
                  <span>Dual upload: Cryptographic PDF + Structured FHIR Observations.</span>
                </div>
                <div className="flex items-start gap-2">
                  <Database className="h-4 w-4 text-indigo-600 mt-0.5" />
                  <span>Automated linkage to Patient ABHA identifier and vault.</span>
                </div>
              </CardContent>
              <CardFooter>
                <Link href="/lab" className="w-full">
                  <Button variant="ghost" size="sm" className="w-full justify-between">
                    <span>Access Lab Gateway</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          </div>
        </div>
      </section>

      {/* Standards Architecture Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-gradient-to-tr from-slate-900 via-slate-800 to-sky-950 p-8 sm:p-12 text-white shadow-xl relative overflow-hidden">
          <div className="max-w-2xl space-y-4 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-xs font-semibold text-sky-200 backdrop-blur-md">
              <Sparkles className="h-3.5 w-3.5 text-sky-300" />
              <span>HL7 FHIR Release 4 Compliance Engine</span>
            </div>
            <h3 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Enterprise Interoperability Across All FHIR Clinical Schemas
            </h3>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Every appointment, prescription, and diagnostic report in NIRMAYA is automatically transformed 
              into standard FHIR JSON resources (`Patient`, `Practitioner`, `Encounter`, `Observation`, `MedicationRequest`, and `DiagnosticReport`).
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <Link href="/fhir">
                <Button variant="emerald" size="md">
                  Explore FHIR Mappings
                </Button>
              </Link>
              <a
                href="https://github.com/SuryanshSwarn09/NIRMAYA"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline" size="md" className="border-white/20 text-white hover:bg-white/10">
                  View Architecture Docs
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
