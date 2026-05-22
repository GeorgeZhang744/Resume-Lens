"use client";

import type { Section } from "@/lib/types";

const OPTIONS = [
  {
    id: "rewrite_bullets" as Section,
    label: "Resume Bullets",
    description: "Rewrite and optimise your resume bullets for ATS and impact.",
  },
  {
    id: "cover_letter" as Section,
    label: "Cover Letter",
    description: "Generate a tailored cover letter for this specific role.",
  },
  {
    id: "interview_prep" as Section,
    label: "Interview Prep",
    description: "Get role-specific interview questions and skill-gap study topics.",
  },
];

interface SectionPickerProps {
  selected: Section[];
  onChange: (selected: Section[]) => void;
}

export default function SectionPicker({ selected, onChange }: SectionPickerProps) {
  function toggle(id: Section) {
    onChange(
      selected.includes(id)
        ? selected.filter((s) => s !== id)
        : [...selected, id]
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium text-zinc-800">Generate</span>
      <div className="grid grid-cols-3 gap-3">
        {OPTIONS.map((opt) => {
          const isOn = selected.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => toggle(opt.id)}
              className={`flex flex-col rounded-lg border p-3 text-left transition-colors ${
                isOn
                  ? "border-zinc-900 bg-zinc-50"
                  : "border-zinc-300 bg-white hover:bg-zinc-50"
              }`}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-zinc-800">{opt.label}</p>
                <div
                  className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors ${
                    isOn
                      ? "border-zinc-900 bg-zinc-900"
                      : "border-zinc-300 bg-white"
                  }`}
                >
                  {isOn && (
                    <svg className="h-2.5 w-2.5 text-white" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
              </div>
              <p className="text-xs leading-relaxed text-zinc-500">{opt.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
