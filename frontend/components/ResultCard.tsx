"use client";

/**
 * Displays analyze API results in a readable layout.
 * Receives typed data only — no fetching logic here.
 */

import { useState } from "react";

import { exportToPdf } from "@/lib/exportPdf";
import type { AnalyzeResponse } from "@/lib/types";

interface ResultCardProps {
  result: AnalyzeResponse;
}

function SkillList({
  title,
  skills,
  emptyMessage,
  variant,
}: {
  title: string;
  skills: string[];
  emptyMessage: string;
  variant: "matched" | "missing";
}) {
  const chipClass =
    variant === "matched"
      ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
      : "bg-amber-50 text-amber-800 ring-amber-200";

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-zinc-800">{title}</h3>
      {skills.length === 0 ? (
        <p className="text-sm text-zinc-500">{emptyMessage}</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <li
              key={skill}
              className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset ${chipClass}`}
            >
              {skill}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function QuestionList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {title}
      </h4>
      <ul className="list-disc space-y-1 pl-5 text-sm text-zinc-700">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function CoverLetterCard({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-800">Cover Letter</h3>
        <button
          onClick={handleCopy}
          className="rounded-md px-3 py-1 text-xs font-medium text-zinc-500 ring-1 ring-inset ring-zinc-200 transition hover:bg-zinc-50 hover:text-zinc-700"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="whitespace-pre-wrap rounded-lg bg-zinc-50 p-4 text-sm leading-relaxed text-zinc-700">
        {text}
      </div>
    </div>
  );
}

export default function ResultCard({ result }: ResultCardProps) {
  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    setExporting(true);
    // Defer to next tick so the button state renders before the (sync) PDF work blocks
    await new Promise((r) => setTimeout(r, 0));
    exportToPdf(result);
    setExporting(false);
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">
          Analysis Results
        </h2>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="rounded-md px-3 py-1.5 text-xs font-medium text-zinc-600 ring-1 ring-inset ring-zinc-200 transition hover:bg-zinc-50 hover:text-zinc-800 disabled:opacity-50"
        >
          {exporting ? "Exporting…" : "Export PDF"}
        </button>
      </div>

      <div className="mb-6 flex items-baseline gap-2">
        <span className="text-sm font-medium text-zinc-600">Match Score</span>
        <span className="text-3xl font-bold text-zinc-900">
          {result.match_score}
        </span>
        <span className="text-sm text-zinc-500">/ 100</span>
      </div>

      <div className="flex flex-col gap-6">
        <SkillList
          title="Matched Skills"
          skills={result.matched_skills}
          emptyMessage="No matched skills listed."
          variant="matched"
        />

        <SkillList
          title="Missing Skills"
          skills={result.missing_skills}
          emptyMessage="No missing skills listed."
          variant="missing"
        />

        <div>
          <div className="mb-2 flex items-center gap-3">
            <h3 className="text-sm font-semibold text-zinc-800">
              Rewritten Bullets
            </h3>
            {result.critique_score > 0 && (
              <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
                AI quality score: {result.critique_score}/10
              </span>
            )}
          </div>
          <ul className="list-disc space-y-2 pl-5 text-sm text-zinc-700">
            {result.rewritten_bullets.map((bullet, index) => (
              <li key={`${index}-${bullet.slice(0, 24)}`}>{bullet}</li>
            ))}
          </ul>
        </div>

        {result.cover_letter && (
          <CoverLetterCard text={result.cover_letter} />
        )}

        {(result.technical_questions.length > 0 ||
          result.behavioral_questions.length > 0 ||
          result.study_topics.length > 0) && (
          <div>
            <h3 className="mb-3 text-sm font-semibold text-zinc-800">
              Interview Prep
            </h3>
            <div className="flex flex-col gap-4 rounded-lg bg-zinc-50 p-4">
              <QuestionList
                title="Technical Questions"
                items={result.technical_questions}
              />
              <QuestionList
                title="Behavioral Questions"
                items={result.behavioral_questions}
              />
              <QuestionList
                title="Study Topics"
                items={result.study_topics}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
