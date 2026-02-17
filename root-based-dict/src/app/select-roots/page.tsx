import type { Metadata } from "next";
import { getValidatedRootsRows } from "@/lib/data";
import SelectRootsWorkflow from "./select-roots-workflow";

export const metadata: Metadata = {
  title: "Select Roots | King Match Explorer",
  description: "Workflow for selecting correct root forms",
};

export default async function SelectRootsPage() {
  const rootsData = await getValidatedRootsRows();

  return (
    <main className="container mx-auto py-8 px-4">
      <SelectRootsWorkflow initialData={rootsData} />
    </main>
  );
}
