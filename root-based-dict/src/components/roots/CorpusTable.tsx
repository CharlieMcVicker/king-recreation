"use client";

import {
  ReconstructableVerb,
  DictionaryEntry,
  getPronominalSetName,
  getCorpusForm,
  Prediction,
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
  const isStative = verb.meta.prediction === Prediction.FullStative;
  const forms = [
    {
      label: "Present-1sg",
      key: "present_1sg",
    },
    { label: "Present", key: "present" },
    {
      label: "Infinitive",
      key: "infinitive",
    },
    {
      label: "Imperative",
      key: "imperative",
    },
    {
      label: "Imperfective",
      key: "imperfective",
    },
    {
      label: "Perfective",
      key: "perfective",
    },
  ];

  const getCorpusLabel = (key: string) => {
    const entryNo = verb.meta.entry_no;
    const parsed = entryNo !== null && entryNo !== undefined ? Number(entryNo) : undefined;
    return getCorpusForm(dictionary, parsed && !isNaN(parsed) ? parsed : undefined, key);
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
    // If key is infinitive and we have a shim, read from the shim
    const targetVerb = key === "infinitive" && verb.shim ? verb.shim : verb;
    const match = targetVerb.morphology.class_name.match(/\[(.*)\]/);
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
            <th className={`px-3 py-2 text-left text-xs font-medium uppercase tracking-wider border-l border-gray-200 dark:border-zinc-800 ${isStative && !verb.shim ? "text-gray-400/80 bg-gray-50/50 dark:bg-zinc-900/30" : "text-gray-500"}`}>
              {forms[2].label} {isStative && !verb.shim && "(N/A)"}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
          <tr className="divide-x divide-gray-200 dark:divide-zinc-800">
            <td className="px-3 py-4 whitespace-nowrap">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${getPronounColor(
                    getPronominalSetName("present_1sg", verb.morphology.config.pron),
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
                    getPronominalSetName("present", verb.morphology.config.pron),
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
            <td className={`px-3 py-4 whitespace-nowrap ${isStative && !verb.shim ? "bg-gray-50/30 dark:bg-zinc-950/20" : ""}`}>
              <div className="flex flex-col">
                {isStative && !verb.shim ? (
                  <span className="text-zinc-400 dark:text-zinc-600 text-xs font-medium italic">
                    ∅ (Stative)
                  </span>
                ) : (
                  <>
                    <span
                      className={`text-sm font-medium ${getPronounColor(
                        getPronominalSetName(
                          "infinitive",
                          verb.shim
                            ? verb.shim.morphology.config.pron
                            : verb.morphology.config.pron,
                        ),
                      )}`}
                    >
                      {getCorpusLabel("infinitive") || "-"}
                    </span>
                    {getVariantTag("infinitive") && (
                      <span className="text-[10px] text-gray-400 uppercase">
                        {getVariantTag("infinitive")}
                      </span>
                    )}
                  </>
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
                    getPronominalSetName("imperative", verb.morphology.config.pron),
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
                    getPronominalSetName("imperfective", verb.morphology.config.pron),
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
                    getPronominalSetName("perfective", verb.morphology.config.pron),
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
