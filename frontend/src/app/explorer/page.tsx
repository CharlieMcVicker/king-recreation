import {
  getClasses,
  getMatches,
  getNearMisses,
  getCorpus,
  getConsistencyAnalysis,
  resolveClassEndings,
} from "@/lib/data";
import {
  Search,
  BookOpen,
  XCircle,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Info,
} from "lucide-react";
import Link from "next/link";
import NavSelect from "@/components/NavSelect";
import MatchExplorer from "@/components/MatchExplorer";

export const dynamic = "force-dynamic";

export default async function ExplorerPage({
  searchParams,
}: {
  searchParams: Promise<{ class?: string; strictness?: string }>;
}) {
  const params = await searchParams;
  const selectedClass = params.class;
  const classes = await getClasses();
  const allMatchesData = await getMatches(); // [SWITCHED] from getInitialMatches
  const consistencyData = await getConsistencyAnalysis();
  const nearMisses = await getNearMisses();
  const corpus = await getCorpus();

  // Group classes for NavSelect
  const groupedClasses = classes.reduce((acc: any[], c: any) => {
    const family = c.class;
    let group = acc.find((g) => g.group === family);
    if (!group) {
      group = { group: family, items: [] };
      acc.push(group);
    }
    group.items.push({
      label: c.macro_name || c.class,
      value: c.macro_name || c.class,
    });
    return acc;
  }, []);

  const consistencyMap = consistencyData.reduce((acc: any, row: any) => {
    acc[`${row.definition}-${row.assigned_class}`] = row;
    return acc;
  }, {});

  const allMatches = allMatchesData.map((m: any) => {
    const consistency = consistencyMap[`${m.definition}-${m.class}`];
    return {
      ...m,
      is_consistent: consistency
        ? String(consistency.is_consistent).toLowerCase() === "true"
        : null,
      mismatch_details: consistency ? consistency.mismatch_details : null,
    };
  });

  const corpusMap = corpus.reduce((acc: any, row: any) => {
    acc[row.definition] = row;
    return acc;
  }, {});

  const classData = selectedClass
    ? resolveClassEndings(selectedClass, classes)
    : null;

  const matches = selectedClass
    ? allMatches.filter(
        (m: any) =>
          m.class === selectedClass &&
          (m.scope === "full" ||
            m.scope === "ending" ||
            m.scope === "reconstructs")
      )
    : [];

  const coveredVerbs = selectedClass
    ? allMatches
        .filter((m: any) => m.class !== selectedClass && m.scope === "full")
        .map((m: any) => m.definition)
    : [];

  const nearMissData = selectedClass
    ? nearMisses.filter((nm: any) => nm.class === selectedClass)
    : [];

  const nearMissVerbs = selectedClass
    ? allMatches.filter(
        (m: any) => m.class === selectedClass && m.scope === "ending"
      )
    : [];

  return (
    <div className="flex flex-col h-full gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Class Explorer</h2>
          <p className="text-gray-500 dark:text-zinc-400">
            Deep dive into specific verb classes and their matching patterns.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative w-64">
            <NavSelect
              name="class"
              defaultValue={selectedClass || ""}
              placeholder="Select a class..."
              options={groupedClasses}
              className="w-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {!selectedClass ? (
        <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-2xl bg-gray-50/50 dark:bg-zinc-900/20 p-12 text-center">
          <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-full text-indigo-600 dark:text-indigo-400 mb-4">
            <Search className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold">No Class Selected</h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400 max-w-xs mx-auto mt-2">
            Choose a verb class from the dropdown above to explore its patterns
            and matches.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Patterns and Specs */}
          <div className="xl:col-span-2 space-y-8">
            <section className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                <h3 className="font-semibold text-sm">
                  Class Pattern: {selectedClass}
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {[
                    "stem final",
                    "present",
                    "imperfective",
                    "perfective",
                    "imperative",
                    "infinitive",
                  ].map((field) => (
                    <div key={field} className="space-y-1">
                      <span className="text-[10px] font-bold uppercase text-gray-400 tracking-wider font-mono">
                        {field}
                      </span>
                      <div className="p-3 bg-gray-50 dark:bg-zinc-950 rounded border border-gray-100 dark:border-zinc-800 font-mono text-sm min-h-[40px] flex items-center">
                        {classData?.[field] || (
                          <span className="text-gray-300 dark:text-zinc-700">
                            -
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <MatchExplorer
              matches={matches}
              classPattern={classData}
              corpus={corpusMap}
              coveredVerbs={coveredVerbs}
            />
          </div>

          {/* Near-Miss Diagnosis */}
          <div className="space-y-8">
            <section className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500" />
                <h3 className="font-semibold text-sm">Near-Miss Diagnosis</h3>
              </div>
              <div className="p-6 space-y-6">
                {nearMissData.map((nm: any) => (
                  <div key={nm.class} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                        Failure Breakdown
                      </span>
                      <span className="text-[10px] text-gray-400">
                        {nm.match_count} matches
                      </span>
                    </div>
                    <div className="space-y-4">
                      {[
                        "present",
                        "imperfective",
                        "perfective",
                        "imperative",
                        "infinitive",
                      ].map((form) => {
                        const successRate = parseFloat(nm[`${form}_rate`]);
                        const failureRate = 1 - successRate;
                        return (
                          <div key={form} className="space-y-1">
                            <div className="flex justify-between text-[10px]">
                              <span className="capitalize">{form}</span>
                              <span
                                className={
                                  failureRate > 0.3
                                    ? "text-red-500 font-bold"
                                    : "text-gray-500"
                                }
                              >
                                {Math.round(failureRate * 100)}% failure
                              </span>
                            </div>
                            <div className="h-1.5 w-full bg-gray-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                  failureRate > 0.5
                                    ? "bg-red-500"
                                    : failureRate > 0.2
                                    ? "bg-amber-500"
                                    : "bg-emerald-500"
                                }`}
                                style={{ width: `${failureRate * 100}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
                {nearMissData.length === 0 && (
                  <div className="text-center py-6">
                    <Info className="w-8 h-8 text-gray-200 mx-auto mb-2" />
                    <p className="text-xs text-gray-400 italic">
                      No near-miss data available for this class.
                    </p>
                  </div>
                )}
              </div>
            </section>

            <section className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <ArrowRight className="w-4 h-4" />
                <h3 className="font-semibold text-sm">Near-Match Verbs</h3>
              </div>
              <div className="p-4">
                <p className="text-[10px] text-gray-400 mb-4 italic leading-relaxed text-center">
                  Verbs that match the class ending but fail the stem final
                  verification.
                </p>
                <div className="space-y-2 max-h-[300px] overflow-auto pr-2">
                  {nearMissVerbs.map((m: any, i: number) => (
                    <div
                      key={i}
                      className="p-2 border border-gray-100 dark:border-zinc-800 rounded text-xs hover:border-indigo-200 dark:hover:border-indigo-900/50 transition-colors"
                    >
                      {m.definition}
                    </div>
                  ))}
                  {nearMissVerbs.length === 0 && (
                    <div className="text-center py-4 text-xs text-gray-400 italic">
                      None found.
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
