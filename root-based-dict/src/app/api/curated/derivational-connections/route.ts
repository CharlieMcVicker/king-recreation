import { NextResponse } from "next/server";
import { updateDerivationalConnection } from "@/lib/data";

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
