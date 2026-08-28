"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthApi } from "./useAuthApi";

type ResetPasswordFormProps = {
  heading: string;
};

export function ResetPasswordForm({ heading }: ResetPasswordFormProps) {
  const router = useRouter();
  const { resetPassword } = useAuthApi();
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const value = new URLSearchParams(window.location.search).get("token");
    setToken(value && value.trim() ? value.trim() : "");
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    if (password !== confirm) {
      setError("New password and confirmation must match.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await resetPassword(token, password);
      router.replace("/login?reset=1");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not reset the password.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (token === null) {
    return (
      <section className="ba-auth">
        <h1>{heading}</h1>
        <p role="status">Reading reset link…</p>
      </section>
    );
  }

  if (!token) {
    return (
      <section className="ba-auth">
        <h1>{heading}</h1>
        <p className="ba-error" role="alert">
          This reset link is missing a token.
        </p>
        <p className="ba-links">
          <Link href="/forgot-password">Request a new reset link</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="ba-auth">
      <h1>{heading}</h1>
      <p>Choose a new password for your Brasaland account.</p>
      <form onSubmit={onSubmit}>
        <label htmlFor="ba-reset-password">
          New password
          <input
            id="ba-reset-password"
            name="new_password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <label htmlFor="ba-reset-confirm">
          Confirm new password
          <input
            id="ba-reset-confirm"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
          />
        </label>
        {error ? (
          <>
            <p className="ba-error" role="alert">
              {error}
            </p>
            <p className="ba-links">
              <Link href="/forgot-password">Request a new reset link</Link>
            </p>
          </>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? "Updating…" : "Update password"}
        </button>
      </form>
    </section>
  );
}
