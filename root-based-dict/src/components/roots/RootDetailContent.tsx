"use client";

import { useState } from "react";
import {
  RootGroup,
  ClassDefinition,
  DictionaryEntry,
  RootConnection,
  ReconstructableVerb,
  getMorphemeSlug,
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

  // Helper to extract morpheme info from "name[subcase]" format
  const parseMorpheme = (tag: string) => {
    const match = tag.match(/^([^\[]+)(?:\[(.*)\])?$/);
    if (!match) return { name: tag, subcase: "default" };
    return { name: match[1], subcase: match[2] || "default" };
  };

  // Group verbs by morpheme
  // Structure: Base -> [Classes with verbs], Morphemes -> Map<Slug, {name, subcase, classes: ...}>
  const baseClasses: typeof rootGroup.classes = [];
  const morphemeGroups: Map<
    string,
    {
      name: string;
      subcase: string;
      classes: typeof rootGroup.classes;
    }
  > = new Map();

  rootGroup.classes.forEach((cls) => {
    // We need to split the class's verbs because a single class entry "verbs" list might contain mix?
    // Actually, in the current backend logic, verbs are grouped into classes. A class node in RootGroup
    // contains a list of verbs.
    // However, the previous logic assumed "post_root_derivations" were separate RootNodes.
    // Now everything is in `rootGroup.classes`.
    // It is possible for a single "class" (e.g. "go-in") to have verbs with different morphemes?
    // Yes, absolutely. The class name identifies the inflection pattern, not the derivation.

    const baseVerbs: typeof cls.verbs = [];
    const derivedVerbsMap: Map<string, typeof cls.verbs> = new Map(); // morphemeTag -> verbs

    cls.verbs.forEach((verb) => {
      // Filter by subvariant first if needed, or do it later?
      // The old logic filtered classes by name.
      // Let's keep filteredClasses logic but applies to all.

      if (!verb.post_root_morpheme) {
        baseVerbs.push(verb);
      } else {
        const tag = verb.post_root_morpheme;
        if (!derivedVerbsMap.has(tag)) {
          derivedVerbsMap.set(tag, []);
        }
        derivedVerbsMap.get(tag)!.push(verb);
      }
    });

    if (baseVerbs.length > 0) {
      baseClasses.push({ ...cls, verbs: baseVerbs });
    }

    derivedVerbsMap.forEach((verbs, tag) => {
      const { name, subcase } = parseMorpheme(tag);
      const key = tag; // Use full tag as key

      if (!morphemeGroups.has(key)) {
        morphemeGroups.set(key, { name, subcase, classes: [] });
      }
      morphemeGroups.get(key)!.classes.push({ ...cls, verbs });
    });
  });

  // Apply Variant Filter
  const filterClasses = (classList: typeof rootGroup.classes) => {
    if (selectedVariant === "All") return classList;
    return classList.filter((c) =>
      c.class_name.includes(`[${selectedVariant}]`),
    );
  };

  const filteredBaseClasses = filterClasses(baseClasses);

  // Convert map to array and sort
  const sortedMorphemeGroups = Array.from(morphemeGroups.values()).sort(
    (a, b) =>
      a.name.localeCompare(b.name) || a.subcase.localeCompare(b.subcase),
  );

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex flex-col gap-6">
        <Link
          href="/"
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

        {/* Base Verbs */}
        {filteredBaseClasses.length > 0 && (
          <div className="grid grid-cols-1 gap-6 mt-4">
            {filteredBaseClasses.map((cls) => (
              <RootClassEntry
                key={cls.class_name}
                verbs={cls.verbs}
                classes={classes}
                dictionary={dictionary}
                allVerbs={allVerbs}
                connections={connections}
              />
            ))}
          </div>
        )}

        {/* Derived Verbs */}
        {sortedMorphemeGroups.length > 0 && (
          <div className="mt-12 flex flex-col gap-12">
            {sortedMorphemeGroups.map((group) => {
              const filteredGroupClasses = filterClasses(group.classes);
              if (filteredGroupClasses.length === 0) return null;

              return (
                <div key={`${group.name}-${group.subcase}`}>
                  <div className="border-t border-gray-200 dark:border-zinc-800 pt-8 mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {rootGroup.h_grade_root}
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-zinc-500 mt-1">
                      Derived via{" "}
                      <Link
                        href={`/morphemes/${getMorphemeSlug(group.name)}`}
                        className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
                      >
                        {group.name}
                      </Link>{" "}
                      {group.subcase !== "default" && `(${group.subcase})`}
                    </p>
                  </div>
                  <div className="grid grid-cols-1 gap-6">
                    {filteredGroupClasses.map((cls) => (
                      <RootClassEntry
                        key={cls.class_name}
                        verbs={cls.verbs}
                        classes={classes}
                        dictionary={dictionary}
                        allVerbs={allVerbs}
                        connections={connections}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {filteredBaseClasses.length === 0 &&
          sortedMorphemeGroups.every(
            (g) => filterClasses(g.classes).length === 0,
          ) && (
            <div className="py-12 text-center text-gray-500 italic border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl">
              No verbs found for the selected endings.
            </div>
          )}
      </div>
    </div>
  );
}
