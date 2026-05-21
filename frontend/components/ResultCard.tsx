"use client";

/**
 * Displays analyze API results in a readable layout.
 * Receives typed data only — no fetching logic here.
 */

import { useState } from "react";

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
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h2 className="mb-6 text-lg font-semibold text-zinc-900">
        Analysis Results
      </h2>

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
          <h3 className="mb-2 text-sm font-semibold text-zinc-800">
            Rewritten Bullets
          </h3>
          <ul className="list-disc space-y-2 pl-5 text-sm text-zinc-700">
            {result.rewritten_bullets.map((bullet, index) => (
              <li key={`${index}-${bullet.slice(0, 24)}`}>{bullet}</li>
            ))}
          </ul>
        </div>

        {result.cover_letter && (
          <CoverLetterCard text={result.cover_letter} />
        )}
      </div>
    </section>
  );
}
