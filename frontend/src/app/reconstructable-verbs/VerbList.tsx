"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { ReconstructableVerb } from "@/lib/data-shared";
import { ConfigFlags } from "./ConfigFlags";

interface VerbListProps {
  verbs: ReconstructableVerb[];
}

export function VerbList({ verbs }: VerbListProps) {
  const [search, setSearch] = useState("");

  // Map first to preserve original index, then filter
  const filtered = verbs
    .map((v, i) => ({ ...v, originalIndex: i }))
    .filter((v) => {
      const term = search.toLowerCase();
      const configFlags = [];
      if (v.config?.pre?.translocutive) configFlags.push("tr");
      if (v.config?.pre?.partitive) configFlags.push("pa");
      if (v.config?.pre?.distributive) configFlags.push("di");
      if (v.config?.pron?.use_3rd_person_object) configFlags.push("3obj");
      if (v.config?.pron?.use_ka_variant) configFlags.push("ka");
      if (v.config?.pron?.set_type)
        configFlags.push(`set ${v.config.pron.set_type.toLowerCase()}`);

      return (
        (v.definition?.toLowerCase().includes(term) ?? false) ||
        (v.class_name?.toLowerCase().includes(term) ?? false) ||
        (v.h_grade_root?.toLowerCase()?.includes(term) ?? false) ||
        (v.glottal_grade_root?.toLowerCase()?.includes(term) ?? false) ||
        configFlags.some((f) => f.includes(term))
      );
    })
    .sort((a, b) => (a.h_grade_root || "").localeCompare(b.h_grade_root || ""));

  // Limit display to 100 items for performance if not searching specific thing
  const displayVerbs = filtered.slice(0, 100);

  return (
    <div className="space-y-6">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search definitions, classes, or roots..."
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
          Showing {displayVerbs.length} of {filtered.length} matches
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayVerbs.map((verb) => (
          <Link
            href={`/reconstructable-verbs/${verb.originalIndex}`}
            key={verb.originalIndex}
            className="group block p-5 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-indigo-500 dark:hover:border-indigo-500 transition-all shadow-sm hover:shadow-md"
          >
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-start gap-2">
                <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
                  {verb.definition}
                </h3>
                <ConfigFlags config={verb.config} className="mt-1" />
              </div>

              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span className="px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 font-mono">
                  {verb.class_name}
                </span>
                <span className="font-mono text-gray-400">
                  {verb.h_grade_root}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-10 text-gray-500">
          No verbs found matching "{search}"
        </div>
      )}
    </div>
  );
}
