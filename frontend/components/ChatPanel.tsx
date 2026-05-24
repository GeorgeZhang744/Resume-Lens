"use client";

/**
 * Follow-up chat panel shown after analysis completes.
 *
 * The agent already knows the resume, JD, and all tool results from the
 * original analysis — the thread_id links this chat to that checkpoint.
 * Users can ask for rewrites, clarifications, or deeper advice without
 * repeating any context.
 */

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

import { sendChatMessage } from "@/lib/api";
import type { AnalyzeResponse, ChatMessage } from "@/lib/types";

interface ChatPanelProps {
  threadId: string;
  onUpdate: (updates: Partial<AnalyzeResponse>) => void;
  canUndo: boolean;
  onUndo: () => void;
}

const SUGGESTIONS = [
  "Make the cover letter more formal.",
  "Rewrite the bullets to sound more senior.",
  "Which skill gap should I focus on first?",
];

export default function ChatPanel({ threadId, onUpdate, canUndo, onUndo }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to latest message whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSend(text?: string) {
    const messageText = (text ?? input).trim();
    if (!messageText || isLoading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text: messageText }]);
    setIsLoading(true);

    try {
      const { reply, updates } = await sendChatMessage({
        thread_id: threadId,
        message: messageText,
      });
      const hasUpdate = Object.keys(updates).length > 0;
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: reply, triggeredUpdate: hasUpdate },
      ]);
      if (hasUpdate) {
        onUpdate(updates);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
      {/* Header */}
      <div className="border-b border-zinc-100 px-6 py-4">
        <h2 className="text-lg font-semibold text-zinc-900">Follow-up Chat</h2>
        <p className="mt-0.5 text-xs text-zinc-500">
          Ask the agent to refine any part of the analysis.
        </p>
      </div>

      {/* Message list */}
      <div className="flex max-h-96 flex-col gap-5 overflow-y-auto px-6 py-5">
        {messages.length === 0 && (
          <div className="flex flex-col gap-3">
            <p className="text-xs text-zinc-400">Try asking…</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => void handleSend(s)}
                  className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs text-zinc-600 transition hover:border-zinc-300 hover:bg-zinc-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => {
          // Find the index of the last message that triggered an update
          const lastUpdateIndex = messages.reduce(
            (last, m, idx) => (m.triggeredUpdate ? idx : last),
            -1
          );
          const showUndo = canUndo && msg.triggeredUpdate && i === lastUpdateIndex;

          return (
          <div key={i} className="flex flex-col gap-1">
            <div
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-800"
              }`}
            >
              {msg.role === "user" ? (
                msg.text
              ) : (
                <ReactMarkdown
                  components={{
                    p:      ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    ul:     ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-4 last:mb-0">{children}</ul>,
                    ol:     ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-4 last:mb-0">{children}</ol>,
                    li:     ({ children }) => <li>{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                    em:     ({ children }) => <em className="italic">{children}</em>,
                    code:   ({ children }) => <code className="rounded bg-zinc-200 px-1 py-0.5 font-mono text-xs">{children}</code>,
                  }}
                >
                  {msg.text}
                </ReactMarkdown>
              )}
            </div>
            </div>
            {showUndo && (
              <div className="flex justify-start pl-1">
                <button
                  onClick={onUndo}
                  className="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 transition hover:bg-amber-100"
                >
                  ↩ Undo this change
                </button>
              </div>
            )}
          </div>
          );
        })}

        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-zinc-100 px-4 py-3 text-sm text-zinc-400">
              Thinking…
            </div>
          </div>
        )}

        {error && (
          <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">
            {error}
          </p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-zinc-100 px-6 py-4">
        <div className="flex items-end gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a follow-up question… (Enter to send)"
            rows={2}
            disabled={isLoading}
            className="flex-1 resize-none rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-800 placeholder-zinc-400 outline-none transition focus:border-zinc-400 focus:bg-white disabled:opacity-50"
          />
          <button
            onClick={() => void handleSend()}
            disabled={!input.trim() || isLoading}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-40"
          >
            Send
          </button>
        </div>
        <p className="mt-1.5 text-xs text-zinc-400">
          Shift+Enter for a new line
        </p>
      </div>
    </section>
  );
}
