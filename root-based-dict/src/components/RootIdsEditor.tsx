"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Database,
  CheckCircle2,
  Filter,
  Keyboard,
  List,
  Zap,
  LayoutDashboard,
} from "lucide-react";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import Link from "next/link";
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

interface RootIdsEditorProps {
  initialData: RootIdRow[];
  currentCorpusId: number;
}

export default function RootIdsEditor({
  initialData,
  currentCorpusId,
}: RootIdsEditorProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const [data, setData] = useState(initialData);

  const showOnlyUnreviewed = searchParams.get("triage") !== "false";

  const setShowOnlyUnreviewed = (val: boolean) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("triage", val.toString());
    router.push(`${pathname}?${params.toString()}`);
  };

  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Grouping for siblings
  const siblingsMap = useMemo(() => {
    const map = new Map<string, RootIdRow[]>();
    data.forEach((row) => {
      const rid = (row.root_id || "").trim();
      if (!rid) return;
      if (!map.has(rid)) {
        map.set(rid, []);
      }
      map.get(rid)!.push(row);
    });
    return map;
  }, [data]);

  const filteredIds = useMemo(() => {
    if (showOnlyUnreviewed) {
      return data
        .filter((row) => !row.user_edited || row.corpus_id === currentCorpusId)
        .map((row) => row.corpus_id);
    }
    return data.map((row) => row.corpus_id);
  }, [data, showOnlyUnreviewed, currentCorpusId]);

  const currentIndex = useMemo(() => {
    return filteredIds.indexOf(currentCorpusId);
  }, [filteredIds, currentCorpusId]);

  const currentRow = useMemo(
    () => data.find((r) => r.corpus_id === currentCorpusId),
    [data, currentCorpusId],
  );

  const [inputRootId, setInputRootId] = useState("");

  useEffect(() => {
    if (currentRow) {
      setInputRootId(currentRow.root_id || "");
      setMessage(null);
    }
  }, [currentRow]);

  const navigateTo = (id: number) => {
    const params = new URLSearchParams(searchParams.toString());
    router.push(`/review-root-ids/${id}?${params.toString()}`);
  };

  const handleNext = () => {
    if (currentIndex < filteredIds.length - 1) {
      navigateTo(filteredIds[currentIndex + 1]);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      navigateTo(filteredIds[currentIndex - 1]);
    }
  };

  const handleSave = async () => {
    if (!currentRow) return;
    setIsSaving(true);
    setMessage(null);
    try {
      const response = await fetch("/api/curated/root-ids", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpusId: currentRow.corpus_id,
          rootId: inputRootId,
        }),
      });

      if (!response.ok) throw new Error("Failed to save");

      // Update local state
      const newData = data.map((r) =>
        r.corpus_id === currentRow.corpus_id
          ? { ...r, root_id: inputRootId, user_edited: "x" }
          : r,
      );
      setData(newData);

      setMessage({ type: "success", text: "Saved!" });

      // Auto advance
      // In unreviewed mode, the current item will still be in filteredIds (see filteredIds useMemo)
      // but after navigation it might disappear if showOnlyUnreviewed is true.
      setTimeout(() => {
        if (currentIndex < filteredIds.length - 1) {
          handleNext();
        } else if (showOnlyUnreviewed) {
          // If we finished the filtered list, try finding the very next unreviewed generally
          const nextUnreviewed = newData.find((r) => !r.user_edited);
          if (nextUnreviewed) {
            navigateTo(nextUnreviewed.corpus_id);
          }
        }
      }, 300);
    } catch (err) {
      console.error(err);
      setMessage({ type: "error", text: "Error saving" });
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, filteredIds.length, showOnlyUnreviewed]);

  if (!currentRow && filteredIds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <CheckCircle2 className="w-16 h-16 text-emerald-500" />
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          All caught up!
        </h2>
        <p className="text-zinc-500">
          No unreviewed words left. (Total entries: {data.length})
        </p>
        <button
          onClick={() => {
            setShowOnlyUnreviewed(false);
          }}
          className="px-6 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg font-medium hover:bg-zinc-200 transition-colors"
        >
          View All Items
        </button>
      </div>
    );
  }

  if (!currentRow) return null;

  const currentSiblings = (siblingsMap.get(inputRootId.trim()) || []).filter(
    (s) => s.corpus_id !== currentRow.corpus_id,
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* Header / Nav */}
      <div className="flex items-center justify-between bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-8">
          <div>
            <div className="text-2xl font-bold tracking-tight">
              {currentIndex + 1}{" "}
              <span className="text-zinc-400 font-normal mx-1">/</span>{" "}
              {filteredIds.length}
            </div>
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
              {showOnlyUnreviewed ? "Unreviewed Only" : "Viewing All"}
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              setShowOnlyUnreviewed(!showOnlyUnreviewed);
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-semibold transition-all ${
              showOnlyUnreviewed
                ? "bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-900/20 dark:border-amber-800/30 dark:text-amber-400"
                : "bg-zinc-50 border-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-100"
            }`}
          >
            <Filter
              className={`w-4 h-4 ${showOnlyUnreviewed ? "fill-current" : ""}`}
            />
            {showOnlyUnreviewed ? "Fast Triage" : "Review All"}
          </button>
        </div>

        <div className="flex gap-2">
          <NavButton onClick={handlePrev} disabled={currentIndex === 0}>
            <ChevronLeft className="w-6 h-6" />
          </NavButton>
          <NavButton
            onClick={handleNext}
            disabled={currentIndex === filteredIds.length - 1}
          >
            <ChevronRight className="w-6 h-6" />
          </NavButton>
        </div>
      </div>

      {/* Item Display */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden shadow-xl shadow-zinc-200/50 dark:shadow-black/20">
        {/* Main Info */}
        <div className="p-10 border-b border-zinc-100 dark:border-zinc-800">
          <div className="flex justify-between items-start mb-6">
            <div className="space-y-2">
              <h2 className="text-4xl font-bold text-zinc-900 dark:text-zinc-100 italic tracking-tight">
                "{currentRow.definition}"
              </h2>
              <div className="flex items-center gap-6 text-sm text-zinc-500 font-medium">
                <span className="flex items-center gap-1.5">
                  <Database className="w-4 h-4 scale-90" />
                  ID:{" "}
                  <span className="text-zinc-800 font-mono font-bold dark:text-zinc-200">
                    {currentRow.corpus_id}
                  </span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Class:{" "}
                  <span className="text-zinc-800 font-bold dark:text-zinc-200">
                    {currentRow.class}
                  </span>
                </span>
              </div>
            </div>
            {currentRow.user_edited && !message && (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 text-[10px] font-black uppercase border border-emerald-100 dark:border-emerald-800/30">
                <CheckCircle2 className="w-3.5 h-3.5" /> Reviewed
              </div>
            )}
            <Link
              href={`/lexical-review/${currentCorpusId}`}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400 text-[10px] font-black uppercase border border-indigo-100 dark:border-indigo-800/30 hover:bg-indigo-100 transition-colors"
            >
              <LayoutDashboard className="w-3.5 h-3.5" /> Lexical Dashboard
            </Link>
            {message && (
              <div
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase border animate-in fade-in slide-in-from-top-2 ${
                  message.type === "success"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800/30"
                    : "bg-rose-50 text-rose-700 border-rose-100 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-800/30"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : (
                  <Database className="w-3.5 h-3.5" />
                )}
                {message.text}
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-8">
            <DetailBox label="H Grade Root" value={currentRow.h_grade} />
            <DetailBox label="G Grade Root" value={currentRow.g_grade} />
            <DetailBox
              label="Suffix Morpheme"
              value={currentRow.post_root_morpheme}
            />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-10 bg-zinc-50 dark:bg-zinc-950/40">
          <label className="block text-[10px] font-black text-zinc-400 mb-3 uppercase tracking-[0.2em]">
            Assigned Root ID (Group Label)
          </label>
          <div className="flex gap-4">
            <input
              autoFocus
              value={inputRootId}
              onChange={(e) => setInputRootId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSave();
                }
              }}
              placeholder="Enter common root id..."
              className="block w-full px-6 py-4 text-3xl font-mono font-bold bg-white dark:bg-zinc-900 border-2 border-zinc-200 dark:border-zinc-800 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none"
            />
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-10 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-400 text-white rounded-2xl font-bold shadow-xl shadow-indigo-500/30 flex items-center gap-3 transition-all active:scale-95"
            >
              {isSaving ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Save</span>
                  <Keyboard className="w-5 h-5 opacity-40" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Sibling List */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold flex items-center justify-between text-zinc-800 dark:text-zinc-200 px-2">
          <div className="flex items-center gap-3">
            <List className="w-6 h-6 text-indigo-500" />
            <span>
              Shared Group:{" "}
              <span className="text-zinc-400 italic">
                {inputRootId.trim() || "(Empty)"}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            {inputRootId.trim() && (
              <Link
                href={`/review-root-ids/groups/${toBase64Url(inputRootId.trim())}`}
                className="text-[10px] font-black uppercase tracking-widest bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400 px-3 py-1.5 rounded-lg border border-indigo-100 dark:border-indigo-800/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-all flex items-center gap-2"
              >
                <Zap className="w-3 h-3" />
                Bulk Edit Group
              </Link>
            )}
            <span className="text-xs font-mono bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded-lg text-zinc-500">
              {currentSiblings.length} OTHER WORDS
            </span>
          </div>
        </h3>

        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl divide-y divide-zinc-100 dark:divide-zinc-800 shadow-sm max-h-[500px] overflow-y-auto custom-scrollbar">
          {currentSiblings.length === 0 ? (
            <div className="p-16 text-center">
              <div className="inline-flex p-4 rounded-full bg-zinc-50 dark:bg-zinc-800/50 mb-4 opacity-50">
                <Database className="w-8 h-8 text-zinc-400" />
              </div>
              <p className="text-zinc-400 font-medium">
                No other words share this ID.
              </p>
            </div>
          ) : (
            currentSiblings.map((s) => (
              <div
                key={s.corpus_id}
                className="p-5 flex justify-between items-center group hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
              >
                <div className="space-y-1">
                  <div className="font-bold text-zinc-900 dark:text-zinc-100">
                    "{s.definition}"
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-zinc-500 font-mono font-medium">
                    <span>ID {s.corpus_id}</span>
                    <span className="w-1 h-1 rounded-full bg-zinc-300" />
                    <span>H: {s.h_grade || "-"}</span>
                    <span className="w-1 h-1 rounded-full bg-zinc-300" />
                    <span>G: {s.g_grade || "-"}</span>
                    <span className="w-1 h-1 rounded-full bg-zinc-300" />
                    <span>{s.class}</span>
                  </div>
                </div>
                {s.user_edited && (
                  <span title="Reviewed" className="text-emerald-500">
                    <CheckCircle2 className="w-4 h-4" />
                  </span>
                )}
                <Link
                  href={`/lexical-review/${s.corpus_id}`}
                  className="p-2 rounded-lg text-zinc-400 hover:text-indigo-600 transition-colors"
                  title="View Dashboard"
                >
                  <LayoutDashboard className="w-4 h-4" />
                </Link>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function DetailBox({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-zinc-50 dark:bg-zinc-950/20 p-4 rounded-xl border border-zinc-100 dark:border-zinc-800/50">
      <div className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-1">
        {label}
      </div>
      <div className="text-lg font-bold text-zinc-900 dark:text-zinc-100 font-mono truncate h-7">
        {value || (
          <span className="opacity-20 font-sans font-normal">None</span>
        )}
      </div>
    </div>
  );
}

function NavButton({
  children,
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="p-3 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-20 disabled:hover:bg-transparent transition-all active:scale-90"
    >
      {children}
    </button>
  );
}
