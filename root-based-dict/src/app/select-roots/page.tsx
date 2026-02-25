import type { Metadata } from "next";
import { getValidatedRootsRows, getChangedVerbIds } from "@/lib/data";
import SelectRootsWorkflow from "@/components/SelectRootsWorkflow";

export const metadata: Metadata = {
  title: "Select Roots | King Match Explorer",
  description: "Workflow for selecting correct root forms",
};

export default async function SelectRootsPage({
  searchParams,
}: {
  searchParams: Promise<{ corpusId?: string }>;
}) {
  const { corpusId } = await searchParams;
  const [rootsData, changedVerbIds] = await Promise.all([
    getValidatedRootsRows(),
    getChangedVerbIds(),
  ]);

  return (
    <main className="container mx-auto py-8 px-4">
      <SelectRootsWorkflow
        initialData={rootsData}
        changedOptionsIds={changedVerbIds}
        initialCorpusId={corpusId ? parseInt(corpusId, 10) : undefined}
      />
    </main>
  );
}
