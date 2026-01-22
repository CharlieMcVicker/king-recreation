import { getReconstructableVerbs, getCorpus } from "@/lib/data";
import ClassBrowser from "@/components/ClassBrowser";

export default async function ClassesPage() {
  const [verbs, corpus] = await Promise.all([
    getReconstructableVerbs(),
    getCorpus(),
  ]);

  // Create a lookup for corpus entries
  const corpusMap = new Map();
  corpus.forEach((entry) => {
    if (entry.corpus_id) {
      corpusMap.set(entry.corpus_id, entry);
    }
  });

  // Group verbs by macro-class
  const verbsByClass: Record<string, any[]> = {};

  verbs.forEach((verb) => {
    // Parse class name (e.g., "go[perf2-inf2]")
    const match = verb.class_name.match(/^([^\[]+)(?:\[(.*)\])?$/);
    const macroClass = match ? match[1] : verb.class_name;
    const subvariant = match && match[2] ? `[${match[2]}]` : "";

    if (!verbsByClass[macroClass]) {
      verbsByClass[macroClass] = [];
    }

    const corpusEntry = verb.corpus_id ? corpusMap.get(verb.corpus_id) : null;

    verbsByClass[macroClass].push({
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

  // Sort verbs within each class by definition for consistent display
  Object.keys(verbsByClass).forEach((key) => {
    verbsByClass[key].sort((a, b) => a.subvariant.localeCompare(b.subvariant));
  });

  return <ClassBrowser data={verbsByClass} />;
}
