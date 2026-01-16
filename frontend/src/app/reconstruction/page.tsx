import { getMatches, getReconstructionFailures } from "@/lib/data";
import Link from "next/link";
import { AlertCircle, ChevronRight, Layers } from "lucide-react";

interface FailureRecord {
  corpus_id: number;
  definition: string;
  class: string;
  mismatch_details: string;
}

interface MatchRecord {
  corpus_id: number;
  definition: string;
  class: string;
  strictness: string;
  scope: string;
}

export default async function ReconstructionFailuresPage() {
  const matches = (await getMatches()) as MatchRecord[];
  const failures = (await getReconstructionFailures()) as FailureRecord[];

  const successfulIds = new Set(matches.map((m) => String(m.corpus_id)));

  // Filter out any failure that corresponds to a successful corpus_id
  const totalFailures = failures.filter(
    (f) => !successfulIds.has(String(f.corpus_id))
  );

  // Group by Class
  const failuresByClass: Record<string, FailureRecord[]> = {};
  totalFailures.forEach((f) => {
    if (!failuresByClass[f.class]) {
      failuresByClass[f.class] = [];
    }
    failuresByClass[f.class].push(f);
  });

  // Sort classes by number of failures (descending)
  const sortedClasses = Object.entries(failuresByClass).sort(
    ([, a], [, b]) => b.length - a.length
  );

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white p-6 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex items-center justify-between pb-6 border-b border-white/10">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-200 to-purple-200 bg-clip-text text-transparent flex items-center gap-3">
              <Layers className="w-8 h-8 text-indigo-300" />
              Reconstruction Failures Analysis
            </h1>
            <p className="mt-2 text-slate-400 text-sm">
              Analyzing{" "}
              <span className="text-white font-semibold">
                {totalFailures.length}
              </span>{" "}
              failures across{" "}
              <span className="text-white font-semibold">
                {sortedClasses.length}
              </span>{" "}
              classes. Grouped by class to identify systemic pattern mismatches.
            </p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-colors text-sm font-medium backdrop-blur-sm"
          >
            ← Back to Dashboard
          </Link>
        </header>

        <div className="space-y-8">
          {sortedClasses.map(([className, classFailures]) => (
            <div
              key={className}
              className="rounded-xl bg-slate-900/40 border border-white/10 overflow-hidden shadow-xl backdrop-blur-sm"
            >
              <div className="px-6 py-4 bg-white/5 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-mono font-bold text-indigo-300">
                    {className}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {classFailures.length} failures
                  </span>
                </div>
              </div>

              <div className="p-4 grid grid-cols-1 gap-3">
                {classFailures.map((fail, idx) => {
                  // Parse mismatch details for nicer display
                  // Expected format: "present: expected 'x', got ['y']; ..."
                  const reasons = fail.mismatch_details.split("; ").map((r) => {
                    const parts = r.split(": ");
                    return {
                      form: parts[0],
                      detail: parts.slice(1).join(": "),
                    };
                  });

                  return (
                    <div
                      key={fail.corpus_id + "-" + idx}
                      className="group flex flex-col md:flex-row md:items-start gap-4 p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all"
                    >
                      <div className="md:w-1/4 shrink-0">
                        <Link
                          href={`/explorer/entry/${fail.corpus_id}`}
                          className="font-semibold text-slate-200 text-sm hover:text-indigo-400 transition-colors"
                        >
                          {fail.definition}
                        </Link>
                        <div className="text-xs text-slate-500 font-mono mt-1">
                          ID: {fail.corpus_id}
                        </div>
                      </div>

                      <div className="flex-1 flex flex-wrap gap-2">
                        {reasons.map((reason, rIdx) => (
                          <div
                            key={rIdx}
                            className="inline-flex items-center text-xs rounded bg-rose-950/30 border border-rose-900/30 px-2 py-1"
                          >
                            <span className="font-mono text-rose-300 font-bold mr-2 uppercase tracking-wider text-[10px] opacity-80">
                              {reason.form}
                            </span>
                            <span
                              className="text-rose-100/80 truncate max-w-xs"
                              title={reason.detail}
                            >
                              {reason.detail}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {sortedClasses.length === 0 && (
            <div className="text-center py-20 bg-white/5 rounded-3xl border border-white/5 border-dashed">
              <p className="text-2xl text-slate-500 font-light">
                No validation failures found!
              </p>
              <p className="text-slate-600 mt-2">
                All verbs matched at least one class.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
