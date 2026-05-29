import { NextResponse } from "next/server";
import { updateStativeShim } from "@/lib/data";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { corpusId, shimKey } = body;

    if (typeof corpusId !== "number") {
      return NextResponse.json(
        { error: "Invalid request body. corpusId is required as a number." },
        { status: 400 },
      );
    }

    // shimKey can be null (to unbind) or an object containing the config keys
    await updateStativeShim(corpusId, shimKey);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating stative shim curation:", error);
    return NextResponse.json(
      { error: "Failed to update stative shim curation" },
      { status: 500 },
    );
  }
}
