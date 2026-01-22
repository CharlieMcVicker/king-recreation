import fs from "fs";
import path from "path";
import Papa from "papaparse";
import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  RootGroup,
  normalize,
  resolveClassEndings,
} from "./data-shared";

// Re-export shared types/functions if needed by other server components
export * from "./data-shared";

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

export async function getRoots(): Promise<RootGroup[]> {
  const verbs = await getReconstructableVerbs();

  // 1. Group by h_grade_root -> glottal_grade_root
  const hGroups: Map<
    string,
    Map<string | null, (ReconstructableVerb & { id: number })[]>
  > = new Map();

  verbs.forEach((verb, idx) => {
    if (!hGroups.has(verb.h_grade_root)) {
      hGroups.set(verb.h_grade_root, new Map());
    }
    const gMap = hGroups.get(verb.h_grade_root)!;
    if (!gMap.has(verb.glottal_grade_root)) {
      gMap.set(verb.glottal_grade_root, []);
    }
    gMap.get(verb.glottal_grade_root)!.push({ ...verb, id: idx });
  });

  const finalGroups: RootGroup[] = [];

  // 2. Apply merging logic: if exactly 2 glottal grades and one is null, merge null into the other
  for (const [h_grade_root, gMap] of hGroups.entries()) {
    const glottalGrades = Array.from(gMap.keys());
    const nullKey = glottalGrades.find((g) => g === null || g === "");

    if (nullKey !== undefined && glottalGrades.length === 2) {
      const attestedKey = glottalGrades.find((g) => g !== nullKey)!;
      const mergedVerbs = [...gMap.get(attestedKey)!, ...gMap.get(nullKey)!];

      const key = `${h_grade_root}|${attestedKey}`;
      finalGroups.push({
        h_grade_root,
        glottal_grade_root: attestedKey,
        slug: Buffer.from(key).toString("base64url"),
        verbs: mergedVerbs,
      });
    } else {
      // 3. Keep as separate groups
      for (const [glottal_grade_root, verbs] of gMap.entries()) {
        const key = `${h_grade_root}|${glottal_grade_root}`;
        finalGroups.push({
          h_grade_root,
          glottal_grade_root,
          slug: Buffer.from(key).toString("base64url"),
          verbs,
        });
      }
    }
  }

  return finalGroups.sort((a, b) =>
    a.h_grade_root.localeCompare(b.h_grade_root)
  );
}

export async function getRootBySlug(slug: string): Promise<RootGroup | null> {
  const roots = await getRoots();
  return roots.find((r) => r.slug === slug) || null;
}

export async function getClasses(): Promise<ClassDefinition[]> {
  const filePath = path.join(DATA_DIR, "classes.csv");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse<ClassDefinition>(fileContent, {
    header: true,
    skipEmptyLines: true,
  });

  // Post-process to generate macro names
  return result.data.map((row) => {
    const macroName = row.subclass ? `${row.class}-${row.subclass}` : row.class;
    return { ...row, macro_name: macroName };
  });
}

// [NEW] Helper to get a lookup map for classes
export async function getClassLookup(): Promise<Map<string, ClassDefinition>> {
  const classes = await getClasses();
  const map = new Map<string, ClassDefinition>();
  classes.forEach((c) => {
    if (c.macro_name) {
      map.set(c.macro_name, c);
    }
  });
  return map;
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

function findCorpusEntries(definition: string, dictionary: DictionaryEntry[]) {
  // 1. Find the entry that matches definition
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
