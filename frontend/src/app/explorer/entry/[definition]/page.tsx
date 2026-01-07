import { getClasses, getMatches, getCorpus } from "@/lib/data";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import EntryExplorer from "@/components/EntryExplorer";

export default async function EntryPage({ params }: { params: Promise<{ definition: string }> }) {
  const { definition } = await params;
  const decodedDef = decodeURIComponent(definition);

  const [classes, allMatches, corpus] = await Promise.all([
    getClasses(),
    getMatches(),
    getCorpus()
  ]);

  const corpusEntry = corpus.find((c: any) => c.definition === decodedDef);

  if (!corpusEntry) {
    return notFound();
  }

  const entryMatches = allMatches.filter((m: any) => m.definition === decodedDef);

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-gray-200 dark:border-zinc-800 pb-6">
        <Link 
            href="/explorer" 
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors w-fit"
        >
            <ArrowLeft className="w-4 h-4" />
            Back to Class Explorer
        </Link>
        <div>
            <div className="flex items-center gap-3 mb-2">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded">Lexical Entry</span>
                {entryMatches.length > 0 ? (
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded uppercase tracking-wider">
                        {entryMatches.length} Matches Found
                    </span>
                ) : (
                    <span className="text-xs font-bold text-red-600 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded uppercase tracking-wider">
                        No Matches
                    </span>
                )}
            </div>
            <h1 className="text-2xl md:text-3xl font-serif font-bold text-gray-900 dark:text-white leading-tight">
                {decodedDef}
            </h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0">
         <EntryExplorer matches={entryMatches} classes={classes} corpusEntry={corpusEntry} />
      </div>
    </div>
  );
}
