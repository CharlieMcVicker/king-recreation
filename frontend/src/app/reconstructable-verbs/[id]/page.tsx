import React from "react";
import { getVerbDetails } from "@/lib/data";
import Link from "next/link";
import {
  ArrowLeft,
  Book,
  GitBranch,
  Table,
  Database,
  Share2,
  ArrowRight,
  Settings,
} from "lucide-react";
import { notFound } from "next/navigation";
import { ConfigFlags } from "../ConfigFlags";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function VerbDetailPage({ params }: PageProps) {
  const resolvedParams = await params;
  const index = parseInt(resolvedParams.id, 10);

  if (isNaN(index)) {
    notFound();
  }

  const data = await getVerbDetails(index);

  if (!data) {
    notFound();
  }

  const { verb, endings, corpusEntries, relatedVerbs } = data;

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl animate-in fade-in duration-500">
      <Link
        href="/reconstructable-verbs"
        className="inline-flex items-center text-sm text-gray-500 hover:text-indigo-600 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Verbs
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 border border-gray-200 dark:border-zinc-800 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Book className="w-32 h-32" />
            </div>
            <div className="relative z-10">
              <h1 className="text-4xl font-bold tracking-tight mb-2 text-gray-900 dark:text-white capitalize">
                {verb.definition}
              </h1>
              <div className="flex flex-wrap items-center gap-3 mt-4">
                <span className="px-3 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-medium font-mono">
                  {verb.class_name}
                </span>

                <ConfigFlags config={verb.config} />

                {corpusEntries.length > 0 && (
                  <span className="px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 font-medium text-sm">
                    {corpusEntries.length} Corpus Forms Found
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-zinc-800 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-gray-500" />
              <h2 className="font-semibold">Construction Roots</h2>
            </div>
            <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="p-4 rounded-lg bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-zinc-700/50">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                  H-Grade Root
                </div>
                <div className="text-xl font-mono text-indigo-600 dark:text-indigo-400">
                  {verb.h_grade_root}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-zinc-700/50">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                  Glottal Grade Root
                </div>
                <div className="text-xl font-mono text-purple-600 dark:text-purple-400">
                  {verb.glottal_grade_root}
                </div>
              </div>
            </div>
          </div>

          {/* Class Endings */}
          {endings && (
            <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-zinc-800 flex items-center gap-2">
                <Table className="w-5 h-5 text-gray-500" />
                <h2 className="font-semibold">
                  Class Endings ({verb.class_name})
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-zinc-800/50">
                    <tr>
                      <th className="px-6 py-3">Stem Final</th>
                      <th className="px-6 py-3">Present</th>
                      <th className="px-6 py-3">Imperfective</th>
                      <th className="px-6 py-3">Perfective</th>
                      <th className="px-6 py-3">Imperative</th>
                      <th className="px-6 py-3">Infinitive</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-zinc-800 font-mono">
                    <tr>
                      <td className="px-6 py-4">
                        {endings["stem final"] || "-"}
                      </td>
                      <td className="px-6 py-4">{endings.present}</td>
                      <td className="px-6 py-4">{endings.imperfective}</td>
                      <td className="px-6 py-4 text-emerald-600 font-medium">
                        {endings.perfective}
                      </td>
                      <td className="px-6 py-4">{endings.imperative}</td>
                      <td className="px-6 py-4 text-purple-600 font-medium">
                        {endings.infinitive}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Corpus Forms */}
          {corpusEntries.length > 0 && (
            <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-zinc-800 flex items-center gap-2">
                <Database className="w-5 h-5 text-gray-500" />
                <h2 className="font-semibold">
                  Corpus Forms (Dictionary Data)
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-zinc-800/50">
                    <tr>
                      <th className="px-6 py-3">Entry No.</th>
                      <th className="px-6 py-3">Syllabary</th>
                      <th className="px-6 py-3">Practical</th>
                      <th className="px-6 py-3">Part of Speech</th>
                      <th className="px-6 py-3">Translation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                    {corpusEntries.map((entry) => (
                      <tr
                        key={entry["Entry No."]}
                        className="hover:bg-gray-50 dark:hover:bg-zinc-800/50"
                      >
                        <td className="px-6 py-4 font-mono text-xs">
                          {entry["Entry No."]}
                        </td>
                        <td className="px-6 py-4 font-serif text-lg">
                          {entry["Syllabary"]}
                        </td>
                        <td className="px-6 py-4 font-medium">
                          {entry["Practical"]}
                        </td>
                        <td className="px-6 py-4 text-gray-500">
                          {entry["Part of speech"]}
                        </td>
                        <td className="px-6 py-4 text-gray-600 dark:text-gray-300">
                          {entry["Translation 1A"]}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: Related Verbs */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <Share2 className="w-5 h-5 text-indigo-500" />
              <h2 className="font-semibold">Related Verbs</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              Verbs sharing the same root ({verb.h_grade_root} /{" "}
              {verb.glottal_grade_root}), but with different classes.
            </p>

            {relatedVerbs.length > 0 ? (
              <div className="space-y-3">
                {relatedVerbs.map((v) => (
                  <Link
                    key={v.index}
                    href={`/reconstructable-verbs/${v.index}`}
                    className="block p-3 rounded-lg border border-gray-100 dark:border-zinc-800 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-indigo-50 dark:hover:bg-indigo-900/10 transition-all group"
                  >
                    <div className="font-medium text-sm text-gray-900 dark:text-gray-200 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 flex justify-between items-start">
                      <span>{v.definition}</span>
                      <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="mt-1 flex items-center justify-between gap-2">
                      <div className="text-xs text-gray-500 font-mono">
                        {v.class_name}
                      </div>
                      <ConfigFlags config={v.config} />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-gray-50 dark:bg-zinc-800/50 rounded-lg text-sm text-gray-500 text-center italic">
                No other verbs share this exact root combination.
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-indigo-500" />
              <h2 className="font-semibold">Reconstruction Config</h2>
            </div>

            <div className="space-y-4">
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                  Active Prefixes
                </div>
                <ConfigFlags
                  config={verb.config}
                  className="scale-110 origin-left ml-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-2 rounded bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-zinc-700/50">
                  <div className="text-[10px] text-gray-500 uppercase">
                    Stem Type
                  </div>
                  <div className="text-sm font-mono">
                    {verb.config.pron.stem_type}
                  </div>
                </div>
                <div className="p-2 rounded bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-zinc-700/50">
                  <div className="text-[10px] text-gray-500 uppercase">
                    Metathesis
                  </div>
                  <div className="text-sm font-mono">
                    {verb.config.pron.metathesis_strategy}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-100 dark:border-zinc-800">
              <h3 className="font-bold text-sm mb-2">Raw JSON Data</h3>
              <pre className="text-[10px] font-mono bg-zinc-950 p-3 rounded overflow-x-auto text-zinc-400">
                {JSON.stringify(verb.config, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
