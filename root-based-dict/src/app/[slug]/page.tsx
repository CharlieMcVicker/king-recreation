import { getRootBySlug, getClasses, getDictionaryEntries } from "@/lib/data";
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
  const entryNos = new Set(
    rootGroup.verbs.map((v) => v.entry_no).filter(Boolean),
  );
  const rootDictionary = dictionary.filter((e) =>
    entryNos.has(Number(e["No."])),
  );

  return (
    <RootDetailContent
      rootGroup={rootGroup}
      classes={classes}
      dictionary={rootDictionary}
    />
  );
}
