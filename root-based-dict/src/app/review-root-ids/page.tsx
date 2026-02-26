import { getRootIdsRows } from "@/lib/data";
import { redirect } from "next/navigation";
import { toBase64Url } from "@/lib/data-shared";

export default async function ReviewRootIdsIndexPage() {
  const rootIdsData = await getRootIdsRows();

  if (rootIdsData.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <p className="text-zinc-500">No data available for review.</p>
      </div>
    );
  }

  // Get all unique root IDs and sort them
  const groups = new Set<string>();
  rootIdsData.forEach((row) => {
    groups.add((row.root_id || "").trim());
  });

  const sortedRootIds = Array.from(groups).sort((a, b) => {
    if (a === "" || a === "|") return -1;
    if (b === "" || b === "|") return 1;
    return a.localeCompare(b);
  });

  // Start with the first group
  const targetId = sortedRootIds[0];
  redirect(`/review-root-ids/groups/${toBase64Url(targetId)}`);
}
