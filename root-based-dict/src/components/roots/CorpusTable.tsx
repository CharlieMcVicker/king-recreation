"use client";

import {
  ReconstructableVerb,
  DictionaryEntry,
  getPronominalSetName,
  getCorpusForm,
} from "@/lib/data-shared";

const TAG_MAP: Record<string, string> = {
  perfective: "perf",
  infinitive: "inf",
  imperative: "imp",
  present: "pres",
  imperfective: "impf",
};

interface CorpusTableProps {
  verb: ReconstructableVerb;
  dictionary: DictionaryEntry[];
}

export default function CorpusTable({ verb, dictionary }: CorpusTableProps) {
  const forms = [
    {
      label: "Present-1sg",
      key: "present_1sg",
      stem: verb.original_stems.present,
    },
    { label: "Present", key: "present", stem: verb.original_stems.present },
    {
      label: "Infinitive",
      key: "infinitive",
      stem: verb.original_stems.infinitive,
    },
    {
      label: "Imperative",
      key: "imperative",
      stem: verb.original_stems.imperative,
    },
    {
      label: "Imperfective",
      key: "imperfective",
      stem: verb.original_stems.imperfective,
    },
    {
      label: "Perfective",
      key: "perfective",
      stem: verb.original_stems.perfective,
    },
  ];

  const getCorpusLabel = (key: string) => {
    return getCorpusForm(dictionary, verb.entry_no, key);
  };

  const getPronounColor = (setName: string | null) => {
    if (!setName) return "text-gray-900 dark:text-gray-100";
    if (setName.includes("Set A")) return "text-red-600 dark:text-red-400";
    if (setName.includes("Set B")) return "text-blue-600 dark:text-blue-400";
    if (setName.includes("to 3rd"))
      return "text-purple-600 dark:text-purple-400";
    return "text-gray-900 dark:text-gray-100";
  };

  const getVariantTag = (key: string) => {
    // Parse variant from class_name like "go[perf2-inf2]"
    const match = verb.class_name.match(/\[(.*)\]/);
    if (!match) return null;
    const mods = match[1].split("-");

    const prefix = TAG_MAP[key];
    if (!prefix) return null;

    const mod = mods.find((m) => m.startsWith(prefix));
    return mod || null;
  };
  return (
    <div className="overflow-hidden border border-gray-200 dark:border-zinc-800 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
        <thead className="bg-gray-50 dark:bg-zinc-900/50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 dark:border-zinc-800">
              {forms[0].label}
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 dark:border-zinc-800">
              {forms[1].label}
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {forms[2].label}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
          <tr className="divide-x divide-gray-200 dark:divide-zinc-800">
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("present_1sg", verb.config.pron)
                  )}`}
                >
                  {getCorpusLabel("present_1sg") || "-"}
                </span>
                {getVariantTag("present_1sg") && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {getVariantTag("present_1sg")}
                  </span>
                )}
              </div>
            </td>
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("present", verb.config.pron)
                  )}`}
                >
                  {getCorpusLabel("present") || "-"}
                </span>
                {getVariantTag("present") && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {getVariantTag("present")}
                  </span>
                )}
              </div>
            </td>
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("infinitive", verb.config.pron)
                  )}`}
                >
                  {getCorpusLabel("infinitive") || "-"}
                </span>
                {getVariantTag("infinitive") && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {getVariantTag("infinitive")}
                  </span>
                )}
              </div>
            </td>
          </tr>
          <tr>
            <th className="bg-gray-50 dark:bg-zinc-900/50 px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 dark:border-zinc-800">
              {forms[3].label}
            </th>
            <th className="bg-gray-50 dark:bg-zinc-900/50 px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 dark:border-zinc-800">
              {forms[4].label}
            </th>
            <th className="bg-gray-50 dark:bg-zinc-900/50 px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {forms[5].label}
            </th>
          </tr>
          <tr className="divide-x divide-gray-200 dark:divide-zinc-800">
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("imperative", verb.config.pron)
                  )}`}
                >
                  {getCorpusLabel("imperative") || "-"}
                </span>
                {getVariantTag("imperative") && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {getVariantTag("imperative")}
                  </span>
                )}
              </div>
            </td>
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("imperfective", verb.config.pron)
                  )}`}
                >
                  {getCorpusLabel("imperfective") || "-"}
                </span>
                {getVariantTag("imperfective") && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {getVariantTag("imperfective")}
                  </span>
                )}
              </div>
            </td>
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("perfective", verb.config.pron)
                  )}`}
                >
                  {getCorpusLabel("perfective") || "-"}
                </span>
                {getVariantTag("perfective") && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {getVariantTag("perfective")}
                  </span>
                )}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
