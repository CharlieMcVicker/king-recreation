export interface PrePronominalConfig {
  translocutive: boolean;
  translocutiveImpOnly: boolean;
  partitive: boolean;
  distributive: boolean;
}

export interface PronominalConfig {
  set_type: string;
  stem_type: string;
  allow_h_metathesis: boolean;
  middle_voice: string;
  middle_voice_h_metathesis: boolean;
  plural_pronouns: boolean;
  use_ka_variant: boolean;
  use_aki_for_1st_set_b: boolean;
  uwa_replaces_v: boolean;
  use_3rd_person_object: boolean;
}

export interface PrefixConfig {
  pre: PrePronominalConfig;
  pron: PronominalConfig;
  stative: boolean;
}

export interface MorphologicalVerb {
  h_grade_root: string;
  glottal_grade_root: string | null;
  post_root_morpheme: string | null;
  class_name: string;
  config: PrefixConfig;
}

export interface ReconstructableVerb {
  meta: VerbMeta;
  morphology: MorphologicalVerb;
  derivations?: ReconstructableVerb[];
  shim?: ReconstructableVerb;
  user_selected?: boolean;
  segmented_forms?: Record<string, string>;
}

export enum Prediction {
  FullEventful = "FullEventful",
  FullStative = "FullStative",
  InfEventful = "InfEventful",
}

export interface VerbMeta {
  corpus_id: number | string;
  definition: string;
  entry_no: number | string | null;
  prediction: Prediction;
}

export interface UserCurationInfo {
  user_selected: string | null;
  pipeline_selected: string | null;
}

export interface AspectInfo {
  verb_class: string;
  post_root_morpheme: string | null;
  stative: boolean;
}

export interface RootInfo {
  h_grade: string;
  g_grade: string | null;
}

export interface ValidatedRootRow {
  originalIndex: number;
  meta: VerbMeta;
  curation: UserCurationInfo;
  aspect: AspectInfo;
  roots: RootInfo;
  config: PrefixConfig;
  metathesis_involved: boolean;
  segmented_forms: string;
}

export interface ClassDefinition {
  class: string;
  subclass: string;
  macro_name?: string;
  "stem final": string;
  present: string;
  imperfective: string;
  perfective: string;
  imperative: string;
  infinitive: string;
  [key: string]: any;
}

export interface DictionaryEntry {
  "Entry No.": string;
  Headword: string;
  "No.": string;
  Syllabary: string;
  Practical: string;
  "Part of speech": string;
  "Grammar sub entry": string;
  "Grammar note": string;
  "Translation 1A": string;
  "Translation 1B": string;
  "Translation 1C": string;
  "Translation 1D": string;
}

export function getCorpusForm(
  entries: DictionaryEntry[],
  entryNo: number | undefined,
  formKey: string,
): string | null {
  if (!entryNo) return null;
  const group = entries.filter((e) => Number(e["No."]) === entryNo);
  if (group.length === 0) return null;

  const findBest = (predicate: (sub: string) => boolean) => {
    const matches = group.filter((e) =>
      predicate((e["Grammar sub entry"] || "").toLowerCase()),
    );
    if (matches.length === 0) return null;

    // Priority: animate > inanimate > generic
    const getPriority = (row: DictionaryEntry) => {
      const sub = (row["Grammar sub entry"] || "").toLowerCase();
      if (sub.includes("animate") && !sub.includes("inanimate")) return 3;
      if (sub.includes("animate")) return 2;
      if (sub.includes("inanimate")) return 1;
      return 0;
    };

    return matches.sort((a, b) => getPriority(b) - getPriority(a))[0].Practical;
  };

  switch (formKey) {
    case "present":
      return findBest(
        (s) =>
          s.startsWith("3rd person singular") &&
          !s.includes("habitual") &&
          !s.includes("past") &&
          !s.includes("infinitive"),
      );
    case "present_1sg":
      return findBest((s) => s.startsWith("1st person singular"));
    case "perfective":
      return findBest((s) => s.includes("remote past"));
    case "imperfective":
      return findBest((s) => s.includes("habitual"));
    case "imperative":
      return findBest((s) => s.includes("imperative"));
    case "infinitive":
      return findBest((s) => s.includes("infinitive"));
    default:
      return null;
  }
}

export interface RootGroup {
  h_grade_root: string;
  glottal_grade_root: string | null;
  slug: string;
  classes: {
    class_name: string;
    verbs: (ReconstructableVerb & { id: number })[];
  }[];
}

export interface EndingGroup {
  endings: Record<string, string>;
  slug: string;
  roots: {
    h_grade_root: string;
    glottal_grade_root: string | null;
    root_slug: string;
    configs: {
      class_name: string;
      verbs: (ReconstructableVerb & { id: number })[];
    }[];
  }[];
}

export interface DerivationalConnection {
  user_approved: string;
  from_root_id: string;
  from_h_grade: string;
  from_g_grade: string;
  from_class: string;
  from_stem_type: string;
  from_corpus_ids: string;
  to_root_id: string;
  to_h_grade: string;
  to_g_grade: string;
  to_class: string;
  to_stem_type: string;
  to_corpus_ids: string;
  to_form_type: string;
  to_stem: string;
}

export function normalize(s: string) {
  if (!s) return "";
  return s.trim().toLowerCase().replace(/['’]/g, "'");
}

export function toBase64Url(str: string): string {
  // Browser-safe base64url for UTF-8
  const utf8Bytes = new TextEncoder().encode(str);
  const binString = String.fromCodePoint(...utf8Bytes);
  return btoa(binString)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export function getEndingSlug(endings: Record<string, string>): string {
  const endingKeys = [
    "present",
    "imperfective",
    "perfective",
    "imperative",
    "infinitive",
  ];
  const key = endingKeys.map((k) => endings[k] || "").join("|");
  return toBase64Url(key);
}

export function getMorphemeSlug(name: string): string {
  return toBase64Url(name);
}

export function getPronominalSetName(
  formName: string,
  config: PronominalConfig,
): string | null {
  const { set_type, use_3rd_person_object } = config;

  if (formName === "present" || formName === "imperfective") {
    return ["Set A", "a"].includes(set_type) ? "3rd Set A" : "3rd Set B";
  }
  if (formName === "perfective" || formName === "infinitive") {
    return "3rd Set B";
  }
  if (formName === "imperative") {
    return use_3rd_person_object
      ? "2nd to 3rd"
      : ["Set A", "a"].includes(set_type)
        ? "2nd Set A"
        : "2nd Set B";
  }
  if (formName === "present_1sg") {
    return use_3rd_person_object
      ? "1st to 3rd"
      : ["Set A", "a"].includes(set_type)
        ? "1st Set A"
        : "1st Set B";
  }
  return null;
}

export function resolveClassEndings(
  classNameFull: string,
  classes: ClassDefinition[],
) {
  const match = classNameFull.match(/^([^\[]+)(?:\[(.*)\])?$/);
  if (!match) return null;

  const baseClassName = match[1];
  const modifiersStr = match[2];

  const classDef = classes.find(
    (c) =>
      c.macro_name === baseClassName ||
      (c.subclass
        ? `${c.class}-${c.subclass}` === baseClassName
        : c.class === baseClassName),
  );

  if (!classDef) return null;

  const result: Record<string, string> = { ...classDef };

  const columns = [
    "present",
    "imperfective",
    "perfective",
    "imperative",
    "infinitive",
  ];

  const overrides: Record<string, number> = {};

  if (modifiersStr) {
    const mods = modifiersStr.split("-");
    mods.forEach((mod) => {
      if (mod.startsWith("perf"))
        overrides["perfective"] = parseInt(mod.replace("perf", ""), 10);
      if (mod.startsWith("inf"))
        overrides["infinitive"] = parseInt(mod.replace("inf", ""), 10);
      if (mod.startsWith("imp"))
        overrides["imperative"] = parseInt(mod.replace("imp", ""), 10);
    });
  }

  columns.forEach((col) => {
    const options = (classDef[col as keyof ClassDefinition] || "").split(";");
    const index = (overrides[col] || 1) - 1;
    if (index >= 0 && index < options.length) {
      result[col] = options[index];
    } else {
      result[col] = options[0];
    }
  });

  return result;
}
