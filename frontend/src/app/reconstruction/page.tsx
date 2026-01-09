import { getReconstructionFailures, getMatches } from "@/lib/data";
import { AlertTriangle, ArrowLeft, RefreshCw, Search } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function ReconstructionPage() {
  const allFailures = await getReconstructionFailures();
  const matches = await getMatches();

  const reconstructableVerbs = new Set(
    matches
      .filter((m: any) => m.scope === "reconstructs")
      .map((m: any) => m.definition)
  );

  const failures = allFailures.filter(
    (f: any) => !reconstructableVerbs.has(f.definition)
  );

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
              Reconstruction Failures
            </h2>
          </div>
          <p className="text-gray-500 dark:text-zinc-400">
            Verbs that fully match class patterns but failed the root
            consistency check.
          </p>
        </div>
        <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/50 rounded-lg px-4 py-2 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-500" />
          <div>
            <div className="text-sm font-semibold text-amber-900 dark:text-amber-100">
              {failures.length} Issues Found
            </div>
            <div className="text-[10px] text-amber-700 dark:text-amber-400 uppercase font-medium tracking-wider">
              Requires attention
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-indigo-600" />
            <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
              Full Matches failing Reconstruction
            </h3>
          </div>
          <div className="relative">
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
                <th className="px-6 py-4">Verb</th>
                <th className="px-6 py-4">Assigned Class</th>
                <th className="px-6 py-4">Mismatch Details</th>
                <th className="px-6 py-4 text-right">Explore</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
              {failures.map((row: any) => (
                <tr
                  key={`${row.definition}-${row.class}`}
                  className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-100">
                    {row.definition}
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      href={`/explorer?class=${row.class}`}
                      className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/30 hover:border-indigo-300 transition-colors"
                    >
                      {row.class}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-xs text-gray-500 dark:text-zinc-400 font-mono italic">
                    {row.mismatch_details}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      href={`/explorer/entry/${encodeURIComponent(
                        row.definition
                      )}`}
                      className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      View Entry
                    </Link>
                  </td>
                </tr>
              ))}
              {failures.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-6 py-12 text-center text-gray-500 italic"
                  >
                    Great job! All full matches are successfully reconstructed.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-indigo-50/50 dark:bg-indigo-900/10 rounded-xl border border-indigo-100 dark:border-indigo-900/30">
          <h4 className="text-sm font-bold text-indigo-900 dark:text-indigo-100 mb-2">
            What does this mean?
          </h4>
          <p className="text-xs text-indigo-800 dark:text-indigo-300 leading-relaxed">
            These verbs match a class's specific endings and its "stem final"
            characters across all 5 forms. However, the{" "}
            <code>reconstruct_from_roots.py</code> script could not find a
            single consistent root that, when combined with the class's rules,
            would regenerate all 5 observed forms perfectly.
          </p>
        </div>
        <div className="p-6 bg-amber-50/50 dark:bg-amber-900/10 rounded-xl border border-amber-100 dark:border-amber-900/30">
          <h4 className="text-sm font-bold text-amber-900 dark:text-amber-100 mb-2">
            Next Steps
          </h4>
          <ul className="text-xs text-amber-800 dark:text-amber-300 list-disc pl-4 space-y-1">
            <li>Check for irregular /h/ alternations or prefix rules.</li>
            <li>
              Verify if the stem final characters in the class spec are too
              restrictive.
            </li>
            <li>
              Investigate the 'Mismatch Details' column for specific failing
              forms.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
