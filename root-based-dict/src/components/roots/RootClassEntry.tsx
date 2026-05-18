"use client";

import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  DerivationalConnection,
  resolveClassEndings,
  getEndingSlug,
} from "@/lib/data-shared";
import CorpusTable from "./CorpusTable";
import { ChevronLeft, GitBranch } from "lucide-react";
import { ConfigFlags } from "@/app/reconstructable-verbs/ConfigFlags";
import Link from "next/link";

interface RootClassEntryProps {
  verbs: (ReconstructableVerb & { id: number })[];
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
  connections: DerivationalConnection[];
  allVerbs: ReconstructableVerb[];
}

interface VerbRowProps {
  verb: ReconstructableVerb & { id: number };
  dictionary: DictionaryEntry[];
  depth?: number;
  label?: string;
}

function VerbRow({ verb, dictionary, depth = 0, label }: VerbRowProps) {
  // Recursive render of children
  const hasChildren = verb.derivations && verb.derivations.length > 0;

  return (
    <div className={`flex flex-col gap-6 ${depth > 0 ? "mt-6" : ""}`}>
      <div className="flex flex-col gap-3">
        {/* Header line for nested items */}
        {label && (
          <h5 className="text-sm font-semibold text-gray-900 dark:text-gray-100 italic bg-indigo-50/50 dark:bg-indigo-900/10 px-3 py-1 rounded w-fit">
            {label}
          </h5>
        )}

        <h4 className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest leading-none">
          With <ConfigFlags config={verb.morphology.config} verb={verb} />
        </h4>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Definition & Pills Slot */}
          <div className="lg:col-span-5 flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <div className="text-lg font-medium text-gray-900 dark:text-gray-100">
                {verb.meta.definition}
              </div>
              {verb.meta.corpus_id && (
                <Link
                  href={`/select-roots?corpusId=${verb.meta.corpus_id}`}
                  className="p-1.5 rounded-lg text-zinc-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all"
                  title="Change derivation"
                >
                  <GitBranch className="w-4 h-4" />
                </Link>
              )}
            </div>
          </div>

          {/* Forms Slot */}
          <div className="lg:col-span-7">
            <CorpusTable verb={verb} dictionary={dictionary} />
          </div>
        </div>
      </div>

      {/* Children Section */}
      {hasChildren && (
        <div className="pl-6 border-l-2 border-indigo-50 dark:border-indigo-900/30 flex flex-col gap-8">
          {/* Derivation Children */}
          {verb.derivations && verb.derivations.length > 0 && (
            <div className="flex flex-col gap-6">
              {verb.derivations.map((child) => (
                <VerbRow
                  key={child.meta.entry_no ?? child.meta.definition} // Fallback key
                  verb={child as ReconstructableVerb & { id: number }}
                  dictionary={dictionary}
                  depth={depth + 1}
                  label={`Derived: [${child.morphology.class_name}]`}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function RootClassEntry({
  verbs,
  classes,
  dictionary,
}: RootClassEntryProps) {
  // All verbs in this group share the same class_name
  const className = verbs?.[0]?.morphology.class_name;
  if (!className) return null; // Safety check

  const endings = resolveClassEndings(className, classes);

  // Extract macro name for the header
  const macroName = className.match(/^([^\[]+)/)?.[1] || className;
  const endingSlug = endings ? getEndingSlug(endings) : null;

  if (!endings) return null;

  return (
    <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-sm">
      {/* Class Header */}
      <div className="bg-gray-50 dark:bg-zinc-800/50 px-6 py-4 border-b border-gray-200 dark:border-zinc-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          With{" "}
          <Link
            href={endingSlug ? `/endings/${endingSlug}` : "#"}
            className="text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            [{macroName}]
          </Link>
        </h3>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-zinc-800">
        {verbs.map((verb) => (
          <div key={verb.id} className="p-6">
            <VerbRow verb={verb} dictionary={dictionary} />
          </div>
        ))}
      </div>
    </div>
  );
}
