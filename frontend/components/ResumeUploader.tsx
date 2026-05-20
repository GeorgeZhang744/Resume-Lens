"use client";

/**
 * Resume file upload + parse via POST /api/resume/parse.
 *
 * Parent receives parsed text through onResumeParsed().
 * Does not call /api/analyze — that stays on the main page.
 */

import { useRef, useState } from "react";

import { uploadResume } from "@/lib/api";

const ACCEPT = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

interface ResumeUploaderProps {
  /** Called when backend successfully extracts text */
  onResumeParsed: (text: string, filename: string) => void;
  /** Minimum parsed text length for parent validation hints */
  minLength: number;
  /** Current parsed resume length (from parent state) */
  resumeTextLength: number;
}

export default function ResumeUploader({
  onResumeParsed,
  minLength,
  resumeTextLength,
}: ResumeUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  async function handleFile(file: File) {
    setUploadError(null);
    setSuccessMessage(null);
    setIsUploading(true);

    try {
      const { resume_text } = await uploadResume(file);
      setFilename(file.name);
      onResumeParsed(resume_text, file.name);
      setSuccessMessage("Resume parsed successfully.");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to upload resume.";
      setUploadError(message);
      setFilename(null);
    } finally {
      setIsUploading(false);
    }
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void handleFile(file);
    e.target.value = "";
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void handleFile(file);
  }

  const parsedReady = resumeTextLength >= minLength;

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium text-zinc-800">Resume</span>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`rounded-lg border-2 border-dashed p-6 transition-colors ${
          isDragging
            ? "border-zinc-500 bg-zinc-50"
            : "border-zinc-300 bg-zinc-50/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={onInputChange}
          disabled={isUploading}
        />

        <p className="text-center text-sm text-zinc-600">
          Drag and drop a PDF or DOCX here, or{" "}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={isUploading}
            className="font-medium text-zinc-900 underline hover:no-underline disabled:opacity-50"
          >
            choose a file
          </button>
        </p>
        <p className="mt-1 text-center text-xs text-zinc-500">
          PDF or DOCX, max 5 MB
        </p>
      </div>

      {isUploading && (
        <p className="text-sm text-zinc-500" role="status">
          Parsing resume…
        </p>
      )}

      {filename && !isUploading && (
        <p className="text-sm text-zinc-700">
          <span className="font-medium">Uploaded:</span> {filename}
          {parsedReady && (
            <span className="text-zinc-500">
              {" "}
              ({resumeTextLength.toLocaleString()} characters)
            </span>
          )}
        </p>
      )}

      {successMessage && !uploadError && (
        <p className="text-sm text-emerald-700" role="status">
          {successMessage}
        </p>
      )}

      {uploadError && (
        <p
          className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
          role="alert"
        >
          {uploadError}
        </p>
      )}

      {filename && resumeTextLength > 0 && resumeTextLength < minLength && (
        <p className="text-xs text-amber-700">
          Parsed text is short ({resumeTextLength} chars). Need at least{" "}
          {minLength} characters to analyze — try a fuller resume file.
        </p>
      )}
    </div>
  );
}
