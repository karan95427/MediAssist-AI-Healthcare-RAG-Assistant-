function DashboardPage() {
  const stats = [
    { label: "Registered Users", value: "01" },
    { label: "Indexed Documents", value: "00" },
    { label: "RAG Sessions", value: "00" },
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-6 md:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-3xl bg-white p-6 shadow-panel">
            <p className="text-sm text-slate-500">{stat.label}</p>
            <p className="mt-3 text-3xl font-semibold text-slate-900">{stat.value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-3xl bg-white p-6 shadow-panel">
          <p className="text-sm font-medium text-brand-600">Platform Status</p>
          <h3 className="mt-1 text-lg font-semibold text-slate-900">MVP foundation is ready</h3>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Authentication, database foundations, routing, and the clinician dashboard shell are scaffolded. AI
            retrieval, embeddings, and ingestion are intentionally deferred to the next milestone.
          </p>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-panel">
          <p className="text-sm font-medium text-brand-600">Next Milestones</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>Implement secure document upload pipeline</li>
            <li>Connect vector indexing and retrieval layer</li>
            <li>Wire Gemini orchestration behind service interfaces</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

export default DashboardPage;
