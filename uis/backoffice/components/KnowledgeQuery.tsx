"use client";

import { FormEvent, useState } from "react";
import { askKnowledge } from "@/lib/knowledge";

export function KnowledgeQuery() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask() {
    const trimmed = question.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const body = await askKnowledge(trimmed);
      setAnswer(body.answer);
    } catch (err) {
      if (err instanceof Error && err.name === "AuthSessionError") return;
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask();
  }

  return (
    <section className="knowledge-query" aria-labelledby="knowledge-query-title">
      <h1 id="knowledge-query-title">Manual assistant</h1>
      <p>
        Ask the way a location manager would. The answer comes from the
        official Brasaland manuals, in the voice of a trained salesperson.
      </p>
      <form onSubmit={onSubmit}>
        <label htmlFor="knowledge-question">
          Question
          <textarea
            id="knowledge-question"
            name="question"
            rows={4}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Looking it up" : "Ask"}
        </button>
      </form>
      {loading ? <p>Checking the manuals.</p> : null}
      {error ? (
        <p role="alert">
          {error}{" "}
          <button type="button" onClick={() => void ask()}>
            Try again
          </button>
        </p>
      ) : null}
      {answer ? (
        <p className="knowledge-answer" role="status">
          {answer}
        </p>
      ) : null}
    </section>
  );
}
