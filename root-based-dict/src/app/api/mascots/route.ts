import { NextResponse } from "next/server";
import {
  getAspectClassMascots,
  updateAspectClassMascot,
  getRoots,
  getAllVerbsFromRoots,
  getValidatedRootsRows,
  getDictionaryEntries,
} from "@/lib/data";
import { DictionaryEntry } from "@/lib/data-shared";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const className = searchParams.get("className") || searchParams.get("class_name");
    const previewCorpusId = searchParams.get("previewCorpusId");

    // If requesting paradigm preview for a specific verb candidate:
    if (previewCorpusId) {
      const cid = Number(previewCorpusId);
      const roots = await getRoots();
      const allVerbs = getAllVerbsFromRoots(roots);
      const dictionary = await getDictionaryEntries();

      let verb = allVerbs.find((v) => Number(v.meta.corpus_id) === cid);
      let definition = verb?.meta.definition;
      let verb_class = verb?.morphology.class_name;
      let prediction = verb?.meta.prediction;
      let entryNo = verb?.meta.entry_no ? Number(verb.meta.entry_no) : undefined;

      if (!verb) {
        const validatedRows = await getValidatedRootsRows({ includeShims: true });
        const verbRows = validatedRows.filter((r) => Number(r.meta.corpus_id) === cid);
        if (verbRows.length === 0) {
          return NextResponse.json({ error: "Corpus ID not found" }, { status: 404 });
        }
        const userSelected = verbRows.find((r) => r.curation.user_selected === "x");
        const pipelineSelected = verbRows.find((r) => r.curation.pipeline_selected === "x");
        const canonical = userSelected || pipelineSelected || verbRows[0];

        definition = canonical.meta.definition;
        verb_class = canonical.aspect.verb_class;
        prediction = canonical.meta.prediction;
        entryNo = canonical.meta.entry_no ? Number(canonical.meta.entry_no) : undefined;
      }

      const getFormDetail = (formKey: string) => {
        if (!entryNo) return { syllabary: "---", practical: "---" };
        const group = dictionary.filter((e) => Number(e["No."]) === entryNo);
        if (group.length === 0) return { syllabary: "---", practical: "---" };

        const matches = (predicate: (sub: string) => boolean) => {
          return group.filter((e) => predicate((e["Grammar sub entry"] || "").toLowerCase()));
        };

        let foundEntries: DictionaryEntry[] = [];
        switch (formKey) {
          case "present":
            foundEntries = matches(
              (s) =>
                s.startsWith("3rd person singular") &&
                !s.includes("habitual") &&
                !s.includes("past") &&
                !s.includes("infinitive"),
            );
            break;
          case "present_1sg":
            foundEntries = matches((s) => s.startsWith("1st person singular"));
            break;
          case "perfective":
            foundEntries = matches((s) => s.includes("remote past"));
            break;
          case "imperfective":
            foundEntries = matches((s) => s.includes("habitual"));
            break;
          case "imperative":
            foundEntries = matches((s) => s.includes("imperative"));
            break;
          case "infinitive":
            foundEntries = matches((s) => s.includes("infinitive"));
            break;
        }

        if (foundEntries.length === 0) return { syllabary: "---", practical: "---" };

        const getPriority = (row: DictionaryEntry) => {
          const sub = (row["Grammar sub entry"] || "").toLowerCase();
          if (sub.includes("animate") && !sub.includes("inanimate")) return 3;
          if (sub.includes("animate")) return 2;
          if (sub.includes("inanimate")) return 1;
          return 0;
        };

        foundEntries.sort((a, b) => getPriority(b) - getPriority(a));
        const best = foundEntries[0];
        return {
          syllabary: best.Syllabary || "---",
          practical: best.Practical || "---",
        };
      };

      const forms = {
        present: getFormDetail("present"),
        present_1sg: getFormDetail("present_1sg"),
        imperfective: getFormDetail("imperfective"),
        perfective: getFormDetail("perfective"),
        imperative: getFormDetail("imperative"),
        infinitive: getFormDetail("infinitive"),
      };

      return NextResponse.json({
        corpus_id: cid,
        definition,
        verb_class,
        prediction,
        forms,
      });
    }

    const roots = await getRoots();
    const allVerbs = getAllVerbsFromRoots(roots);
    const curatedMascots = await getAspectClassMascots();

    // Map existing mascot assignments
    const mascotMap = new Map<string, number | null>();
    curatedMascots.forEach((m) => {
      const fullKey = m.subclass ? `${m.class}-${m.subclass}` : m.class;
      const cid =
        m.mascot_corpus_id !== null && m.mascot_corpus_id !== undefined && m.mascot_corpus_id !== ""
          ? Number(m.mascot_corpus_id)
          : null;
      if (fullKey) mascotMap.set(fullKey, cid);
      if (m.class) mascotMap.set(m.class, cid);
    });

    // If filtering candidates for a specific class name:
    if (className) {
      const candidateMap = new Map<
        number,
        { corpus_id: number; definition: string; verb_class: string; entry_no: any }
      >();

      allVerbs.forEach((v) => {
        if (v.morphology?.class_name === className) {
          const cid = Number(v.meta.corpus_id);
          if (!isNaN(cid) && !candidateMap.has(cid)) {
            candidateMap.set(cid, {
              corpus_id: cid,
              definition: v.meta.definition,
              verb_class: v.morphology.class_name,
              entry_no: v.meta.entry_no,
            });
          }
        }
      });

      const candidates = Array.from(candidateMap.values()).sort((a, b) => a.corpus_id - b.corpus_id);
      const mascotCorpusId = mascotMap.get(className) ?? null;

      return NextResponse.json({ candidates, mascotCorpusId });
    }

    // Default: return all unique morphology.class_name strings directly from hierarchical-dict.json
    const candidateCounts = new Map<string, number>();

    allVerbs.forEach((v) => {
      const cName = v.morphology?.class_name;
      if (cName) {
        candidateCounts.set(cName, (candidateCounts.get(cName) || 0) + 1);
      }
    });

    const uniqueClassNames = Array.from(candidateCounts.keys()).sort((a, b) => a.localeCompare(b));

    const resultClasses = uniqueClassNames.map((cName) => {
      const plainMascotId = mascotMap.get(cName) ?? null;
      return {
        class_name: cName,
        mascot_corpus_id: plainMascotId,
        candidate_count: candidateCounts.get(cName) || 0,
      };
    });

    return NextResponse.json({ classes: resultClasses });
  } catch (error) {
    console.error("Error in GET /api/mascots:", error);
    return NextResponse.json({ error: "Failed to fetch mascot data" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const className = body.className || body.class_name;
    const mascotCorpusId = body.mascotCorpusId !== undefined ? body.mascotCorpusId : body.mascot_corpus_id;

    if (!className) {
      return NextResponse.json(
        { error: "Invalid request body. class_name is required." },
        { status: 400 },
      );
    }

    const cid =
      mascotCorpusId !== null && mascotCorpusId !== undefined && mascotCorpusId !== ""
        ? Number(mascotCorpusId)
        : null;

    await updateAspectClassMascot(className, "", "Plain", cid);

    return NextResponse.json({ success: true, class_name: className, mascotCorpusId: cid });
  } catch (error) {
    console.error("Error updating mascot assignment:", error);
    return NextResponse.json(
      { error: "Failed to update mascot assignment" },
      { status: 500 },
    );
  }
}
