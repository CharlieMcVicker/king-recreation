import type { Metadata } from "next";
import { getRootIdsRows } from "@/lib/data";
import RootIdsEditor from "@/components/RootIdsEditor";
import { notFound } from "next/navigation";

export const metadata: Metadata = {
  title: "Review Root IDs | Root-based dictionary",
  description:
    "Sequential review interface for assigning and verifying root_id groupings",
};

export default async function ReviewRootIdDetailsPage({
  params,
}: {
  params: Promise<{ corpusId: string }>;
}) {
  const { corpusId } = await params;
  const id = parseInt(corpusId, 10);

  if (isNaN(id)) {
    notFound();
  }

  const rootIdsData = await getRootIdsRows();

  // Verify the ID exists
  const exists = rootIdsData.some((r) => r.corpus_id === id);
  if (!exists) {
    notFound();
  }

  return (
    <main className="container mx-auto py-8 px-4">
      <RootIdsEditor initialData={rootIdsData} currentCorpusId={id} />
    </main>
  );
}
