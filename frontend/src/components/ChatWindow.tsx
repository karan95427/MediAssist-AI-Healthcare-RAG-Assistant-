import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  askQuestion,
  clearConversationHistory,
  fetchConversationHistory,
  type ConversationItem,
} from "../services/assistantService";
import LoadingSpinner from "./LoadingSpinner";
import MessageBubble from "./MessageBubble";

type ChatTranscriptItem =
  | { kind: "user"; id: string; content: string }
  | { kind: "assistant"; id: string; content: string; mode?: string };

const starterPrompts = [
  "What is HbA1c?",
  "Explain my report in simple words.",
  "What questions should I ask my doctor?",
];

function ChatWindow() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ConversationItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setIsLoadingHistory(true);
        const data = await fetchConversationHistory();
        setHistory(data);
      } catch {
        setError("Unable to load conversation history.");
      } finally {
        setIsLoadingHistory(false);
      }
    };

    void loadHistory();
  }, []);

  const transcript = useMemo<ChatTranscriptItem[]>(() => {
    return [...history].reverse().flatMap((entry) => [
      { kind: "user" as const, id: `user-${entry.id}`, content: entry.question },
      { kind: "assistant" as const, id: `assistant-${entry.id}`, content: entry.answer, mode: entry.mode },
    ]);
  }, [history]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript.length, isSending]);

  const submitQuestion = async (value: string) => {
    const trimmedQuestion = value.trim();
    if (!trimmedQuestion || isSending) {
      return;
    }

    setError(null);
    setIsSending(true);
    try {
      const response = await askQuestion(trimmedQuestion);
      const optimisticEntry: ConversationItem = {
        id: Date.now(),
        question: trimmedQuestion,
        answer: response.answer,
        mode: response.mode,
        sources: response.sources,
        created_at: new Date().toISOString(),
      };
      setHistory((current) => [optimisticEntry, ...current]);
      setQuestion("");
    } catch {
      setError("Unable to generate an answer right now.");
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submitQuestion(question);
  };

  const handleClearHistory = async () => {
    if (history.length === 0 || isClearing) {
      return;
    }

    setError(null);
    setIsClearing(true);
    try {
      await clearConversationHistory();
      setHistory([]);
    } catch {
      setError("Unable to clear conversation history.");
    } finally {
      setIsClearing(false);
    }
  };

  const latestHistory = history.slice(0, 6);

  return (
    <section className="grid w-full gap-3 lg:grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="hidden min-h-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:flex lg:flex-col">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase text-emerald-600 dark:text-emerald-400">History</p>
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Recent chats</h2>
          </div>
          <button
            type="button"
            onClick={handleClearHistory}
            disabled={history.length === 0 || isClearing}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-rose-300 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-45 dark:border-slate-700 dark:text-slate-300 dark:hover:border-rose-500 dark:hover:text-rose-300"
          >
            {isClearing ? "Clearing" : "Clear"}
          </button>
        </div>

        <div className="mt-4 flex-1 space-y-2 overflow-y-auto pr-1">
          {isLoadingHistory ? <LoadingSpinner /> : null}
          {!isLoadingHistory && latestHistory.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
              Your questions will appear here.
            </p>
          ) : null}
          {latestHistory.map((entry) => (
            <button
              key={entry.id}
              type="button"
              onClick={() => setQuestion(entry.question)}
              className="block w-full rounded-2xl border border-slate-200 p-3 text-left transition hover:border-emerald-300 hover:bg-emerald-50 dark:border-slate-800 dark:hover:border-emerald-600 dark:hover:bg-emerald-950/40"
            >
              <p className="line-clamp-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{entry.question}</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {new Date(entry.created_at).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>
      </aside>

      <div className="flex min-h-[calc(100vh-100px)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-200 px-4 py-4 dark:border-slate-800 sm:px-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase text-emerald-600 dark:text-emerald-400">Medical chatbot</p>
              <h1 className="text-xl font-semibold text-slate-950 dark:text-white">Ask MediAssist</h1>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                Local Qwen LoRA ready
              </span>
              <button
                type="button"
                onClick={handleClearHistory}
                disabled={history.length === 0 || isClearing}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-rose-300 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-45 dark:border-slate-700 dark:text-slate-300 dark:hover:border-rose-500 dark:hover:text-rose-300 lg:hidden"
              >
                {isClearing ? "Clearing" : "Clear history"}
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto bg-slate-50 px-3 py-5 dark:bg-slate-950 sm:px-6">
          <div className="mx-auto flex max-w-4xl flex-col gap-4">
            {transcript.length === 0 && !isLoadingHistory ? (
              <div className="mx-auto max-w-2xl py-10 text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500 text-lg font-bold text-white shadow-sm">
                  MA
                </div>
                <h2 className="mt-5 text-2xl font-semibold text-slate-950 dark:text-white">Start a healthcare conversation</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                  Ask about general health topics or uploaded report content. For urgent symptoms or treatment decisions, contact a qualified clinician.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {starterPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => void submitQuestion(prompt)}
                      className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-emerald-600 dark:hover:text-emerald-300"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {transcript.map((item) => (
              <MessageBubble
                key={item.id}
                role={item.kind === "user" ? "user" : "assistant"}
                content={item.content}
                mode={item.kind === "assistant" ? item.mode : undefined}
              />
            ))}

            {isSending ? <MessageBubble role="assistant" content="Thinking..." isPending /> : null}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <form className="border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 sm:p-4" onSubmit={handleSubmit}>
          {error ? <p className="mb-3 text-sm font-medium text-rose-600 dark:text-rose-300">{error}</p> : null}
          <div className="mx-auto flex max-w-4xl items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 focus-within:border-emerald-400 dark:border-slate-700 dark:bg-slate-950 dark:focus-within:border-emerald-500">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={1}
              placeholder="Message MediAssist..."
              className="max-h-36 min-h-11 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400 dark:text-white dark:placeholder:text-slate-500"
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submitQuestion(question);
                }
              }}
            />
            <button
              type="submit"
              disabled={isSending || question.trim().length === 0}
              className="h-11 rounded-xl bg-emerald-500 px-5 text-sm font-semibold text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSending ? "Sending" : "Send"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

export default ChatWindow;
