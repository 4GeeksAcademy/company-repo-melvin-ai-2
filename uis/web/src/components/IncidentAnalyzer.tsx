"use client";

import { useState } from "react";
import { AnalysisSummaryView } from "@/components/AnalysisSummaryView";
import { FileDropzone } from "@/components/FileDropzone";
import {
  analyzeIncidentsCsv,
  exportResultsUrl,
  type AnalysisSummary,
} from "@/lib/api";

export function IncidentAnalyzer() {
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setFileName(file.name);
    try {
      const next = await analyzeIncidentsCsv(file);
      setSummary(next);
    } catch (err) {
      setSummary(null);
      setError(err instanceof Error ? err.message : "Analysis failed.");
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
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {summary ? (
        <>
          <div className="actions">
            <a className="button" href={exportResultsUrl()} download>
              Download results CSV
            </a>
          </div>
          <AnalysisSummaryView summary={summary} />
        </>
      ) : null}
    </div>
  );
}
