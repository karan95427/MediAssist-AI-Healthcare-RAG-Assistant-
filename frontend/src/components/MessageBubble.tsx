import ReactMarkdown from "react-markdown";

type MessageBubbleProps = {
  role: "assistant" | "user";
  content: string;
  mode?: string;
  isPending?: boolean;
};

function MessageBubble({ role, content, mode, isPending = false }: MessageBubbleProps) {
  const isAssistant = role === "assistant";

  return (
    <div className={`flex gap-3 ${isAssistant ? "justify-start" : "justify-end"}`}>
      {isAssistant ? (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500 text-xs font-bold text-white">
          MA
        </div>
      ) : null}

      <div
        className={`max-w-[min(46rem,85%)] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${
          isAssistant
            ? "border border-slate-200 bg-white text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
            : "bg-slate-950 text-white dark:bg-emerald-500 dark:text-white"
        }`}
      >
        {mode ? <p className="mb-2 text-xs font-semibold uppercase text-emerald-600 dark:text-emerald-300">{mode}</p> : null}
        {isPending ? (
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            <span>{content}</span>
          </div>
        ) : (
          <div className={`prose prose-sm max-w-none ${isAssistant ? "dark:prose-invert" : "prose-invert"}`}>
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
