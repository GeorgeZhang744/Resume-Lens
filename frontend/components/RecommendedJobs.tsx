"use client";

/**
 * Fetches and renders job recommendations from the user's resume text.
 * Calls POST /api/jobs once on mount — no JD or prior analysis required.
 * Handles loading, error, and empty states cleanly.
 */

import { useEffect, useState } from "react";

import JobCard from "@/components/JobCard";
import { fetchJobRecommendations } from "@/lib/api";
import type { JobResult } from "@/lib/types";

interface RecommendedJobsProps {
  resumeText: string;
}

export default function RecommendedJobs({ resumeText }: RecommendedJobsProps) {
  const [jobs, setJobs] = useState<JobResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchJobRecommendations(resumeText);
        if (!cancelled) setJobs(data.jobs);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load jobs.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [resumeText]);

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-zinc-900">
        Matching Jobs
      </h2>

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-600" />
          Finding matching roles…
        </div>
      )}

      {!isLoading && error && (
        <p className="text-sm text-red-600">{error}</p>
      )}

      {!isLoading && !error && jobs.length === 0 && (
        <p className="text-sm text-zinc-400">No matching jobs found.</p>
      )}

      {!isLoading && jobs.length > 0 && (
        <div className="flex flex-col gap-3">
          {jobs.map((job) => (
            <JobCard key={job.job_id || job.title} job={job} />
          ))}
        </div>
      )}
    </section>
  );
}
