import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Edge Middleware for NIRMAYA:
 * Enforces strict 4-quadrant role boundaries across patient, clinician, laboratory, and administrative portals.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const token = request.cookies.get("nirmaya_token")?.value;
  const role = request.cookies.get("nirmaya_role")?.value?.toLowerCase();

  // If already authenticated and visiting login or register, redirect immediately to their portal
  const isAuthPage = pathname === "/login" || pathname === "/register";
  if (isAuthPage && token && role) {
    const dest =
      role === "doctor"
        ? "/doctor"
        : role === "lab"
        ? "/lab"
        : role === "admin"
        ? "/admin"
        : "/patient";
    return NextResponse.redirect(new URL(dest, request.url));
  }

  // Protected application workspaces
  const isProtectedPortal =
    pathname.startsWith("/patient") ||
    pathname.startsWith("/doctor") ||
    pathname.startsWith("/lab") ||
    pathname.startsWith("/admin");

  if (!isProtectedPortal) {
    return NextResponse.next();
  }

  // 1. Unauthenticated requests are redirected to login with returnUrl
  if (!token || !role) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("returnUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 2. Administrator role has supervisory authorization across all workspaces
  if (role === "admin") {
    return NextResponse.next();
  }

  // 3. Strict 4-Quadrant Partitioning:
  // - Patient / Citizen role is strictly confined to /patient
  if (role === "patient" && !pathname.startsWith("/patient")) {
    return NextResponse.redirect(new URL("/patient", request.url));
  }

  // - Clinician / Doctor role is strictly confined to /doctor
  if (role === "doctor" && !pathname.startsWith("/doctor")) {
    return NextResponse.redirect(new URL("/doctor", request.url));
  }

  // - Laboratory Technician role is strictly confined to /lab
  if (role === "lab" && !pathname.startsWith("/lab")) {
    return NextResponse.redirect(new URL("/lab", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/register",
    "/patient/:path*",
    "/doctor/:path*",
    "/lab/:path*",
    "/admin/:path*",
  ],
};
