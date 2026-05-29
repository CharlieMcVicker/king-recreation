import { NextResponse } from "next/server";
import { updateStativeShim } from "@/lib/data";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { corpusId, rowIndex } = body;

    if (typeof corpusId !== "number") {
      return NextResponse.json(
        { error: "Invalid request body. corpusId is required as a number." },
        { status: 400 },
      );
    }

    if (typeof rowIndex !== "number") {
      return NextResponse.json(
        { error: "Invalid request body. rowIndex is required as a number." },
        { status: 400 },
      );
    }

    await updateStativeShim(corpusId, rowIndex);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating stative shim curation:", error);
    return NextResponse.json(
      { error: "Failed to update stative shim curation" },
      { status: 500 },
    );
  }
}
