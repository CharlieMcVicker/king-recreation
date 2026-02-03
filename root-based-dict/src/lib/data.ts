import fs from "fs";
import path from "path";
import Papa from "papaparse";
import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  RootGroup,
  EndingGroup,
  RootConnection,
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

export async function getConnections(): Promise<RootConnection[]> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "root_connections.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data as any[];
}

export async function getRoots(): Promise<RootGroup[]> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "hierarchical-dict.json");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const roots: RootGroup[] = JSON.parse(fileContent);

  // Post-process to add slugs and ensure verb IDs if missing
  let verbIndex = 0;
  return roots.map((root) => {
    // Generate slug from key
    // Distinguish null (unattested/none) from empty string (actually empty or merged)
    const gGrade =
      root.glottal_grade_root === null ? "__null__" : root.glottal_grade_root;
    const key = `${root.h_grade_root}|${gGrade}`;
    const slug = Buffer.from(key).toString("base64url");

    // Ensure verbs have IDs (using global index for uniqueness across the app if needed,
    // though previously it was index in the flat list)
    const addIds = (
      verbs: ReconstructableVerb[],
    ): (ReconstructableVerb & { id: number })[] => {
      return verbs.map((v) => {
        const vWithId = {
          ...v,
          id: v.corpus_id ?? verbIndex,
          derivations: v.derivations
            ? (addIds(v.derivations) as any[])
            : undefined,
          middle_voice: v.middle_voice
            ? (addIds(v.middle_voice) as any[])
            : undefined,
        };
        verbIndex++;
        return vWithId;
      });
    };

    const classes = root.classes.map((cls) => ({
      ...cls,
      verbs: addIds(cls.verbs),
    }));

    return {
      ...root,
      slug,
      classes,
    };
  });
}

export async function getRootBySlug(slug: string): Promise<RootGroup | null> {
  const roots = await getRoots();
  return roots.find((r) => r.slug === slug) || null;
}

export async function getEndingGroups(): Promise<EndingGroup[]> {
  const classes = await getClasses();
  const roots = await getRoots();

  const groups: Map<string, EndingGroup> = new Map();

  for (const root of roots) {
    for (const cls of root.classes) {
      const endings = resolveClassEndings(cls.class_name, classes);
      if (!endings) continue;

      const endingKeys = [
        "present",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
      ];
      const endingValues = endingKeys.map((k) => endings[k]);
      const groupKey = endingValues.join("|");

      if (!groups.has(groupKey)) {
        const slug = Buffer.from(groupKey).toString("base64url");
        const endingsMap: Record<string, string> = {};
        endingKeys.forEach((k, i) => {
          endingsMap[k] = endingValues[i];
        });

        groups.set(groupKey, {
          endings: endingsMap,
          slug,
          roots: [],
        });
      }

      const group = groups.get(groupKey)!;

      // Find or create root in this group
      let groupRoot = group.roots.find(
        (r) =>
          r.h_grade_root === root.h_grade_root &&
          r.glottal_grade_root === root.glottal_grade_root,
      );

      if (!groupRoot) {
        groupRoot = {
          h_grade_root: root.h_grade_root,
          glottal_grade_root: root.glottal_grade_root,
          root_slug: root.slug,
          configs: [],
        };
        group.roots.push(groupRoot);
      }

      // Add this class config
      groupRoot.configs.push({
        class_name: cls.class_name,
        verbs: cls.verbs,
      });
    }
  }

  return Array.from(groups.values()).sort((a, b) => {
    return a.endings.present.localeCompare(b.endings.present);
  });
}

export async function getEndingGroupBySlug(
  slug: string,
): Promise<EndingGroup | null> {
  const groups = await getEndingGroups();
  return groups.find((g) => g.slug === slug) || null;
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
          (v.h_grade_root === null && verb.h_grade_root === null)),
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
