"use client";

import { useState } from "react";
import {
  RootGroup,
  ClassDefinition,
  DictionaryEntry,
  RootConnection,
  ReconstructableVerb,
} from "@/lib/data-shared";
import RootClassEntry from "@/components/roots/RootClassEntry";
import SubvariantFilter from "@/components/roots/SubvariantFilter";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

interface RootDetailContentProps {
  rootGroup: RootGroup;
  classes: ClassDefinition[];
  dictionary: DictionaryEntry[];
  connections: RootConnection[];
  allVerbs: ReconstructableVerb[];
}

export default function RootDetailContent({
  rootGroup,
  classes,
  dictionary,
  connections,
  allVerbs,
}: RootDetailContentProps) {
  const [selectedVariant, setSelectedVariant] = useState("All");

  // Get unique subvariants from all classes in this root group
  const subvariants = Array.from(
    new Set(
      rootGroup.classes
        .map((c) => {
          const match = c.class_name.match(/\[(.*)\]/);
          return match ? match[1] : null;
        })
        .filter((v): v is string => v !== null),
    ),
  ).sort();

  const filteredClasses =
    selectedVariant === "All"
      ? rootGroup.classes
      : rootGroup.classes.filter((c) =>
          c.class_name.includes(`[${selectedVariant}]`),
        );

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex flex-col gap-6">
        <Link
          href="/roots"
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-indigo-600 transition-colors w-fit"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Root Dictionary
        </Link>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {rootGroup.h_grade_root}
            </h1>
            {rootGroup.glottal_grade_root && (
              <p className="text-xl text-gray-500 dark:text-zinc-500 italic">
                ({rootGroup.glottal_grade_root})
              </p>
            )}
          </div>

          <SubvariantFilter
            options={subvariants}
            selected={selectedVariant}
            onChange={setSelectedVariant}
          />
        </div>

        <div className="grid grid-cols-1 gap-6 mt-4">
          {filteredClasses.length > 0 ? (
            filteredClasses.map((cls) => (
              <RootClassEntry
                key={cls.class_name}
                verbs={cls.verbs}
                classes={classes}
                dictionary={dictionary}
                allVerbs={allVerbs}
                connections={connections}
              />
            ))
          ) : (
            <div className="py-12 text-center text-gray-500 italic border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl">
              No verbs found for the selected endings.
            </div>
          )}
        </div>

        {rootGroup.post_root_derivations &&
          rootGroup.post_root_derivations.length > 0 && (
            <div className="mt-12">
              <div className="border-t border-gray-200 dark:border-zinc-800 pt-8 mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Post-root Derivations
                </h2>
                <p className="text-sm text-gray-500 dark:text-zinc-500 mt-1">
                  Roots that are derived from this root
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {rootGroup.post_root_derivations.map((derivation) => (
                  <Link
                    key={derivation.slug}
                    href={`/roots/${derivation.slug}`}
                    className="p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl hover:border-indigo-500 transition-all hover:shadow-md group"
                  >
                    <div className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-indigo-600 transition-colors">
                      {derivation.h_grade_root}
                    </div>
                    {derivation.glottal_grade_root && (
                      <div className="text-sm text-gray-500 dark:text-zinc-500 italic">
                        ({derivation.glottal_grade_root})
                      </div>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}
      </div>
    </div>
  );
}
