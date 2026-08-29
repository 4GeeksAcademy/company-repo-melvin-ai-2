"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ErrorBanner } from "./ErrorBanner";
import { useAuthApi } from "./useAuthApi";

type LoginFormProps = {
  heading: string;
  homePath?: string;
};

export function LoginForm({ heading, homePath = "/" }: LoginFormProps) {
  const router = useRouter();
  const { login } = useAuthApi();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("reset") === "1") {
      setNotice("Password updated. Sign in with your new password.");
    }
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.replace(homePath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ba-auth">
      <h1>{heading}</h1>
      <p>Sign in with your Brasaland account.</p>
      {notice ? (
        <p className="ba-notice" role="status">
          {notice}
        </p>
      ) : null}
      <form onSubmit={onSubmit}>
        <label htmlFor="ba-login-email">
          Email
          <input
            id="ba-login-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label htmlFor="ba-login-password">
          Password
          <input
            id="ba-login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <ErrorBanner message={error} homeHref={homePath} /> : null}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="ba-links">
        <Link href="/forgot-password">Forgot your password?</Link>
        <Link href="/register">Create an account</Link>
      </p>
    </section>
  );
}
