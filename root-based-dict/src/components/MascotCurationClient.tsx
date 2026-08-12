"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Search,
  CheckCircle2,
  ChevronRight,
  BookOpen,
  Save,
  RefreshCw,
} from "lucide-react";

export interface AspectClassItem {
  class_name: string;
  mascot_corpus_id: number | null;
  candidate_count: number;
}

export interface CandidateItem {
  corpus_id: number;
  definition: string;
  verb_class: string;
  entry_no?: number;
}

interface FormDetail {
  syllabary: string;
  practical: string;
}

interface ParadigmPreview {
  corpus_id: number;
  definition: string;
  verb_class: string;
  prediction: string;
  forms: Record<string, FormDetail>;
}

interface MascotCurationClientProps {
  initialClasses: AspectClassItem[];
}

export default function MascotCurationClient({
  initialClasses,
}: MascotCurationClientProps) {
  const [classList, setClassList] = useState<AspectClassItem[]>(initialClasses);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedClass, setSelectedClass] = useState<AspectClassItem | null>(
    initialClasses[0] || null
  );

  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [candidateQuery, setCandidateQuery] = useState("");
  const [loadingCandidates, setLoadingCandidates] = useState(false);

  const [preview, setPreview] = useState<ParadigmPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [selectedCorpusId, setSelectedCorpusId] = useState<number | null>(null);

  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Load candidates when selectedClass changes
  useEffect(() => {
    if (!selectedClass) return;

    setCandidateQuery("");
    setLoadingCandidates(true);

    fetch(`/api/mascots?className=${encodeURIComponent(selectedClass.class_name)}`)
      .then((res) => res.json())
      .then((data) => {
        const fetchedCandidates: CandidateItem[] = data.candidates || [];
        const fetchedMascotId = data.mascotCorpusId ?? selectedClass.mascot_corpus_id ?? null;

        setCandidates(fetchedCandidates);
        setLoadingCandidates(false);

        setSelectedCorpusId(fetchedMascotId);
        if (fetchedMascotId !== null) {
          loadPreview(fetchedMascotId);
        } else {
          setPreview(null);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch candidates:", err);
        setLoadingCandidates(false);
      });
  }, [selectedClass?.class_name]);

  const loadPreview = (corpusId: number) => {
    setLoadingPreview(true);
    fetch(`/api/mascots?previewCorpusId=${corpusId}`)
      .then((res) => res.json())
      .then((data) => {
        setPreview(data);
        setLoadingPreview(false);
      })
      .catch((err) => {
        console.error("Failed to fetch preview:", err);
        setLoadingPreview(false);
      });
  };

  const handleSelectCandidate = (cid: number) => {
    setSelectedCorpusId(cid);
    loadPreview(cid);
  };

  const handleSave = async (cidToSave: number | null) => {
    if (!selectedClass) return;
    setSaving(true);
    setStatusMessage(null);

    try {
      const res = await fetch("/api/mascots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          className: selectedClass.class_name,
          mascotCorpusId: cidToSave,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setStatusMessage(
          cidToSave !== null
            ? `Mascot #${cidToSave} successfully saved for "${selectedClass.class_name}"!`
            : `Mascot cleared for "${selectedClass.class_name}".`
        );

        setSelectedCorpusId(cidToSave);

        // Update selected class and class list state
        setSelectedClass((prev) => (prev ? { ...prev, mascot_corpus_id: cidToSave } : null));
        setClassList((prev) =>
          prev.map((item) =>
            item.class_name === selectedClass.class_name
              ? { ...item, mascot_corpus_id: cidToSave }
              : item
          )
        );

        if (cidToSave === null) {
          setPreview(null);
        }
      } else {
        setStatusMessage(`Error: ${data.error || "Failed to save mascot"}`);
      }
    } catch (err) {
      setStatusMessage("Failed to save mascot. Check console.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const filteredClasses = classList.filter((c) =>
    c.class_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredCandidates = candidates.filter((cand) => {
    return (
      String(cand.corpus_id).includes(candidateQuery) ||
      cand.definition.toLowerCase().includes(candidateQuery.toLowerCase())
    );
  });

  const activeAssignedId = selectedClass?.mascot_corpus_id ?? null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-500" />
            Aspect Class Mascot Curation
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
            Curate baseline representative verb mascots per aspect class directly from hierarchical-dict.json.
          </p>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 rounded-lg bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 text-sm border border-emerald-200 dark:border-emerald-800/40 flex items-center justify-between">
          <span>{statusMessage}</span>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-xs underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main split grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Class Selection sidebar */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl p-4 border border-gray-200 dark:border-zinc-800 flex flex-col h-[750px]">
          <div className="mb-4 space-y-2">
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
              Aspect Classes ({filteredClasses.length})
            </h2>
            <div className="relative">
              <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search class names..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-sm rounded-md bg-zinc-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {filteredClasses.map((item) => {
              const isSelected = selectedClass?.class_name === item.class_name;
              const hasMascot = item.mascot_corpus_id !== null && item.mascot_corpus_id !== undefined;

              return (
                <button
                  key={item.class_name}
                  onClick={() => setSelectedClass(item)}
                  className={`w-full text-left p-3 rounded-lg border text-sm transition-all flex items-center justify-between ${
                    isSelected
                      ? "bg-amber-50 border-amber-400 dark:bg-amber-950/30 dark:border-amber-700 text-amber-900 dark:text-amber-100 font-medium"
                      : "bg-zinc-50/50 dark:bg-zinc-800/40 border-gray-100 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-800 dark:text-zinc-200"
                  }`}
                >
                  <div className="space-y-0.5 min-w-0 pr-2">
                    <div className="font-mono text-sm font-semibold truncate">{item.class_name}</div>
                    <div className="text-xs text-zinc-400">
                      {item.candidate_count} candidate{item.candidate_count === 1 ? "" : "s"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {hasMascot ? (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-xs font-mono font-medium">
                        <CheckCircle2 className="w-3 h-3" />
                        #{item.mascot_corpus_id}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-zinc-200 dark:bg-zinc-700 text-zinc-500 dark:text-zinc-400 text-xs font-medium">
                        Unassigned
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 text-zinc-400" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Mascot Curation and Paradigm Preview Panel */}
        <div className="md:col-span-2 space-y-6 flex flex-col">
          {selectedClass ? (
            <>
              {/* Active Class Header Card */}
              <div className="bg-white dark:bg-zinc-900 rounded-xl p-5 border border-gray-200 dark:border-zinc-800 flex flex-col gap-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="text-xs uppercase tracking-wider font-bold text-amber-500">
                      Selected Class Name
                    </div>
                    <h2 className="text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100 mt-0.5">
                      {selectedClass.class_name}
                    </h2>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                      {selectedClass.candidate_count} matching candidate verb{selectedClass.candidate_count === 1 ? "" : "s"} in hierarchical-dict.json
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleSave(selectedCorpusId)}
                      disabled={saving || selectedCorpusId === activeAssignedId || selectedCorpusId === null}
                      className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white rounded-lg font-medium text-sm transition-colors shadow-sm"
                    >
                      <Save className="w-4 h-4" />
                      {saving ? "Saving..." : "Save Mascot"}
                    </button>

                    {activeAssignedId !== null && (
                      <button
                        onClick={() => handleSave(null)}
                        disabled={saving}
                        className="px-3 py-2 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-lg text-sm font-medium transition-colors"
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Candidates search & selection */}
              <div className="bg-white dark:bg-zinc-900 rounded-xl p-5 border border-gray-200 dark:border-zinc-800 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-amber-500" />
                    Select Mascot Candidate ({filteredCandidates.length})
                  </h3>
                  <div className="w-64 relative">
                    <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      placeholder="Filter candidate verbs..."
                      value={candidateQuery}
                      onChange={(e) => setCandidateQuery(e.target.value)}
                      className="w-full pl-8 pr-3 py-1 text-xs rounded-md bg-zinc-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none"
                    />
                  </div>
                </div>

                {loadingCandidates ? (
                  <div className="p-8 text-center text-sm text-zinc-400 flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-amber-500" />
                    Loading candidate verbs...
                  </div>
                ) : filteredCandidates.length === 0 ? (
                  <div className="p-6 text-center text-sm text-zinc-400 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
                    No candidate verbs match the current filter.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
                    {filteredCandidates.map((cand) => {
                      const isCandidateSelected = selectedCorpusId === cand.corpus_id;
                      return (
                        <button
                          key={cand.corpus_id}
                          onClick={() => handleSelectCandidate(cand.corpus_id)}
                          className={`p-2.5 rounded-lg border text-left transition-all flex items-center justify-between ${
                            isCandidateSelected
                              ? "bg-amber-500/10 border-amber-500 text-amber-900 dark:text-amber-100 font-medium"
                              : "bg-zinc-50 dark:bg-zinc-800/40 border-gray-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-800 dark:text-zinc-200"
                          }`}
                        >
                          <div className="min-w-0 pr-2 space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-amber-600 dark:text-amber-400 font-bold">
                                #{cand.corpus_id}
                              </span>
                            </div>
                            <div className="text-sm truncate">{cand.definition}</div>
                          </div>
                          {isCandidateSelected && (
                            <CheckCircle2 className="w-4 h-4 text-amber-500 flex-shrink-0" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* 6-Form Paradigm Preview Grid */}
              <div className="bg-white dark:bg-zinc-900 rounded-xl p-5 border border-gray-200 dark:border-zinc-800 space-y-4 flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    6-Form Paradigm Preview
                  </h3>
                  {preview && (
                    <span className="text-xs font-mono bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 px-2 py-0.5 rounded">
                      Corpus #{preview.corpus_id} - "{preview.definition}"
                    </span>
                  )}
                </div>

                {loadingPreview ? (
                  <div className="p-12 text-center text-sm text-zinc-400 flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-amber-500" />
                    Loading paradigm preview...
                  </div>
                ) : !preview ? (
                  <div className="p-12 text-center text-sm text-zinc-400 bg-zinc-50 dark:bg-zinc-800/30 rounded-lg">
                    Select a candidate verb above to preview its 6-form paradigm table.
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {[
                      { key: "present", label: "Present (3sg)" },
                      { key: "present_1sg", label: "Present (1sg)" },
                      { key: "imperfective", label: "Imperfective" },
                      { key: "perfective", label: "Perfective" },
                      { key: "imperative", label: "Imperative" },
                      { key: "infinitive", label: "Infinitive" },
                    ].map((formItem) => {
                      const detail = preview.forms[formItem.key] || {
                        syllabary: "---",
                        practical: "---",
                      };
                      return (
                        <div
                          key={formItem.key}
                          className="bg-zinc-50 dark:bg-zinc-800/50 p-3.5 rounded-lg border border-gray-100 dark:border-zinc-800 space-y-1.5"
                        >
                          <div className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
                            {formItem.label}
                          </div>
                          <div className="text-lg font-serif font-bold text-amber-600 dark:text-amber-400">
                            {detail.syllabary}
                          </div>
                          <div className="text-sm font-mono text-zinc-700 dark:text-zinc-300">
                            {detail.practical}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-zinc-400 bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800">
              Select an aspect class from the left sidebar to curate its mascot.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
