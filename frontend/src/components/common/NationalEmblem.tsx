import React from "react";

interface NationalEmblemProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function NationalEmblem({ className = "", size = "md" }: NationalEmblemProps) {
  const sizeMap = {
    sm: "h-6 w-auto",
    md: "h-9 w-auto",
    lg: "h-12 w-auto",
  };

  return (
    <svg
      viewBox="0 0 120 180"
      fill="currentColor"
      aria-label="State Emblem of India (Ashok Stambh)"
      className={`${sizeMap[size]} ${className}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized Four Lions Capital of Ashoka (Sovereign DPI Emblem) */}
      <g fillRule="evenodd" clipRule="evenodd">
        {/* Central Crown & Mane */}
        <path d="M60 12 C52 12, 48 18, 44 24 C40 18, 36 14, 30 16 C25 18, 24 24, 27 30 C30 36, 36 40, 42 42 C40 48, 40 54, 42 60 C44 66, 48 70, 54 72 C56 68, 58 64, 60 64 C62 64, 64 68, 66 72 C72 70, 76 66, 78 60 C80 54, 80 48, 78 42 C84 40, 90 36, 93 30 C96 24, 95 18, 90 16 C84 14, 80 18, 76 24 C72 18, 68 12, 60 12 Z" opacity="0.95" />
        {/* Left Lion Profile */}
        <path d="M38 32 C34 32, 28 35, 25 40 C22 45, 23 52, 27 57 C31 62, 37 64, 41 63 C40 57, 40 50, 41 44 C39 40, 39 36, 38 32 Z" opacity="0.9" />
        {/* Right Lion Profile */}
        <path d="M82 32 C86 32, 92 35, 95 40 C98 45, 97 52, 93 57 C89 62, 83 64, 79 63 C80 57, 80 50, 79 44 C81 40, 81 36, 82 32 Z" opacity="0.9" />
        {/* Abacus Base Platform */}
        <rect x="22" y="74" width="76" height="8" rx="2" />
        {/* Ashoka Chakra in Center of Abacus */}
        <circle cx="60" cy="94" r="12" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="60" cy="94" r="2.5" />
        {/* 24 Spoke Radiants (Representative 8 spokes for clean SVG rendering) */}
        <line x1="60" y1="82" x2="60" y2="106" stroke="currentColor" strokeWidth="1.2" />
        <line x1="48" y1="94" x2="72" y2="94" stroke="currentColor" strokeWidth="1.2" />
        <line x1="51.5" y1="85.5" x2="68.5" y2="102.5" stroke="currentColor" strokeWidth="1.2" />
        <line x1="51.5" y1="102.5" x2="68.5" y2="85.5" stroke="currentColor" strokeWidth="1.2" />
        {/* Galloping Horse (Left) & Bull (Right) silhouette indicators */}
        <path d="M30 92 C32 89, 36 89, 38 92 C39 94, 38 97, 35 97 C32 97, 29 95, 30 92 Z" />
        <path d="M82 92 C84 89, 88 89, 90 92 C91 94, 90 97, 87 97 C84 97, 81 95, 82 92 Z" />
        {/* Inverted Lotus Bell Base */}
        <path d="M26 106 C30 114, 42 120, 60 120 C78 120, 90 114, 94 106 L26 106 Z" />
        <path d="M32 120 C36 128, 46 132, 60 132 C74 132, 84 128, 88 120 L32 120 Z" opacity="0.75" />
        {/* Lower Foundation Plinth */}
        <rect x="18" y="134" width="84" height="6" rx="1.5" />
      </g>
      {/* Satyameva Jayate (सत्यमेव जयते) Inscription */}
      <text
        x="60"
        y="158"
        textAnchor="middle"
        fontSize="11"
        fontWeight="bold"
        fontFamily="serif"
        letterSpacing="1"
      >
        सत्यमेव जयते
      </text>
    </svg>
  );
}
