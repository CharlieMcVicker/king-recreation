import fs from "fs";
import path from "path";
import Papa from "papaparse";

// Define types based on the JSON and CSV structures

export interface ReconstructableVerb {
  definition: string;
  h_grade_root: string;
  glottal_grade_root: string | null;
  class_name: string;
  corpus_id: number | null;
  config: {
    pre: {
      translocutive: boolean;
      partitive: boolean;
      distributive: boolean;
    };
    pron: {
      set_type: string;
      stem_type: string;
      metathesis_strategy: string;
      use_ka_variant: boolean;
      use_uwa_for_3rd_set_b: boolean;
      use_aki_for_1st_set_b: boolean;
      use_3rd_person_object: boolean;
    };
  };
  original_stems: {
    present: string;
    imperfective: string;
    perfective: string;
    imperative: string;
    infinitive: string;
  };
}

export interface ClassDefinition {
  class: string;
  "stem final": string;
  present: string;
  imperfective: string;
  perfective: string;
  imperative: string;
  infinitive: string;
  [key: string]: any; // Allow indexing
}

export interface DictionaryEntry {
  "Entry No.": string;
  Headword: string;
  "No.": string;
  Syllabary: string;
  Practical: string;
  "Part of speech": string;
  "Translation 1A": string;
  "Translation 1B": string;
  "Translation 1C": string;
  "Translation 1D": string;
  // Add other fields as needed, these are the most critical
}

const DATA_DIR = path.join(process.cwd(), "../data");
const ARTIFACTS_DATA_DIR = path.join(process.cwd(), "../artifacts/data");
const REPORTS_DIR = path.join(process.cwd(), "../artifacts/reports");

export async function getVerbCoverage(): Promise<any> {
  const filePath = path.join(REPORTS_DIR, "verb_coverage.json");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(fileContent);
}

export async function getMatchCounts(): Promise<any[]> {
  const filePath = path.join(REPORTS_DIR, "class_match_counts.csv");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getStemDerivationFailures(): Promise<any[]> {
  const filePath = path.join(REPORTS_DIR, "stem_derivation_failures.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getReconstructionFailures(): Promise<any[]> {
  const filePath = path.join(REPORTS_DIR, "reconstruction_failures.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getMatches(): Promise<any[]> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "matches_validated.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getInitialMatches(): Promise<any[]> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "matches_initial.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getNearMisses(): Promise<any[]> {
  const filePath = path.join(REPORTS_DIR, "class_near_misses.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getCorpus(): Promise<any[]> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "corpus.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getConsistencyAnalysis(): Promise<any[]> {
  const filePath = path.join(REPORTS_DIR, "consistency_analysis.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function getReconstructableVerbs(): Promise<
  ReconstructableVerb[]
> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "reconstructable_verbs.json");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(fileContent);
}

export async function getClasses(): Promise<ClassDefinition[]> {
  const filePath = path.join(DATA_DIR, "classes.csv");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse<ClassDefinition>(fileContent, {
    header: true,
    skipEmptyLines: true,
  });
  return result.data;
}

export async function getDictionaryEntries(): Promise<DictionaryEntry[]> {
  const filePath = path.join(DATA_DIR, "cherokee_nation_dictionary.csv");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse<DictionaryEntry>(fileContent, {
    header: true,
    skipEmptyLines: true,
  });
  return result.data;
}

export async function getVerbDetails(index: number) {
  const verbs = await getReconstructableVerbs();
  const verb = verbs[index];
  if (!verb) return null;

  const classes = await getClasses();
  const dictionary = await getDictionaryEntries();

  // Parse class endings
  const endings = resolveClassEndings(verb.class_name, classes);

  // Find corpus forms
  const corpusEntries = findCorpusEntries(verb.definition, dictionary);

  // Find related verbs (same root)
  const relatedVerbs = verbs
    .map((v, i) => ({ ...v, index: i }))
    .filter(
      (v) =>
        v.index !== index &&
        (v.h_grade_root === verb.h_grade_root ||
          (v.h_grade_root === null && verb.h_grade_root === null))
    );

  return {
    verb,
    endings,
    corpusEntries,
    relatedVerbs,
    index,
  };
}

export async function readCsv(dir: string, filename: string): Promise<any[]> {
  const filePath = path.join(dir, filename);
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

function normalize(s: string) {
  if (!s) return "";
  return s.trim().toLowerCase().replace(/['’]/g, "'");
}

export function resolveClassEndings(
  classNameFull: string,
  classes: ClassDefinition[]
) {
  // Parse "go[perf2-inf2]" -> base: "go", modifiers: { perfective: 2, infinitive: 2 }
  const match = classNameFull.match(/^([^\[]+)(?:\[(.*)\])?$/);
  if (!match) return null;

  const baseClassName = match[1];
  const modifiersStr = match[2];

  const classDef = classes.find((c) => c.class === baseClassName);
  if (!classDef) return null;

  const result: Record<string, string> = { ...classDef };

  // Default selection (1st option) if not specified
  // The CSV fields like 'perfective' contain "opt1;opt2"
  // We need to resolve the specific option.

  const columns = [
    "present",
    "imperfective",
    "perfective",
    "imperative",
    "infinitive",
  ];

  // Map of modifier code to column index (1-based index of option)
  const overrides: Record<string, number> = {};

  if (modifiersStr) {
    // modifiers like "perf2-inf2"
    const mods = modifiersStr.split("-");
    mods.forEach((mod) => {
      if (mod.startsWith("perf"))
        overrides["perfective"] = parseInt(mod.replace("perf", ""), 10);
      if (mod.startsWith("inf"))
        overrides["infinitive"] = parseInt(mod.replace("inf", ""), 10);
      if (mod.startsWith("imp"))
        overrides["imperative"] = parseInt(mod.replace("imp", ""), 10);
      // Add others if they exist (pres/impf usually don't have alts but could)
    });
  }

  columns.forEach((col) => {
    const options = (classDef[col as keyof ClassDefinition] || "").split(";");
    const index = (overrides[col] || 1) - 1; // 0-based
    // Handle the asterisk or other simplified markers if present?
    // CSV has things like ";*". "sv;invs;es".
    // Let's just pick the option at index.
    if (index >= 0 && index < options.length) {
      result[col] = options[index];
    } else {
      result[col] = options[0]; // Fallback
    }
  });

  return result;
}

function findCorpusEntries(definition: string, dictionary: DictionaryEntry[]) {
  // 1. Find the entry that matches definition
  // Trying exact match on Translation 1A/B...
  // Clean definition (trim, lowercase?)

  const target = normalize(definition);

  const matchingEntry = dictionary.find((entry) => {
    // Check logical columns
    const translations = [
      entry["Translation 1A"],
      entry["Translation 1B"],
      entry["Translation 1C"],
      entry["Translation 1D"],
    ];
    return translations.some((t) => normalize(t) === target);
  });

  if (!matchingEntry) return [];

  const groupNo = matchingEntry["No."];
  if (!groupNo) return [matchingEntry];

  // 2. Return all entries with same 'No.'
  return dictionary.filter((e) => e["No."] === groupNo);
}
