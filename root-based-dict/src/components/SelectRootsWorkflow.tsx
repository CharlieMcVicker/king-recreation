"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Keyboard,
  ArrowLeft,
  ArrowRight,
  Database,
  Filter,
  Eye,
  EyeOff,
  LayoutDashboard,
} from "lucide-react";
import Link from "next/link";

import { ValidatedRootRow } from "@/lib/data-shared";

interface SelectRootsWorkflowProps {
  initialData: ValidatedRootRow[];
  changedOptionsIds?: number[];
  initialCorpusId?: number;
}

export default function SelectRootsWorkflow({
  initialData,
  changedOptionsIds = [],
  initialCorpusId,
}: SelectRootsWorkflowProps) {
  const [showAllRows, setShowAllRows] = useState(false);
  const [showOnlyUnreviewed, setShowOnlyUnreviewed] = useState(false);
  const [showOnlyChanged, setShowOnlyChanged] = useState(false);

  // Group data by corpus_id
  const { groupedData, allCorpusIds } = useMemo(() => {
    const groups: Record<number, ValidatedRootRow[]> = {};
    const ids: number[] = [];

    initialData.forEach((row) => {
      const corpusId = Number(row.meta.corpus_id);
      if (isNaN(corpusId)) return;
      if (!groups[corpusId]) {
        groups[corpusId] = [];
        ids.push(corpusId);
      }
      groups[corpusId].push(row);
    });

    return { groupedData: groups, allCorpusIds: ids };
  }, [initialData]);

  const uniqueCorpusIds = useMemo(() => {
    let ids = allCorpusIds;

    if (showOnlyUnreviewed) {
      ids = ids.filter((id) => {
        const derivations = groupedData[id] || [];
        return !derivations.some((d) => d.curation.user_selected === "x");
      });
    }

    if (showOnlyChanged) {
      const changedSet = new Set(changedOptionsIds);
      ids = ids.filter((id) => changedSet.has(id));
    }

    return ids;
  }, [
    allCorpusIds,
    showOnlyUnreviewed,
    showOnlyChanged,
    groupedData,
    changedOptionsIds,
  ]);

  const [currentIndex, setCurrentIndex] = useState(0);

  // Set initial index if initialCorpusId is provided
  useEffect(() => {
    if (initialCorpusId !== undefined) {
      const index = uniqueCorpusIds.indexOf(initialCorpusId);
      if (index !== -1) {
        setCurrentIndex(index);
      } else if (allCorpusIds.includes(initialCorpusId)) {
        // If not found in filtered list but exists in data, clear filters
        setShowOnlyUnreviewed(false);
        setShowOnlyChanged(false);
      }
    }
  }, [initialCorpusId, uniqueCorpusIds, allCorpusIds]);
  const [selectedDerivationIndex, setSelectedDerivationIndex] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Reset index if it becomes out of bounds due to filtering
  useEffect(() => {
    if (currentIndex >= uniqueCorpusIds.length && uniqueCorpusIds.length > 0) {
      setCurrentIndex(0);
    }
  }, [uniqueCorpusIds.length, currentIndex]);

  const currentCorpusId = uniqueCorpusIds[currentIndex];
  const derivations = groupedData[currentCorpusId] || [];

  // Initialize selection based on user_selected or pipeline_selected
  useEffect(() => {
    if (derivations.length > 0) {
      const userSelectedIndex = derivations.findIndex(
        (d) => d.curation.user_selected === "x",
      );
      if (userSelectedIndex !== -1) {
        setSelectedDerivationIndex(userSelectedIndex);
      } else {
        const pipelineSelectedIndex = derivations.findIndex(
          (d) => d.curation.pipeline_selected === "x",
        );
        setSelectedDerivationIndex(
          pipelineSelectedIndex !== -1 ? pipelineSelectedIndex : 0,
        );
      }
    }
  }, [currentIndex, derivations]);

  const handleNext = () => {
    if (currentIndex < uniqueCorpusIds.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setMessage(null);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setMessage(null);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      const response = await fetch("/api/select-roots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpusId: currentCorpusId,
          rowIndex: selectedDerivationIndex,
        }),
      });

      if (!response.ok) throw new Error("Failed to save selection");

      setMessage({ type: "success", text: "Selection saved!" });
      // Auto advance
      setTimeout(handleNext, 500);
    } catch (err) {
      console.error(err);
      setMessage({ type: "error", text: "Failed to save selection" });
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" || e.key === "k") {
        setSelectedDerivationIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === "ArrowRight" || e.key === "j") {
        setSelectedDerivationIndex((prev) =>
          Math.min(derivations.length - 1, prev + 1),
        );
      } else if (e.key === "Enter") {
        handleSave();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [derivations.length, selectedDerivationIndex, currentCorpusId]);

  if (!currentCorpusId) return <div>No data loaded.</div>;

  // Defensive access: ensure we always have a derivation if any exist,
  // even if the index is temporarily out of bounds during navigation.
  const selectedDerivation =
    derivations[selectedDerivationIndex] || derivations[0];

  const getValue = (obj: any, path: string) => {
    return path.split(".").reduce((acc, part) => acc && acc[part], obj);
  };

  const rows = useMemo(
    () => [
      { label: "Class", key: "aspect.verb_class" },
      { label: "Stem Type", key: "config.pron.stem_type" },
      { label: "Prediction", key: "meta.prediction" },
      { label: "H Grade", key: "roots.h_grade" },
      { label: "G Grade", key: "roots.g_grade" },
      { label: "Morpheme", key: "aspect.post_root_morpheme" },
      { label: "Stative", key: "aspect.stative" },
      { label: "Metathesis", key: "metathesis_involved" },
      { label: "Set A/B", key: "config.pron.set_type" },
      { label: "Allow H Meta", key: "config.pron.allow_h_metathesis" },
      { label: "Middle Voice", key: "config.pron.middle_voice" },
      { label: "MV H Meta", key: "config.pron.middle_voice_h_metathesis" },
      { label: "Plural", key: "config.pron.plural_pronouns" },
      { label: "Ka Variant", key: "config.pron.use_ka_variant" },
      { label: "Aki 1st", key: "config.pron.use_aki_for_1st_set_b" },
      { label: "Uwa V", key: "config.pron.uwa_replaces_v" },
      { label: "3rd Obj", key: "config.pron.use_3rd_person_object" },
      { label: "Transloc", key: "config.pre.translocutive" },
      { label: "Transloc (Imp)", key: "config.pre.translocutiveImpOnly" },
      { label: "Partitive", key: "config.pre.partitive" },
      { label: "Distributive", key: "config.pre.distributive" },
    ],
    [],
  );

  const redundantRowKeys = useMemo(() => {
    if (derivations.length <= 1) return new Set<string>();

    const redundant = new Set<string>();
    rows.forEach((row) => {
      const firstVal = getValue(derivations[0], row.key);
      const allSame = derivations.every(
        (d) => getValue(d, row.key) === firstVal,
      );
      if (allSame) {
        redundant.add(row.key);
      }
    });
    return redundant;
  }, [derivations, rows]);

  const visibleRows = showAllRows
    ? rows
    : rows.filter((r) => !redundantRowKeys.has(r.key));

  const renderCell = (val: any) => {
    if (typeof val === "boolean") {
      return val ? "Yes" : "No";
    }
    return val || "-";
  };

  const getFormReconstruction = (derivation: ValidatedRootRow) => {
    try {
      return JSON.parse(derivation.segmented_forms);
    } catch (e) {
      return {};
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between bg-white dark:bg-zinc-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100 italic">
              "{derivations[0]?.meta.definition}"
            </h1>
            <span className="px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-xs font-mono text-zinc-500">
              ID: {currentCorpusId}
            </span>
            {selectedDerivation?.curation.user_selected === "x" && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 text-[10px] font-bold uppercase tracking-wider border border-emerald-100 dark:border-emerald-800/30">
                <CheckCircle2 className="w-3 h-3" />
                User Approved
              </span>
            )}
            {selectedDerivation?.curation.pipeline_selected === "x" && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400 text-[10px] font-bold uppercase tracking-wider border border-amber-100 dark:border-amber-800/30">
                <AlertCircle className="w-3 h-3" />
                Pipeline Selected
              </span>
            )}
            <Link
              href={`/lexical-review/${currentCorpusId}`}
              className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400 text-[10px] font-bold uppercase tracking-wider border border-indigo-100 dark:border-indigo-800/30 hover:bg-indigo-100 transition-colors"
            >
              <LayoutDashboard className="w-3 h-3" />
              Lexical Dashboard
            </Link>
          </div>
          <p className="text-sm text-zinc-500 flex items-center gap-2">
            <Database className="w-4 h-4" />
            Entry No. {derivations[0]?.meta.entry_no}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right mr-4">
            <div className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
              {uniqueCorpusIds.length > 0 ? currentIndex + 1 : 0} /{" "}
              {uniqueCorpusIds.length}
            </div>
            <div className="text-xs text-zinc-500">
              {showOnlyUnreviewed
                ? "Unreviewed words"
                : showOnlyChanged
                  ? "Words with changed options"
                  : "Words reviewed"}
            </div>
          </div>

          <div className="flex gap-1">
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className="p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex === uniqueCorpusIds.length - 1}
              className="p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main UI */}
      <div className="grid grid-cols-1 gap-6">
        {/* Tabular View */}
        <div className="overflow-x-auto bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800">
          <table className="w-full text-left border-collapse table-fixed min-w-[800px]">
            <thead>
              <tr className="bg-zinc-50 dark:bg-zinc-950">
                <th className="w-40 p-4 font-semibold text-zinc-900 dark:text-zinc-100 border-b border-gray-200 dark:border-zinc-800">
                  Feature
                </th>
                {derivations.map((derivation, idx) => {
                  const isSelected = idx === selectedDerivationIndex;
                  const isPipeline = derivation.curation.pipeline_selected === "x";
                  const isUser = derivation.curation.user_selected === "x";
                  const pipelineDiffers =
                    derivation.curation.pipeline_selected === "x" &&
                    derivation.curation.user_selected !== "x" &&
                    derivations.some((d) => d.curation.user_selected === "x");

                  return (
                    <th
                      key={idx}
                      onClick={() => setSelectedDerivationIndex(idx)}
                      className={`p-4 border-b border-gray-200 dark:border-zinc-800 cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-indigo-50/50 dark:bg-indigo-900/10"
                          : "hover:bg-zinc-100 dark:hover:bg-zinc-800"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className={`text-xs font-bold uppercase tracking-wider ${
                            isSelected
                              ? "text-indigo-600 dark:text-indigo-400"
                              : "text-zinc-500"
                          }`}
                        >
                          Choice {idx + 1}
                        </span>
                        {isPipeline && (
                          <span
                            title="Pipeline Choice"
                            className="text-zinc-400"
                          >
                            <AlertCircle className="w-4 h-4 fill-zinc-100 dark:fill-zinc-800" />
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-4 h-4 rounded-full border flex items-center justify-center transition-colors ${
                            isSelected
                              ? "bg-indigo-600 border-indigo-600"
                              : "border-gray-300 dark:border-zinc-700"
                          }`}
                        >
                          {isSelected && (
                            <div className="w-1.5 h-1.5 rounded-full bg-white" />
                          )}
                        </div>
                        <span
                          className={`text-sm font-medium ${isSelected ? "text-indigo-900 dark:text-indigo-100" : "text-zinc-600 dark:text-zinc-400"}`}
                        >
                          {isSelected ? "Focused" : "Select"}
                        </span>
                      </div>
                      {isPipeline && (
                        <div className="mt-2 text-[10px] font-medium text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-900/20 px-1.5 py-0.5 rounded inline-block">
                          Pipeline Selected
                        </div>
                      )}
                      {isUser && (
                        <div className="mt-2 text-[10px] font-medium text-emerald-600 dark:text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 px-1.5 py-0.5 rounded inline-block">
                          User Approved
                        </div>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row, rowIdx) => (
                <tr
                  key={row.key}
                  className="group hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                >
                  <td className="p-3 border-b border-gray-100 dark:border-zinc-800 font-medium text-zinc-600 dark:text-zinc-400 text-sm">
                    {row.label}
                  </td>
                  {derivations.map((derivation, devIdx) => {
                    const val = getValue(derivation, row.key);
                    const selectedVal = selectedDerivation
                      ? getValue(selectedDerivation, row.key)
                      : undefined;
                    const isDiff =
                      devIdx !== selectedDerivationIndex &&
                      selectedDerivation &&
                      val !== selectedVal;
                    const isFocusColumn = devIdx === selectedDerivationIndex;

                    return (
                      <td
                        key={devIdx}
                        className={`p-3 border-b border-gray-100 dark:border-zinc-800 text-sm transition-colors ${
                          isFocusColumn
                            ? "bg-indigo-50/30 dark:bg-indigo-900/5 font-medium text-zinc-900 dark:text-zinc-100"
                            : "text-zinc-600 dark:text-zinc-400"
                        } ${isDiff ? "bg-amber-50 dark:bg-amber-900/20 text-amber-900 dark:text-amber-200" : ""}`}
                      >
                        {renderCell(val)}
                      </td>
                    );
                  })}
                </tr>
              ))}

              {/* Special row for segmented forms */}
              <tr className="bg-zinc-50 dark:bg-zinc-950 font-semibold italic">
                <td className="p-3 border-b border-gray-100 dark:border-zinc-800 text-sm">
                  Reconstruction
                </td>
                {derivations.map((derivation, devIdx) => {
                  const forms = getFormReconstruction(derivation);
                  const isFocusColumn = devIdx === selectedDerivationIndex;
                  return (
                    <td
                      key={devIdx}
                      className={`p-3 border-b border-gray-100 dark:border-zinc-800 text-xs font-mono space-y-1 ${
                        isFocusColumn
                          ? "bg-indigo-50/50 dark:bg-indigo-900/10"
                          : ""
                      }`}
                    >
                      {Object.entries(forms).map(([key, val]) => (
                        <div key={key} title={key}>
                          <span className="text-[10px] opacity-50 block uppercase tracking-tighter">
                            {key.replace("_", " ")}
                          </span>
                          <span
                            className={
                              isFocusColumn
                                ? "text-indigo-600 dark:text-indigo-400"
                                : ""
                            }
                          >
                            {val as string}
                          </span>
                        </div>
                      ))}
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between bg-white dark:bg-zinc-900 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800">
          <div className="flex items-center gap-6 text-sm text-zinc-500">
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                <ArrowLeft className="w-3 h-3" />{" "}
                <ArrowRight className="w-3 h-3" />
              </span>
              <span>Navigate Choices</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                Enter
              </span>
              <span>Save & Next</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAllRows(!showAllRows)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showAllRows
                  ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                  : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              {showAllRows ? (
                <Eye className="w-4 h-4" />
              ) : (
                <EyeOff className="w-4 h-4" />
              )}
              {showAllRows ? "Showing All" : "Hiding Shared"}
              <span className="ml-1 text-[10px] opacity-60">
                ({redundantRowKeys.size} hidden)
              </span>
            </button>

            <button
              onClick={() => {
                setShowOnlyUnreviewed(!showOnlyUnreviewed);
                setCurrentIndex(0); // Reset on toggle
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showOnlyUnreviewed
                  ? "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
                  : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              <Filter
                className={`w-4 h-4 ${showOnlyUnreviewed ? "fill-current" : ""}`}
              />
              {showOnlyUnreviewed ? "Unreviewed Only" : "Show All Verbs"}
            </button>

            <button
              onClick={() => {
                setShowOnlyChanged(!showOnlyChanged);
                setCurrentIndex(0);
              }}
              disabled={changedOptionsIds.length === 0}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-30 ${
                showOnlyChanged
                  ? "bg-indigo-100 text-indigo-900 dark:bg-indigo-900/40 dark:text-indigo-100"
                  : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              <AlertCircle
                className={`w-4 h-4 ${showOnlyChanged ? "fill-current" : ""}`}
              />
              Review New Options
              {changedOptionsIds.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-indigo-500 text-white text-[10px] font-bold">
                  {changedOptionsIds.length}
                </span>
              )}
            </button>
          </div>

          <div className="flex items-center gap-4">
            {message && (
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium animate-in fade-in slide-in-from-right-2 ${
                  message.type === "success"
                    ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400"
                    : "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                {message.text}
              </div>
            )}

            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-400 text-white rounded-lg font-semibold shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  Confirm Selection
                  <Keyboard className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
