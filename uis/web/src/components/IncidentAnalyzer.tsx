"use client";

import { useState } from "react";
import { ErrorBanner } from "@repo/auth";
import { AnalysisSummaryView } from "@/components/AnalysisSummaryView";
import { FileDropzone } from "@/components/FileDropzone";
import {
  analyzeIncidentsCsv,
  downloadResultsCsv,
  type AnalysisSummary,
} from "@/lib/api";

export function IncidentAnalyzer() {
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [lastFile, setLastFile] = useState<File | null>(null);
  const [downloading, setDownloading] = useState(false);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setLastFile(file);
    setFileName(file.name);
    try {
      const next = await analyzeIncidentsCsv(file);
      setSummary(next);
    } catch (err) {
      setSummary(null);
      setError(
        err instanceof Error
          ? err.message
          : "Could not analyze that file. Try again or contact hello@brasaland.com.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="analyzer">
      <FileDropzone disabled={busy} onFileSelected={handleFile} />
      {fileName ? <p className="muted">Selected: {fileName}</p> : null}
      {busy ? <p role="status">Analyzing…</p> : null}
      {error ? (
        <ErrorBanner
          message={error}
          onRetry={lastFile ? () => void handleFile(lastFile) : undefined}
        />
      ) : null}

      {summary ? (
        <>
          <div className="actions">
            <button
              type="button"
              className="button"
              disabled={downloading}
              onClick={async () => {
                setDownloading(true);
                setError(null);
                try {
                  await downloadResultsCsv();
                } catch (err) {
                  setError(
                    err instanceof Error
                      ? err.message
                      : "Could not download results. Try again.",
                  );
                } finally {
                  setDownloading(false);
                }
              }}
            >
              {downloading ? "Downloading…" : "Download results CSV"}
            </button>
          </div>
          <AnalysisSummaryView summary={summary} />
        </>
      ) : null}
    </div>
  );
}
