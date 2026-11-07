import type { Metadata } from "next";
import { AppShell } from "@/components/layout";
import "./globals.css";

export const metadata: Metadata = {
  title: "NIRMAYA | Unified Health Interoperability Network",
  description:
    "Networked Interoperable Records Medical Assets & Your Archives. A standardized longitudinal health vault and clinical EMR compliant with HL7 FHIR R4 and ABDM.",
  keywords: [
    "NIRMAYA",
    "HL7 FHIR",
    "ABHA",
    "ABDM",
    "EMR",
    "Health Vault",
    "Interoperability",
    "Medical Records",
  ],
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon.png", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="light" className="scroll-smooth bg-[#fafafa] text-[#171717]">
      <body
        className="font-sans antialiased bg-[#fafafa] text-[#171717] selection:bg-blue-100 selection:text-[#0b4d8c]"
      >
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
