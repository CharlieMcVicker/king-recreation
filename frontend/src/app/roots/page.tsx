import { getRoots } from "@/lib/data";
import Link from "next/link";
import { Search } from "lucide-react";

export default async function RootsPage() {
  const roots = await getRoots();

  return (
    <div className="max-w-5xl mx-auto py-8">
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Root Dictionary
          </h1>
          <p className="text-gray-500 dark:text-zinc-400">
            Browse Cherokee verb roots and their associated reconstructable
            verbs.
          </p>
        </div>

        {/* Root List Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {roots.map((root) => (
            <Link
              key={root.slug}
              href={`/roots/${root.slug}`}
              className="group bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-6 hover:border-indigo-500 dark:hover:border-indigo-400 transition-all shadow-sm flex flex-col items-center text-center"
            >
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                {root.h_grade_root}
              </div>
              {root.glottal_grade_root && (
                <div className="text-sm text-gray-500 dark:text-zinc-500 italic">
                  ({root.glottal_grade_root})
                </div>
              )}
              <div className="mt-4 text-xs font-medium text-gray-400 uppercase tracking-wider">
                {root.verbs.length} {root.verbs.length === 1 ? "verb" : "verbs"}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
