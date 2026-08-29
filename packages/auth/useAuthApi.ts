"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { authFetch, fieldErrorsFromApi, getBrasalandApiBase, parseApiError, brasalandFetch } from "./client";
import { clearToken, setToken } from "./token";
import type { AuthMe, FieldErrors, TokenResponse } from "./types";

export function useAuthApi() {
  const router = useRouter();

  const login = useCallback(async (email: string, password: string) => {
    const response = await brasalandFetch(`${getBrasalandApiBase()}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(parseApiError(payload, "Could not log in."));
    }
    const data = payload as TokenResponse;
    setToken(data.access_token);
  }, []);

  const register = useCallback(
    async (input: {
      email: string;
      password: string;
      name?: string;
      phone?: string;
      address?: string;
    }): Promise<FieldErrors | void> => {
      const response = await brasalandFetch(`${getBrasalandApiBase()}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const fields = fieldErrorsFromApi(payload);
        if (Object.keys(fields).length > 0) return fields;
        throw new Error(parseApiError(payload, "Could not register."));
      }
      await login(input.email, input.password);
    },
    [login],
  );

  const loadMe = useCallback(async (): Promise<AuthMe> => {
    const response = await authFetch("/auth/me");
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(parseApiError(payload, "Could not load profile."));
    }
    return payload as AuthMe;
  }, []);

  const saveProfile = useCallback(
    async (input: { name?: string; phone?: string; address?: string }) => {
      const response = await authFetch("/profiles/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiError(payload, "Could not update profile."));
      }
      return payload as AuthMe["profile"];
    },
    [],
  );

  const logout = useCallback(() => {
    clearToken();
    router.replace("/login");
  }, [router]);

  const forgotPassword = useCallback(async (email: string) => {
    const response = await brasalandFetch(`${getBrasalandApiBase()}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(parseApiError(payload, "Could not send the reset email."));
    }
  }, []);

  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    const response = await brasalandFetch(`${getBrasalandApiBase()}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(parseApiError(payload, "Could not reset the password."));
    }
  }, []);

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      const response = await authFetch("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiError(payload, "Could not change the password."));
      }
    },
    [],
  );

  return {
    login,
    register,
    loadMe,
    saveProfile,
    logout,
    forgotPassword,
    resetPassword,
    changePassword,
  };
}
