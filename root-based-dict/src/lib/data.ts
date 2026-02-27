import fs from "fs";
import path from "path";
import Papa from "papaparse";
import {
  ReconstructableVerb,
  ClassDefinition,
  DictionaryEntry,
  RootGroup,
  EndingGroup,
  DerivationalConnection,
  normalize,
  resolveClassEndings,
} from "./data-shared";

// Re-export shared types/functions if needed by other server components
export * from "./data-shared";

const DATA_DIR = path.join(process.cwd(), "../data");
const ARTIFACTS_DATA_DIR = path.join(process.cwd(), "../artifacts/data");
const CONNECTIONS_DATA_DIR = path.join(process.cwd(), "../curated");
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

export async function getChangedVerbIds(): Promise<number[]> {
  const dataPath = path.join(DATA_DIR, "verb_selection_snapshot.json");
  const reportsPath = path.join(REPORTS_DIR, "verb_selection_snapshot.json");

  if (!fs.existsSync(dataPath) || !fs.existsSync(reportsPath)) return [];

  const data1 = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
  const data2 = JSON.parse(fs.readFileSync(reportsPath, "utf-8"));

  const diffIds: number[] = [];
  const map1 = new Map<number, any>(
    data1.map((item: any) => [item.corpus_id, item]),
  );

  for (const item2 of data2) {
    const item1 = map1.get(item2.corpus_id);
    if (!item1) {
      diffIds.push(item2.corpus_id);
      continue;
    }

    const str1 = JSON.stringify(item1.options);
    const str2 = JSON.stringify(item2.options);

    if (str1 !== str2) {
      diffIds.push(item2.corpus_id);
    }
  }

  // Check for items in map1 that are not in data2
  const ids2 = new Set(data2.map((i: any) => i.corpus_id));
  for (const [id, _] of map1) {
    if (!ids2.has(id) && !diffIds.includes(id)) {
      diffIds.push(id);
    }
  }

  return diffIds;
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

let corpusCache: any[] | null = null;

export async function getCorpus(): Promise<any[]> {
  if (corpusCache) return corpusCache;

  let filePath = path.join(ARTIFACTS_DATA_DIR, "corpus.csv");
  if (!fs.existsSync(filePath)) {
    filePath = path.join(process.cwd(), "../artifacts/corpora/corpus.csv");
  }
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  corpusCache = result.data;
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

export async function getConnections(): Promise<DerivationalConnection[]> {
  const filePath = path.join(
    CONNECTIONS_DATA_DIR,
    "derivational_suffix_connections.csv",
  );
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
  });
  return result.data as DerivationalConnection[];
}

export async function getRoots(): Promise<RootGroup[]> {
  const filePath = path.join(ARTIFACTS_DATA_DIR, "hierarchical-dict.json");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const rawRoots: any[] = JSON.parse(fileContent);

  let verbIndex = 0;

  const processRoot = (root: any): RootGroup => {
    // Ensure verbs have IDs
    const addIds = (
      verbs: ReconstructableVerb[],
    ): (ReconstructableVerb & { id: number })[] => {
      if (!verbs) return [];
      return verbs.map((v) => {
        const vWithId = {
          ...v,
          id: v.corpus_id ?? verbIndex,
          derivations: v.derivations
            ? (addIds(v.derivations) as any[])
            : undefined,
        };
        verbIndex++;
        return vWithId;
      });
    };

    const classes = root.classes.map((cls: any) => ({
      ...cls,
      verbs: addIds(cls.verbs),
    }));

    return {
      ...root,
      // Use slug from JSON
      slug: root.slug,
      classes,
    };
  };

  return rawRoots.map(processRoot);
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

export interface MorphemeGroup {
  name: string;
  slug: string;
  subcases: {
    subcase: string;
    roots: RootGroup[];
  }[];
  total_roots: number;
}

export async function getMorphemeGroups(): Promise<MorphemeGroup[]> {
  const roots = await getRoots();
  const groupsMap: Map<string, Map<string, RootGroup[]>> = new Map();

  // Helper to extract morpheme info from "name[subcase]" format
  const parseMorpheme = (tag: string) => {
    const match = tag.match(/^([^\[]+)(?:\[(.*)\])?$/);
    if (!match) return { name: tag, subcase: "default" };
    return { name: match[1], subcase: match[2] || "default" };
  };

  roots.forEach((root) => {
    // 1. Group verbs by morpheme for this specific root
    // Key: "name|subcase" -> Map<ClassName, Verbs[]>
    const morphemeVerbs = new Map<
      string,
      Map<string, (typeof root.classes)[0]["verbs"]>
    >();

    root.classes.forEach((cls) => {
      cls.verbs.forEach((verb) => {
        if (verb.post_root_morpheme) {
          const { name, subcase } = parseMorpheme(verb.post_root_morpheme);
          const key = `${name}|${subcase}`;

          if (!morphemeVerbs.has(key)) {
            morphemeVerbs.set(key, new Map()); // ClassName -> Verbs
          }
          const classMap = morphemeVerbs.get(key)!;

          if (!classMap.has(cls.class_name)) {
            classMap.set(cls.class_name, []);
          }
          classMap.get(cls.class_name)!.push(verb);
        }
      });
    });

    // 2. Distribute to the global groups map
    morphemeVerbs.forEach((classMap, key) => {
      const [name, subcase] = key.split("|");

      if (!groupsMap.has(name)) {
        groupsMap.set(name, new Map());
      }

      const subcaseMap = groupsMap.get(name)!;
      if (!subcaseMap.has(subcase)) {
        subcaseMap.set(subcase, []);
      }

      // Construct a "Filtered Root" that only contains the relevant verbs
      // We verify the root effectively "has" these classes
      const filteredClasses = Array.from(classMap.entries()).map(
        ([className, verbs]) => ({
          class_name: className,
          verbs: verbs,
        }),
      );

      const filteredRoot: RootGroup = {
        ...root,
        classes: filteredClasses,
      };

      subcaseMap.get(subcase)!.push(filteredRoot);
    });
  });

  return Array.from(groupsMap.entries())
    .map(([name, subcaseMap]) => {
      const subcases = Array.from(subcaseMap.entries()).map(
        ([subcase, roots]) => ({
          subcase,
          roots,
        }),
      );
      const total_roots = subcases.reduce((acc, s) => acc + s.roots.length, 0);
      return {
        name,
        slug: Buffer.from(name).toString("base64url"),
        subcases,
        total_roots,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

export async function getMorphemeGroupBySlug(
  slug: string,
): Promise<MorphemeGroup | null> {
  const groups = await getMorphemeGroups();
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

export async function getValidatedRootsRows(): Promise<any[]> {
  const filePath = path.join(
    process.cwd(),
    "../curated/validated_reconstructable_roots.csv",
  );
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function updateUserSelection(
  corpusId: number,
  rowIndex: number,
): Promise<void> {
  const filePath = path.join(
    process.cwd(),
    "../curated/validated_reconstructable_roots.csv",
  );
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const parsed = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });

  const rows = parsed.data as any[];

  // Find all indices for this corpus_id
  const indices: number[] = [];
  rows.forEach((row, idx) => {
    if (row.corpus_id === corpusId) {
      indices.push(idx);
    }
  });

  if (rowIndex < 0 || rowIndex >= indices.length) {
    throw new Error(
      `Invalid rowIndex ${rowIndex} for corpusId ${corpusId}. Found ${indices.length} rows.`,
    );
  }

  // Clear existing selection for this corpus_id
  indices.forEach((idx) => {
    rows[idx].user_selected = "";
  });

  // Set new selection
  const targetGlobalIndex = indices[rowIndex];
  rows[targetGlobalIndex].user_selected = "x";

  // Write back
  const csv = Papa.unparse(rows, {
    quotes: false, // Default is false, but complex fields will be quoted automatically
    quoteChar: '"',
    escapeChar: '"',
    delimiter: ",",
    header: true,
    newline: "\n",
    skipEmptyLines: false, // Don't skip empty lines
    columns: undefined, // Use all columns
  });

  fs.writeFileSync(filePath, csv);
}
export async function getRootIdsRows(): Promise<any[]> {
  const filePath = path.join(process.cwd(), "../curated/root_ids.csv");
  if (!fs.existsSync(filePath)) return [];
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });
  return result.data;
}

export async function updateRootId(
  corpusId: number,
  rootId: string,
): Promise<void> {
  const filePath = path.join(process.cwd(), "../curated/root_ids.csv");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const parsed = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });

  const rows = parsed.data as any[];
  const rowIndex = rows.findIndex((row) => row.corpus_id === corpusId);

  if (rowIndex === -1) {
    throw new Error(`Corpus ID ${corpusId} not found in root_ids.csv`);
  }

  rows[rowIndex].root_id = rootId;
  rows[rowIndex].user_edited = "x";

  const csv = Papa.unparse(rows, {
    quotes: false,
    quoteChar: '"',
    escapeChar: '"',
    delimiter: ",",
    header: true,
    newline: "\n",
    skipEmptyLines: false,
  });

  fs.writeFileSync(filePath, csv);
}
export async function updateRootIdsBulk(
  updates: { corpusId: number; rootId: string }[],
): Promise<void> {
  const filePath = path.join(process.cwd(), "../curated/root_ids.csv");
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const parsed = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });

  const rows = parsed.data as any[];
  const updateMap = new Map<number, string>(
    updates.map((u) => [u.corpusId, u.rootId]),
  );

  rows.forEach((row) => {
    if (updateMap.has(row.corpus_id)) {
      row.root_id = updateMap.get(row.corpus_id);
      row.user_edited = "x";
    }
  });

  const csv = Papa.unparse(rows, {
    quotes: false,
    quoteChar: '"',
    escapeChar: '"',
    delimiter: ",",
    header: true,
    newline: "\n",
    skipEmptyLines: false,
  });

  fs.writeFileSync(filePath, csv);
}

export async function getDefinitions(
  corpusIds: string | number | null | undefined,
): Promise<{ id: number; definition: string }[]> {
  const ids = String(corpusIds || "")
    .split(";")
    .map((id) => parseInt(id.trim(), 10))
    .filter((id) => !isNaN(id));
  const corpus = await getCorpus();
  const corpusMap = new Map<number, string>(
    corpus.map((c: any) => [c.corpus_id, c.definition]),
  );

  return ids.map((id) => ({
    id,
    definition: corpusMap.get(id) || "No definition found",
  }));
}

export async function updateDerivationalConnection(
  key: {
    from_root_id: string;
    from_h_grade: string;
    from_g_grade: string;
    from_class: string;
    to_root_id: string;
    to_h_grade: string;
    to_g_grade: string;
    to_class: string;
  },
  approved: boolean,
): Promise<void> {
  const filePath = path.join(
    CONNECTIONS_DATA_DIR,
    "derivational_suffix_connections.csv",
  );
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const parsed = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
  });

  const rows = parsed.data as any[];
  const rowIndex = rows.findIndex(
    (row) =>
      row.from_root_id === key.from_root_id &&
      row.from_h_grade === key.from_h_grade &&
      row.from_g_grade === key.from_g_grade &&
      row.from_class === key.from_class &&
      row.to_root_id === key.to_root_id &&
      row.to_h_grade === key.to_h_grade &&
      row.to_g_grade === key.to_g_grade &&
      row.to_class === key.to_class,
  );

  if (rowIndex === -1) {
    throw new Error(
      `Connection not found in derivational_suffix_connections.csv`,
    );
  }

  rows[rowIndex].user_approved = approved ? "x" : "";

  const csv = Papa.unparse(rows, {
    quotes: false,
    quoteChar: '"',
    escapeChar: '"',
    delimiter: ",",
    header: true,
    newline: "\n",
    skipEmptyLines: false,
  });

  fs.writeFileSync(filePath, csv);
}
