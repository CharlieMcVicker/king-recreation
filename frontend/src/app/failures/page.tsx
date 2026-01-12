import { getStemDerivationFailures } from "@/lib/data";
import { AlertTriangle, ArrowLeft, Bug, Search } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function DerivationFailuresPage() {
  const failures = await getStemDerivationFailures();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/"
              className="p-1 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-md transition-colors text-gray-400 hover:text-indigo-600"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h2 className="text-2xl font-bold tracking-tight">
              Derivation Failures
            </h2>
          </div>
          <p className="text-gray-500 dark:text-zinc-400">
            Verbs that could not be parsed by the stem derivation logic.
          </p>
        </div>
        <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/50 rounded-lg px-4 py-2 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-500" />
          <div>
            <div className="text-sm font-semibold text-red-900 dark:text-red-100">
              {failures.length} Failures Found
            </div>
            <div className="text-[10px] text-red-700 dark:text-red-400 uppercase font-medium tracking-wider">
              Requires attention
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bug className="w-4 h-4 text-indigo-600" />
            <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
              Unparseable Verbs
            </h3>
          </div>
          <div className="relative hidden">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search verbs..."
              className="pl-9 pr-4 py-1.5 text-xs bg-white dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-200 dark:border-zinc-800 text-gray-400 uppercase text-[10px] tracking-widest font-bold">
                <th className="px-6 py-4">Definition</th>
                <th className="px-6 py-4">Present</th>
                <th className="px-6 py-4">Present 1sg</th>
                <th className="px-6 py-4">Imperfective</th>
                <th className="px-6 py-4">Perfective</th>
                <th className="px-6 py-4">Imperative</th>
                <th className="px-6 py-4">Infinitive</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
              {failures.map((row: any, i: number) => (
                <tr
                  key={i}
                  className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-100 max-w-xs truncate" title={row.definition}>
                    <Link 
                      href={`/failures/${encodeURIComponent(row.definition)}`}
                      className="text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      {row.definition}
                    </Link>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">{row.present}</td>
                  <td className="px-6 py-4 font-mono text-xs">{row.present_1sg}</td>
                  <td className="px-6 py-4 font-mono text-xs">{row.imperfective}</td>
                  <td className="px-6 py-4 font-mono text-xs">{row.perfective}</td>
                  <td className="px-6 py-4 font-mono text-xs">{row.imperative}</td>
                  <td className="px-6 py-4 font-mono text-xs">{row.infinitive}</td>
                </tr>
              ))}
              {failures.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-6 py-12 text-center text-gray-500 italic"
                  >
                    No failures found!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-6 bg-indigo-50/50 dark:bg-indigo-900/10 rounded-xl border border-indigo-100 dark:border-indigo-900/30">
        <h4 className="text-sm font-bold text-indigo-900 dark:text-indigo-100 mb-2">
          About this data
        </h4>
        <p className="text-xs text-indigo-800 dark:text-indigo-300 leading-relaxed">
            These are verbs where <code>derive_stems.py</code> failed to parse the stems correctly.
            This usually indicates that the verb forms do not match expected patterns or have irregularities that are not yet handled.
        </p>
      </div>
    </div>
  );
}
