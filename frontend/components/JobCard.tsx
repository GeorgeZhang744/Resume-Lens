/**
 * Displays a single job listing: title, company, location, type, salary,
 * description excerpt, and an Apply button.
 */

import type { JobResult } from "@/lib/types";

export default function JobCard({ job }: { job: JobResult }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 transition-colors hover:bg-white">
      {/* Header row */}
      <div className="mb-2 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-zinc-900">
            {job.title}
          </h3>
          <p className="text-sm text-zinc-500">{job.company}</p>
        </div>

        {job.apply_link && (
          <a
            href={job.apply_link}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 rounded-md px-3 py-1 text-xs font-medium text-zinc-600 ring-1 ring-inset ring-zinc-300 transition hover:bg-zinc-100 hover:text-zinc-900"
          >
            Apply ↗
          </a>
        )}
      </div>

      {/* Meta chips */}
      <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1">
        {job.location && (
          <span className="text-xs text-zinc-400">{job.location}</span>
        )}
        {job.employment_type && (
          <>
            {job.location && <span className="text-xs text-zinc-300">·</span>}
            <span className="text-xs text-zinc-400">{job.employment_type}</span>
          </>
        )}
        {job.salary && (
          <>
            {(job.location || job.employment_type) && (
              <span className="text-xs text-zinc-300">·</span>
            )}
            <span className="text-xs font-medium text-emerald-700">
              {job.salary}
            </span>
          </>
        )}
      </div>

      {/* Description excerpt */}
      {job.description && (
        <p className="line-clamp-2 text-xs leading-relaxed text-zinc-500">
          {job.description}
        </p>
      )}
    </div>
  );
}
