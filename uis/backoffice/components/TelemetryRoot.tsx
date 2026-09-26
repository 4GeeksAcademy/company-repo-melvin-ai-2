"use client";

import { Component, useEffect, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { useReportWebVitals } from "next/web-vitals";
import { setAuthTelemetry } from "@repo/auth";
import { installClientErrorTracking, track } from "@/lib/telemetry";

const VITALS = new Set(["LCP", "CLS", "INP", "FCP", "TTFB"]);

export function TelemetryRoot({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "/";

  useReportWebVitals((metric) => {
    if (!VITALS.has(metric.name)) return;
    track("page_vital_recorded", {
      route: pathname,
      vital_name: metric.name,
      vital_value: metric.value,
    });
  });

  useEffect(() => {
    setAuthTelemetry((eventType, properties) => {
      track(eventType, properties);
    });
    installClientErrorTracking();
    return () => setAuthTelemetry(null);
  }, []);

  useEffect(() => {
    track("backoffice_page_viewed", { route: pathname });
  }, [pathname]);

  return <>{children}</>;
}

export function TelemetryErrorBoundary({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Boundary>{children}</Boundary>;
}

type BoundaryProps = { children: ReactNode };
type BoundaryState = { failed: boolean };

class Boundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error): void {
    track("client_error_uncaught", {
      error_name: error.name || "Error",
      route: window.location.pathname,
    });
  }

  render() {
    if (this.state.failed) {
      return (
        <p role="alert" style={{ padding: "1.5rem" }}>
          This Brasaland page hit a problem. Refresh and try again.
        </p>
      );
    }
    return this.props.children;
  }
}
