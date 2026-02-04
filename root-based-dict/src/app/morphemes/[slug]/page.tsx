import { getMorphemeGroupBySlug } from "@/lib/data";
import Link from "next/link";
import { ChevronLeft, ArrowRight } from "lucide-react";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function MorphemeDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const group = await getMorphemeGroupBySlug(slug);

  if (!group) {
    notFound();
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <Link
        href="/morphemes"
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 dark:text-zinc-400 dark:hover:text-indigo-400 transition-colors mb-6 group w-fit"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to morphemes
      </Link>

      <div className="mb-12">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2 capitalize">
          {group.name.replace(/-/g, " ")}
        </h1>
        <p className="text-lg text-gray-500 dark:text-zinc-400">
          Viewing {group.total_roots} roots with the "{group.name}" post-root
          morpheme.
        </p>
      </div>

      <div className="flex flex-col gap-12">
        {group.subcases.map((subcase) => (
          <div key={subcase.subcase}>
            <h2 className="text-xl font-bold text-gray-800 dark:text-zinc-200 mb-6 flex items-center gap-3">
              <span className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                {subcase.subcase === "default"
                  ? "Standard Form"
                  : `Subcase: ${subcase.subcase}`}
              </span>
              <div className="h-px flex-1 bg-gray-100 dark:bg-zinc-800" />
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {subcase.roots.map((root) => {
                const verbCount = root.classes.reduce(
                  (acc, cls) => acc + cls.verbs.length,
                  0,
                );
                return (
                  <Link
                    key={root.slug}
                    href={`/${root.slug}`}
                    className="group bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-6 hover:border-indigo-500 dark:hover:border-indigo-400 transition-all shadow-sm flex flex-col items-center text-center"
                  >
                    <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {root.h_grade_root}
                    </div>
                    {root.glottal_grade_root && (
                      <div className="text-sm text-gray-500 dark:text-zinc-500 italic">
                        ({root.glottal_grade_root})
                      </div>
                    )}
                    <div className="mt-4 text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {verbCount} {verbCount === 1 ? "verb" : "verbs"}
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
