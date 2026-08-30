"use client";

import { useRef, useState } from "react";
import type { Note } from "@/types/candidate";
import { addNote, deleteNote } from "@/lib/api";
import { formatDateTime } from "@/lib/labels";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SuccessMessage } from "@/components/ui/SuccessMessage";

interface NotesSectionProps {
  candidateId: string;
  initialNotes: Note[];
}

export function NotesSection({ candidateId, initialNotes }: NotesSectionProps) {
  const [notes, setNotes] = useState<Note[]>(initialNotes);
  const [content, setContent] = useState("");
  const [adding, setAdding] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const retryAction = useRef<(() => void) | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) return;

    retryAction.current = () => formRef.current?.requestSubmit();
    setAdding(true);
    setError(null);
    setSuccess(null);
    try {
      const note = await addNote(candidateId, trimmed);
      setNotes((prev) => [note, ...prev]);
      setContent("");
      setSuccess("Note added.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not add that note. Try again or contact hello@brasaland.com.",
      );
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (noteId: string) => {
    const previous = notes;
    retryAction.current = () => void handleDelete(noteId);
    setNotes((prev) => prev.filter((n) => n.id !== noteId));
    setDeletingId(noteId);
    setError(null);
    setSuccess(null);
    try {
      await deleteNote(candidateId, noteId);
      setSuccess("Note deleted.");
    } catch (err) {
      setNotes(previous);
      setError(
        err instanceof Error
          ? err.message
          : "Could not delete that note. Try again or contact hello@brasaland.com.",
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-stone-900">Internal Notes</h2>

      <form ref={formRef} onSubmit={handleAdd} className="space-y-2">
        <label htmlFor="note-content" className="block text-sm font-medium text-stone-700">
          Add a note
        </label>
        <textarea
          id="note-content"
          rows={3}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Write an internal note about this candidate..."
          className="w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-[#c0392b] focus:outline-none focus:ring-1 focus:ring-[#c0392b]"
        />
        <button
          type="submit"
          disabled={adding || !content.trim()}
          className="rounded-md bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {adding ? "Adding..." : "Add note"}
        </button>
      </form>

      {success && <SuccessMessage message={success} />}
      {error && (
        <ErrorMessage
          message={error}
          onRetry={() => retryAction.current?.()}
        />
      )}

      {notes.length === 0 ? (
        <p className="text-sm text-stone-500">No notes yet.</p>
      ) : (
        <ul className="divide-y divide-stone-100 rounded-lg border border-stone-200 bg-white">
          {notes.map((note) => (
            <li key={note.id} className="flex items-start justify-between gap-4 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm text-stone-800">{note.content}</p>
                <p className="mt-1 text-xs text-stone-400">
                  {formatDateTime(note.created_at)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(note.id)}
                disabled={deletingId === note.id}
                className="shrink-0 text-xs font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
              >
                {deletingId === note.id ? "Deleting..." : "Delete"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
