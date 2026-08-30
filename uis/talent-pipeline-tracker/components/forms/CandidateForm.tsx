"use client";

import { useEffect, useRef, useState } from "react";
import type { CandidateCreateInput } from "@/types/candidate";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SuccessMessage } from "@/components/ui/SuccessMessage";

export interface CandidateFormValues {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: string;
  linkedin_url: string;
  cv_url: string;
}

export const emptyFormValues: CandidateFormValues = {
  full_name: "",
  email: "",
  phone: "",
  position: "",
  experience_years: "",
  linkedin_url: "",
  cv_url: "",
};

interface FieldErrors {
  full_name?: string;
  email?: string;
  phone?: string;
  position?: string;
  experience_years?: string;
}

function validate(values: CandidateFormValues): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.full_name.trim()) {
    errors.full_name = "Full name is required";
  }
  if (!values.email.trim()) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = "Enter a valid email address";
  }
  if (!values.phone.trim()) {
    errors.phone = "Phone is required";
  }
  if (!values.position.trim()) {
    errors.position = "Position is required";
  }
  const years = Number(values.experience_years);
  if (values.experience_years === "" || Number.isNaN(years) || years < 0) {
    errors.experience_years = "Enter a valid number of years (0 or more)";
  }

  return errors;
}

export function toCreateInput(values: CandidateFormValues): CandidateCreateInput {
  return {
    full_name: values.full_name.trim(),
    email: values.email.trim(),
    phone: values.phone.trim(),
    position: values.position.trim(),
    experience_years: Number(values.experience_years),
    linkedin_url: values.linkedin_url.trim() || null,
    cv_url: values.cv_url.trim() || null,
  };
}

const SUCCESS_REDIRECT_MS = 1200;

interface CandidateFormProps {
  initialValues?: CandidateFormValues;
  submitLabel: string;
  successMessage: string;
  onSubmit: (data: CandidateCreateInput) => Promise<void>;
  onSuccess: () => void;
}

export function CandidateForm({
  initialValues = emptyFormValues,
  submitLabel,
  successMessage,
  onSubmit,
  onSuccess,
}: CandidateFormProps) {
  const [values, setValues] = useState<CandidateFormValues>(initialValues);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) clearTimeout(redirectTimerRef.current);
    };
  }, []);

  const handleChange = (field: keyof CandidateFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (success) return;

    const fieldErrors = validate(values);
    if (Object.keys(fieldErrors).length > 0) {
      setErrors(fieldErrors);
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit(toCreateInput(values));
      setSuccess(true);
      redirectTimerRef.current = setTimeout(() => {
        onSuccess();
      }, SUCCESS_REDIRECT_MS);
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Could not save this candidate. Try again or contact hello@brasaland.com.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const locked = submitting || success;

  const inputClass = (field: keyof FieldErrors) =>
    `w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-1 disabled:bg-stone-50 disabled:text-stone-500 ${
      errors[field]
        ? "border-red-400 focus:border-red-500 focus:ring-red-500"
        : "border-stone-300 focus:border-[#c0392b] focus:ring-[#c0392b]"
    }`;

  return (
    <form ref={formRef} onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="full_name" className="mb-1 block text-sm font-medium text-stone-700">
            Full name <span className="text-red-500">*</span>
          </label>
          <input
            id="full_name"
            type="text"
            value={values.full_name}
            onChange={(e) => handleChange("full_name", e.target.value)}
            disabled={locked}
            className={inputClass("full_name")}
          />
          {errors.full_name && (
            <p className="mt-1 text-xs text-red-600">{errors.full_name}</p>
          )}
        </div>

        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-stone-700">
            Email <span className="text-red-500">*</span>
          </label>
          <input
            id="email"
            type="email"
            value={values.email}
            onChange={(e) => handleChange("email", e.target.value)}
            disabled={locked}
            className={inputClass("email")}
          />
          {errors.email && (
            <p className="mt-1 text-xs text-red-600">{errors.email}</p>
          )}
        </div>

        <div>
          <label htmlFor="phone" className="mb-1 block text-sm font-medium text-stone-700">
            Phone <span className="text-red-500">*</span>
          </label>
          <input
            id="phone"
            type="tel"
            value={values.phone}
            onChange={(e) => handleChange("phone", e.target.value)}
            disabled={locked}
            className={inputClass("phone")}
            placeholder="+57 300 123 4567"
          />
          {errors.phone && (
            <p className="mt-1 text-xs text-red-600">{errors.phone}</p>
          )}
        </div>

        <div>
          <label htmlFor="position" className="mb-1 block text-sm font-medium text-stone-700">
            Position <span className="text-red-500">*</span>
          </label>
          <input
            id="position"
            type="text"
            value={values.position}
            onChange={(e) => handleChange("position", e.target.value)}
            disabled={locked}
            className={inputClass("position")}
            placeholder="e.g. Kitchen Staff, Floor Manager"
          />
          {errors.position && (
            <p className="mt-1 text-xs text-red-600">{errors.position}</p>
          )}
        </div>

        <div>
          <label htmlFor="experience_years" className="mb-1 block text-sm font-medium text-stone-700">
            Years of experience <span className="text-red-500">*</span>
          </label>
          <input
            id="experience_years"
            type="number"
            min="0"
            step="1"
            value={values.experience_years}
            onChange={(e) => handleChange("experience_years", e.target.value)}
            disabled={locked}
            className={inputClass("experience_years")}
          />
          {errors.experience_years && (
            <p className="mt-1 text-xs text-red-600">{errors.experience_years}</p>
          )}
        </div>

        <div>
          <label htmlFor="linkedin_url" className="mb-1 block text-sm font-medium text-stone-700">
            LinkedIn URL
          </label>
          <input
            id="linkedin_url"
            type="url"
            value={values.linkedin_url}
            onChange={(e) => handleChange("linkedin_url", e.target.value)}
            disabled={locked}
            className={inputClass("experience_years")}
            placeholder="https://linkedin.com/in/..."
          />
        </div>

        <div>
          <label htmlFor="cv_url" className="mb-1 block text-sm font-medium text-stone-700">
            CV URL
          </label>
          <input
            id="cv_url"
            type="url"
            value={values.cv_url}
            onChange={(e) => handleChange("cv_url", e.target.value)}
            disabled={locked}
            className={inputClass("experience_years")}
            placeholder="https://..."
          />
        </div>
      </div>

      {success && <SuccessMessage message={successMessage} />}

      {submitError && (
        <ErrorMessage
          message={submitError}
          onRetry={() => formRef.current?.requestSubmit()}
        />
      )}

      <button
        type="submit"
        disabled={locked}
        className="rounded-md bg-[#c0392b] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#a93226] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {success ? "Saved" : submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
