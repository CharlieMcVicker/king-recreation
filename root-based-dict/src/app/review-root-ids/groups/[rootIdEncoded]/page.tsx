import type { Metadata } from "next";
import { getRootIdsRows } from "@/lib/data";
import RootGroupSequenceEditor from "@/components/RootGroupSequenceEditor";
import { notFound } from "next/navigation";
import { toBase64Url } from "@/lib/data-shared";

export const metadata: Metadata = {
  title: "Group Sequence Edit Root IDs | King Match Explorer",
  description: "Grouped review interface for root_id groups in sequence",
};

export default async function RootGroupSequencePage({
  params,
}: {
  params: Promise<{ rootIdEncoded: string }>;
}) {
  const { rootIdEncoded } = await params;

  // Try to decode. It's base64url.
  let currentRootId = "";
  try {
    const buffer = Buffer.from(rootIdEncoded, "base64url");
    currentRootId = buffer.toString("utf-8");
  } catch (e) {
    // If decoding fails, it might be that it's just "empty" or invalid
    // usually we'll handle this by redirecting to a valid one from the index.
  }

  const rootIdsData = await getRootIdsRows();

  // Pregroup by root_id to get the sequence of distinct IDs
  const groups = new Map<string, any[]>();
  rootIdsData.forEach((row) => {
    const rid = (row.root_id || "").trim();
    if (!groups.has(rid)) {
      groups.set(rid, []);
    }
    groups.get(rid)!.push(row);
  });

  // Sort distinct root IDs.
  // Maybe empty/pipes first, then alphabetical?
  const sortedRootIds = Array.from(groups.keys()).sort((a, b) => {
    // Put empty or "|" at the top
    if (a === "" || a === "|") return -1;
    if (b === "" || b === "|") return 1;
    return a.localeCompare(b);
  });

  const currentIndex = sortedRootIds.indexOf(currentRootId);
  if (currentIndex === -1 && currentRootId !== "") {
    // If not found and not empty, it's invalid
    // unless we allow creating new groups?
    // For now, let's just 404 if it's not in the data and not empty.
    // But wait, the user might have just changed all items out of this group.
  }

  const prevRootId = currentIndex > 0 ? sortedRootIds[currentIndex - 1] : null;
  const nextRootId =
    currentIndex < sortedRootIds.length - 1
      ? sortedRootIds[currentIndex + 1]
      : null;

  return (
    <main className="container mx-auto py-8 px-4">
      <RootGroupSequenceEditor
        initialData={rootIdsData}
        rootId={currentRootId}
        prevRootId={prevRootId}
        nextRootId={nextRootId}
        currentIndex={currentIndex}
        totalGroups={sortedRootIds.length}
      />
    </main>
  );
}
