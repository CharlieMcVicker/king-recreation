import {
  getMorphemeGroupBySlug,
  getClasses,
  getDictionaryEntries,
} from "@/lib/data";
import { notFound } from "next/navigation";
import MorphemeDetailContent from "@/components/morphemes/MorphemeDetailContent";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function MorphemeDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const group = await getMorphemeGroupBySlug(slug);

  if (!group) {
    notFound();
  }

  const [classes, dictionary] = await Promise.all([
    getClasses(),
    getDictionaryEntries(),
  ]);

  return (
    <MorphemeDetailContent
      group={group}
      classes={classes}
      dictionary={dictionary}
    />
  );
}
