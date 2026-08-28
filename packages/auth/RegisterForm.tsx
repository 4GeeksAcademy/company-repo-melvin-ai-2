"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import type { FieldErrors } from "./types";
import { useAuthApi } from "./useAuthApi";

type RegisterFormProps = {
  heading: string;
  homePath?: string;
};

export function RegisterForm({ heading, homePath = "/" }: RegisterFormProps) {
  const router = useRouter();
  const { register } = useAuthApi();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldErrors>({});
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setFields({});
    try {
      const fieldErrors = await register({
        email,
        password,
        name: name || undefined,
        phone: phone || undefined,
        address: address || undefined,
      });
      if (fieldErrors) {
        setFields(fieldErrors);
        return;
      }
      router.replace(homePath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ba-auth">
      <h1>{heading}</h1>
      <p>Create a Brasaland operator account.</p>
      <form onSubmit={onSubmit}>
        <label htmlFor="ba-reg-email">
          Email
          <input
            id="ba-reg-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          {fields.email ? (
            <span className="ba-field-error">{fields.email}</span>
          ) : null}
        </label>
        <label htmlFor="ba-reg-password">
          Password
          <input
            id="ba-reg-password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {fields.password ? (
            <span className="ba-field-error">{fields.password}</span>
          ) : null}
        </label>
        <label htmlFor="ba-reg-name">
          Name
          <input
            id="ba-reg-name"
            name="name"
            type="text"
            autoComplete="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label htmlFor="ba-reg-phone">
          Phone
          <input
            id="ba-reg-phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
        <label htmlFor="ba-reg-address">
          Address
          <input
            id="ba-reg-address"
            name="address"
            type="text"
            autoComplete="street-address"
            value={address}
            onChange={(event) => setAddress(event.target.value)}
          />
        </label>
        {error ? (
          <p className="ba-error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? "Creating account…" : "Register"}
        </button>
      </form>
      <p className="ba-links">
        <Link href="/login">Already have an account?</Link>
      </p>
    </section>
  );
}
