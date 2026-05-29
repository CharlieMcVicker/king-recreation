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
  Save,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { ConfigFlags } from "@/app/reconstructable-verbs/ConfigFlags";
import { getCorpusForm, DictionaryEntry } from "@/lib/data-shared";

interface StativeVerbEntry {
  canonical: any;
  shims: any[];
  currentShim: any | null;
}

interface ReviewStativeShimsProps {
  initialStativeVerbs: StativeVerbEntry[];
  dictionary: DictionaryEntry[];
}

export default function ReviewStativeShims({
  initialStativeVerbs,
  dictionary,
}: ReviewStativeShimsProps) {
  const [verbs, setVerbs] = useState(initialStativeVerbs);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAll, setShowAll] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedShimIndex, setSelectedShimIndex] = useState<number | null>(null);

  const filteredVerbs = useMemo(() => {
    if (showAll) return verbs;
    return verbs.filter((v) => !v.currentShim);
  }, [verbs, showAll]);

  const current = filteredVerbs[currentIndex];

  // Set the selected shim index when current verb changes
  useEffect(() => {
    if (!current) {
      setSelectedShimIndex(null);
      return;
    }

    if (current.currentShim) {
      // Find which shim in current.shims matches current.currentShim config
      const idx = current.shims.findIndex((s) => {
        return (
          s.meta.prediction === current.currentShim.prediction &&
          s.aspect.verb_class === current.currentShim.class &&
          s.roots.h_grade === current.currentShim.h_grade &&
          s.roots.g_grade === current.currentShim.g_grade &&
          s.aspect.post_root_morpheme === current.currentShim.post_root_morpheme &&
          s.config.pron.set_type === current.currentShim.set_a_b &&
          s.config.pron.stem_type === current.currentShim.stem_type &&
          s.config.pron.allow_h_metathesis === current.currentShim.allow_h_metathesis &&
          s.config.pron.middle_voice === current.currentShim.middle_voice &&
          s.config.pron.middle_voice_h_metathesis === current.currentShim.middle_voice_h_metathesis &&
          s.config.pron.plural_pronouns === current.currentShim.plural &&
          s.config.pron.use_ka_variant === current.currentShim.ka_variant &&
          s.config.pron.use_aki_for_1st_set_b === current.currentShim.aki_1st &&
          s.config.pron.uwa_replaces_v === current.currentShim.uwa_v &&
          s.config.pron.use_3rd_person_object === current.currentShim["3rd_person_object"] &&
          s.config.pre.translocutive === current.currentShim.translocutive &&
          s.config.pre.translocutiveImpOnly === current.currentShim.translocutive_imp_only &&
          s.config.pre.partitive === current.currentShim.partitive &&
          s.config.pre.distributive === current.currentShim.distributive
        );
      });
      setSelectedShimIndex(idx !== -1 ? idx : null);
    } else {
      // Fallback to pipeline choice (the one with pipeline_selected === "x" or true)
      const pipeIdx = current.shims.findIndex(
        (s) => s.curation.pipeline_selected === "x" || s.curation.pipeline_selected === true
      );
      setSelectedShimIndex(pipeIdx !== -1 ? pipeIdx : 0);
    }
  }, [current]);

  const handleSaveShim = async (shimToSave: any | null) => {
    if (!current) return;

    setIsSaving(true);
    const corpusId = Number(current.canonical.meta.corpus_id);

    // Build shimKey matching StativeShimRow fields
    const shimKey = shimToSave
      ? {
          prediction: shimToSave.meta.prediction,
          class: shimToSave.aspect.verb_class,
          h_grade: shimToSave.roots.h_grade,
          g_grade: shimToSave.roots.g_grade,
          post_root_morpheme: shimToSave.aspect.post_root_morpheme,
          set_a_b: shimToSave.config.pron.set_type,
          stem_type: shimToSave.config.pron.stem_type,
          allow_h_metathesis: shimToSave.config.pron.allow_h_metathesis,
          middle_voice: shimToSave.config.pron.middle_voice,
          middle_voice_h_metathesis: shimToSave.config.pron.middle_voice_h_metathesis,
          plural: shimToSave.config.pron.plural_pronouns,
          ka_variant: shimToSave.config.pron.use_ka_variant,
          aki_1st: shimToSave.config.pron.use_aki_for_1st_set_b,
          uwa_v: shimToSave.config.pron.uwa_replaces_v,
          "3rd_person_object": shimToSave.config.pron.use_3rd_person_object,
          translocutive: shimToSave.config.pre.translocutive,
          translocutive_imp_only: shimToSave.config.pre.translocutiveImpOnly,
          partitive: shimToSave.config.pre.partitive,
          distributive: shimToSave.config.pre.distributive,
        }
      : null;

    try {
      const response = await fetch("/api/curated/stative-shims", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ corpusId, shimKey }),
      });

      if (!response.ok) throw new Error("Failed to save");

      // Update local state
      const updated = verbs.map((v) => {
        if (Number(v.canonical.meta.corpus_id) === corpusId) {
          return {
            ...v,
            currentShim: shimKey ? { ...shimKey, corpus_id: corpusId } : null,
          };
        }
        return v;
      });

      setVerbs(updated);

      // Auto-advance if reviewing unreviewed
      if (shimKey && !showAll) {
        if (currentIndex >= filteredVerbs.length - 1) {
          setCurrentIndex(Math.max(0, filteredVerbs.length - 2));
        }
      } else if (shimKey) {
        if (currentIndex < filteredVerbs.length - 1) {
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
          Math.min(filteredVerbs.length - 1, prev + 1),
        );
      } else if (e.key === "Enter") {
        if (current && selectedShimIndex !== null) {
          handleSaveShim(current.shims[selectedShimIndex]);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, filteredVerbs, selectedShimIndex, current]);

  useEffect(() => {
    setCurrentIndex(0);
  }, [showAll]);

  if (!current && filteredVerbs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
        <div className="p-6 bg-zinc-100 dark:bg-zinc-900 rounded-full">
          <CheckCircle2 className="w-16 h-16 text-emerald-500" />
        </div>
        <div className="space-y-2">
          <h2 className="text-3xl font-bold">All Stative Shims Curated!</h2>
          <p className="text-zinc-500 max-w-md">
            Every stative verb has been mapped to its infinitive shim. Toggle
            "Show All" to review previous mappings.
          </p>
        </div>
        <button
          onClick={() => setShowAll(true)}
          className="px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all active:scale-95"
        >
          Show All Stative Verbs
        </button>
      </div>
    );
  }

  const reviewedCount = verbs.filter((v) => v.currentShim).length;
  const currentStativeForm = (key: string) => {
    const entryNo = current.canonical.meta.entry_no;
    const parsed = entryNo ? Number(entryNo) : undefined;
    return getCorpusForm(dictionary, parsed, key);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20">
      {/* Header Banner */}
      <div className="flex items-center justify-between bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800 sticky top-4 z-10">
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
              Shim Progress
            </span>
            <span className="font-bold text-lg">
              {reviewedCount} / {verbs.length} stative verbs curated
            </span>
            <div className="w-32 h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full mt-1 overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-500"
                style={{
                  width: `${(reviewedCount / verbs.length) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="w-px h-10 bg-zinc-200 dark:bg-zinc-800" />

          <div className="flex items-center gap-3">
            <label className="text-sm font-bold text-zinc-500">
              Uncurated Only
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
            {currentIndex + 1} of {filteredVerbs.length} shown
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
                  Math.min(filteredVerbs.length - 1, p + 1),
                )
              }
              disabled={currentIndex === filteredVerbs.length - 1}
              className="p-2.5 rounded-xl border-2 border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-20 transition-all"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-stretch relative">
        <div className="hidden md:flex absolute inset-0 items-center justify-center pointer-events-none z-0">
          <div className="w-full border-t-2 border-dashed border-zinc-200 dark:border-zinc-800 absolute" />
          <div className="bg-zinc-50 dark:bg-zinc-950 p-4 rounded-full border-2 border-zinc-200 dark:border-zinc-800 shadow-xl">
            <ArrowRight className="w-8 h-8 text-indigo-500" />
          </div>
        </div>

        {/* LEFT COLUMN: Stative Verb details */}
        <div className="md:col-span-5 bg-white dark:bg-zinc-900 rounded-3xl p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm relative z-[1] space-y-6">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-50 dark:bg-indigo-900/20 p-2 rounded-lg text-indigo-500">
              <Info className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-black uppercase tracking-tight text-zinc-400">
              Stative Verb
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                Definition
              </span>
              <h3 className="text-2xl font-bold italic">
                "{current.canonical.meta.definition}"
              </h3>
            </div>

            <div className="p-4 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/50 dark:border-amber-900/30 rounded-2xl">
              <span className="text-[10px] font-black uppercase tracking-widest text-amber-600 dark:text-amber-400 block mb-1">
                Target Infinitive to Account For
              </span>
              <div className="text-2xl font-mono font-black text-amber-900 dark:text-amber-100">
                {currentStativeForm("infinitive") || "-"}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                  Corpus ID
                </span>
                <div className="font-mono font-bold text-sm">
                  {current.canonical.meta.corpus_id}
                </div>
              </div>
              <div>
                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                  H-Grade Root
                </span>
                <div className="font-mono font-bold text-sm bg-zinc-50 dark:bg-zinc-950 px-2 py-1 rounded border border-zinc-200 dark:border-zinc-800 w-fit">
                  {current.canonical.roots.h_grade}
                </div>
              </div>
            </div>

            <div className="space-y-3 pt-6 border-t border-zinc-100 dark:border-zinc-800">
              <div className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                Attested Forms
              </div>
              <div className="space-y-2">
                {[
                  { label: "1sg Present", key: "present_1sg" },
                  { label: "3rd Present", key: "present" },
                  { label: "Imperfective", key: "imperfective" },
                  { label: "Perfective", key: "perfective" },
                  { label: "Imperative", key: "imperative" },
                ].map((form) => (
                  <div
                    key={form.key}
                    className="flex justify-between items-center p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-800"
                  >
                    <span className="text-xs font-bold text-zinc-400">
                      {form.label}
                    </span>
                    <span className="text-sm font-mono font-bold">
                      {currentStativeForm(form.key) || "-"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Infinitive Shim candidates */}
        <div className="md:col-span-7 bg-white dark:bg-zinc-900 rounded-3xl p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm relative z-[1] space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-emerald-50 dark:bg-emerald-900/20 p-2 rounded-lg text-emerald-500">
                <Database className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-black uppercase tracking-tight text-zinc-400">
                Infinitive Shim Candidates
              </h2>
            </div>

            {current.currentShim && (
              <button
                onClick={() => handleSaveShim(null)}
                disabled={isSaving}
                className="flex items-center gap-1 text-xs text-rose-500 hover:text-rose-600 font-bold border border-rose-200 dark:border-rose-800 px-3 py-1.5 rounded-xl hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Unbind Shim
              </button>
            )}
          </div>

          <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
            {current.shims.length === 0 ? (
              <div className="p-8 text-center text-zinc-500 bg-zinc-50 dark:bg-zinc-800/20 rounded-2xl border border-zinc-100 dark:border-zinc-800">
                No InfEventful shims found matching root.
              </div>
            ) : (
              current.shims.map((shim, idx) => {
                const isSelected = selectedShimIndex === idx;
                const isSaved =
                  current.currentShim &&
                  shim.meta.prediction === current.currentShim.prediction &&
                  shim.aspect.verb_class === current.currentShim.class &&
                  shim.roots.h_grade === current.currentShim.h_grade &&
                  shim.roots.g_grade === current.currentShim.g_grade &&
                  shim.aspect.post_root_morpheme === current.currentShim.post_root_morpheme &&
                  shim.config.pron.set_type === current.currentShim.set_a_b &&
                  shim.config.pron.stem_type === current.currentShim.stem_type;

                const isPipelineSelected =
                  shim.curation.pipeline_selected === "x" || shim.curation.pipeline_selected === true;

                // Extract infinitive segmented form
                let infSeg = "-";
                if (shim.segmented_forms) {
                  try {
                    const parsedSeg = typeof shim.segmented_forms === "string"
                      ? JSON.parse(shim.segmented_forms)
                      : shim.segmented_forms;
                    infSeg = parsedSeg.infinitive || "-";
                  } catch (e) {}
                }

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedShimIndex(idx)}
                    className={`p-5 rounded-2xl border-2 cursor-pointer transition-all flex flex-col gap-4 relative ${
                      isSelected
                        ? "border-indigo-500 bg-indigo-50/10 dark:bg-indigo-900/10"
                        : "border-zinc-200 dark:border-zinc-800 bg-white hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800/50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isSelected ? (
                          <CheckCircle2 className="w-5 h-5 text-indigo-500" />
                        ) : (
                          <Circle className="w-5 h-5 text-zinc-300" />
                        )}
                        <span className="font-mono font-bold text-lg">
                          {getCorpusForm(dictionary, Number(shim.meta.entry_no), "infinitive") || "-"}
                        </span>
                      </div>

                      <div className="flex gap-2">
                        {isSaved && (
                          <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400 text-[10px] font-black uppercase tracking-wider">
                            Bound Choice
                          </span>
                        )}
                        {isPipelineSelected && (
                          <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-400 text-[10px] font-black uppercase tracking-wider">
                            Pipeline Default
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="text-zinc-400 uppercase tracking-wide text-[9px] font-bold block">
                          Class
                        </span>
                        <span className="font-semibold">{shim.aspect.verb_class}</span>
                      </div>
                      <div>
                        <span className="text-zinc-400 uppercase tracking-wide text-[9px] font-bold block">
                          Morpheme
                        </span>
                        <span className="font-semibold">{shim.aspect.post_root_morpheme || "-"}</span>
                      </div>
                      <div>
                        <span className="text-zinc-400 uppercase tracking-wide text-[9px] font-bold block">
                          Segmented Inf
                        </span>
                        <span className="font-mono text-indigo-500 dark:text-indigo-400 font-bold truncate block">
                          {infSeg}
                        </span>
                      </div>
                      <div className="flex items-end justify-end">
                        <ConfigFlags config={shim.config} />
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Floating Action Bar */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl p-4 rounded-3xl border border-zinc-200 dark:border-zinc-800 shadow-2xl z-20 w-full max-w-xl">
        <button
          onClick={() => {
            if (selectedShimIndex !== null) {
              handleSaveShim(current.shims[selectedShimIndex]);
            }
          }}
          disabled={isSaving || selectedShimIndex === null}
          className="flex-1 h-14 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all active:scale-95 shadow-xl disabled:opacity-50"
        >
          {isSaving ? (
            <div className="w-6 h-6 border-3 border-zinc-400 border-t-zinc-600 rounded-full animate-spin" />
          ) : (
            <>
              <Save className="w-6 h-6" /> Save Bind (Enter)
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
                Math.min(filteredVerbs.length - 1, p + 1),
              )
            }
            disabled={currentIndex === filteredVerbs.length - 1}
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
