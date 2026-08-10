"use client";

import React, { useState } from "react";
import {
  Book,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface LexicalHeroProps {
  data: any[]; // The derivations from getValidatedRootsRows filter
}

export default function LexicalHero({ data }: LexicalHeroProps) {
  const [isOpen, setIsOpen] = useState(true);

  if (!data || data.length === 0) return null;

  const main = data[0];
  const userSelected =
    data.find((d) => d.user_selected === "x") ||
    data.find((d) => d.pipeline_selected === "x") ||
    main;

  const rows = [
    { label: "Class", value: userSelected.class },
    { label: "Stem Type", value: userSelected.stem_type },
    { label: "H Grade", value: userSelected.h_grade },
    { label: "G Grade", value: userSelected.g_grade },
    { label: "Morpheme", value: userSelected.post_root_morpheme },
  ];

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-zinc-50 dark:bg-zinc-800/50 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2 font-semibold text-zinc-900 dark:text-zinc-100">
          <Book className="w-4 h-4 text-amber-500" />
          Lexical Identity
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {isOpen && (
        <div className="p-6">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-8">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 italic">
                "{main.definition}"
              </h2>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-xs font-mono text-zinc-500">
                  Corpus ID: {main.corpus_id}
                </span>
                {userSelected.user_selected === "x" ? (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 text-[10px] font-bold uppercase tracking-wider border border-emerald-100 dark:border-emerald-800/30">
                    <CheckCircle2 className="w-3 h-3" />
                    Approved
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400 text-[10px] font-bold uppercase tracking-wider border border-amber-100 dark:border-amber-800/30">
                    <AlertCircle className="w-3 h-3" />
                    Pipeline
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 flex-1 max-w-2xl">
              {rows.map((row, i) => (
                <div key={i} className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                    {row.label}
                  </div>
                  <div
                    className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate"
                    title={row.value}
                  >
                    {row.value || "-"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-zinc-50 dark:bg-zinc-800/30 rounded-lg p-4 border border-zinc-100 dark:border-zinc-800/50">
            <div className="flex items-start gap-3">
              <Info className="w-4 h-4 text-zinc-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  Reconstruction Summary
                </p>
                <div className="text-xs text-zinc-500 font-mono">
                  {userSelected.segmented_forms
                    ? Object.entries(JSON.parse(userSelected.segmented_forms))
                        .map(([k, v]) => `${k}:${v}`)
                        .join(" | ")
                    : "No reconstruction available."}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
