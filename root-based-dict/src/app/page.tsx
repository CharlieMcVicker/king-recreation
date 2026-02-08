import { getRoots } from "@/lib/data";
import RootSearch from "@/components/RootSearch";

export default async function RootsPage() {
  const roots = await getRoots();

  return (
    <div className="max-w-5xl mx-auto py-8">
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Root Dictionary
          </h1>
          <p className="text-gray-500 dark:text-zinc-400">
            Browse Cherokee verb roots and their associated reconstructable
            verbs.
          </p>
        </div>

        <RootSearch initialRoots={roots} />
      </div>
    </div>
  );
}
