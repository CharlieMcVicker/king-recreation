import { NextResponse } from "next/server";
import {
  updateDerivationalConnection,
  getDerivationalConnectionsForCorpus,
} from "@/lib/data";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const corpusId = searchParams.get("corpusId");

  if (corpusId) {
    const id = parseInt(corpusId, 10);
    const results = await getDerivationalConnectionsForCorpus(id);
    return NextResponse.json(results);
  }

  return NextResponse.json({ error: "corpusId required" }, { status: 400 });
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { key, approved } = body;

    if (!key) {
      return NextResponse.json({ error: "Missing key" }, { status: 400 });
    }

    await updateDerivationalConnection(key, approved);

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error("Error updating derivational connection:", error);
    return NextResponse.json(
      { error: error.message || "Internal server error" },
      { status: 500 },
    );
  }
}
