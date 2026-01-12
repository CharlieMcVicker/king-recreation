import { execFile } from "child_process";
import path from "path";

export async function analyzeDefinition(definition: string): Promise<any> {
  const projectRoot = path.resolve(process.cwd(), "..");
  const pythonPath = path.join(projectRoot, ".venv", "bin", "python3");

  return new Promise((resolve, reject) => {
    execFile(
      pythonPath,
      ["-m", "king_recreation.analyze_failure", definition],
      { cwd: projectRoot },
      (error, stdout, stderr) => {
        if (error) {
          console.error("Python script error:", error);
          console.error("Stderr:", stderr);
          reject(new Error(stderr || error.message));
          return;
        }

        try {
          const data = JSON.parse(stdout);
          resolve(data);
        } catch (parseError) {
          console.error("JSON parse error:", parseError);
          reject(new Error("Invalid response from analysis script"));
        }
      }
    );
  });
}
