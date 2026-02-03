"use client";

import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  RootConnection,
  resolveClassEndings,
  getEndingSlug,
  getPronominalSetName,
} from "@/lib/data-shared";
import CorpusTable from "./CorpusTable";
import { ConfigFlags } from "@/app/reconstructable-verbs/ConfigFlags";
import Link from "next/link";

interface RootClassEntryProps {
  verbs: (ReconstructableVerb & { id: number })[];
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
  connections: RootConnection[];
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
  const hasChildren =
    (verb.middle_voice && verb.middle_voice.length > 0) ||
    (verb.derivations && verb.derivations.length > 0);

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
          With [{getPronominalSetName("present", verb.config.pron)}]
        </h4>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Definition & Pills Slot */}
          <div className="lg:col-span-5 flex flex-col gap-3">
            <div className="text-lg font-medium text-gray-900 dark:text-gray-100">
              {verb.definition}
            </div>

            <ConfigFlags config={verb.config} verb={verb} />
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
          {/* Middle Voice Children */}
          {verb.middle_voice && verb.middle_voice.length > 0 && (
            <div className="flex flex-col gap-6">
              {verb.middle_voice.map((child) => (
                <VerbRow
                  key={child.entry_no ?? child.definition} // Fallback key
                  verb={child as ReconstructableVerb & { id: number }}
                  dictionary={dictionary}
                  depth={depth + 1}
                  label="Middle Voice"
                />
              ))}
            </div>
          )}

          {/* Derivation Children */}
          {verb.derivations && verb.derivations.length > 0 && (
            <div className="flex flex-col gap-6">
              {verb.derivations.map((child) => (
                <VerbRow
                  key={child.entry_no ?? child.definition} // Fallback key
                  verb={child as ReconstructableVerb & { id: number }}
                  dictionary={dictionary}
                  depth={depth + 1}
                  label={`Derived: [${child.class_name}]`}
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
  const className = verbs?.[0]?.class_name;
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
