import type { Metadata } from "next";
import { getRootIdsRows } from "@/lib/data";
import RootGroupEditor from "@/components/RootGroupEditor";
import { notFound } from "next/navigation";

export const metadata: Metadata = {
  title: "Group Edit Root IDs | King Match Explorer",
  description: "Bulk edit interface for root_id groups",
};

export default async function RootGroupPage({
  params,
}: {
  params: Promise<{ rootIdEncoded: string }>;
}) {
  const { rootIdEncoded } = await params;

  // Try to decode. It's base64url.
  let rootId = "";
  try {
    const buffer = Buffer.from(rootIdEncoded, "base64url");
    rootId = buffer.toString("utf-8");
  } catch (e) {
    notFound();
  }

  const rootIdsData = await getRootIdsRows();

  // Verify the group exists
  const exists = rootIdsData.some((r) => r.root_id === rootId);
  if (!exists && rootId !== "") {
    // "" might be a valid starting point for unassigned
    // If it doesn't exist, we might still want to allow viewing "empty" or unassigned
    // but usually we redirect here from an existing ID.
  }

  return (
    <main className="container mx-auto py-8 px-4">
      <RootGroupEditor initialData={rootIdsData} rootId={rootId} />
    </main>
  );
}
