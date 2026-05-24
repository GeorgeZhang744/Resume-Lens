"use client";

/**
 * Client-side PDF export for the analysis report.
 *
 * Uses jsPDF directly against structured data — no DOM screenshotting,
 * no canvas, no layout dependencies. Each section is written with explicit
 * coordinates so the output is clean and predictable.
 */

import type { jsPDF as JsPDFType } from "jspdf";

import type { AnalyzeResponse } from "@/lib/types";

// Page geometry (A4, mm)
const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN = 20;
const CONTENT_W = PAGE_W - MARGIN * 2;
const BOTTOM_LIMIT = PAGE_H - MARGIN; // y beyond this → new page

// ── helpers ──────────────────────────────────────────────────────────────────

function heading(doc: JsPDFType, text: string, y: number): number {
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(30, 30, 30);
  doc.text(text, MARGIN, y);
  return y + 6;
}

function body(doc: JsPDFType, text: string, y: number): number {
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(60, 60, 60);
  const lines = doc.splitTextToSize(text, CONTENT_W) as string[];
  lines.forEach((line: string) => {
    if (y > BOTTOM_LIMIT) {
      doc.addPage();
      y = MARGIN + 6;
    }
    doc.text(line, MARGIN, y);
    y += 5;
  });
  return y;
}

function bullet(doc: JsPDFType, text: string, y: number): number {
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(60, 60, 60);
  const lines = doc.splitTextToSize(`• ${text}`, CONTENT_W - 4) as string[];
  lines.forEach((line: string, i: number) => {
    if (y > BOTTOM_LIMIT) {
      doc.addPage();
      y = MARGIN + 6;
    }
    // Indent continuation lines to align under the text (past the bullet)
    doc.text(line, i === 0 ? MARGIN : MARGIN + 4, y);
    y += 5;
  });
  return y;
}

function divider(doc: JsPDFType, y: number): number {
  doc.setDrawColor(220, 220, 220);
  doc.line(MARGIN, y, PAGE_W - MARGIN, y);
  return y + 5;
}

function gap(y: number, amount = 5): number {
  return y + amount;
}

function checkPage(doc: JsPDFType, y: number): number {
  if (y > BOTTOM_LIMIT) {
    doc.addPage();
    return MARGIN + 6;
  }
  return y;
}

// ── main export ───────────────────────────────────────────────────────────────

export async function exportToPdf(result: AnalyzeResponse): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  let y = MARGIN;

  // ── Title ──
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(15, 15, 15);
  doc.text("AI Job Match Report", MARGIN, y);
  y += 7;

  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(130, 130, 130);
  doc.text(
    `Generated ${new Date().toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })}`,
    MARGIN,
    y
  );
  y += 4;
  y = divider(doc, y);

  // ── Match Score ──
  y = checkPage(doc, y);
  doc.setFontSize(28);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(15, 15, 15);
  doc.text(`${result.match_score}`, MARGIN, y + 8);

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(100, 100, 100);
  doc.text("/ 100  Match Score", MARGIN + 16, y + 8);
  y += 16;
  y = gap(y, 2);

  // ── Matched Skills ──
  if (result.matched_skills.length > 0) {
    y = checkPage(doc, y);
    y = heading(doc, "Matched Skills", y);
    y = body(doc, result.matched_skills.join("  ·  "), y);
    y = gap(y);
  }

  // ── Missing Skills ──
  if (result.missing_skills.length > 0) {
    y = checkPage(doc, y);
    y = heading(doc, "Missing Skills", y);
    y = body(doc, result.missing_skills.join("  ·  "), y);
    y = gap(y);
  }

  y = divider(doc, y);

  // ── Rewritten Bullets ──
  if (result.rewritten_bullets.length > 0) {
    y = checkPage(doc, y);
    const scoreLabel =
      result.critique_score > 0
        ? `  (AI quality score: ${result.critique_score}/10)`
        : "";
    y = heading(doc, `Rewritten Resume Bullets${scoreLabel}`, y);
    for (const b of result.rewritten_bullets) {
      y = checkPage(doc, y);
      y = bullet(doc, b, y);
    }
    y = gap(y);
    y = divider(doc, y);
  }

  // ── Cover Letter ──
  if (result.cover_letter) {
    y = checkPage(doc, y);
    y = heading(doc, "Cover Letter", y);
    y = body(doc, result.cover_letter, y);
    y = gap(y);
    y = divider(doc, y);
  }

  // ── Interview Prep ──
  const hasInterviewPrep =
    result.technical_questions.length > 0 ||
    result.behavioral_questions.length > 0 ||
    result.study_topics.length > 0;

  if (hasInterviewPrep) {
    y = checkPage(doc, y);
    y = heading(doc, "Interview Prep", y);
    y = gap(y, 2);

    if (result.technical_questions.length > 0) {
      y = checkPage(doc, y);
      y = heading(doc, "Technical Questions", y);
      for (const q of result.technical_questions) {
        y = checkPage(doc, y);
        y = bullet(doc, q, y);
      }
      y = gap(y);
    }

    if (result.behavioral_questions.length > 0) {
      y = checkPage(doc, y);
      y = heading(doc, "Behavioral Questions", y);
      for (const q of result.behavioral_questions) {
        y = checkPage(doc, y);
        y = bullet(doc, q, y);
      }
      y = gap(y);
    }

    if (result.study_topics.length > 0) {
      y = checkPage(doc, y);
      y = heading(doc, "Study Topics", y);
      for (const t of result.study_topics) {
        y = checkPage(doc, y);
        y = bullet(doc, t, y);
      }
      y = gap(y);
    }

    y = divider(doc, y);
  }

  // ── Agent Summary ──
  if (result.final_report) {
    y = checkPage(doc, y);
    y = heading(doc, "Agent Summary", y);
    y = body(doc, result.final_report, y);
  }

  doc.save("job-match-report.pdf");
}
