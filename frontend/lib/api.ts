/**
 * API client for the FastAPI backend.
 *
 * - uploadResume(): multipart file upload → parsed text
 * - analyzeJobMatch(): JSON analyze using parsed resume + JD
 */

import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ChatRequest,
  ChatResponse,
  JobSearchRequest,
  JobSearchResponse,
  ResumeParseResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Max upload size (must match backend: 5 MB) */
export const MAX_RESUME_FILE_BYTES = 5 * 1024 * 1024;

const ALLOWED_RESUME_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const ALLOWED_RESUME_EXTENSIONS = [".pdf", ".docx"];

/**
 * Parse a human-readable error message from a failed response.
 *
 * Handles three formats:
 *  - slowapi 429: { "error": "Rate limit exceeded: 5 per 1 hour" }
 *  - FastAPI validation: { "detail": [{ "msg": "..." }] }
 *  - FastAPI plain:      { "detail": "some string" }
 */
async function parseErrorMessage(response: Response): Promise<string> {
  const fallback = `Request failed (${response.status})`;
  try {
    const data = (await response.json()) as {
      detail?: unknown;
      error?: string;
    };

    // --- slowapi rate-limit response ---
    if (response.status === 429) {
      const raw = data.error ?? "";
      // e.g. "Rate limit exceeded: 5 per 1 hour"
      const match = /:\s*(.+)$/.exec(raw);
      const limit = match ? match[1].trim() : raw || "rate limit";
      return `Rate limit reached (${limit}). Please try again later.`;
    }

    // --- FastAPI error response ---
    const { detail } = data;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail[0]?.msg) {
      return String(detail[0].msg);
    }
  } catch {
    // not JSON
  }
  return fallback;
}

function validateResumeFile(file: File): void {
  const name = file.name.toLowerCase();
  const extOk = ALLOWED_RESUME_EXTENSIONS.some((ext) => name.endsWith(ext));
  const typeOk = ALLOWED_RESUME_TYPES.includes(file.type);

  if (!extOk && !typeOk) {
    throw new Error("Only PDF and DOCX files are supported.");
  }
  if (file.size > MAX_RESUME_FILE_BYTES) {
    throw new Error("File is too large. Maximum size is 5 MB.");
  }
  if (file.size === 0) {
    throw new Error("File is empty.");
  }
}

/**
 * Upload resume file; backend returns extracted plain text.
 * Uses FormData (multipart/form-data), not JSON.
 */
export async function uploadResume(file: File): Promise<ResumeParseResponse> {
  validateResumeFile(file);

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/resume/parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json() as Promise<ResumeParseResponse>;
}

/**
 * Send resume and job description to the backend for analysis.
 */
export async function analyzeJobMatch(
  payload: AnalyzeRequest
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json() as Promise<AnalyzeResponse>;
}

/**
 * Find job recommendations based on resume text alone — no JD required.
 * The backend extracts a search query from the resume via LLM, then queries JSearch.
 */
export async function fetchJobRecommendations(
  resumeText: string
): Promise<JobSearchResponse> {
  const payload: JobSearchRequest = { resume_text: resumeText };

  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json() as Promise<JobSearchResponse>;
}

/**
 * Send a follow-up message to an existing analysis thread.
 * The backend uses the thread_id to load the checkpoint and continue
 * the conversation with full context from the original analysis.
 */
export async function sendChatMessage(
  payload: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json() as Promise<ChatResponse>;
}
