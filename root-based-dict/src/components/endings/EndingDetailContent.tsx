"use client";

import {
  EndingGroup,
  ClassDefinition,
  DictionaryEntry,
} from "@/lib/data-shared";
import EndingRootEntry from "./EndingRootEntry";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

interface EndingDetailContentProps {
  endingGroup: EndingGroup;
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
}

export default function EndingDetailContent({
  endingGroup,
  classes,
  dictionary,
}: EndingDetailContentProps) {
  const endingKeys = [
    { label: "Present", key: "present" },
    { label: "Imperfective", key: "imperfective" },
    { label: "Perfective", key: "perfective" },
    { label: "Imperative", key: "imperative" },
    { label: "Infinitive", key: "infinitive" },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex flex-col gap-6">
        <Link
          href="/endings"
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-indigo-600 transition-colors w-fit"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Endings Dictionary
        </Link>

        <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm">
          <h1 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
            Aspect Endings Set
          </h1>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {endingKeys.map(({ label, key }) => (
              <div key={key} className="flex flex-col">
                <span className="text-xs text-gray-500 dark:text-zinc-500 mb-1">
                  {label}
                </span>
                <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                  -{endingGroup.endings[key] || "∅"}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 mt-4">
          {endingGroup.roots.map((root, rootIdx) => (
            <EndingRootEntry
              key={`${root.h_grade_root}-${rootIdx}`}
              root={root}
              classes={classes}
              dictionary={dictionary}
            />
          ))}
          {endingGroup.roots.length === 0 && (
            <div className="py-12 text-center text-gray-500 italic border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl">
              No verbs found for this set of endings.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
