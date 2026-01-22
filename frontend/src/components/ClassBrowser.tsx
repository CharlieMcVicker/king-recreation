"use client";

import { useState, useMemo } from "react";
import { ChevronDown, Search, Book, Layers, Folder } from "lucide-react";

interface VerbData {
  definition: string;
  h_grade_root: string;
  subvariant: string;
  corpusForms: {
    present: string;
    present_1sg: string;
    imperfective: string;
    perfective: string;
    imperative: string;
    infinitive: string;
  };
}

// [UPDATED] Hierarchical data structure
export interface ClassHierarchy {
  [abstractClass: string]: {
    [macroClass: string]: VerbData[];
  };
}

interface ClassBrowserProps {
  data: ClassHierarchy;
}

export default function ClassBrowser({ data }: ClassBrowserProps) {
  const [selectedAbstractClass, setSelectedAbstractClass] =
    useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");

  const abstractClasses = useMemo(() => Object.keys(data).sort(), [data]);

  const selectedClassData = useMemo(() => {
    if (!selectedAbstractClass) return null;
    return data[selectedAbstractClass];
  }, [selectedAbstractClass, data]);

  // Aggregate all verbs for search, or just list them by macro class
  const filteredGroups = useMemo(() => {
    if (!selectedClassData) return null;

    const groups: Record<string, VerbData[]> = {};
    let hasMatches = false;

    Object.entries(selectedClassData).forEach(([macroName, verbs]) => {
      let filtered = verbs;
      if (searchTerm) {
        const lower = searchTerm.toLowerCase();
        filtered = verbs.filter(
          (v) =>
            v.definition.toLowerCase().includes(lower) ||
            v.subvariant.toLowerCase().includes(lower)
        );
      }
      if (filtered.length > 0) {
        groups[macroName] = filtered;
        hasMatches = true;
      }
    });

    return { groups, hasMatches };
  }, [selectedClassData, searchTerm]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            Class Family Explorer
          </h1>
          <p className="text-slate-400 text-lg">
            Browse verbs grouped by their abstract class families.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Controls */}
          <div className="md:col-span-1 space-y-6">
            <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-6 shadow-xl text-sm">
              <label className="block font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Select Class Family
              </label>
              <div className="relative">
                <select
                  value={selectedAbstractClass}
                  onChange={(e) => setSelectedAbstractClass(e.target.value)}
                  className="w-full appearance-none bg-slate-800 border border-slate-700 text-slate-100 py-3 px-4 pr-10 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-slate-600 transition-colors cursor-pointer"
                >
                  <option value="" disabled>
                    Choose a family...
                  </option>
                  {abstractClasses.map((cls) => (
                    <option key={cls} value={cls}>
                      {cls}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
                  <ChevronDown className="h-5 w-5" />
                </div>
              </div>

              {selectedAbstractClass && (
                <div className="mt-6 animate-in fade-in slide-in-from-top-4 duration-300">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Filter verbs..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full bg-slate-800 border-none text-slate-100 py-2.5 pl-9 pr-4 rounded-xl placeholder:text-slate-600 focus:ring-2 focus:ring-blue-500/50 transition-all font-medium text-sm"
                    />
                  </div>
                </div>
              )}
            </div>

            {selectedAbstractClass && (
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
                <div className="flex items-center gap-3 text-blue-400 mb-2">
                  <Folder className="h-5 w-5" />
                  <span className="font-semibold text-lg">
                    {selectedAbstractClass} Family
                  </span>
                </div>
                <div className="text-sm text-slate-400 space-y-1 mt-3">
                  {Object.keys(data[selectedAbstractClass]).map((macro) => (
                    <div key={macro} className="flex items-center gap-2">
                      <Layers className="h-3 w-3 opacity-50" />
                      <span>{macro}</span>
                      <span className="text-slate-600 text-xs">
                        ({data[selectedAbstractClass][macro].length})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Results Table */}
          <div className="md:col-span-3 space-y-8">
            {!selectedAbstractClass ? (
              <div className="h-96 flex flex-col items-center justify-center text-slate-600 bg-slate-900/30 rounded-3xl border-2 border-dashed border-slate-800">
                <Book className="h-16 w-16 mb-4 opacity-50" />
                <p className="text-xl font-medium">
                  Select a class family to begin
                </p>
              </div>
            ) : !filteredGroups?.hasMatches ? (
              <div className="p-12 text-center text-slate-500 bg-slate-900 border border-slate-800 rounded-2xl">
                No verbs match your search.
              </div>
            ) : (
              // Iterate over each macro class group
              Object.entries(filteredGroups.groups)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([macroName, verbs]) => (
                  <div
                    key={macroName}
                    className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in duration-500"
                  >
                    <div className="bg-slate-900/80 border-b border-slate-800 p-4 flex items-center gap-3 sticky top-0 backdrop-blur-md z-10">
                      <Layers className="h-5 w-5 text-blue-400" />
                      <h2 className="font-bold text-lg text-slate-200">
                        {macroName}
                      </h2>
                      <span className="bg-slate-800 text-slate-400 text-xs px-2 py-0.5 rounded-full">
                        {verbs.length} verbs
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-950/30 border-b border-slate-800">
                            <th className="p-4 pl-6 font-semibold text-slate-400 uppercase text-xs tracking-wider w-1/3">
                              Verb & Subvariant
                            </th>
                            <th className="p-4 font-semibold text-slate-400 uppercase text-xs tracking-wider">
                              Corpus Forms
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {verbs.map((verb, idx) => (
                            <tr
                              key={idx}
                              className="group hover:bg-slate-800/50 transition-colors"
                            >
                              <td className="p-6 align-top">
                                <div className="flex flex-col gap-2">
                                  <span className="font-bold text-lg text-slate-200 group-hover:text-blue-300 transition-colors">
                                    {verb.definition}
                                  </span>
                                  <span className="text-sm font-mono text-slate-400">
                                    {verb.h_grade_root}
                                  </span>
                                  {verb.subvariant && (
                                    <span className="inline-flex self-start px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                                      {verb.subvariant}
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="p-6">
                                <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
                                  <FormRow
                                    label="Pres"
                                    value={verb.corpusForms.present}
                                  />
                                  <FormRow
                                    label="1sg"
                                    value={verb.corpusForms.present_1sg}
                                  />
                                  <FormRow
                                    label="Impf"
                                    value={verb.corpusForms.imperfective}
                                  />
                                  <FormRow
                                    label="Perf"
                                    value={verb.corpusForms.perfective}
                                  />
                                  <FormRow
                                    label="Imp"
                                    value={verb.corpusForms.imperative}
                                  />
                                  <FormRow
                                    label="Inf"
                                    value={verb.corpusForms.infinitive}
                                  />
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function FormRow({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div className="flex items-baseline gap-3">
      <span className="text-xs font-bold text-slate-500 uppercase w-8 text-right shrink-0">
        {label}
      </span>
      <span className="font-mono text-slate-300">{value}</span>
    </div>
  );
}
