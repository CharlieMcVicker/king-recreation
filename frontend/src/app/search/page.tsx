import { getCorpus } from "@/lib/data";
import SearchClient from "@/components/SearchClient";

export const dynamic = "force-dynamic";

export default async function SearchPage() {
  const corpus = await getCorpus();

  return (
    <div className="h-full">
      <SearchClient corpus={corpus} />
    </div>
  );
}
