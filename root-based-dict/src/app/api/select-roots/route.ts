import { NextResponse } from "next/server";
import { updateUserSelection } from "@/lib/data";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { corpusId, originalIndex } = body;

    if (typeof corpusId !== "number" || typeof originalIndex !== "number") {
      return NextResponse.json(
        { error: "Invalid request body. corpusId and originalIndex are required." },
        { status: 400 },
      );
    }

    await updateUserSelection(corpusId, originalIndex);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating user selection:", error);
    return NextResponse.json(
      { error: "Failed to update selection" },
      { status: 500 },
    );
  }
}
