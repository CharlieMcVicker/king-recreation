"use client";

import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  resolveClassEndings,
} from "@/lib/data-shared";
import CorpusTable from "./CorpusTable";
import { ConfigFlags } from "@/app/reconstructable-verbs/ConfigFlags";

interface RootClassEntryProps {
  verbs: (ReconstructableVerb & { id: number })[];
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
}

export default function RootClassEntry({
  verbs,
  classes,
  dictionary,
}: RootClassEntryProps) {
  // All verbs in this group share the same class_name
  const className = verbs[0].class_name;
  const endings = resolveClassEndings(className, classes);

  // Extract macro name for the header
  const macroName = className.match(/^([^\[]+)/)?.[1] || className;

  if (!endings) return null;

  return (
    <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-sm">
      {/* Class Header */}
      <div className="bg-gray-50 dark:bg-zinc-800/50 px-6 py-4 border-b border-gray-200 dark:border-zinc-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          With{" "}
          <span className="text-indigo-600 dark:text-indigo-400">
            [{macroName}]
          </span>
        </h3>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-zinc-800">
        {verbs.map((verb) => (
          <div key={verb.id} className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Definition & Pills Slot */}
              <div className="lg:col-span-5 flex flex-col gap-3">
                <div className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  {verb.definition}
                </div>

                <ConfigFlags config={verb.config} />
              </div>

              {/* Forms Slot */}
              <div className="lg:col-span-7">
                <CorpusTable verb={verb} dictionary={dictionary} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
