"use client";

import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  resolveClassEndings,
} from "@/lib/data-shared";
import CorpusTable from "../roots/CorpusTable";
import { ConfigFlags } from "@/app/reconstructable-verbs/ConfigFlags";

import Link from "next/link";

interface EndingRootEntryProps {
  root: {
    h_grade_root: string;
    glottal_grade_root: string | null;
    root_slug: string;
    configs: {
      class_name: string;
      verbs: (ReconstructableVerb & { id: number })[];
    }[];
  };
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
}

export default function EndingRootEntry({
  root,
  classes,
  dictionary,
}: EndingRootEntryProps) {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-sm">
      {/* Root Header */}
      <div className="bg-gray-50 dark:bg-zinc-800/50 px-6 py-4 border-b border-gray-200 dark:border-zinc-800 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Root:{" "}
          <Link
            href={`/${root.root_slug}`}
            className="text-indigo-600 dark:text-indigo-400 font-bold hover:underline"
          >
            {root.h_grade_root}
          </Link>
          {root.glottal_grade_root && (
            <span className="text-gray-400 dark:text-zinc-500 italic ml-2">
              ({root.glottal_grade_root})
            </span>
          )}
        </h3>
        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
          {root.configs.length}{" "}
          {root.configs.length === 1 ? "config" : "configs"}
        </div>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-zinc-800">
        {root.configs.map((config, configIdx) => (
          <div key={configIdx} className="p-6 bg-white dark:bg-zinc-900">
            <div className="mb-4">
              <span className="text-xs font-semibold px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                Class: {config.class_name}
              </span>
            </div>
            <div className="flex flex-col gap-8">
              {config.verbs.map((verb) => (
                <div
                  key={verb.id}
                  className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-6 last:pb-0 border-b last:border-0 border-gray-100 dark:border-zinc-800/50"
                >
                  {/* Definition & Pills Slot */}
                  <div className="lg:col-span-5 flex flex-col gap-3">
                    <div className="text-lg font-medium text-gray-900 dark:text-gray-100">
                      {verb.definition}
                    </div>

                    <ConfigFlags config={verb.morphology.config} verb={verb} />
                  </div>

                  {/* Forms Slot */}
                  <div className="lg:col-span-7">
                    <CorpusTable verb={verb} dictionary={dictionary} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
