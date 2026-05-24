/**
 * Shared TypeScript types for the analyze API.
 * Keeps request/response shapes in one place for components and api.ts.
 */

/** The optional report sections the user can request */
export type Section = "rewrite_bullets" | "cover_letter" | "interview_prep";

export const ALL_SECTIONS: Section[] = [
  "rewrite_bullets",
  "cover_letter",
  "interview_prep",
];

/** Body sent to POST /api/analyze */
export interface AnalyzeRequest {
  resume_text: string;
  jd_text: string;
  sections: Section[];
}

/** JSON returned from POST /api/analyze */
export interface AnalyzeResponse {
  thread_id: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  rewritten_bullets: string[];
  critique_score: number;
  cover_letter: string;
  technical_questions: string[];
  behavioral_questions: string[];
  study_topics: string[];
  final_report: string;
}

/** Body sent to POST /api/chat */
export interface ChatRequest {
  thread_id: string;
  message: string;
}

/** JSON returned from POST /api/chat */
export interface ChatResponse {
  reply: string;
  updates: Partial<AnalyzeResponse>;
}

/** A single message in the chat panel */
export interface ChatMessage {
  role: "user" | "agent";
  text: string;
  triggeredUpdate?: boolean;
}

/** JSON returned from POST /api/resume/parse */
export interface ResumeParseResponse {
  resume_text: string;
}

/** Body sent to POST /api/jobs */
export interface JobSearchRequest {
  resume_text: string;
}

/** A single job listing returned by POST /api/jobs */
export interface JobResult {
  job_id: string;
  title: string;
  company: string;
  location: string;
  employment_type: string;
  apply_link: string;
  description: string;
  salary: string;
}

/** JSON returned from GET /api/jobs */
export interface JobSearchResponse {
  jobs: JobResult[];
}
