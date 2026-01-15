import React from "react";
import { getReconstructableVerbs } from "@/lib/data";
import { VerbList } from "./VerbList";

export default async function ReconstructableVerbsPage() {
  const verbs = await getReconstructableVerbs();

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Reconstructable Verbs
        </h1>
        <p className="text-gray-500 dark:text-zinc-400">
          Explore {verbs.length} successfully reconstructed verbs, their
          classes, and corpus forms.
        </p>
      </div>

      <VerbList verbs={verbs} />
    </div>
  );
}
