import type { Metadata } from "next";
import { getAspectClassMascots, getRoots, getAllVerbsFromRoots } from "@/lib/data";
import MascotCurationClient from "@/components/MascotCurationClient";

export const metadata: Metadata = {
  title: "Curate Mascots | Root-based dictionary",
  description: "Select and validate aspect class mascots for dictionary paradigms.",
};

export default async function CurateMascotsPage() {
  const roots = await getRoots();
  const allVerbs = getAllVerbsFromRoots(roots);
  const curatedMascots = await getAspectClassMascots();

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

  const candidateCounts = new Map<string, number>();
  allVerbs.forEach((v) => {
    const cName = v.morphology?.class_name;
    if (cName) {
      candidateCounts.set(cName, (candidateCounts.get(cName) || 0) + 1);
    }
  });

  const uniqueClassNames = Array.from(candidateCounts.keys()).sort((a, b) => a.localeCompare(b));

  const initialClasses = uniqueClassNames.map((cName) => ({
    class_name: cName,
    mascot_corpus_id: mascotMap.get(cName) ?? null,
    candidate_count: candidateCounts.get(cName) || 0,
  }));

  return (
    <main className="max-w-7xl mx-auto">
      <MascotCurationClient initialClasses={initialClasses} />
    </main>
  );
}
