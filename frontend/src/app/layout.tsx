import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { AppShell } from "@/components/layout";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600"],
});

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
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth bg-white text-[#111111]">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased bg-white text-[#111111] selection:bg-slate-200 selection:text-black`}
      >
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
