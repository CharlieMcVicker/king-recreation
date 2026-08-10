"use client";

import { MorphemeGroup, ClassDefinition, DictionaryEntry } from "@/lib/data";
import MorphemeRootEntry from "./MorphemeRootEntry";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

interface MorphemeDetailContentProps {
  group: MorphemeGroup;
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
}

export default function MorphemeDetailContent({
  group,
  classes,
  dictionary,
}: MorphemeDetailContentProps) {
  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <Link
        href="/morphemes"
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 dark:text-zinc-400 dark:hover:text-indigo-400 transition-colors mb-6 group w-fit"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to Morphemes
      </Link>

      <div className="mb-12">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2 capitalize">
          {group.name.replace(/-/g, " ")}
        </h1>
        <p className="text-lg text-gray-500 dark:text-zinc-400">
          Viewing {group.total_roots} roots with the "{group.name}" post-root
          morpheme.
        </p>
      </div>

      <div className="flex flex-col gap-12">
        {group.subcases.map((subcase) => (
          <div key={subcase.subcase}>
            <h2 className="text-xl font-bold text-gray-800 dark:text-zinc-200 mb-6 flex items-center gap-3">
              <span className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                {subcase.subcase === "default"
                  ? "Standard Form"
                  : `Subcase: ${subcase.subcase}`}
              </span>
              <div className="h-px flex-1 bg-gray-100 dark:bg-zinc-800" />
            </h2>

            <div className="grid grid-cols-1 gap-8">
              {subcase.roots.map((root, idx) => (
                <MorphemeRootEntry
                  key={`${root.slug}-${idx}`}
                  root={root as any}
                  classes={classes}
                  dictionary={dictionary}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
