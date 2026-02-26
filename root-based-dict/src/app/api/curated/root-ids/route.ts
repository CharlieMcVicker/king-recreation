import { NextResponse } from "next/server";
import { updateRootId } from "@/lib/data";

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
