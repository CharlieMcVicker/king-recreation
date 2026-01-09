import { getVerbCoverage, getMatchCounts } from "@/lib/data";
import {
  BarChart3,
  CheckCircle2,
  Target,
  ArrowUpRight,
  Filter,
} from "lucide-react";
import Image from "next/image";

import { HeatmapGallery } from "@/components/dashboard/HeatmapGallery";

export default async function Dashboard() {
  const coverage = await getVerbCoverage();
  const matchCounts = await getMatchCounts();

  const metrics = [
    {
      label: "Reconstructible",
      value: `${coverage.strict_reconstructs.coverage_pct.toFixed(1)}%`,
      total:
        coverage.strict_reconstructs["0"] +
        coverage.strict_reconstructs["1"] +
        coverage.strict_reconstructs["2+"],
      matched:
        coverage.strict_reconstructs["1"] + coverage.strict_reconstructs["2+"],
      icon: CheckCircle2,
      color: "text-emerald-600",
      bg: "bg-emerald-50 dark:bg-emerald-900/20",
    },
    {
      label: "Full Match",
      value: `${coverage.strict_full.coverage_pct.toFixed(1)}%`,
      total:
        coverage.strict_full["0"] +
        coverage.strict_full["1"] +
        coverage.strict_full["2+"],
      matched: coverage.strict_full["1"] + coverage.strict_full["2+"],
      icon: Target,
      color: "text-blue-600",
      bg: "bg-blue-50 dark:bg-blue-900/20",
    },
    {
      label: "Ending Match",
      value: `${coverage.strict_ending.coverage_pct.toFixed(1)}%`,
      total:
        coverage.strict_ending["0"] +
        coverage.strict_ending["1"] +
        coverage.strict_ending["2+"],
      matched: coverage.strict_ending["1"] + coverage.strict_ending["2+"],
      icon: Filter,
      color: "text-indigo-600",
      bg: "bg-indigo-50 dark:bg-indigo-900/20",
    },
  ];

  const charts = [
    {
      title: "Verb Coverage",
      src: "/artifacts/visualizations/verb_coverage.png",
    },
    {
      title: "Class Distribution (Filtered)",
      src: "/artifacts/visualizations/class_distribution_filtered.png",
    },
    {
      title: "Class Distribution (Full)",
      src: "/artifacts/visualizations/class_distribution_full.png",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Dashboard Overview
        </h2>
        <p className="text-gray-500 dark:text-zinc-400">
          High-level insights into linguistic verb classification.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-2 rounded-lg ${metric.bg} ${metric.color}`}>
                <metric.icon className="w-5 h-5" />
              </div>
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                {metric.label}
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{metric.value}</span>
              <span className="text-xs text-gray-500">coverage</span>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-50 dark:border-zinc-800/50 flex justify-between text-xs text-gray-500">
              <span>Matched: {metric.matched}</span>
              <span>Total: {metric.total}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Gallery */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Visualization Gallery</h3>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {charts.map((chart) => (
            <div
              key={chart.title}
              className="bg-white dark:bg-zinc-900 p-4 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm"
            >
              <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-400" />
                {chart.title}
              </h4>
              <div className="relative aspect-video rounded-lg overflow-hidden bg-gray-50 dark:bg-zinc-950 flex items-center justify-center border border-gray-100 dark:border-zinc-800">
                <img
                  src={chart.src}
                  alt={chart.title}
                  className="max-w-full max-h-full object-contain"
                />
              </div>
            </div>
          ))}
          <HeatmapGallery />
        </div>
      </div>

      {/* Match Table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Class captures</h3>
          <div className="flex gap-2">
            <button className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors">
              <Filter className="w-3.5 h-3.5" />
              Filter
            </button>
          </div>
        </div>
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-200 dark:border-zinc-800 text-gray-400 uppercase text-[10px] tracking-widest font-bold">
                  <th className="px-6 py-4">Class</th>
                  <th className="px-6 py-4">Reconstructs</th>
                  <th className="px-6 py-4">Full Matches</th>
                  <th className="px-6 py-4">Ending Matches</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                {matchCounts.slice(0, 10).map((row: any) => (
                  <tr
                    key={row.class}
                    className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
                  >
                    <td className="px-6 py-4 font-semibold text-indigo-600 dark:text-indigo-400">
                      {row.class}
                    </td>
                    <td className="px-6 py-4 text-emerald-600 font-medium">
                      {row.strict_reconstructs}
                    </td>
                    <td className="px-6 py-4">{row.strict_full}</td>
                    <td className="px-6 py-4">{row.strict_ending}</td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                        <ArrowUpRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="p-4 border-t border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 text-center">
            <button className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline">
              View all {matchCounts.length} classes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
