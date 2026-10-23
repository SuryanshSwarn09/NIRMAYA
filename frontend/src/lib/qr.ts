/**
 * ABDM Compliant Vector QR Code Engine
 * Provides client-side SVG and Data URL generation for Digital ABHA ID Cards.
 */

import QRCode from "qrcode";

export interface AbdmQrClaims {
  hidn: string;
  hid: string;
  name: string;
  gender: string;
  dob?: string | null;
  state_name?: string | null;
  dist_name?: string | null;
  mobile?: string | null;
  blood_group?: string | null;
  issue_date?: string;
  signature?: string;
  [key: string]: any;
}

export interface QrRenderOptions {
  width?: number;
  margin?: number;
  color?: {
    dark?: string;
    light?: string;
  };
  errorCorrectionLevel?: "L" | "M" | "Q" | "H";
}

/**
 * Generate a pure vector SVG markup string for a QR code payload.
 * Safe for SSR and client rendering.
 */
export async function generateQrSvgString(
  payload: string,
  options?: QrRenderOptions
): Promise<string> {
  const qrOpts: QRCode.QRCodeToStringOptions = {
    type: "svg",
    errorCorrectionLevel: options?.errorCorrectionLevel || "M",
    margin: options?.margin !== undefined ? options.margin : 1,
    width: options?.width || 256,
    color: {
      dark: options?.color?.dark || "#111111",
      light: options?.color?.light || "#ffffff",
    },
  };

  try {
    return await QRCode.toString(payload, qrOpts);
  } catch (err) {
    console.error("Failed to generate vector QR SVG", err);
    throw err;
  }
}

/**
 * Generate a PNG Data URL (base64) for canvas drawing or file export.
 */
export async function generateQrDataUrl(
  payload: string,
  options?: QrRenderOptions
): Promise<string> {
  const qrOpts: QRCode.QRCodeToDataURLOptions = {
    errorCorrectionLevel: options?.errorCorrectionLevel || "M",
    margin: options?.margin !== undefined ? options.margin : 1,
    width: options?.width || 512,
    color: {
      dark: options?.color?.dark || "#111111",
      light: options?.color?.light || "#ffffff",
    },
  };

  try {
    return await QRCode.toDataURL(payload, qrOpts);
  } catch (err) {
    console.error("Failed to generate QR Data URL", err);
    throw err;
  }
}

/**
 * Encode normalized ABDM patient claims into standardized compact QR JSON string.
 */
export function encodeAbdmQrPayload(claims: AbdmQrClaims): string {
  const normalized: AbdmQrClaims = {
    hidn: claims.hidn,
    hid: claims.hid,
    name: claims.name,
    gender: claims.gender,
    dob: claims.dob || null,
    state_name: claims.state_name || null,
    dist_name: claims.dist_name || null,
    mobile: claims.mobile || null,
    blood_group: claims.blood_group || null,
    issue_date: claims.issue_date || new Date().toISOString(),
    signature: claims.signature,
  };

  return JSON.stringify(normalized);
}

/**
 * Parse and perform client-side structure verification of an ABDM QR string.
 */
export function decodeAbdmQrPayload(qrString: string): {
  isValid: boolean;
  data?: AbdmQrClaims;
  error?: string;
} {
  try {
    const parsed = JSON.parse(qrString);
    if (!parsed || typeof parsed !== "object") {
      return { isValid: false, error: "Payload is not a JSON object" };
    }

    const requiredFields = ["hidn", "hid", "name", "gender"];
    for (const f of requiredFields) {
      if (!parsed[f]) {
        return { isValid: false, error: `Missing mandatory ABDM field: '${f}'` };
      }
    }

    return { isValid: true, data: parsed as AbdmQrClaims };
  } catch (e: any) {
    return { isValid: false, error: `Invalid JSON syntax: ${e.message}` };
  }
}
