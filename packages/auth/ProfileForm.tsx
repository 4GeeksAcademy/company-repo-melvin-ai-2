"use client";

import { FormEvent, useEffect, useState } from "react";
import type { AuthMe } from "./types";
import { useAuthApi } from "./useAuthApi";

export function ProfileForm() {
  const { loadMe, saveProfile } = useAuthApi();
  const [me, setMe] = useState<AuthMe | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    loadMe()
      .then((data) => {
        if (!active) return;
        setMe(data);
        setName(data.profile.name ?? "");
        setPhone(data.profile.phone ?? "");
        setAddress(data.profile.address ?? "");
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load profile.");
      });
    return () => {
      active = false;
    };
  }, [loadMe]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const profile = await saveProfile({ name, phone, address });
      setName(profile.name ?? "");
      setPhone(profile.phone ?? "");
      setAddress(profile.address ?? "");
      setNotice("Profile saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ba-auth">
      <h1>Account profile</h1>
      <p>
        Email and role come from your Brasaland user. Name and contact live on
        your profile.
      </p>
      {me ? (
        <p>
          Signed in as <strong>{me.email}</strong> ({me.role})
        </p>
      ) : null}
      <form onSubmit={onSubmit}>
        <label htmlFor="ba-prof-name">
          Name
          <input
            id="ba-prof-name"
            name="name"
            type="text"
            autoComplete="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label htmlFor="ba-prof-phone">
          Phone
          <input
            id="ba-prof-phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
        <label htmlFor="ba-prof-address">
          Address
          <input
            id="ba-prof-address"
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
        {notice ? <p role="status">{notice}</p> : null}
        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Save profile"}
        </button>
      </form>
    </section>
  );
}
