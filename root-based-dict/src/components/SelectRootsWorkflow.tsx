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
} from "lucide-react";

interface ValidatedRootRow {
  corpus_id: number;
  entry_no: number;
  user_selected: string;
  pipeline_selected: string;
  definition: string;
  stative: boolean;
  class: string;
  post_root_morpheme: string;
  h_grade: string;
  g_grade: string;
  metathesis_involved: boolean;
  set_a_b: string;
  stem_type: string;
  allow_h_metathesis: boolean;
  middle_voice: string;
  middle_voice_h_metathesis: boolean;
  plural: boolean;
  ka_variant: boolean;
  aki_1st: boolean;
  uwa_v: boolean;
  "3rd_person_object": boolean;
  translocutive: boolean;
  translocutive_imp_only: boolean;
  partitive: boolean;
  distributive: boolean;
  distributive_fut_prog: boolean;
  segmented_forms: string; // JSON string
}

interface SelectRootsWorkflowProps {
  initialData: ValidatedRootRow[];
}

export default function SelectRootsWorkflow({
  initialData,
}: SelectRootsWorkflowProps) {
  const [showAllRows, setShowAllRows] = useState(false);
  const [showOnlyUnreviewed, setShowOnlyUnreviewed] = useState(false);

  // Group data by corpus_id
  const { groupedData, allCorpusIds } = useMemo(() => {
    const groups: Record<number, ValidatedRootRow[]> = {};
    const ids: number[] = [];

    initialData.forEach((row) => {
      if (!groups[row.corpus_id]) {
        groups[row.corpus_id] = [];
        ids.push(row.corpus_id);
      }
      groups[row.corpus_id].push(row);
    });

    return { groupedData: groups, allCorpusIds: ids };
  }, [initialData]);

  const uniqueCorpusIds = useMemo(() => {
    if (!showOnlyUnreviewed) return allCorpusIds;

    return allCorpusIds.filter((id) => {
      const derivations = groupedData[id] || [];
      return !derivations.some((d) => d.user_selected === "x");
    });
  }, [allCorpusIds, showOnlyUnreviewed, groupedData]);

  const [currentIndex, setCurrentIndex] = useState(0);
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
        (d) => d.user_selected === "x",
      );
      if (userSelectedIndex !== -1) {
        setSelectedDerivationIndex(userSelectedIndex);
      } else {
        const pipelineSelectedIndex = derivations.findIndex(
          (d) => d.pipeline_selected === "x",
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

  const rows = useMemo(
    () => [
      { label: "Class", key: "class" },
      { label: "Stem Type", key: "stem_type" },
      { label: "H Grade", key: "h_grade" },
      { label: "G Grade", key: "g_grade" },
      { label: "Morpheme", key: "post_root_morpheme" },
      { label: "Stative", key: "stative" },
      { label: "Metathesis", key: "metathesis_involved" },
      { label: "Set A/B", key: "set_a_b" },
      { label: "Allow H Meta", key: "allow_h_metathesis" },
      { label: "Middle Voice", key: "middle_voice" },
      { label: "MV H Meta", key: "middle_voice_h_metathesis" },
      { label: "Plural", key: "plural" },
      { label: "Ka Variant", key: "ka_variant" },
      { label: "Aki 1st", key: "aki_1st" },
      { label: "Uwa V", key: "uwa_v" },
      { label: "3rd Obj", key: "3rd_person_object" },
      { label: "Transloc", key: "translocutive" },
      { label: "Transloc (Imp Only)", key: "translocutive_imp_only" },
      { label: "Partitive", key: "partitive" },
      { label: "Distributive", key: "distributive" },
      { label: "Dist (Fut/Prog)", key: "distributive_fut_prog" },
    ],
    [],
  );

  const redundantRowKeys = useMemo(() => {
    if (derivations.length <= 1) return new Set<string>();

    const redundant = new Set<string>();
    rows.forEach((row) => {
      const firstVal = (derivations[0] as any)[row.key];
      const allSame = derivations.every(
        (d) => (d as any)[row.key] === firstVal,
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
              "{derivations[0]?.definition}"
            </h1>
            <span className="px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-xs font-mono text-zinc-500">
              ID: {currentCorpusId}
            </span>
            {selectedDerivation?.user_selected === "x" && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 text-[10px] font-bold uppercase tracking-wider border border-emerald-100 dark:border-emerald-800/30">
                <CheckCircle2 className="w-3 h-3" />
                User Approved
              </span>
            )}
            {selectedDerivation?.pipeline_selected === "x" && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400 text-[10px] font-bold uppercase tracking-wider border border-amber-100 dark:border-amber-800/30">
                <AlertCircle className="w-3 h-3" />
                Pipeline Selected
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-500 flex items-center gap-2">
            <Database className="w-4 h-4" />
            Entry No. {derivations[0]?.entry_no}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right mr-4">
            <div className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
              {uniqueCorpusIds.length > 0 ? currentIndex + 1 : 0} /{" "}
              {uniqueCorpusIds.length}
            </div>
            <div className="text-xs text-zinc-500">
              {showOnlyUnreviewed ? "Unreviewed words" : "Words reviewed"}
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
                  const isPipeline = derivation.pipeline_selected === "x";
                  const isUser = derivation.user_selected === "x";
                  const pipelineDiffers =
                    derivation.pipeline_selected === "x" &&
                    derivation.user_selected !== "x" &&
                    derivations.some((d) => d.user_selected === "x");

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
                    const val = (derivation as any)[row.key];
                    const selectedVal = selectedDerivation
                      ? (selectedDerivation as any)[row.key]
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
