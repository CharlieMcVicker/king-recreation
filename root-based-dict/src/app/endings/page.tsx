import { getEndingGroups } from "@/lib/data";
import Link from "next/link";
import { Layers } from "lucide-react";

export default async function EndingsPage() {
  const groups = await getEndingGroups();

  return (
    <div className="max-w-5xl mx-auto py-8">
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Endings Dictionary
          </h1>
          <p className="text-gray-500 dark:text-zinc-400">
            Browse reconstructable verbs grouped by their aspect ending sets.
          </p>
        </div>

        {/* Ending Groups Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {groups.map((group) => (
            <Link
              key={group.slug}
              href={`/endings/${group.slug}`}
              className="group bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-6 hover:border-indigo-500 dark:hover:border-indigo-400 transition-all shadow-sm flex flex-col"
            >
              <div className="flex-1 flex flex-col gap-2">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
                  Endings:
                </div>
                <div className="flex flex-wrap gap-x-2 gap-y-1">
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    -{group.endings.present || "∅"}
                  </span>
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    -{group.endings.imperfective || "∅"}
                  </span>
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    -{group.endings.perfective || "∅"}
                  </span>
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    -{group.endings.imperative || "∅"}
                  </span>
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    -{group.endings.infinitive || "∅"}
                  </span>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-medium text-gray-400 uppercase tracking-wider">
                  <Layers className="w-3.5 h-3.5" />
                  {group.roots.length}{" "}
                  {group.roots.length === 1 ? "root" : "roots"}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
