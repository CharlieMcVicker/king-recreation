import { getMorphemeGroups } from "@/lib/data";
import Link from "next/link";
import { Layers } from "lucide-react";

export default async function MorphemesPage() {
  const groups = await getMorphemeGroups();

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-2">
            <Layers className="w-8 h-8 text-indigo-500" />
            Post-Root Morphemes
          </h1>
          <p className="text-gray-500 dark:text-zinc-400">
            Browse verb roots grouped by their post-root morpheme derivations.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {groups.map((group) => (
            <Link
              key={group.slug}
              href={`/morphemes/${group.slug}`}
              className="group bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-6 hover:border-indigo-500 dark:hover:border-indigo-400 transition-all shadow-sm flex flex-col"
            >
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors capitalize">
                {group.name.replace(/-/g, " ")}
              </div>
              <div className="text-sm text-gray-500 dark:text-zinc-500 mb-4">
                {group.subcases.length}{" "}
                {group.subcases.length === 1 ? "subcase" : "subcases"}
              </div>
              <div className="mt-auto pt-4 border-t border-gray-50 dark:border-zinc-800 text-xs font-medium text-gray-400 uppercase tracking-wider">
                {group.total_roots} {group.total_roots === 1 ? "root" : "roots"}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
