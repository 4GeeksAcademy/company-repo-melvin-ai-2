"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { hasToken } from "./token";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!hasToken()) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <p role="status" style={{ padding: "1.5rem" }}>
        Checking your Brasaland session…
      </p>
    );
  }

  return <>{children}</>;
}
