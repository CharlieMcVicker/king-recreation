import {
  getEndingGroupBySlug,
  getClasses,
  getDictionaryEntries,
} from "@/lib/data";
import EndingDetailContent from "@/components/endings/EndingDetailContent";
import Link from "next/link";

export default async function EndingDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const endingGroup = await getEndingGroupBySlug(slug);
  const classes = await getClasses();

  if (!endingGroup) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <h2 className="text-2xl font-bold">Ending group not found</h2>
        <Link
          href="/endings"
          className="text-indigo-600 hover:underline mt-4 inline-block"
        >
          Return to Endings Dictionary
        </Link>
      </div>
    );
  }

  const dictionary = await getDictionaryEntries();

  return (
    <EndingDetailContent
      endingGroup={endingGroup}
      classes={classes}
      dictionary={dictionary}
    />
  );
}
