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

export default function RootClassEntry({
  verbs,
  classes,
  dictionary,
  connections = [],
  allVerbs = [],
}: RootClassEntryProps) {
  // All verbs in this group share the same class_name
  const className = verbs?.[0]?.class_name;
  if (!className) return null; // Safety check

  const endings = resolveClassEndings(className, classes);

  // Extract macro name for the header
  const macroName = className.match(/^([^\[]+)/)?.[1] || className;
  const endingSlug = endings ? getEndingSlug(endings) : null;

  if (!endings) return null;

  const getConnectedVerbsByClass = (verb: ReconstructableVerb) => {
    if (!connections || !allVerbs) return {}; // Safety check

    const relevantConns = connections.filter((c) => {
      const toIds = String(c.to_corpus_ids)
        .split(";")
        .map((id) => parseInt(id.trim(), 10));
      return toIds.includes(verb.corpus_id || -1);
    });

    const grouped: Record<
      string,
      { verb: ReconstructableVerb; connection: RootConnection }[]
    > = {};

    relevantConns.forEach((conn) => {
      const fromId = parseInt(conn.from_corpus_ids, 10);
      const sourceVerb = allVerbs.find((v) => v.corpus_id === fromId);
      if (sourceVerb) {
        const key = sourceVerb.class_name;
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push({ verb: sourceVerb, connection: conn });
      }
    });

    return grouped;
  };

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
        {verbs.map((verb) => {
          const connectedGroups = getConnectedVerbsByClass(verb);

          const debugInfo = {
            verbId: verb.corpus_id,
            totalConns: connections.length,
            sampleConnTo: connections[0]?.to_corpus_ids,
            sampleConnType: typeof connections[0]?.to_corpus_ids,
            matchCount: Object.keys(connectedGroups).length,
          };

          return (
            <div key={verb.id} className="p-6">
              <div className="flex flex-col gap-6">
                <div className="flex flex-col gap-3">
                  <h4 className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest">
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

                {/* Connections Section */}
                {Object.keys(connectedGroups).length > 0 && (
                  <div className="mt-4 pl-6 border-l-2 border-indigo-50 dark:border-indigo-900/30 flex flex-col gap-8">
                    {Object.entries(connectedGroups).map(
                      ([className, items]) => {
                        const subMacroName =
                          className.match(/^([^\[]+)/)?.[1] || className;
                        return (
                          <div key={className} className="flex flex-col gap-4">
                            <h5 className="text-sm font-semibold text-gray-900 dark:text-gray-100 italic bg-indigo-50/50 dark:bg-indigo-900/10 px-3 py-1 rounded w-fit">
                              Building on {items[0].connection.to_form_type}:
                              With [{subMacroName}]
                            </h5>
                            <div className="flex flex-col gap-6">
                              {items.map(({ verb: v }) => (
                                <div
                                  key={v.corpus_id}
                                  className="flex flex-col gap-2"
                                >
                                  <h6 className="text-[10px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest pl-2">
                                    With [
                                    {getPronominalSetName(
                                      "present",
                                      v.config.pron,
                                    )}
                                    ]
                                  </h6>
                                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pl-2">
                                    <div className="lg:col-span-5 flex flex-col gap-2">
                                      <div className="text-md font-medium text-gray-800 dark:text-gray-200">
                                        {v.definition}
                                      </div>
                                      <ConfigFlags config={v.config} verb={v} />
                                    </div>
                                    <div className="lg:col-span-7">
                                      <CorpusTable
                                        verb={v}
                                        dictionary={dictionary}
                                      />
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      },
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
