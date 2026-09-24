import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Edge Middleware for NIRMAYA:
 * Enforces session authentication and clinical role boundaries across portal routes.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protected clinical portals
  const isProtectedPortal =
    pathname.startsWith("/patient") ||
    pathname.startsWith("/doctor") ||
    pathname.startsWith("/lab");

  if (!isProtectedPortal) {
    return NextResponse.next();
  }

  const token = request.cookies.get("nirmaya_token")?.value;
  const role = request.cookies.get("nirmaya_role")?.value?.toLowerCase();

  // If no active auth token exists, redirect to login with returnUrl
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("returnUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Role-boundary guards for specialized clinical workspaces
  if (pathname.startsWith("/doctor") && role === "patient") {
    // Redirect patients trying to access doctor workspace to patient vault
    return NextResponse.redirect(new URL("/patient", request.url));
  }

  if (pathname.startsWith("/patient") && role === "lab") {
    // Redirect lab persona trying to access patient vault to lab gateway
    return NextResponse.redirect(new URL("/lab", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/patient/:path*",
    "/doctor/:path*",
    "/lab/:path*",
  ],
};
