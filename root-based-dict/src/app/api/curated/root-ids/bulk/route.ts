import { NextResponse } from "next/server";
import { updateRootIdsBulk } from "@/lib/data";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { updates } = body;

    if (!Array.isArray(updates)) {
      return NextResponse.json(
        { error: "Invalid request body. 'updates' array is required." },
        { status: 400 },
      );
    }

    await updateRootIdsBulk(updates);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error bulk updating root IDs:", error);
    return NextResponse.json(
      { error: "Failed to update root IDs" },
      { status: 500 },
    );
  }
}
