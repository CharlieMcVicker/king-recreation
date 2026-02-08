"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { RootGroup } from "@/lib/data-shared";

interface RootSearchProps {
  initialRoots: RootGroup[];
}

export default function RootSearch({ initialRoots }: RootSearchProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredRoots = useMemo(() => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return initialRoots;

    return initialRoots.filter((root) => {
      const hGrade = (root.h_grade_root || "").toLowerCase();
      const gGrade = (root.glottal_grade_root || "").toLowerCase();
      const definitions = root.classes
        .flatMap((cls) => cls.verbs.map((v) => v.definition.toLowerCase()))
        .join(" ");

      return (
        hGrade.includes(query) ||
        gGrade.includes(query) ||
        definitions.includes(query)
      );
    });
  }, [initialRoots, searchQuery]);

  return (
    <div className="flex flex-col gap-8">
      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search roots or definitions..."
          className="w-full pl-10 pr-4 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 transition-all text-gray-900 dark:text-gray-100"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Root List Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {filteredRoots.map((root) => {
          const allVerbs = root.classes.flatMap((cls) => cls.verbs);
          const uniqueDefinitions = Array.from(
            new Set(allVerbs.map((v) => v.definition)),
          );

          return (
            <Link
              key={root.slug}
              href={`/${root.slug}`}
              className="group bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-6 hover:border-indigo-500 dark:hover:border-indigo-400 transition-all shadow-sm flex flex-col items-center text-center h-full"
            >
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                {root.h_grade_root}
              </div>
              {root.glottal_grade_root && (
                <div className="text-sm text-gray-500 dark:text-zinc-500 italic mb-3">
                  ({root.glottal_grade_root})
                </div>
              )}

              <div className="flex-grow flex flex-col justify-center gap-1 w-full overflow-hidden">
                {uniqueDefinitions.slice(0, 3).map((def, i) => (
                  <div
                    key={i}
                    className="text-xs text-gray-600 dark:text-zinc-400 line-clamp-1 italic"
                  >
                    {def}
                  </div>
                ))}
                {uniqueDefinitions.length > 3 && (
                  <div className="text-xs text-gray-400 dark:text-zinc-500">
                    + {uniqueDefinitions.length - 3} more
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-50 dark:border-zinc-800/50 w-full text-xs font-medium text-gray-400 dark:text-zinc-500 uppercase tracking-wider">
                {allVerbs.length} {allVerbs.length === 1 ? "verb" : "verbs"}
              </div>
            </Link>
          );
        })}
      </div>

      {filteredRoots.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-zinc-500">
          No roots found matching "{searchQuery}"
        </div>
      )}
    </div>
  );
}
