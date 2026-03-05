import type { Metadata } from "next";
import { getValidatedRootsRows } from "@/lib/data";
import { notFound } from "next/navigation";
import LexicalHero from "@/components/LexicalHero";
import RootAssignmentPanel from "@/components/RootAssignmentPanel";
import DerivationsPanel from "@/components/DerivationsPanel";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";

export const metadata: Metadata = {
  title: "Lexical Review | King Match Explorer",
  description:
    "Unified dashboard for root assignments and derivational context.",
};

export default async function LexicalReviewPage({
  params,
}: {
  params: Promise<{ corpusId: string }>;
}) {
  const { corpusId } = await params;
  const id = parseInt(corpusId, 10);

  if (isNaN(id)) {
    notFound();
  }

  const allRootsData = await getValidatedRootsRows();
  const derivations = allRootsData.filter((r) => r.corpus_id === id);

  if (derivations.length === 0) {
    notFound();
  }

  return (
    <main className="max-w-6xl mx-auto space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/select-roots"
          className="flex items-center gap-2 text-sm font-medium text-zinc-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Root Selection
        </Link>

        <Link
          href={`/select-roots?corpusId=${id}`}
          className="flex items-center gap-2 text-sm font-medium text-zinc-500 hover:text-indigo-600 transition-colors"
        >
          Open in Root Selection
          <ExternalLink className="w-4 h-4" />
        </Link>
      </div>

      <div className="space-y-6">
        <LexicalHero data={derivations} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <RootAssignmentPanel corpusId={id} />
          <DerivationsPanel corpusId={id} />
        </div>
      </div>

      <div className="bg-amber-50 dark:bg-amber-900/10 rounded-xl p-4 border border-amber-100 dark:border-amber-900/20">
        <p className="text-xs text-amber-800 dark:text-amber-400 leading-relaxed font-medium">
          <strong>Reviewer Tip:</strong> Use the "Peer Groups" list in the Root
          Assignment panel to ensure you aren't creating orphan root groups. If
          you change a Root ID, all words in that group will be updated once
          processed by the pipeline.
        </p>
      </div>
    </main>
  );
}
