"use client";

import { useRef } from "react";
import { useRouter } from "next/navigation";
import { createRecord } from "@/lib/api";
import { BackLink } from "@/components/layout/BackLink";
import { CandidateForm } from "@/components/forms/CandidateForm";

export function NewCandidateContent() {
  const router = useRouter();
  const createdIdRef = useRef<string | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <BackLink href="/" label="Back to candidates" />
        <h1 className="mt-2 text-2xl font-bold text-stone-900">Register Candidate</h1>
        <p className="mt-1 text-sm text-stone-500">
          Add a new applicant to the Brasaland hiring pipeline.
        </p>
      </div>

      <div className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <CandidateForm
          submitLabel="Register candidate"
          successMessage="Candidate registered successfully."
          onSubmit={async (data) => {
            const created = await createRecord(data);
            createdIdRef.current = created.id;
          }}
          onSuccess={() => {
            const id = createdIdRef.current;
            if (id) {
              router.push(`/candidates/${id}`);
            } else {
              router.push("/");
            }
          }}
        />
      </div>
    </div>
  );
}
