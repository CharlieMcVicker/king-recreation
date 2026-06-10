import { getValidatedRootsRows, getStativeShims, getDictionaryEntries } from "@/lib/data";
import { getCorpusForm } from "@/lib/data-shared";
import ReviewStativeShims from "@/components/ReviewStativeShims";

export default async function ReviewStativeShimsPage() {
  const allValidatedRows = await getValidatedRootsRows();
  const currentShims = await getStativeShims();
  const dictionary = await getDictionaryEntries();

  // Group rows by corpus_id
  const rowsByCorpusId = new Map<number, any[]>();
  allValidatedRows.forEach((r) => {
    const cid = Number(r.meta.corpus_id);
    if (!rowsByCorpusId.has(cid)) rowsByCorpusId.set(cid, []);
    rowsByCorpusId.get(cid)!.push(r);
  });

  const stativeVerbs: any[] = [];
  rowsByCorpusId.forEach((rows, cid) => {
    const userSelected = rows.find((r) => r.curation.user_selected === "x");
    const pipelineSelected = rows.find((r) => r.curation.pipeline_selected === "x");
    const canonical = userSelected || pipelineSelected || rows[0];

    if (canonical && canonical.meta.prediction === "FullStative") {
      const entryNo = canonical.meta.entry_no ? Number(canonical.meta.entry_no) : undefined;
      const dictInfinitive = getCorpusForm(dictionary, entryNo, "infinitive");
      if (!dictInfinitive || dictInfinitive.trim() === "" || dictInfinitive === "-") {
        return;
      }

      const shims = allValidatedRows.filter((r) => {
        if (r.meta.prediction !== "InfEventful") return false;
        if (r.roots.h_grade !== canonical.roots.h_grade) return false;

        // glottal_grade_root (g_grade): must match unless either side is null/empty/undefined
        const baseG = canonical.roots.g_grade;
        const shimG = r.roots.g_grade;
        if (
          baseG !== null && baseG !== undefined && baseG !== "" &&
          shimG !== null && shimG !== undefined && shimG !== "" &&
          baseG !== shimG
        ) {
          return false;
        }

        // middle_voice: must match
        if (canonical.config.pron.middle_voice !== r.config.pron.middle_voice) {
          return false;
        }

        // plural_pronouns (plural): must match
        if (canonical.config.pron.plural_pronouns !== r.config.pron.plural_pronouns) {
          return false;
        }

        return true;
      });
      
      // Find currently selected shim in stative_shims.csv
      const currentShim = currentShims.find((s) => Number(s.corpus_id) === cid);

      stativeVerbs.push({
        canonical,
        shims,
        currentShim: currentShim || null,
      });
    }
  });

  // Sort by corpus_id
  stativeVerbs.sort((a, b) => Number(a.canonical.meta.corpus_id) - Number(b.canonical.meta.corpus_id));

  return (
    <div className="container mx-auto p-4">
      <ReviewStativeShims initialStativeVerbs={stativeVerbs} dictionary={dictionary} />
    </div>
  );
}
