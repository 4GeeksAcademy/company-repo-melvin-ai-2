"use client";

import { FormEvent, useState } from "react";
import { citiesByCountry, locationsByCity } from "@/data/site";

type Country = keyof typeof citiesByCountry | "";
type Errors = Record<string, string>;

const messages = {
  fullName: "Enter your full name (first and last name)",
  email: "Enter a valid email (example: name@email.com)",
  phone:
    "Phone must include country code (example: +57 300 123 4567 or +1 305 123 4567)",
  country: "Select your country",
  city: "Select your city",
  referral: "Tell us how you found Brasaland",
  birthDate: "You must be 18 or older to register for Brasa Points",
  terms: "You must accept the Brasa Points program terms to continue",
};

const isAdult = (dateValue: string): boolean => {
  if (!dateValue) return false;
  const [year, month, day] = dateValue.split("-").map(Number);
  const birthDate = new Date(year, month - 1, day);
  const today = new Date();
  const adultDate = new Date(
    today.getFullYear() - 18,
    today.getMonth(),
    today.getDate(),
  );
  return birthDate <= adultDate;
};

export function LoyaltyForm() {
  const [country, setCountry] = useState<Country>("");
  const [city, setCity] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const nextErrors: Errors = {};
    const fullName = String(form.get("fullName") ?? "").trim();
    const email = String(form.get("email") ?? "");
    const phone = String(form.get("phone") ?? "").trim();
    const referral = String(form.get("referral") ?? "");
    const birthDate = String(form.get("birthDate") ?? "");

    if (fullName.split(/\s+/).length < 2) nextErrors.fullName = messages.fullName;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = messages.email;
    }
    if (!/^\+(57|1)\s?[\d\s()-]{7,}$/.test(phone)) {
      nextErrors.phone = messages.phone;
    }
    if (!country) nextErrors.country = messages.country;
    if (!city) nextErrors.city = messages.city;
    if (!referral) nextErrors.referral = messages.referral;
    if (!isAdult(birthDate)) nextErrors.birthDate = messages.birthDate;
    if (!form.get("terms")) nextErrors.terms = messages.terms;

    setErrors(nextErrors);
    setSubmitted(Object.keys(nextErrors).length === 0);
    if (Object.keys(nextErrors).length > 0) {
      requestAnimationFrame(() => {
        const firstError = document.querySelector<HTMLElement>("[aria-invalid='true']");
        firstError?.focus();
      });
    }
  }

  if (submitted) {
    return (
      <div className="success-panel" role="status" tabIndex={-1}>
        <span aria-hidden="true">✓</span>
        <h2>Welcome to Brasa Points!</h2>
        <p>
          Your registration was successful. You will receive a confirmation
          email with your account details and how to start earning points.
        </p>
        <button className="button button-primary" onClick={() => setSubmitted(false)}>
          Register another member
        </button>
      </div>
    );
  }

  const fieldError = (name: string) =>
    errors[name] ? (
      <span className="field-error" id={`${name}-error`}>
        {errors[name]}
      </span>
    ) : null;

  const errorProps = (name: string) => ({
    "aria-invalid": Boolean(errors[name]),
    "aria-describedby": errors[name] ? `${name}-error` : undefined,
  });

  return (
    <form className="loyalty-form" noValidate onSubmit={handleSubmit}>
      <div className="form-grid">
        <label>
          Full name *
          <input name="fullName" autoComplete="name" {...errorProps("fullName")} />
          {fieldError("fullName")}
        </label>
        <label>
          Email *
          <input
            name="email"
            type="email"
            autoComplete="email"
            {...errorProps("email")}
          />
          {fieldError("email")}
        </label>
        <label>
          Phone *
          <input
            name="phone"
            type="tel"
            autoComplete="tel"
            placeholder="+57 300 123 4567"
            {...errorProps("phone")}
          />
          {fieldError("phone")}
        </label>
        <label>
          Country *
          <select
            name="country"
            value={country}
            onChange={(event) => {
              setCountry(event.target.value as Country);
              setCity("");
            }}
            {...errorProps("country")}
          >
            <option value="">Select country</option>
            {Object.keys(citiesByCountry).map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
          {fieldError("country")}
        </label>
        <label>
          City *
          <select
            name="city"
            value={city}
            disabled={!country}
            onChange={(event) => setCity(event.target.value)}
            {...errorProps("city")}
          >
            <option value="">Select city</option>
            {country &&
              citiesByCountry[country].map((item) => (
                <option key={item}>{item}</option>
              ))}
          </select>
          {fieldError("city")}
        </label>
        <label>
          Favorite location
          <select name="favoriteLocation" disabled={!city}>
            <option value="">No preference yet</option>
            {(locationsByCity[city] ?? []).map((item) => (
              <option key={item}>Brasaland {item}</option>
            ))}
          </select>
        </label>
        <label>
          How did you find us? *
          <select name="referral" {...errorProps("referral")}>
            <option value="">Select one</option>
            <option>Social media</option>
            <option>Recommendation</option>
            <option>Walked by</option>
            <option>Internet search</option>
            <option>Other</option>
          </select>
          {fieldError("referral")}
        </label>
        <label>
          Date of birth *
          <input name="birthDate" type="date" {...errorProps("birthDate")} />
          {fieldError("birthDate")}
        </label>
      </div>

      <fieldset>
        <legend>Dietary preferences</legend>
        <div className="choice-row">
          {["No restrictions", "Vegetarian", "Gluten-free", "Other"].map(
            (option) => (
              <label className="choice" key={option}>
                <input name="dietary" type="checkbox" value={option} />
                {option}
              </label>
            ),
          )}
        </div>
      </fieldset>

      <label className="choice choice-block">
        <input name="terms" type="checkbox" {...errorProps("terms")} />
        I accept the Brasa Points program terms. *
      </label>
      {fieldError("terms")}
      <label className="choice choice-block">
        <input name="marketing" type="checkbox" />
        I want to receive offers by email.
      </label>

      <button className="button button-primary submit-button" type="submit">
        Create my Brasa Points account <span aria-hidden="true">→</span>
      </button>
    </form>
  );
}
