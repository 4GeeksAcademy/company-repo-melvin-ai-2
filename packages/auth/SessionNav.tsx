"use client";

import Link from "next/link";
import { useAuthApi } from "./useAuthApi";

export function SessionNav() {
  const { logout } = useAuthApi();

  return (
    <div className="ba-session">
      <Link href="/account/profile">Profile</Link>
      <Link href="/account/change-password">Change password</Link>
      <button type="button" onClick={logout}>
        Log out
      </button>
    </div>
  );
}
