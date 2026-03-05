"use client";

import React, { useState, useEffect } from "react";
import {
  GitCompare,
  Loader2,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
} from "lucide-react";
import { DerivationalConnection } from "@/lib/data-shared";

interface DerivationsPanelProps {
  corpusId: number;
}

export default function DerivationsPanel({ corpusId }: DerivationsPanelProps) {
  const [connections, setConnections] = useState<DerivationalConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(true);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(
          `/api/curated/derivational-connections?corpusId=${corpusId}`,
        );
        const data = await res.json();
        setConnections(data);
      } catch (err) {
        console.error("Failed to fetch connections", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [corpusId]);

  const handleToggle = async (conn: DerivationalConnection) => {
    const connId = `${conn.from_root_id}-${conn.to_root_id}-${conn.to_stem}`;
    setTogglingId(connId);
    const newStatus = conn.user_approved !== "x";

    try {
      const res = await fetch("/api/curated/derivational-connections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          key: {
            from_root_id: conn.from_root_id,
            from_h_grade: conn.from_h_grade,
            from_g_grade: conn.from_g_grade,
            from_class: conn.from_class,
            to_root_id: conn.to_root_id,
            to_h_grade: conn.to_h_grade,
            to_g_grade: conn.to_g_grade,
            to_class: conn.to_class,
          },
          approved: newStatus,
        }),
      });

      if (res.ok) {
        setConnections((prev) =>
          prev.map((c) =>
            c.from_root_id === conn.from_root_id &&
            c.to_root_id === conn.to_root_id &&
            c.to_class === conn.to_class
              ? { ...c, user_approved: newStatus ? "x" : "" }
              : c,
          ),
        );
      }
    } catch (err) {
      console.error("Toggle failed", err);
    } finally {
      setTogglingId(null);
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
          <GitCompare className="w-4 h-4 text-emerald-500" />
          Derivational Connections
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {isOpen && (
        <div className="p-4">
          {connections.length > 0 ? (
            <div className="space-y-3">
              {connections.map((conn, idx) => {
                const isFrom = String(conn.from_corpus_ids || "")
                  .split(";")
                  .map((s) => s.trim())
                  .includes(String(corpusId));
                const connId = `${conn.from_root_id}-${conn.to_root_id}-${conn.to_stem}`;
                const isApproved = conn.user_approved === "x";

                return (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/30"
                  >
                    <button
                      onClick={() => handleToggle(conn)}
                      disabled={togglingId === connId}
                      className={`mt-1 shrink-0 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                        isApproved
                          ? "bg-emerald-500 border-emerald-500 text-white"
                          : "border-gray-300 dark:border-zinc-700 hover:border-emerald-500"
                      }`}
                    >
                      {togglingId === connId ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : isApproved ? (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      ) : null}
                    </button>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`text-[10px] font-bold uppercase tracking-tighter px-1.5 py-0.5 rounded ${
                            isFrom
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400"
                              : "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400"
                          }`}
                        >
                          {isFrom ? "Source" : "Target"}
                        </span>
                        <span className="text-xs font-mono text-zinc-400 truncate">
                          {isFrom
                            ? `→ ${conn.to_root_id}`
                            : `← ${conn.from_root_id}`}
                        </span>
                      </div>

                      <div className="text-xs text-zinc-600 dark:text-zinc-400 leading-tight">
                        {isFrom ? (
                          <>
                            Derived into{" "}
                            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                              {conn.to_root_id}
                            </span>{" "}
                            ({conn.to_class})
                          </>
                        ) : (
                          <>
                            Derived from{" "}
                            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                              {conn.from_root_id}
                            </span>{" "}
                            ({conn.from_class})
                          </>
                        )}
                      </div>

                      <div className="mt-2 flex flex-wrap gap-1">
                        <span className="text-[10px] px-1.5 py-0.5 bg-zinc-200 dark:bg-zinc-700 rounded text-zinc-600 dark:text-zinc-300">
                          {conn.to_form_type}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-zinc-200 dark:bg-zinc-700 rounded text-zinc-600 dark:text-zinc-300 font-italic">
                          {conn.to_stem}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center bg-zinc-50 dark:bg-zinc-800/30 rounded-lg border border-dashed border-gray-200 dark:border-zinc-800">
              <GitCompare className="w-8 h-8 text-zinc-300 dark:text-zinc-700 mx-auto mb-2" />
              <p className="text-sm text-zinc-400">
                No derivational connections found.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
