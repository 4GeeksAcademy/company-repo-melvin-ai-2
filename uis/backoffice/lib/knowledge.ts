import { authFetch } from "@repo/auth";

export type KnowledgeAnswer = {
  answer: string;
};

export async function askKnowledge(question: string): Promise<KnowledgeAnswer> {
  const response = await authFetch("/knowledge/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new Error(
      "The manual assistant is unavailable. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as KnowledgeAnswer;
}
