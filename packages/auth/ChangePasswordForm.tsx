"use client";

import { FormEvent, useState } from "react";
import { useAuthApi } from "./useAuthApi";

export function ChangePasswordForm() {
  const { changePassword } = useAuthApi();
  const [currentPassword, setCurrentPassword] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== confirm) {
      setError("New password and confirmation must match.");
      setNotice(null);
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await changePassword(currentPassword, password);
      setCurrentPassword("");
      setPassword("");
      setConfirm("");
      setNotice("Password updated.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not change the password.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ba-auth">
      <h1>Change password</h1>
      <p>Enter your current Brasaland password, then choose a new one.</p>
      {notice ? (
        <p className="ba-notice" role="status">
          {notice}
        </p>
      ) : null}
      <form onSubmit={onSubmit}>
        <label htmlFor="ba-change-current">
          Current password
          <input
            id="ba-change-current"
            name="current_password"
            type="password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
        </label>
        <label htmlFor="ba-change-new">
          New password
          <input
            id="ba-change-new"
            name="new_password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <label htmlFor="ba-change-confirm">
          Confirm new password
          <input
            id="ba-change-confirm"
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
          <p className="ba-error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? "Updating…" : "Update password"}
        </button>
      </form>
    </section>
  );
}
