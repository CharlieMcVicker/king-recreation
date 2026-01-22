import { getReconstructableVerbs, getCorpus, getClassLookup } from "@/lib/data";
import ClassBrowser from "@/components/ClassBrowser";

export default async function ClassesPage() {
  const [verbs, corpus, classLookup] = await Promise.all([
    getReconstructableVerbs(),
    getCorpus(),
    getClassLookup(),
  ]);

  // Create a lookup for corpus entries
  const corpusMap = new Map();
  corpus.forEach((entry: any) => {
    if (entry.corpus_id) {
      corpusMap.set(entry.corpus_id, entry);
    }
  });

  // Group verbs by abstract class -> macro class
  const verbsByHierarchy: Record<string, Record<string, any[]>> = {};

  verbs.forEach((verb: any) => {
    // Parse class name (e.g., "go[perf2-inf2]")
    const match = verb.class_name.match(/^([^\[]+)(?:\[(.*)\])?$/);
    const macroClass = match ? match[1] : verb.class_name;
    const subvariant = match && match[2] ? `[${match[2]}]` : "";

    // Resolve abstract class
    const classDef = classLookup.get(macroClass);
    const abstractClass = classDef ? classDef.class : macroClass;

    if (!verbsByHierarchy[abstractClass]) {
      verbsByHierarchy[abstractClass] = {};
    }
    if (!verbsByHierarchy[abstractClass][macroClass]) {
      verbsByHierarchy[abstractClass][macroClass] = [];
    }

    const corpusEntry = verb.corpus_id ? corpusMap.get(verb.corpus_id) : null;

    verbsByHierarchy[abstractClass][macroClass].push({
      definition: verb.definition,
      h_grade_root: verb.h_grade_root,
      subvariant: subvariant,
      corpusForms: {
        present: corpusEntry?.present || "",
        present_1sg: corpusEntry?.present_1sg || "",
        imperfective: corpusEntry?.imperfective || "",
        perfective: corpusEntry?.perfective || "",
        imperative: corpusEntry?.imperative || "",
        infinitive: corpusEntry?.infinitive || "",
      },
    });
  });

  // Sort verbs within each group
  Object.keys(verbsByHierarchy).forEach((abstractKey) => {
    Object.keys(verbsByHierarchy[abstractKey]).forEach((macroKey) => {
      verbsByHierarchy[abstractKey][macroKey].sort((a, b) =>
        a.subvariant.localeCompare(b.subvariant)
      );
    });
  });

  return <ClassBrowser data={verbsByHierarchy} />;
}
