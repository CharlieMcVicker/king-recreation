import { NextResponse } from "next/server";
import { updateRootId, searchRootIds, getRootIdsRows } from "@/lib/data";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const search = searchParams.get("search");
  const corpusId = searchParams.get("corpusId");

  if (search) {
    const results = await searchRootIds(search);
    return NextResponse.json(results);
  }

  if (corpusId) {
    const id = parseInt(corpusId, 10);
    const rows = await getRootIdsRows();
    const row = rows.find((r) => r.corpus_id === id);
    return NextResponse.json(row || null);
  }

  const rows = await getRootIdsRows();
  return NextResponse.json(rows);
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { corpusId, rootId } = body;

    if (typeof corpusId !== "number" || typeof rootId !== "string") {
      return NextResponse.json(
        { error: "Invalid request body. corpusId and rootId are required." },
        { status: 400 },
      );
    }

    await updateRootId(corpusId, rootId);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating root ID:", error);
    return NextResponse.json(
      { error: "Failed to update root ID" },
      { status: 500 },
    );
  }
}
