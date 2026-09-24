"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

export type UserRole = "patient" | "doctor" | "lab" | "admin";

export interface AuthUser {
  id: string;
  email: string;
  role: UserRole;
  fullName?: string;
  abhaId?: string;
  hprId?: string;
  isVerified?: boolean;
}

export interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<boolean>;
  loginWithToken: (token: string, user: AuthUser) => void;
  loginAsDemoRole: (role: UserRole) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to set cookies for Next.js Edge Middleware
function setAuthCookies(token: string, role: string) {
  if (typeof document !== "undefined") {
    document.cookie = `nirmaya_token=${token}; path=/; max-age=86400; SameSite=Lax`;
    document.cookie = `nirmaya_role=${role}; path=/; max-age=86400; SameSite=Lax`;
  }
}

function clearAuthCookies() {
  if (typeof document !== "undefined") {
    document.cookie = "nirmaya_token=; path=/; max-age=0; SameSite=Lax";
    document.cookie = "nirmaya_role=; path=/; max-age=0; SameSite=Lax";
  }
}

// Preset clinical demo identities matching backend seed data & ABDM sandbox
export const DEMO_PERSONAS: Record<UserRole, AuthUser> = {
  doctor: {
    id: "doc-ananya-sharma",
    email: "ananya.sharma@aiims.edu",
    role: "doctor",
    fullName: "Dr. Ananya Sharma",
    hprId: "ananya.sharma@hpr.abdm",
    isVerified: true,
  },
  patient: {
    id: "pat-arun-patel",
    email: "arun.patel@example.com",
    role: "patient",
    fullName: "Arun Patel",
    abhaId: "91-8472-1092-4821",
    isVerified: true,
  },
  lab: {
    id: "lab-apollo-delhi",
    email: "diagnostics@apollolabs.com",
    role: "lab",
    fullName: "Apollo Diagnostics Central",
    isVerified: true,
  },
  admin: {
    id: "admin-system-root",
    email: "admin@nirmaya.network",
    role: "admin",
    fullName: "NIRMAYA Root Administrator",
    isVerified: true,
  },
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem("nirmaya_token");
      const storedUser = localStorage.getItem("nirmaya_user");

      if (storedToken && storedUser) {
        const parsedUser = JSON.parse(storedUser) as AuthUser;
        setToken(storedToken);
        setUser(parsedUser);
        setAuthCookies(storedToken, parsedUser.role);
      }
    } catch {
      clearAuthCookies();
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithToken = (newToken: string, newUser: AuthUser) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("nirmaya_token", newToken);
    localStorage.setItem("nirmaya_user", JSON.stringify(newUser));
    setAuthCookies(newToken, newUser.role);
  };

  const login = async (email: string, _password?: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      // Determine if matching a demo persona
      const matchedPersona = Object.values(DEMO_PERSONAS).find(
        (p) => p.email.toLowerCase() === email.toLowerCase()
      );

      const targetRole = matchedPersona ? matchedPersona.role : "patient";
      const targetSub = matchedPersona ? matchedPersona.id : `user-${Date.now()}`;

      // Request signed JWT from backend test-token endpoint
      const response = await apiClient.post<{ access_token: string }>(
        "/api/v1/auth/test-token",
        {
          email,
          role: targetRole,
          sub: targetSub,
          expires_minutes: 120,
        }
      );

      const resolvedUser: AuthUser = matchedPersona || {
        id: targetSub,
        email,
        role: targetRole,
        fullName: email.split("@")[0],
        isVerified: true,
      };

      loginWithToken(response.access_token, resolvedUser);
      return true;
    } catch {
      // Fallback client simulation if backend is not actively responding
      const fallbackUser: AuthUser = {
        id: `sim-${Date.now()}`,
        email,
        role: "patient",
        fullName: email.split("@")[0],
        isVerified: true,
      };
      loginWithToken("simulated-jwt-token-active", fallbackUser);
      return true;
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsDemoRole = async (role: UserRole): Promise<boolean> => {
    const persona = DEMO_PERSONAS[role];
    setIsLoading(true);
    try {
      const response = await apiClient.post<{ access_token: string }>(
        "/api/v1/auth/test-token",
        {
          email: persona.email,
          role: persona.role,
          sub: persona.id,
          expires_minutes: 180,
        }
      );

      loginWithToken(response.access_token, persona);
      return true;
    } catch {
      // Simulated offline token
      loginWithToken(`simulated-jwt-role-${role}`, persona);
      return true;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("nirmaya_token");
    localStorage.removeItem("nirmaya_user");
    clearAuthCookies();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user ? user.role : null,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        loginWithToken,
        loginAsDemoRole,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
