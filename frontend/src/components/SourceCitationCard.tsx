import type { SourceCitation } from "../services/assistantService";

type SourceCitationCardProps = {
  source: SourceCitation;
};

function SourceCitationCard({ source }: SourceCitationCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
        <span>{source.document}</span>
        <span>Page {source.page}</span>
        <span>Similarity {source.similarity.toFixed(2)}</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{source.snippet}</p>
    </div>
  );
}

export default SourceCitationCard;
