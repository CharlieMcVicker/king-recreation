"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Circle,
  ArrowRight,
  Database,
  Info,
  ExternalLink,
  LayoutDashboard,
} from "lucide-react";
import Link from "next/link";

interface Definition {
  id: number;
  definition: string;
}

interface DerivationalConnectionWithDefinitions {
  user_approved: string;
  from_root_id: string;
  from_h_grade: string;
  from_g_grade: string;
  from_class: string;
  from_stem_type: string;
  from_corpus_ids: string;
  to_root_id: string;
  to_h_grade: string;
  to_g_grade: string;
  to_class: string;
  to_stem_type: string;
  to_corpus_ids: string;
  to_form_type: string;
  to_stem: string;
  from_definitions: Definition[];
  to_definitions: Definition[];
}

interface ReviewDerivationsProps {
  initialConnections: DerivationalConnectionWithDefinitions[];
}

export default function ReviewDerivations({
  initialConnections,
}: ReviewDerivationsProps) {
  const [connections, setConnections] = useState(initialConnections);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAll, setShowAll] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const filteredConnections = useMemo(() => {
    if (showAll) return connections;
    return connections.filter((c) => !c.user_approved);
  }, [connections, showAll]);

  const current = filteredConnections[currentIndex];

  const handleToggleApproved = async () => {
    if (!current) return;

    const newApproved = !current.user_approved;
    setIsSaving(true);

    try {
      const response = await fetch("/api/curated/derivational-connections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          key: {
            from_root_id: current.from_root_id,
            from_h_grade: current.from_h_grade,
            from_g_grade: current.from_g_grade,
            from_class: current.from_class,
            to_root_id: current.to_root_id,
            to_h_grade: current.to_h_grade,
            to_g_grade: current.to_g_grade,
            to_class: current.to_class,
          },
          approved: newApproved,
        }),
      });

      if (!response.ok) throw new Error("Failed to update");

      // Update local state
      const updated = connections.map((c) => {
        if (
          c.from_root_id === current.from_root_id &&
          c.from_h_grade === current.from_h_grade &&
          c.from_g_grade === current.from_g_grade &&
          c.from_class === current.from_class &&
          c.to_root_id === current.to_root_id &&
          c.to_h_grade === current.to_h_grade &&
          c.to_g_grade === current.to_g_grade &&
          c.to_class === current.to_class
        ) {
          return { ...c, user_approved: newApproved ? "x" : "" };
        }
        return c;
      });

      setConnections(updated);

      // Auto-advance if approving and filtering unreviewed
      if (newApproved && !showAll) {
        // Current index stays same because current item will disappear from filtered list
        // unless it's the last item
        if (currentIndex >= filteredConnections.length - 1) {
          setCurrentIndex(Math.max(0, filteredConnections.length - 2));
        }
      } else if (newApproved) {
        // If showing all, just advance
        if (currentIndex < filteredConnections.length - 1) {
          setCurrentIndex(currentIndex + 1);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;

      if (e.key === "ArrowLeft") {
        setCurrentIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === "ArrowRight") {
        setCurrentIndex((prev) =>
          Math.min(filteredConnections.length - 1, prev + 1),
        );
      } else if (e.key === "Enter") {
        handleToggleApproved();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, filteredConnections, handleToggleApproved]);

  // Reset index when filter changes
  useEffect(() => {
    setCurrentIndex(0);
  }, [showAll]);

  if (!current && filteredConnections.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
        <div className="p-6 bg-zinc-100 dark:bg-zinc-900 rounded-full">
          <CheckCircle2 className="w-16 h-16 text-emerald-500" />
        </div>
        <div className="space-y-2">
          <h2 className="text-3xl font-bold">All Connections Reviewed!</h2>
          <p className="text-zinc-500 max-w-md">
            You've triaged all heuristic proposals. Toggle "Show All" if you
            want to review your previous approvals.
          </p>
        </div>
        <button
          onClick={() => setShowAll(true)}
          className="px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all active:scale-95"
        >
          Show All Connections
        </button>
      </div>
    );
  }

  const reviewedCount = connections.filter((c) => c.user_approved).length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800 sticky top-4 z-10">
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
              Review Progress
            </span>
            <span className="font-bold text-lg">
              {reviewedCount} / {connections.length}
            </span>
            <div className="w-32 h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full mt-1 overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-500"
                style={{
                  width: `${(reviewedCount / connections.length) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="w-px h-10 bg-zinc-200 dark:bg-zinc-800" />

          <div className="flex items-center gap-3">
            <label className="text-sm font-bold text-zinc-500">
              Unreviewed Only
            </label>
            <button
              onClick={() => setShowAll(!showAll)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
                !showAll ? "bg-indigo-600" : "bg-zinc-200 dark:bg-zinc-700"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  !showAll ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-xs font-mono text-zinc-400 bg-zinc-50 dark:bg-zinc-950 px-3 py-1 rounded-lg border border-zinc-100 dark:border-zinc-800">
            {currentIndex + 1} of {filteredConnections.length} shown
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentIndex((p) => Math.max(0, p - 1))}
              disabled={currentIndex === 0}
              className="p-2.5 rounded-xl border-2 border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-20 transition-all"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <button
              onClick={() =>
                setCurrentIndex((p) =>
                  Math.min(filteredConnections.length - 1, p + 1),
                )
              }
              disabled={currentIndex === filteredConnections.length - 1}
              className="p-2.5 rounded-xl border-2 border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-20 transition-all"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Connection View */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative items-stretch">
        {/* Connector Line/Icon */}
        <div className="hidden md:flex absolute inset-0 items-center justify-center pointer-events-none z-0">
          <div className="w-full border-t-2 border-dashed border-zinc-200 dark:border-zinc-800 absolute" />
          <div className="bg-zinc-50 dark:bg-zinc-950 p-4 rounded-full border-2 border-zinc-200 dark:border-zinc-800 shadow-xl">
            <ArrowRight className="w-8 h-8 text-indigo-500" />
          </div>
        </div>

        {/* FROM Side */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm relative z-[1]">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-50 dark:bg-indigo-900/20 p-2 rounded-lg text-indigo-500">
                <Info className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-black uppercase tracking-tight text-zinc-400">
                Base Word
              </h2>
            </div>
            <div className="flex gap-2">
              {current.from_corpus_ids.split(";").map((id) => (
                <Link
                  key={id}
                  href={`/lexical-review/${id.trim()}`}
                  className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800 text-zinc-400 hover:text-indigo-600 border border-zinc-200 dark:border-zinc-700 transition-colors"
                  title={`View Dashboard for ${id.trim()}`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                </Link>
              ))}
            </div>
          </div>

          <div className="space-y-8">
            <div className="space-y-1">
              <div className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                Root ID
              </div>
              <div
                className={`text-3xl font-mono font-bold ${
                  current.from_root_id !== current.to_root_id
                    ? "text-indigo-600 dark:text-indigo-400"
                    : "text-zinc-900 dark:text-zinc-100"
                }`}
              >
                {current.from_root_id}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <Field
                label="H-Grade"
                value={current.from_h_grade}
                otherValue={current.to_h_grade}
              />
              <Field
                label="G-Grade"
                value={current.from_g_grade}
                otherValue={current.to_g_grade}
              />
              <Field
                label="Class"
                value={current.from_class}
                otherValue={current.to_class}
              />
              <Field
                label="Stem Type"
                value={current.from_stem_type}
                otherValue={current.to_stem_type}
              />
            </div>

            <div className="space-y-4 pt-6 border-t border-zinc-100 dark:border-zinc-800">
              <div className="text-[10px] font-black uppercase tracking-widest text-zinc-400 flex items-center gap-2">
                <Database className="w-3 h-3" /> Definitions for{" "}
                {current.from_corpus_ids}
              </div>
              <div className="space-y-3">
                {current.from_definitions.map((d) => (
                  <div
                    key={d.id}
                    className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-800"
                  >
                    <div className="text-xs font-bold text-zinc-400 mb-1">
                      #{d.id}
                    </div>
                    <div className="text-lg font-medium italic">
                      "{d.definition}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* TO Side */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm relative z-[1]">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="bg-emerald-50 dark:bg-emerald-900/20 p-2 rounded-lg text-emerald-500">
                <ExternalLink className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-black uppercase tracking-tight text-zinc-400">
                Derived Word
              </h2>
            </div>
            <div className="flex gap-2">
              {current.to_corpus_ids.split(";").map((id) => (
                <Link
                  key={id}
                  href={`/lexical-review/${id.trim()}`}
                  className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800 text-zinc-400 hover:text-indigo-600 border border-zinc-200 dark:border-zinc-700 transition-colors"
                  title={`View Dashboard for ${id.trim()}`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                </Link>
              ))}
            </div>
          </div>

          <div className="space-y-8">
            <div className="space-y-1">
              <div className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                Root ID
              </div>
              <div
                className={`text-3xl font-mono font-bold ${
                  current.from_root_id !== current.to_root_id
                    ? "text-indigo-600 dark:text-indigo-400"
                    : "text-zinc-900 dark:text-zinc-100"
                }`}
              >
                {current.to_root_id}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <Field
                label="H-Grade"
                value={current.to_h_grade}
                otherValue={current.from_h_grade}
                highlight
              />
              <Field
                label="G-Grade"
                value={current.to_g_grade}
                otherValue={current.from_g_grade}
                highlight
              />
              <Field
                label="Class"
                value={current.to_class}
                otherValue={current.from_class}
                highlight
              />
              <Field
                label="Stem Type"
                value={current.to_stem_type}
                otherValue={current.from_stem_type}
                highlight
              />
            </div>

            <div className="space-y-4 pt-6 border-t border-zinc-100 dark:border-zinc-800">
              <div className="text-[10px] font-black uppercase tracking-widest text-zinc-400 flex items-center gap-2">
                <Database className="w-3 h-3" /> Definitions for{" "}
                {current.to_corpus_ids}
              </div>
              <div className="space-y-3">
                {current.to_definitions.map((d) => (
                  <div
                    key={d.id}
                    className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-800"
                  >
                    <div className="text-xs font-bold text-zinc-400 mb-1">
                      #{d.id}
                    </div>
                    <div className="text-lg font-medium italic">
                      "{d.definition}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl p-4 rounded-3xl border border-zinc-200 dark:border-zinc-800 shadow-2xl z-20 w-full max-w-xl">
        <button
          onClick={handleToggleApproved}
          disabled={isSaving}
          className={`flex-1 h-14 rounded-2xl font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all active:scale-95 shadow-xl ${
            current.user_approved
              ? "bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-300 dark:hover:bg-zinc-700"
              : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20"
          }`}
        >
          {isSaving ? (
            <div className="w-6 h-6 border-3 border-zinc-400 border-t-zinc-600 rounded-full animate-spin" />
          ) : current.user_approved ? (
            <>
              <Circle className="w-6 h-6" /> Un-Approve
            </>
          ) : (
            <>
              <CheckCircle2 className="w-6 h-6" /> Approve (Enter)
            </>
          )}
        </button>

        <div className="flex gap-2">
          <button
            onClick={() => setCurrentIndex((p) => Math.max(0, p - 1))}
            disabled={currentIndex === 0}
            className="h-14 w-14 rounded-2xl border-2 border-zinc-200 dark:border-zinc-800 flex items-center justify-center hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-20 transition-all shadow-sm"
            title="Previous (Left Arrow)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          <button
            onClick={() =>
              setCurrentIndex((p) =>
                Math.min(filteredConnections.length - 1, p + 1),
              )
            }
            disabled={currentIndex === filteredConnections.length - 1}
            className="h-14 w-14 rounded-2xl border-2 border-zinc-200 dark:border-zinc-800 flex items-center justify-center hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-20 transition-all shadow-sm"
            title="Next (Right Arrow)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  otherValue,
  highlight,
}: {
  label: string;
  value: string;
  otherValue: string;
  highlight?: boolean;
}) {
  const isDifferent = value !== otherValue;
  return (
    <div className="space-y-1">
      <div className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
        {label}
      </div>
      <div
        className={`px-3 py-1.5 rounded-lg border font-mono font-bold text-sm transition-all ${
          isDifferent
            ? "bg-rose-50 dark:bg-rose-900/10 border-rose-100 dark:border-rose-900/30 text-rose-600 dark:text-rose-400"
            : "bg-zinc-50 dark:bg-zinc-950 border-zinc-100 dark:border-zinc-900 text-zinc-700 dark:text-zinc-300"
        }`}
      >
        {value || "-"}
      </div>
    </div>
  );
}
