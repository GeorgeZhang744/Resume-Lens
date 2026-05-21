"use client";

/**
 * Main page — orchestrates upload → analyze workflow.
 *
 * State:
 * - resumeText: plain text from POST /api/resume/parse (not typed by user)
 * - resumeFilename: display name after successful upload
 * - jdText: job description (JDInput)
 * - isLoading / error / result: analyze flow
 *
 * Flow:
 * 1. ResumeUploader → uploadResume() → set resumeText
 * 2. User pastes JD
 * 3. Analyze → analyzeJobMatch({ resume_text, jd_text })
 */

import { useState } from "react";

import AnalyzeButton from "@/components/AnalyzeButton";
import ChatPanel from "@/components/ChatPanel";
import JDInput from "@/components/JDInput";
import ResultCard from "@/components/ResultCard";
import ResumeUploader from "@/components/ResumeUploader";
import { analyzeJobMatch } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

type UpdatedSections = Set<keyof AnalyzeResponse>;

const MIN_TEXT_LENGTH = 30;

export default function Home() {
  const [resumeText, setResumeText] = useState("");
  const [resumeFilename, setResumeFilename] = useState<string | null>(null);
  const [jdText, setJdText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [updatedSections, setUpdatedSections] = useState<UpdatedSections>(new Set());

  const resumeValid = resumeText.trim().length >= MIN_TEXT_LENGTH;
  const jdValid = jdText.trim().length >= MIN_TEXT_LENGTH;
  const canSubmit = resumeValid && jdValid && !isLoading;

  function handleResumeParsed(text: string, filename: string) {
    setResumeText(text);
    setResumeFilename(filename);
    setResult(null);
    setError(null);
  }

  function handleUpdate(updates: Partial<AnalyzeResponse>) {
    setResult((prev) => (prev ? { ...prev, ...updates } : prev));
    setUpdatedSections(new Set(Object.keys(updates) as (keyof AnalyzeResponse)[]));
    // Clear highlights after 1.5 s
    setTimeout(() => setUpdatedSections(new Set()), 1500);
  }

  async function handleAnalyze() {
    setError(null);
    setResult(null);

    if (!resumeText.trim()) {
      setError("Please upload a resume (PDF or DOCX) before analyzing.");
      return;
    }

    if (!resumeValid || !jdValid) {
      setError(
        `Resume and job description need at least ${MIN_TEXT_LENGTH} characters each.`
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
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">

        {/* Input form */}
        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            AI Job Match Agent
          </h1>
          <p className="mt-2 text-sm text-zinc-600">
            Upload your resume, paste a job description, and get a match score
            with AI-rewritten bullets.
          </p>
        </header>

        <div className="flex flex-col gap-6 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <ResumeUploader
            onResumeParsed={handleResumeParsed}
            minLength={MIN_TEXT_LENGTH}
            resumeTextLength={resumeText.trim().length}
          />

          {resumeFilename && resumeValid && (
            <p className="text-xs text-zinc-500">
              Ready to analyze using text from{" "}
              <span className="font-medium">{resumeFilename}</span>.
            </p>
          )}

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

        {/* Results — report on the left, chat pinned to the right */}
        {result && (
          <div className="mt-8 grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_480px]">
            <ResultCard result={result} updatedSections={updatedSections} />
            <div className="sticky top-6">
              <ChatPanel threadId={result.thread_id} onUpdate={handleUpdate} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
