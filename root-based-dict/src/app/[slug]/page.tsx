import {
  getRootBySlug,
  getClasses,
  getDictionaryEntries,
  getConnections,
  getReconstructableVerbs,
  getRootIdsRows,
} from "@/lib/data";
import RootDetailContent from "@/components/roots/RootDetailContent";
import Link from "next/link";

export default async function RootDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const rootGroup = await getRootBySlug(slug);
  const classes = await getClasses();
  const connections = await getConnections();
  const allVerbs = await getReconstructableVerbs();

  if (!rootGroup) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <h2 className="text-2xl font-bold">Root not found</h2>
        <Link
          href="/"
          className="text-indigo-600 hover:underline mt-4 inline-block"
        >
          Return to Dictionary
        </Link>
      </div>
    );
  }

  const dictionary = await getDictionaryEntries();

  const entryNos = new Set<number>();
  const collectEntryNos = (group: any) => {
    group.classes.forEach((c: any) => {
      c.verbs.forEach((v: any) => {
        const entryNo = v.meta?.entry_no ?? v.entry_no;
        if (entryNo) entryNos.add(Number(entryNo));
      });
    });
  };

  collectEntryNos(rootGroup);

  // Also include entry numbers for connected verbs
  const allRootVerbs = rootGroup.classes.flatMap((c) => c.verbs);
  const rootCorpusIds = new Set(
    allRootVerbs
      .map((v) => Number(v.meta.corpus_id))
      .filter((id) => !isNaN(id)),
  );

  const relevantConnections = connections.filter((conn) => {
    const toIds = String(conn.to_corpus_ids)
      .split(";")
      .map((id) => parseInt(id.trim(), 10));
    return toIds.some((id) => rootCorpusIds.has(id));
  });

  const connectedCorpusIds = new Set<number>();
  relevantConnections.forEach((conn) => {
    String(conn.from_corpus_ids)
      .split(";")
      .forEach((s) => {
        const id = parseInt(s.trim(), 10);
        if (!isNaN(id)) connectedCorpusIds.add(id);
      });
  });

  const connectedVerbs = allVerbs.filter(
    (v) => v.meta.corpus_id !== null && connectedCorpusIds.has(Number(v.meta.corpus_id)),
  );

  connectedVerbs.forEach((v) => {
    if (v.meta.entry_no) entryNos.add(Number(v.meta.entry_no));
  });

  const rootDictionary = dictionary.filter((e) =>
    entryNos.has(Number(e["No."])),
  );

  const rootIdsRows = await getRootIdsRows();
  const rootIdGroup =
    rootIdsRows.find((row) => rootCorpusIds.has(row.corpus_id))?.root_id ||
    null;

  return (
    <RootDetailContent
      rootGroup={rootGroup}
      classes={classes}
      dictionary={rootDictionary}
      connections={connections}
      allVerbs={allVerbs}
      rootIdGroup={rootIdGroup}
    />
  );
}
