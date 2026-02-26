import { getRootIdsRows } from "@/lib/data";
import { redirect } from "next/navigation";

export default async function ReviewRootIdsIndexPage() {
  const rootIdsData = await getRootIdsRows();

  // Find first unreviewed, or just the first if all reviewed
  const firstUnreviewed = rootIdsData.find((r) => !r.user_edited);
  const targetId = firstUnreviewed
    ? firstUnreviewed.corpus_id
    : rootIdsData[0]?.corpus_id;

  if (targetId !== undefined) {
    redirect(`/review-root-ids/${targetId}`);
  }

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <p className="text-zinc-500">No data available for review.</p>
    </div>
  );
}
