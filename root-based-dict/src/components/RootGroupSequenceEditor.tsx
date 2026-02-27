"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  CheckCircle2,
  Database,
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  LayoutGrid,
  Search,
  CheckSquare,
  Square,
  Zap,
  Tag,
  Hash,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toBase64Url } from "@/lib/data-shared";

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

interface RootGroupSequenceEditorProps {
  initialData: RootIdRow[];
  rootId: string;
  prevRootId: string | null;
  nextRootId: string | null;
  currentIndex: number;
  totalGroups: number;
  rootSlug?: string | null;
}

export default function RootGroupSequenceEditor({
  initialData,
  rootId,
  prevRootId,
  nextRootId,
  currentIndex,
  totalGroups,
  rootSlug,
}: RootGroupSequenceEditorProps) {
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
    return data.filter((r) => (r.root_id || "").trim() === rootId.trim());
  }, [data, rootId]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      if (e.key === "ArrowLeft" && prevRootId !== null) {
        router.push(`/review-root-ids/groups/${toBase64Url(prevRootId)}`);
      }
      if (e.key === "ArrowRight" && nextRootId !== null) {
        router.push(`/review-root-ids/groups/${toBase64Url(nextRootId)}`);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [prevRootId, nextRootId, router]);

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

      // If we moved the WHOLE group, maybe auto-advance?
      if (selectedIds.size === groupWords.length && nextRootId !== null) {
        setTimeout(() => {
          router.push(`/review-root-ids/groups/${toBase64Url(nextRootId)}`);
        }, 1000);
      }
    } catch (err) {
      console.error(err);
      setMessage({ type: "error", text: "Bulk update failed" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSelectAllAndSet = () => {
    setSelectedIds(new Set(groupWords.map((w) => w.corpus_id)));
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      {/* Navigation Bar */}
      <div className="flex items-center justify-between bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-6">
          <Link
            href="/review-root-ids"
            className="flex items-center gap-2 text-sm font-bold text-zinc-500 hover:text-indigo-600 transition-colors"
          >
            <LayoutGrid className="w-4 h-4" />
            Exit to Review
          </Link>
          <div className="w-px h-6 bg-zinc-200 dark:bg-zinc-800" />
          <div className="flex flex-col">
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
              Sequence Position
            </span>
            <span className="font-bold text-lg">
              {currentIndex + 1} / {totalGroups}
            </span>
          </div>
        </div>

        <div className="flex gap-3">
          <Link
            href={
              prevRootId !== null
                ? `/review-root-ids/groups/${toBase64Url(prevRootId)}`
                : "#"
            }
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl border-2 font-bold transition-all ${
              prevRootId !== null
                ? "border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                : "opacity-20 cursor-not-allowed"
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
            Previous Group
          </Link>
          <Link
            href={
              nextRootId !== null
                ? `/review-root-ids/groups/${toBase64Url(nextRootId)}`
                : "#"
            }
            className={`flex items-center gap-2 px-6 py-2.5 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl font-bold transition-all shadow-lg hover:shadow-xl active:scale-95 ${
              nextRootId !== null ? "" : "opacity-20 cursor-not-allowed"
            }`}
          >
            Next Group
            <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Group Info & Global Action */}
      <div className="bg-white dark:bg-zinc-900 p-8 rounded-3xl shadow-sm border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between mb-8">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-indigo-500 mb-1">
              <Tag className="w-4 h-4" />
              <span className="text-[10px] font-black uppercase tracking-widest">
                Active Root Group
              </span>
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 font-mono">
              "{rootId || <span className="text-zinc-300 italic">None</span>}"
            </h1>
            {rootSlug && (
              <Link
                href={`/${rootSlug}`}
                className="inline-flex items-center gap-2 mt-2 text-sm text-indigo-500 hover:text-indigo-600 font-bold transition-colors group/link"
              >
                View in Dictionary
                <ArrowRight className="w-3.5 h-3.5 group-hover/link:translate-x-0.5 transition-transform" />
              </Link>
            )}
          </div>

          <div className="flex items-center gap-8">
            <div className="text-right">
              <div className="text-xs font-black uppercase tracking-widest text-zinc-400">
                Words
              </div>
              <div className="text-3xl font-bold">{groupWords.length}</div>
            </div>
            <div className="text-right">
              <div className="text-xs font-black uppercase tracking-widest text-zinc-400">
                Reviewed
              </div>
              <div className="text-3xl font-bold text-emerald-500">
                {groupWords.filter((w) => w.user_edited).length}
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Bulk Action Panel */}
        <div className="bg-indigo-50/30 dark:bg-indigo-900/10 rounded-2xl p-6 border border-indigo-100 dark:border-indigo-800/30">
          <div className="flex flex-col md:flex-row gap-6 items-end">
            <div className="flex-1 space-y-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                  New ID for{" "}
                  {selectedIds.size === 0
                    ? "all items"
                    : `${selectedIds.size} selected items`}
                </label>
                {selectedIds.size === 0 && (
                  <button
                    onClick={handleSelectAllAndSet}
                    className="text-[10px] font-black uppercase tracking-widest text-indigo-500 hover:underline"
                  >
                    Select All to Move
                  </button>
                )}
              </div>
              <div className="relative">
                <Hash className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-300" />
                <input
                  value={newRootId}
                  onChange={(e) => setNewRootId(e.target.value)}
                  className="w-full pl-12 pr-5 py-4 text-2xl font-mono font-bold bg-white dark:bg-zinc-800 border-2 border-zinc-200 dark:border-zinc-700 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all shadow-inner"
                  placeholder="Enter target Root ID..."
                />
              </div>
            </div>
            <button
              onClick={handleBulkUpdate}
              disabled={
                isSaving || (selectedIds.size === 0 && newRootId === rootId)
              }
              className="h-16 px-10 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-200 dark:disabled:bg-zinc-800 disabled:text-zinc-400 text-white rounded-xl font-bold shadow-xl shadow-indigo-500/20 flex items-center gap-3 transition-all active:scale-95 whitespace-nowrap"
            >
              {isSaving ? (
                <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Apply to {selectedIds.size || groupWords.length}{" "}
                  {selectedIds.size === groupWords.length ||
                  selectedIds.size === 0
                    ? "All"
                    : ""}
                </>
              )}
            </button>
          </div>

          {message && (
            <div
              className={`mt-4 p-4 rounded-xl text-sm font-bold flex items-center gap-3 animate-in fade-in slide-in-from-top-1 ${
                message.type === "success"
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800/30"
                  : "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400 border border-rose-100 dark:border-rose-800/30"
              }`}
            >
              {message.type === "success" ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-current" />
              )}
              {message.text}
            </div>
          )}
        </div>
      </div>

      {/* Word List with "Check to Move" UI */}
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
            {selectedIds.size} of {groupWords.length} items selected for move
          </div>
        </div>

        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {groupWords.length === 0 ? (
            <div className="p-20 text-center space-y-4">
              <Search className="w-12 h-12 text-zinc-200 mx-auto" />
              <p className="text-zinc-400 font-medium">
                No words found in this group anymore.
              </p>
              {nextRootId && (
                <Link
                  href={`/review-root-ids/groups/${toBase64Url(nextRootId)}`}
                  className="inline-flex items-center gap-2 bg-indigo-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-indigo-500 transition-all"
                >
                  Go to Next Group
                  <ChevronRight className="w-5 h-5" />
                </Link>
              )}
            </div>
          ) : (
            groupWords.map((row) => (
              <div
                key={row.corpus_id}
                className={`flex items-center gap-6 p-6 transition-all group ${
                  selectedIds.has(row.corpus_id)
                    ? "bg-indigo-50/30 dark:bg-indigo-900/5"
                    : "hover:bg-zinc-50/50 dark:hover:bg-zinc-800/20"
                }`}
              >
                <div
                  onClick={() => toggleSelection(row.corpus_id)}
                  className="flex-shrink-0 cursor-pointer"
                >
                  {selectedIds.has(row.corpus_id) ? (
                    <CheckSquare className="w-7 h-7 text-indigo-500 fill-indigo-500/5" />
                  ) : (
                    <Square className="w-7 h-7 text-zinc-200 dark:text-zinc-700 group-hover:text-zinc-400" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-bold text-2xl text-zinc-900 dark:text-zinc-100 italic">
                      "{row.definition}"
                    </span>
                    {row.user_edited && (
                      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 text-[8px] font-black uppercase tracking-widest border border-emerald-100 dark:border-emerald-800/30">
                        <CheckCircle2 className="w-2.5 h-2.5" /> Reviewed
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono font-medium text-zinc-400">
                    <span className="flex items-center gap-1">
                      <Database className="w-3 h-3" /> {row.corpus_id}
                    </span>
                    <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                    <span className="px-1.5 py-0.5 bg-zinc-100 dark:bg-zinc-800 rounded font-bold text-zinc-600 dark:text-zinc-300">
                      {row.class}
                    </span>
                    <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                    <span>
                      H:{" "}
                      <span className="text-zinc-700 dark:text-zinc-300 font-bold">
                        {row.h_grade || "-"}
                      </span>
                    </span>
                    <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                    <span>
                      G:{" "}
                      <span className="text-zinc-700 dark:text-zinc-300 font-bold">
                        {row.g_grade || "-"}
                      </span>
                    </span>
                    {row.post_root_morpheme && (
                      <>
                        <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                        <span>
                          Suffix:{" "}
                          <span className="text-zinc-700 dark:text-zinc-300 font-bold">
                            {row.post_root_morpheme}
                          </span>
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex-shrink-0 flex items-center gap-2">
                  <Link
                    href={`/review-root-ids/${row.corpus_id}`}
                    title="View detailed individual editor"
                    className="p-3 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 hover:text-indigo-500 transition-all shadow-sm"
                  >
                    <Search className="w-5 h-5" />
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
