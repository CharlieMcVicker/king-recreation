"use client";

import { useState } from "react";
import { BarChart3, Filter, Settings2 } from "lucide-react";

export function HeatmapGallery() {
  const [filtered, setFiltered] = useState<boolean>(true);

  const currentSrc = `/artifacts/visualizations/near_miss_heatmap_strict_${
    filtered ? "filtered" : "full"
  }.png`;
  const currentTitle = `Near-Miss Heatmap (${filtered ? "Filtered" : "Full"})`;

  return (
    <div className="bg-white dark:bg-zinc-900 p-4 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-gray-400" />
          Near-Miss Heatmap
        </h4>

        <div className="flex items-center gap-2">
          {/* Filter Toggle */}
          <button
            onClick={() => setFiltered(!filtered)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              filtered
                ? "bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/20 dark:border-indigo-800 dark:text-indigo-400"
                : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50 dark:bg-zinc-900 dark:border-zinc-800 dark:text-gray-400 dark:hover:bg-zinc-800"
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            {filtered ? "Filtered" : "Full View"}
          </button>
        </div>
      </div>

      <div className="relative aspect-video rounded-lg overflow-hidden bg-gray-50 dark:bg-zinc-950 flex items-center justify-center border border-gray-100 dark:border-zinc-800">
        <img
          src={currentSrc}
          alt={currentTitle}
          className="max-w-full max-h-full object-contain"
        />
      </div>
    </div>
  );
}
