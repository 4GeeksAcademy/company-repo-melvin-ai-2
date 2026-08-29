"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ErrorBanner } from "./ErrorBanner";
import { useAuthApi } from "./useAuthApi";

type ForgotPasswordFormProps = {
  heading: string;
};

export function ForgotPasswordForm({ heading }: ForgotPasswordFormProps) {
  const { forgotPassword } = useAuthApi();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await forgotPassword(email);
      setSubmitted(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not send the reset email.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ba-auth">
      <h1>{heading}</h1>
      <p>
        Enter the email for your Brasaland operator account. If it is
        registered, we will send a reset link.
      </p>
      {submitted ? (
        <p className="ba-notice" role="status">
          If that address is registered, you’ll receive a link shortly.
        </p>
      ) : (
        <form onSubmit={onSubmit}>
          <label htmlFor="ba-forgot-email">
            Email
            <input
              id="ba-forgot-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          {error ? <ErrorBanner message={error} /> : null}
          <button type="submit" disabled={busy}>
            {busy ? "Sending…" : "Send reset link"}
          </button>
        </form>
      )}
      <p className="ba-links">
        <Link href="/login">Back to sign in</Link>
      </p>
    </section>
  );
}
