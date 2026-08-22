"use client";

import { useId, useState, type DragEvent } from "react";

type FileDropzoneProps = {
  disabled?: boolean;
  onFileSelected: (file: File) => void;
};

export function FileDropzone({ disabled, onFileSelected }: FileDropzoneProps) {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);

  function acceptFile(file: File | undefined) {
    if (!file || disabled) return;
    onFileSelected(file);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files?.[0]);
  }

  return (
    <div
      className={`dropzone${dragging ? " dropzone--active" : ""}`}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <p>
        Drag and drop a Brasaland incidents CSV here, or choose a file.
      </p>
      <label className="button button--secondary" htmlFor={inputId}>
        Choose CSV
      </label>
      <input
        id={inputId}
        type="file"
        accept=".csv,text/csv"
        disabled={disabled}
        onChange={(event) => acceptFile(event.target.files?.[0])}
      />
    </div>
  );
}
