"use client";

import React, { useState, useMemo } from "react";
import {
  CheckCircle2,
  Database,
  ArrowLeft,
  LayoutGrid,
  Search,
  CheckSquare,
  Square,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface RootIdRow {
  corpus_id: number;
  definition: string;
  h_grade: string;
  g_grade: string;
  class: string;
  post_root_morpheme: string;
  root_id: string;
  user_edited: string;
}

interface RootGroupEditorProps {
  initialData: RootIdRow[];
  rootId: string;
}

export default function RootGroupEditor({
  initialData,
  rootId,
}: RootGroupEditorProps) {
  const router = useRouter();
  const [data, setData] = useState(initialData);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [newRootId, setNewRootId] = useState(rootId);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const groupWords = useMemo(() => {
    return data.filter((r) => r.root_id === rootId);
  }, [data, rootId]);

  const toggleSelection = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleAll = () => {
    if (selectedIds.size === groupWords.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(groupWords.map((w) => w.corpus_id)));
    }
  };

  const handleBulkUpdate = async () => {
    if (selectedIds.size === 0) return;
    if (newRootId === rootId) {
      setMessage({ type: "error", text: "New Root ID must be different" });
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      const updates = Array.from(selectedIds).map((id) => ({
        corpusId: id,
        rootId: newRootId,
      }));

      const response = await fetch("/api/curated/root-ids/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updates }),
      });

      if (!response.ok) throw new Error("Failed to update bulk");

      // Update local state
      const newData = data.map((r) =>
        selectedIds.has(r.corpus_id)
          ? { ...r, root_id: newRootId, user_edited: "x" }
          : r,
      );
      setData(newData);
      setSelectedIds(new Set());
      setMessage({ type: "success", text: `Updated ${updates.length} items!` });

      // If none left in this group, maybe redirect or just let them see the empty state
    } catch (err) {
      console.error(err);
      setMessage({ type: "error", text: "Bulk update failed" });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      {/* Header */}
      <div className="bg-white dark:bg-zinc-900 p-8 rounded-3xl shadow-sm border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link
              href="/review-root-ids"
              className="p-2 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
                Group Editor
              </h1>
              <p className="text-zinc-500 text-sm font-medium">
                Editing group:{" "}
                <span className="font-mono bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded italic">
                  "{rootId}"
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right mr-2">
              <div className="text-xs font-black uppercase tracking-widest text-zinc-400">
                Word Count
              </div>
              <div className="text-xl font-bold">{groupWords.length}</div>
            </div>
            <LayoutGrid className="w-8 h-8 text-indigo-500 opacity-20" />
          </div>
        </div>

        {/* Bulk Action Panel */}
        <div className="bg-zinc-50 dark:bg-zinc-950/50 rounded-2xl p-6 border border-zinc-100 dark:border-zinc-800/50">
          <div className="flex flex-col md:flex-row gap-6 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400 ml-1">
                Move Selected To New ID
              </label>
              <input
                value={newRootId}
                onChange={(e) => setNewRootId(e.target.value)}
                className="w-full px-5 py-3 text-xl font-mono font-bold bg-white dark:bg-zinc-900 border-2 border-zinc-200 dark:border-zinc-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all"
                placeholder="Enter target Root ID..."
              />
            </div>
            <button
              onClick={handleBulkUpdate}
              disabled={isSaving || selectedIds.size === 0}
              className="h-14 px-8 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-200 dark:disabled:bg-zinc-800 disabled:text-zinc-400 text-white rounded-xl font-bold shadow-xl shadow-indigo-500/20 flex items-center gap-3 transition-all active:scale-95 whitespace-nowrap"
            >
              {isSaving ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Update {selectedIds.size} Selected
                </>
              )}
            </button>
          </div>

          {message && (
            <div
              className={`mt-4 p-3 rounded-lg text-sm font-bold flex items-center gap-2 animate-in fade-in slide-in-from-top-1 ${
                message.type === "success"
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400"
                  : "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400"
              }`}
            >
              {message.type === "success" ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-current" />
              )}
              {message.text}
            </div>
          )}
        </div>
      </div>

      {/* List */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl overflow-hidden shadow-sm">
        <div className="p-6 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/50 dark:bg-zinc-950/20">
          <button
            onClick={toggleAll}
            className="flex items-center gap-3 px-4 py-2 rounded-xl hover:bg-white dark:hover:bg-zinc-800 transition-all font-bold text-sm text-zinc-600 dark:text-zinc-400 border border-transparent hover:border-zinc-200"
          >
            {selectedIds.size === groupWords.length ? (
              <CheckSquare className="w-5 h-5 text-indigo-500" />
            ) : (
              <Square className="w-5 h-5" />
            )}
            {selectedIds.size === groupWords.length
              ? "Deselect All"
              : "Select All"}
          </button>

          <div className="text-xs font-mono text-zinc-400 uppercase tracking-widest">
            Showing {groupWords.length} words in group
          </div>
        </div>

        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {groupWords.length === 0 ? (
            <div className="p-20 text-center space-y-4">
              <Search className="w-12 h-12 text-zinc-200 mx-auto" />
              <p className="text-zinc-400 font-medium">
                No words found in this group.
              </p>
              <Link
                href="/review-root-ids"
                className="text-indigo-500 font-bold hover:underline"
              >
                Back to Review
              </Link>
            </div>
          ) : (
            groupWords.map((row) => (
              <div
                key={row.corpus_id}
                onClick={() => toggleSelection(row.corpus_id)}
                className={`flex items-center gap-6 p-6 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/30 transition-all ${
                  selectedIds.has(row.corpus_id)
                    ? "bg-indigo-50/50 dark:bg-indigo-900/10"
                    : ""
                }`}
              >
                <div className="flex-shrink-0">
                  {selectedIds.has(row.corpus_id) ? (
                    <CheckSquare className="w-6 h-6 text-indigo-500 fill-indigo-500/10" />
                  ) : (
                    <Square className="w-6 h-6 text-zinc-200 dark:text-zinc-700" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-bold text-xl text-zinc-900 dark:text-zinc-100 italic truncate mb-1">
                    "{row.definition}"
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono font-medium text-zinc-400">
                    <span className="flex items-center gap-1">
                      <Database className="w-3 h-3" /> {row.corpus_id}
                    </span>
                    <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                    <span>{row.class}</span>
                    <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                    <span>H: {row.h_grade || "-"}</span>
                    <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                    <span>G: {row.g_grade || "-"}</span>
                  </div>
                </div>

                <div className="flex-shrink-0 flex items-center gap-3">
                  {row.user_edited && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 text-[9px] font-black uppercase tracking-tighter border border-emerald-100 dark:border-emerald-800/30">
                      <CheckCircle2 className="w-3 h-3" /> Reviewed
                    </div>
                  )}
                  <Link
                    href={`/review-root-ids/${row.corpus_id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="p-3 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 hover:text-indigo-500 transition-all border border-transparent hover:border-zinc-200"
                  >
                    <Database className="w-5 h-5" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
