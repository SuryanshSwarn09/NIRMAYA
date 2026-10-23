# Week 7: Patient Portal Frontend, ABHA Card & Telemedicine

**Milestone Target:** Develop and integrate the responsive Patient Portal UI in Next.js 15, Cal.com design system patient health vault, interactive ABHA ID Card generator with QR payload, vitals telemetry visualizations, and WebRTC consultation prep.

---

## Daily Schedule & Architectural Focus

| Day | Focus Area | Planned Deliverables | Status |
|---|---|---|---|
| **Day 31** | Patient Portal App Shell & Layout | Patient dashboard layout, navigation drawer, Cal.com clinical tokens | **Completed** |
| **Day 32** | ABHA ID Card Generator & QR | Digital ABHA Card canvas, QR code payload renderer, SVG export | **Completed** |
| **Day 33** | Problem List & Active Conditions UI | Patient-facing problem list, SNOMED CT condition badges, clinical cards | **Completed** |
| **Day 34** | Vitals Telemetry & Observational Charts | Recharts vital sign tracking (Blood Pressure, SpO2, Heart Rate, BMI) | Planned |
| **Day 35** | E2E Patient Portal Verification | Playwright integration tests, responsive verification, and sprint review | Planned |

---

## Architectural Highlights

- **Cal.com Clean Aesthetics:** Minimalist border styling (`border-[#E1E1E1]`), `#FFFFFF` canvas, and `#111111` typography.
- **ABHA QR Verification:** Standards-compliant QR payload encoding ABHA Number, ABHA Address, Name, and cryptographic signature.
- **Longitudinal Telemetry:** Visual time-series charts displaying patient vitals mapped to LOINC clinical codes.
