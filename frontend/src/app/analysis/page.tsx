import Link from "next/link";
import { getMatchCounts, getReconstructionFailures } from "@/lib/data";
import {
  AlertTriangle,
  ArrowDownRight,
  BarChart3,
  Filter,
  Search,
  X,
} from "lucide-react";

export default async function AnalysisPage(props: {
  searchParams: Promise<{ class?: string }>;
}) {
  const searchParams = await props.searchParams;
  const matchCounts = await getMatchCounts();
  const allFailures = await getReconstructionFailures();
  const selectedClass = searchParams.class;

  // Calculate "Reconstruction Gap" (Full Matches - Strictly Reconstructs)
  // We only care about classes where we have data (Full Matches > 0)
  const gapAnalysis = matchCounts
    .map((row: any) => ({
      class: row.class,
      full: parseInt(row.strict_full || 0),
      reconstructs: parseInt(row.strict_reconstructs || 0),
      gap:
        parseInt(row.strict_full || 0) - parseInt(row.strict_reconstructs || 0),
    }))
    .filter((row: any) => row.full > 0)
    .sort((a: any, b: any) => b.gap - a.gap);

  const failures = selectedClass
    ? allFailures.filter((f: any) => f.class === selectedClass)
    : allFailures;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Reconstruction Analysis
        </h2>
        <p className="text-gray-500 dark:text-zinc-400">
          Deep dive into reconstruction performance and failure modes.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Gap Analysis Table */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-500" />
              Reconstruction Gap
            </h3>
            <span className="text-xs text-gray-500">
              (Full Matches - Reconstructed)
            </span>
          </div>
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-200 dark:border-zinc-800 text-gray-400 uppercase text-[10px] tracking-widest font-bold">
                    <th className="px-4 py-3">Class</th>
                    <th className="px-4 py-3 text-right">Full</th>
                    <th className="px-4 py-3 text-right">Rec</th>
                    <th className="px-4 py-3 text-right">Gap</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                  {gapAnalysis.map((row: any) => (
                    <tr
                      key={row.class}
                      className={`hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors ${
                        selectedClass === row.class
                          ? "bg-indigo-50/50 dark:bg-indigo-900/10"
                          : ""
                      }`}
                    >
                      <td className="px-4 py-3 font-semibold">
                        <Link
                          href={`/analysis?class=${encodeURIComponent(
                            row.class
                          )}`}
                          className="text-indigo-600 dark:text-indigo-400 hover:underline"
                        >
                          {row.class}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-500">
                        {row.full}
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-600">
                        {row.reconstructs}
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-red-500">
                        {row.gap > 0
                          ? `-${row.gap}`
                          : row.gap < 0
                          ? `+${Math.abs(row.gap)}`
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Failure Details */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Failure Details
              </h3>
              {selectedClass && (
                <div className="flex items-center gap-2 px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs font-medium rounded-lg">
                  Filtered by {selectedClass}
                  <Link href="/analysis" className="hover:text-indigo-500">
                    <X className="w-3 h-3" />
                  </Link>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-2.5 top-2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search failures..."
                  className="pl-9 pr-4 py-1.5 text-sm bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
            <div className="max-h-[800px] overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-200 dark:border-zinc-800 text-gray-400 uppercase text-[10px] tracking-widest font-bold sticky top-0 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-sm z-10">
                    <th className="px-6 py-4">Definition</th>
                    <th className="px-6 py-4 w-24">Class</th>
                    <th className="px-6 py-4">Mismatch Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                  {failures.map((row: any, i: number) => (
                    <tr
                      key={i}
                      className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors group"
                    >
                      <td
                        className="px-6 py-4 font-medium max-w-xs truncate"
                        title={row.definition}
                      >
                        {row.definition}
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 dark:bg-zinc-800 text-xs font-medium text-gray-700 dark:text-gray-300">
                          {row.class}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs text-red-600/80 dark:text-red-400/80 font-mono break-all leading-relaxed">
                        {row.mismatch_details}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 text-center text-xs text-gray-500 flex justify-between items-center">
              <span>
                Showing {failures.length} failures across{" "}
                {new Set(failures.map((f: any) => f.class)).size} classes
              </span>
              {selectedClass && (
                <Link
                  href="/analysis"
                  className="text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  Show all classes
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
