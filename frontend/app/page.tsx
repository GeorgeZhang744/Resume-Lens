"use client";

/**
 * Main page — orchestrates the analyze workflow.
 *
 * State management:
 * - resumeText / jdText: user input (controlled by JDInput)
 * - isLoading: true while API request is in flight
 * - error: user-facing message if validation or API fails
 * - result: AnalyzeResponse shown by ResultCard after success
 *
 * API flow:
 * 1. User clicks Analyze → handleAnalyze()
 * 2. Client-side validation (minimum length)
 * 3. analyzeJobMatch() in lib/api.ts POSTs to backend
 * 4. On success, result state updates and ResultCard renders
 */

import { useState } from "react";

import AnalyzeButton from "@/components/AnalyzeButton";
import JDInput from "@/components/JDInput";
import ResultCard from "@/components/ResultCard";
import { analyzeJobMatch } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

const MIN_TEXT_LENGTH = 30;

export default function Home() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const resumeValid = resumeText.trim().length >= MIN_TEXT_LENGTH;
  const jdValid = jdText.trim().length >= MIN_TEXT_LENGTH;
  const canSubmit = resumeValid && jdValid && !isLoading;

  async function handleAnalyze() {
    setError(null);
    setResult(null);

    if (!resumeValid || !jdValid) {
      setError(
        `Please enter at least ${MIN_TEXT_LENGTH} characters in both fields.`
      );
      return;
    }

    setIsLoading(true);

    try {
      const data = await analyzeJobMatch({
        resume_text: resumeText.trim(),
        jd_text: jdText.trim(),
      });
      setResult(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-full bg-zinc-50">
      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            AI Job Match Agent
          </h1>
          <p className="mt-2 text-sm text-zinc-600">
            Paste your resume and a job description to see how well they match.
          </p>
        </header>

        <div className="flex flex-col gap-6 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <JDInput
            id="resume"
            label="Resume"
            placeholder="Paste your resume text here…"
            value={resumeText}
            onChange={setResumeText}
            minLength={MIN_TEXT_LENGTH}
          />

          <JDInput
            id="job-description"
            label="Job Description"
            placeholder="Paste the job description here…"
            value={jdText}
            onChange={setJdText}
            minLength={MIN_TEXT_LENGTH}
          />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <AnalyzeButton
              onClick={handleAnalyze}
              isLoading={isLoading}
              disabled={!canSubmit}
            />
            {isLoading && (
              <p className="text-sm text-zinc-500" role="status">
                Analyzing your resume against the job description…
              </p>
            )}
          </div>

          {error && (
            <p
              className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              {error}
            </p>
          )}
        </div>

        {result && (
          <div className="mt-8">
            <ResultCard result={result} />
          </div>
        )}
      </main>
    </div>
  );
}
