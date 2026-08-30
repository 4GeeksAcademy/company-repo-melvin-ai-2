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
  const [errorKind, setErrorKind] = useState<"analyze" | "download" | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [lastFile, setLastFile] = useState<File | null>(null);
  const [downloading, setDownloading] = useState(false);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setErrorKind(null);
    setLastFile(file);
    setFileName(file.name);
    try {
      const next = await analyzeIncidentsCsv(file);
      setSummary(next);
    } catch (err) {
      setSummary(null);
      setErrorKind("analyze");
      setError(
        err instanceof Error
          ? err.message
          : "Could not analyze that file. Try again or contact hello@brasaland.com.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setError(null);
    setErrorKind(null);
    try {
      await downloadResultsCsv();
    } catch (err) {
      setErrorKind("download");
      setError(
        err instanceof Error
          ? err.message
          : "Could not download results. Try again.",
      );
    } finally {
      setDownloading(false);
    }
  }

  const retry =
    errorKind === "download"
      ? () => void handleDownload()
      : lastFile
        ? () => void handleFile(lastFile)
        : undefined;

  return (
    <div className="analyzer">
      <FileDropzone disabled={busy} onFileSelected={handleFile} />
      {fileName ? <p className="muted">Selected: {fileName}</p> : null}
      {busy ? <p role="status">Analyzing…</p> : null}
      {error ? <ErrorBanner message={error} onRetry={retry} /> : null}

      {summary ? (
        <>
          <div className="actions">
            <button
              type="button"
              className="button"
              disabled={downloading}
              onClick={() => void handleDownload()}
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
