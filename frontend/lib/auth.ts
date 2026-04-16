"use client";

import { useEffect, useState } from "react";
import { AuthUser } from "@/lib/types";

const AUTH_STORAGE_KEY = "hotel_booking_auth";

export type AuthState = {
  token: string;
  user: AuthUser;
};

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) {
      return null;
    }

    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const decoded = window.atob(padded);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload) {
    return true;
  }

  const exp = payload.exp;
  if (typeof exp !== "number") {
    // Treat tokens without exp as invalid for protected flows.
    return true;
  }

  const nowInSeconds = Math.floor(Date.now() / 1000);
  return exp <= nowInSeconds;
}

function isValidAuthState(value: unknown): value is AuthState {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<AuthState>;
  if (typeof candidate.token !== "string" || !candidate.token.trim()) {
    return false;
  }

  if (!candidate.user || typeof candidate.user !== "object") {
    return false;
  }

  const user = candidate.user as Partial<AuthUser>;
  return typeof user.id === "string" && typeof user.email === "string";
}

export function getAuthState(): AuthState | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isValidAuthState(parsed)) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }

    if (isTokenExpired(parsed.token)) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }

    return parsed;
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function saveAuthState(auth: AuthState) {
  if (typeof window === "undefined") {
    return;
  }

  if (isTokenExpired(auth.token)) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

export function clearAuthState() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    queueMicrotask(() => {
      const authState = getAuthState();
      setAuth(authState);
      setIsLoading(false);
    });
  }, []);

  return { auth, isLoading };
}
