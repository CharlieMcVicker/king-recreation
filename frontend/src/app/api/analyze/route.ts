import { NextRequest, NextResponse } from "next/server";
import { execFile } from "child_process";
import path from "path";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const definition = searchParams.get("definition");

  if (!definition) {
    return NextResponse.json(
      { error: "Definition parameter is required" },
      { status: 400 }
    );
  }

  const projectRoot = path.resolve(process.cwd(), "..");
  const pythonPath = path.join(projectRoot, ".venv", "bin", "python3");

  return new Promise<NextResponse>((resolve) => {
    execFile(
      pythonPath,
      ["-m", "king_recreation.analyze_failure", definition],
      { cwd: projectRoot },
      (error, stdout, stderr) => {
        if (error) {
          console.error("Python script error:", error);
          console.error("Stderr:", stderr);
          resolve(
            NextResponse.json(
              { error: "Failed to analyze definition", details: stderr },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const data = JSON.parse(stdout);
          resolve(NextResponse.json(data));
        } catch (parseError) {
          console.error("JSON parse error:", parseError);
          resolve(
            NextResponse.json(
              { error: "Invalid response from analysis script", output: stdout },
              { status: 500 }
            )
          );
        }
      }
    );
  });
}
