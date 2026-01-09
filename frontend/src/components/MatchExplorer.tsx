"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle, XCircle, ArrowRight, Info } from "lucide-react";

interface Match {
  definition: string;
  class: string;
  scope: string;
  is_consistent?: boolean | null;
  mismatch_details?: string | null;
  stem_final_match_present: string;
  stem_final_match_imperfective: string;
  stem_final_match_perfective: string;
  stem_final_match_imperative: string;
  stem_final_match_infinitive: string;
}

interface MatchExplorerProps {
  matches: Match[];
  classPattern: any;
  corpus?: Record<string, any>;
  coveredVerbs?: string[];
}

export default function MatchExplorer({
  matches,
  classPattern,
  corpus,
  coveredVerbs = [],
}: MatchExplorerProps) {
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(
    matches[0] || null
  );
  const [scopeFilter, setScopeFilter] = useState<
    "all" | "full" | "ending" | "reconstructs"
  >("all");
  const [hideCovered, setHideCovered] = useState(false);

  const coveredSet = new Set(coveredVerbs);

  const filteredMatches = matches.filter((m) => {
    if (hideCovered && coveredSet.has(m.definition)) return false;
    if (scopeFilter === "all") return true;
    return m.scope === scopeFilter;
  });

  const forms = [
    { key: "present", label: "Present" },
    { key: "imperfective", label: "Imperfective" },
    { key: "perfective", label: "Perfective" },
    { key: "imperative", label: "Imperative" },
    { key: "infinitive", label: "Infinitive" },
  ];

  const getScopeColor = (scope: string) => {
    switch (scope) {
      case "full":
        return "bg-emerald-500";
      case "reconstructs":
        return "bg-indigo-600";
      case "ending":
        return "bg-amber-500";
      default:
        return "bg-gray-300";
    }
  };

  const getScopeLabel = (scope: string) => {
    switch (scope) {
      case "full":
        return "Full Match";
      case "reconstructs":
        return "Gold Standard";
      case "ending":
        return "Near Miss";
      default:
        return scope;
    }
  };

  const getScopeBadgeClass = (scope: string) => {
    switch (scope) {
      case "full":
        return "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400";
      case "reconstructs":
        return "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 ring-1 ring-indigo-500/30";
      case "ending":
        return "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400";
      default:
        return "bg-gray-100 dark:bg-zinc-800 text-gray-600";
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-[600px]">
      {/* Scrollable List */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm flex flex-col h-full overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center justify-between">
          <h3 className="font-semibold text-sm">
            Verbs ({filteredMatches.length})
          </h3>
          <select
            value={scopeFilter}
            onChange={(e) => setScopeFilter(e.target.value as any)}
            className="text-xs bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Scopes</option>
            <option value="full">Full Match</option>
            <option value="reconstructs">Reconstructs</option>
            <option value="ending">Near Miss</option>
          </select>
          <div className="flex items-center gap-1.5 ml-3">
            <input
              type="checkbox"
              id="hideCovered"
              checked={hideCovered}
              onChange={(e) => setHideCovered(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 w-3.5 h-3.5"
            />
            <label
              htmlFor="hideCovered"
              className="text-[10px] text-gray-500 select-none cursor-pointer font-medium uppercase tracking-wide"
            >
              Hide Covered
            </label>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-zinc-800">
          {filteredMatches.map((match, i) => (
            <button
              key={`${match.definition}-${i}`}
              onClick={() => setSelectedMatch(match)}
              className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors ${
                selectedMatch?.definition === match.definition
                  ? "bg-indigo-50/50 dark:bg-indigo-900/10 border-r-2 border-indigo-500"
                  : ""
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${getScopeColor(
                    match.scope
                  )}`}
                />
                <span className="text-sm font-medium line-clamp-1">
                  {match.definition}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {match.scope !== "full" && (
                  <span
                    className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                      match.scope === "reconstructs"
                        ? "text-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-900/30"
                        : "text-amber-600 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-900/30"
                    }`}
                  >
                    {match.scope === "reconstructs" ? "Recon" : "Miss"}
                  </span>
                )}
                <ArrowRight
                  className={`w-4 h-4 transition-transform ${
                    selectedMatch?.definition === match.definition
                      ? "translate-x-1 text-indigo-500"
                      : "text-gray-300"
                  }`}
                />
              </div>
            </button>
          ))}
          {filteredMatches.length === 0 && (
            <div className="p-8 text-center text-gray-400 text-sm italic">
              No matches found for this filter.
            </div>
          )}
        </div>
      </div>

      {/* Detail View */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm flex flex-col h-full overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20">
          <h3 className="font-semibold text-sm">Match Details</h3>
        </div>

        {selectedMatch ? (
          <div className="p-6 space-y-8 flex-1 overflow-y-auto">
            <div>
              <div className="flex items-start justify-between gap-4 mb-2">
                <h4 className="text-lg font-bold leading-tight">
                  {selectedMatch.definition}
                </h4>
                <Link
                  href={`/explorer/entry/${encodeURIComponent(
                    selectedMatch.definition
                  )}`}
                  className="shrink-0 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 flex items-center gap-1 bg-indigo-50 dark:bg-indigo-900/20 px-2 py-1 rounded transition-colors"
                >
                  View Entry <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
              <div className="flex gap-2">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${getScopeBadgeClass(
                    selectedMatch.scope
                  )}`}
                >
                  {getScopeLabel(selectedMatch.scope)}
                </span>
                {selectedMatch.is_consistent !== null && (
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                      selectedMatch.is_consistent
                        ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400"
                        : "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
                    }`}
                  >
                    {selectedMatch.is_consistent
                      ? "Consistent Root"
                      : "Inconsistent Root"}
                  </span>
                )}
              </div>
            </div>

            {selectedMatch.mismatch_details && (
              <div className="p-3 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/20 rounded text-[11px] text-red-800 dark:text-red-200 font-mono">
                <strong>Root Mismatch:</strong> {selectedMatch.mismatch_details}
              </div>
            )}

            <div className="space-y-4">
              <h5 className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">
                Form-level Match Results
              </h5>
              <div className="space-y-3">
                {forms.map((form) => {
                  const rawValue =
                    selectedMatch[
                      `stem_final_match_${form.key}` as keyof Match
                    ];
                  const isMatch =
                    String(rawValue || "")
                      .trim()
                      .toLowerCase() === "true";
                  const actualForm =
                    corpus?.[selectedMatch.definition]?.[form.key];

                  return (
                    <div
                      key={form.key}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-zinc-950 rounded border border-gray-100 dark:border-zinc-800"
                    >
                      <div className="flex flex-col gap-1">
                        <span className="text-xs font-semibold capitalize">
                          {form.label}
                        </span>
                        {actualForm && (
                          <span className="text-lg font-serif text-gray-800 dark:text-zinc-200 leading-none py-1">
                            {actualForm}
                          </span>
                        )}
                        <span className="text-[10px] font-mono text-gray-400">
                          Pattern: {classPattern[form.key] || "-"}
                        </span>
                      </div>
                      {isMatch ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/20 rounded-lg">
              <div className="flex gap-3">
                <Info className="w-5 h-5 text-amber-500 shrink-0" />
                <div className="text-xs text-amber-800 dark:text-amber-200 leading-relaxed">
                  <strong>Stem Final Rule:</strong> For a "full" match, all five
                  forms must match the class pattern at the stem-final boundary.
                  If any form shows an{" "}
                  <XCircle className="w-3 h-3 inline pb-0.5" />, the match scope
                  is limited to "ending" (Near Miss).
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-gray-400">
            <Info className="w-12 h-12 mb-4 opacity-20" />
            <p className="text-sm italic">
              Select a verb to see detailed matching results.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
