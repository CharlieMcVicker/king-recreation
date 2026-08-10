"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Loader2,
  ChevronDown,
  ChevronUp,
  Database,
} from "lucide-react";

interface RootAssignmentPanelProps {
  corpusId: number;
}

export default function RootAssignmentPanel({
  corpusId,
}: RootAssignmentPanelProps) {
  const [rootId, setRootId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`/api/curated/root-ids?corpusId=${corpusId}`);
        const data = await res.json();
        if (data) {
          setRootId(data.root_id || "");
          // Initial search to see who else is in this group
          if (data.root_id) {
            performSearch(data.root_id);
          }
        }
      } catch (err) {
        console.error("Failed to fetch root ID", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [corpusId]);

  const performSearch = async (query: string) => {
    if (!query) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const res = await fetch(
        `/api/curated/root-ids?search=${encodeURIComponent(query)}`,
      );
      const data = await res.json();
      setSearchResults(data.filter((d: any) => d.corpus_id !== corpusId));
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch("/api/curated/root-ids", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ corpusId, rootId }),
      });
      if (res.ok) {
        performSearch(rootId);
      }
    } catch (err) {
      console.error("Save failed", err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading)
    return (
      <div className="p-4 animate-pulse bg-zinc-100 dark:bg-zinc-800 rounded-xl h-24" />
    );

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-zinc-50 dark:bg-zinc-800/50 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2 font-semibold text-zinc-900 dark:text-zinc-100">
          <Database className="w-4 h-4 text-indigo-500" />
          Root Assignment
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {isOpen && (
        <div className="p-4 space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Root ID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={rootId}
                onChange={(e) => {
                  setRootId(e.target.value);
                  performSearch(e.target.value);
                }}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                className="flex-1 bg-white dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter root_id..."
              />
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 transition-colors"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Save"
                )}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
                Peer Groups{" "}
                {searchResults.length > 0 && `(${searchResults.length})`}
              </h4>
              {isSearching && (
                <Loader2 className="w-3 h-3 animate-spin text-zinc-400" />
              )}
            </div>

            <div className="max-h-48 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
              {searchResults.length > 0 ? (
                searchResults.map((res) => (
                  <div
                    key={res.corpus_id}
                    className="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 text-xs border border-transparent hover:border-zinc-200 dark:hover:border-zinc-700"
                  >
                    <span
                      className="text-zinc-900 dark:text-zinc-100 font-medium truncate flex-1 mr-2"
                      title={res.definition}
                    >
                      {res.definition}
                    </span>
                    <span className="text-zinc-400 font-mono shrink-0">
                      ID: {res.corpus_id}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-zinc-400 italic py-2">
                  {rootId
                    ? "No other words share this Root ID."
                    : "Type to see connections..."}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
