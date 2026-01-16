"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Search, ArrowRight, BookOpen } from "lucide-react";
import { useRouter } from "next/navigation";

interface CorpusEntry {
  definition: string;
  present: string;
  imperfective: string;
  perfective: string;
  imperative: string;
  infinitive: string;
  corpus_id: number;
}

export default function SearchClient({ corpus }: { corpus: CorpusEntry[] }) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const results = useMemo(() => {
    if (!query || query.length < 2) return [];

    const lowerQuery = query.toLowerCase();

    return corpus.filter((entry) => {
      // Check definition
      if (entry.definition?.toLowerCase().includes(lowerQuery)) return true;

      // Check forms
      const forms = [
        entry.present,
        entry.imperfective,
        entry.perfective,
        entry.imperative,
        entry.infinitive,
      ];

      return forms.some(
        (form) => form && form.toLowerCase().includes(lowerQuery)
      );
    });
  }, [corpus, query]);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Search Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">Dictionary Search</h1>
        <p className="text-gray-500 dark:text-zinc-400">
          Find lexical entries by definition or by searching for specific verb
          forms.
        </p>
      </div>

      {/* Search Input */}
      <div className="relative max-w-2xl mx-auto">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full rounded-xl border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 pl-11 pr-4 py-4 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:focus:ring-indigo-900/50"
          placeholder="Search by english definition or cherokee form..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
      </div>

      {/* Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-sm text-gray-500 px-2">
          <span>
            {query.length >= 2
              ? `${results.length} results found`
              : "Enter at least 2 characters to search"}
          </span>
        </div>

        <div className="grid gap-4">
          {results.map((entry) => (
            <Link
              key={entry.definition}
              href={`/explorer/entry/${entry.corpus_id}`}
              className="group block bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 p-6 hover:border-indigo-500 dark:hover:border-indigo-500 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    {entry.definition}
                  </h3>

                  {/* Show matching forms if query matches a form */}
                  {query.length >= 2 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {[
                        { label: "Present", val: entry.present },
                        { label: "Imperfective", val: entry.imperfective },
                        { label: "Perfective", val: entry.perfective },
                        { label: "Imperative", val: entry.imperative },
                        { label: "Infinitive", val: entry.infinitive },
                      ].map((form) => {
                        if (
                          form.val &&
                          form.val.toLowerCase().includes(query.toLowerCase())
                        ) {
                          return (
                            <span
                              key={form.label}
                              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300"
                            >
                              {form.label}:{" "}
                              <span className="font-serif ml-1">
                                {form.val}
                              </span>
                            </span>
                          );
                        }
                        return null;
                      })}
                    </div>
                  )}
                </div>
                <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-indigo-500 transform group-hover:translate-x-1 transition-all" />
              </div>
            </Link>
          ))}

          {query.length >= 2 && results.length === 0 && (
            <div className="text-center py-12 border-2 border-dashed border-gray-100 dark:border-zinc-800 rounded-xl">
              <BookOpen className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p className="text-gray-500">
                No entries found matching "{query}"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
